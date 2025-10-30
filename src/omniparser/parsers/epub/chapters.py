"""
Chapter extraction and processing module for EPUB parsing.

Handles TOC-based and spine-based chapter detection, with support for
position mapping, content extraction, and chapter post-processing.
"""

# Standard library
import logging
import re
from typing import Dict, List, Optional, Tuple

# Third-party
import ebooklib
from ebooklib import epub

# Local
from ...models import Chapter
from ...utils.html_extractor import HTMLTextExtractor
from .toc import TocEntry
from .utils import count_words, estimate_reading_time

logger = logging.getLogger(__name__)


def extract_content_and_chapters(
    book: epub.EpubBook,
    toc_entries: Optional[List[TocEntry]],
    options: Dict,
    warnings: List[str],
) -> Tuple[str, List[Chapter]]:
    """Extract full content and detect chapters.

    Routes to TOC-based or spine-based detection based on availability.
    Post-processes chapters to filter empty ones and handle duplicates.

    Args:
        book: EpubBook object.
        toc_entries: TOC entries if available, None otherwise.
        options: Parser configuration dictionary containing:
            - min_chapter_length: Minimum words per chapter (default: 100)
        warnings: List to append warnings to.

    Returns:
        Tuple of (full_content, chapters_list).
    """
    if toc_entries:
        logger.info("Using TOC-based chapter detection")
        content, chapters = extract_chapters_from_toc(book, toc_entries, warnings)
    else:
        logger.info("Using spine-based chapter detection (no TOC)")
        content, chapters = extract_chapters_from_spine(book, warnings)

    # Post-process chapters
    chapters = postprocess_chapters(chapters, options, warnings)

    return content, chapters


def extract_chapters_from_toc(
    book: epub.EpubBook, toc_entries: List[TocEntry], warnings: List[str]
) -> Tuple[str, List[Chapter]]:
    """Extract chapters using TOC-based detection.

    Maps TOC entries to spine items and creates chapter boundaries based on
    TOC structure. This is the preferred method as it respects the author's
    intended chapter divisions.

    Algorithm:
    1. Extract all spine items (reading order)
    2. Build position map: file_name -> position in full content
    3. Extract text from all spine items sequentially
    4. For each TOC entry:
       - Find start position from position map
       - Find end position from next TOC entry's position
       - Extract chapter content slice
       - Create Chapter object

    Args:
        book: EpubBook object.
        toc_entries: List of TOC entries from parse_toc().
        warnings: List to append warnings to.

    Returns:
        Tuple of (full_content, chapters_list).
    """
    # Get all spine items (reading order)
    spine_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

    if not spine_items:
        logger.warning("No spine items found in EPUB")
        return "", []

    # Build position map
    position_map = _build_position_map(spine_items, warnings)

    # Extract all text and build full content
    extractor = HTMLTextExtractor()
    full_content_parts: List[str] = []
    cumulative_length = 0

    for item in spine_items:
        try:
            # Get HTML content
            content_bytes = item.get_content()
            html_string = content_bytes.decode("utf-8", errors="ignore")

            # Extract text
            text = extractor.extract_text(html_string)

            # Record start position for this file
            file_name = item.get_name()
            position_map[(file_name, "")] = cumulative_length

            full_content_parts.append(text)
            cumulative_length += len(text)

            # Add spacing between spine items
            full_content_parts.append("\n\n")
            cumulative_length += 2

        except Exception as e:
            logger.warning(
                f"Failed to extract content from spine item {item.get_id()}: {e}"
            )
            warnings.append(f"Failed to extract content from {item.get_id()}: {e}")

    # Join all content
    full_content = "".join(full_content_parts).strip()

    # Create chapters from TOC entries
    chapters = _create_chapters_from_toc(
        full_content, toc_entries, position_map, warnings
    )

    logger.info(
        f"Extracted {len(chapters)} chapters using TOC (total {len(full_content)} characters)"
    )
    return full_content, chapters


def extract_chapters_from_spine(
    book: epub.EpubBook, warnings: List[str]
) -> Tuple[str, List[Chapter]]:
    """Extract chapters using spine-based detection (fallback method).

    Creates one chapter per spine item when TOC is not available. This is a
    simple fallback that may not match the author's intended chapter structure.

    Algorithm:
    1. Get all spine items in reading order
    2. For each spine item:
       - Extract HTML to text
       - Extract title from item metadata, first <h1>, or generate
       - Create Chapter object
       - Track cumulative position

    Args:
        book: EpubBook object.
        warnings: List to append warnings to.

    Returns:
        Tuple of (full_content, chapters_list).
    """
    # Get all spine items (reading order)
    spine_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

    if not spine_items:
        logger.warning("No spine items found in EPUB")
        return "", []

    extractor = HTMLTextExtractor()
    full_content_parts: List[str] = []
    chapters: List[Chapter] = []
    cumulative_length = 0
    chapter_id = 1

    logger.info(f"Processing {len(spine_items)} spine items")

    for item in spine_items:
        try:
            # Get HTML content
            content_bytes = item.get_content()
            html_string = content_bytes.decode("utf-8", errors="ignore")

            # Extract text
            text = extractor.extract_text(html_string)

            # Record start position
            start_position = cumulative_length

            # Extract title
            title = _extract_spine_item_title(item, html_string, extractor, chapter_id)

            # Add content to full document
            full_content_parts.append(text)
            cumulative_length += len(text)

            # Calculate end position
            end_position = cumulative_length

            # Add spacing between chapters
            full_content_parts.append("\n\n")
            cumulative_length += 2

            # Calculate word count
            word_count = len(text.split())

            # Create chapter object
            chapter = Chapter(
                chapter_id=chapter_id,
                title=title,
                content=text,
                start_position=start_position,
                end_position=end_position,
                word_count=word_count,
                level=1,  # All spine items are top-level
                metadata={
                    "detection_method": "spine",
                    "source_item_id": item.get_id(),
                    "source_file_name": item.get_name(),
                },
            )

            chapters.append(chapter)
            chapter_id += 1

            logger.debug(
                f"Created chapter {chapter_id - 1}: '{title}' ({word_count} words)"
            )

        except Exception as e:
            logger.warning(
                f"Failed to extract content from spine item {item.get_id()}: {e}"
            )
            warnings.append(f"Failed to extract content from {item.get_id()}: {e}")

    # Join all content
    full_content = "".join(full_content_parts).strip()

    logger.info(
        f"Extracted {len(chapters)} chapters using spine (total {len(full_content)} characters)"
    )
    return full_content, chapters


def postprocess_chapters(
    chapters: List[Chapter], options: Dict, warnings: List[str]
) -> List[Chapter]:
    """Post-process chapters: filter empty ones and handle duplicates.

    Applies the following filters:
    1. Remove chapters below min_chapter_length threshold
    2. Disambiguate duplicate chapter titles
    3. Re-number chapter IDs to be sequential after filtering

    Args:
        chapters: List of chapters to process.
        options: Parser configuration dictionary containing:
            - min_chapter_length: Minimum words per chapter (default: 100)
        warnings: List to append warnings to.

    Returns:
        Filtered and cleaned chapter list.
    """
    min_length = options.get("min_chapter_length", 100)

    # Filter empty/short chapters
    filtered_chapters: List[Chapter] = []
    removed_count = 0

    for chapter in chapters:
        if chapter.word_count < min_length:
            logger.debug(
                f"Filtering chapter '{chapter.title}' ({chapter.word_count} words < {min_length} minimum)"
            )
            warnings.append(
                f"Filtered short chapter: '{chapter.title}' ({chapter.word_count} words)"
            )
            removed_count += 1
        else:
            filtered_chapters.append(chapter)

    if removed_count > 0:
        logger.info(f"Filtered {removed_count} short chapters (< {min_length} words)")

    # Handle duplicate titles
    title_counts: Dict[str, int] = {}
    for chapter in filtered_chapters:
        title = chapter.title
        if title in title_counts:
            # Duplicate found - add disambiguation
            title_counts[title] += 1
            new_title = f"{title} ({title_counts[title]})"
            logger.debug(f"Disambiguating duplicate title: '{title}' -> '{new_title}'")
            chapter.title = new_title
        else:
            title_counts[title] = 1

    # Re-number chapter IDs to be sequential after filtering
    for i, chapter in enumerate(filtered_chapters, start=1):
        chapter.chapter_id = i

    return filtered_chapters


# ============================================================================
# Helper Functions
# ============================================================================


def _build_position_map(
    spine_items: List[epub.EpubHtml], warnings: List[str]
) -> Dict[Tuple[str, str], int]:
    """Build a map of (file_name, anchor) -> position in full content.

    Initial positions are set to 0; these are updated during text extraction.
    Anchors are currently not handled (all entries use empty string "").

    Args:
        spine_items: List of spine items from book.get_items_of_type().
        warnings: List to append warnings to.

    Returns:
        Dictionary mapping (file_name, anchor) tuples to positions.
    """
    position_map: Dict[Tuple[str, str], int] = {}
    for item in spine_items:
        file_name = item.get_name()
        # TODO: Handle anchors within files for precise positioning
        position_map[(file_name, "")] = 0
    return position_map


def _create_chapters_from_toc(
    full_content: str,
    toc_entries: List[TocEntry],
    position_map: Dict[Tuple[str, str], int],
    warnings: List[str],
) -> List[Chapter]:
    """Create Chapter objects from TOC entries.

    For each TOC entry:
    1. Extract href and parse into file_name and anchor
    2. Look up start position from position_map
    3. Find end position from next entry's position (or end of content)
    4. Extract content slice
    5. Create Chapter object with metadata

    Args:
        full_content: Complete document text.
        toc_entries: List of TOC entries.
        position_map: Mapping of (file_name, anchor) -> position.
        warnings: List to append warnings to.

    Returns:
        List of created Chapter objects.
    """
    chapters: List[Chapter] = []
    chapter_id = 1

    for i, toc_entry in enumerate(toc_entries):
        try:
            # Parse href to get file name and anchor
            href = toc_entry.href
            if not href:
                logger.warning(f"TOC entry '{toc_entry.title}' has no href, skipping")
                continue

            # Split href into file and anchor
            if "#" in href:
                file_name, anchor = href.split("#", 1)
            else:
                file_name, anchor = href, ""

            # Get start position from position map
            if (file_name, "") not in position_map:
                logger.warning(
                    f"TOC entry '{toc_entry.title}' references unknown file '{file_name}', skipping"
                )
                continue

            start_position = position_map[(file_name, "")]

            # Determine end position (start of next chapter or end of content)
            if i + 1 < len(toc_entries):
                # Get next TOC entry's position
                next_href = toc_entries[i + 1].href
                if next_href:
                    if "#" in next_href:
                        next_file, next_anchor = next_href.split("#", 1)
                    else:
                        next_file, next_anchor = next_href, ""

                    if (next_file, "") in position_map:
                        end_position = position_map[(next_file, "")]
                    else:
                        end_position = len(full_content)
                else:
                    end_position = len(full_content)
            else:
                end_position = len(full_content)

            # Extract chapter content
            chapter_content = full_content[start_position:end_position].strip()

            # Calculate word count
            word_count = len(chapter_content.split())

            # Create chapter object
            chapter = Chapter(
                chapter_id=chapter_id,
                title=toc_entry.title,
                content=chapter_content,
                start_position=start_position,
                end_position=end_position,
                word_count=word_count,
                level=toc_entry.level,
                metadata={"detection_method": "toc", "source_href": href},
            )

            chapters.append(chapter)
            chapter_id += 1

            logger.debug(
                f"Created chapter {chapter_id - 1}: '{toc_entry.title}' ({word_count} words)"
            )

        except Exception as e:
            logger.warning(
                f"Failed to create chapter from TOC entry '{toc_entry.title}': {e}"
            )
            warnings.append(f"Failed to create chapter '{toc_entry.title}': {e}")

    return chapters


def _extract_spine_item_title(
    item: epub.EpubHtml, html_string: str, extractor: HTMLTextExtractor, chapter_id: int
) -> str:
    """Extract title from spine item.

    Tries in order:
    1. Item's title attribute
    2. First <h1> tag content
    3. Generated title

    Args:
        item: EpubHtml item to extract title from.
        html_string: HTML content of spine item.
        extractor: HTMLTextExtractor instance for text extraction.
        chapter_id: Chapter number for fallback title generation.

    Returns:
        Extracted or generated title.
    """
    title = None

    # Try to get title from item's title attribute
    if hasattr(item, "title") and item.title:
        title = item.title
    # Try to extract from first heading in HTML
    elif "<h1" in html_string.lower():
        # Simple regex to extract first h1 content
        h1_match = re.search(
            r"<h1[^>]*>(.*?)</h1>", html_string, re.IGNORECASE | re.DOTALL
        )
        if h1_match:
            # Extract text from h1 (strip HTML tags)
            h1_html = h1_match.group(1)
            title = extractor.extract_text(h1_html).strip()

    # Fallback to generated title
    if not title:
        title = f"Chapter {chapter_id}"

    return title
