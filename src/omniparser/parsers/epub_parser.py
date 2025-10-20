"""
EPUB parser implementation using EbookLib.

This module provides the EPUBParser class for parsing EPUB files and converting
them to OmniParser's universal Document format. It includes TOC-based and
spine-based chapter detection, metadata extraction, image handling, and text
cleaning.

Ported and adapted from epub2tts project with TTS-specific features removed.
"""

import logging
import re
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ebooklib
from ebooklib import epub
from PIL import Image

from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo

logger = logging.getLogger(__name__)


class TocEntry:
    """Internal representation of a table of contents entry.

    This is used during TOC parsing to build the chapter structure before
    converting to OmniParser's Chapter model.

    Attributes:
        title: Chapter title from TOC.
        href: EPUB internal reference (e.g., "chapter1.xhtml#section").
        level: Heading level (1=main chapter, 2=subsection, etc.).
        children: List of nested TocEntry objects.
    """

    def __init__(
        self,
        title: str,
        href: str,
        level: int = 1,
        children: Optional[List["TocEntry"]] = None,
    ):
        self.title = title
        self.href = href
        self.level = level
        self.children = children or []


class EPUBParser(BaseParser):
    """Parser for EPUB files using EbookLib library.

    Features:
    - TOC-based chapter detection (primary method)
    - Spine-based chapter detection (fallback when no TOC)
    - Comprehensive metadata extraction from OPF
    - Image extraction with safe temp directory cleanup
    - HTML to plain text conversion
    - Text cleaning integration

    Options:
        extract_images (bool): Extract images from EPUB. Default: True
        detect_chapters (bool): Enable chapter detection. Default: True
        clean_text (bool): Apply text cleaning. Default: True
        min_chapter_length (int): Minimum words per chapter. Default: 100
        use_toc (bool): Use TOC for chapter detection. Default: True
        use_spine_fallback (bool): Use spine if TOC missing. Default: True

    Example:
        >>> parser = EPUBParser({'extract_images': True, 'clean_text': True})
        >>> doc = parser.parse(Path('book.epub'))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize EPUB parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
        self.options.setdefault("extract_images", True)
        self.options.setdefault("detect_chapters", True)
        self.options.setdefault("clean_text", True)
        self.options.setdefault("min_chapter_length", 100)
        self.options.setdefault("use_toc", True)
        self.options.setdefault("use_spine_fallback", True)

        # Initialize tracking
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is an EPUB.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .epub extension, False otherwise.
        """
        return file_path.suffix.lower() in [".epub"]

    def parse(self, file_path: Path) -> Document:
        """Parse EPUB file and return Document object.

        This is the main entry point for EPUB parsing. It orchestrates:
        1. File validation
        2. EPUB loading
        3. Metadata extraction
        4. TOC extraction
        5. Content and chapter extraction
        6. Image extraction (if enabled)
        7. Text cleaning (if enabled)
        8. Document object creation

        Args:
            file_path: Path to EPUB file.

        Returns:
            Document object with parsed content, chapters, images, and metadata.

        Raises:
            FileReadError: If file cannot be read or is not a valid EPUB.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.
        """
        import time

        self._start_time = time.time()
        self._warnings = []

        try:
            # Step 1: Validate EPUB file
            self._validate_epub(file_path)

            # Step 2: Load EPUB with ebooklib
            logger.info(f"Loading EPUB: {file_path}")
            book = self._load_epub(file_path)

            # Step 3: Extract metadata
            logger.info("Extracting metadata")
            metadata = self._extract_metadata(book, file_path)

            # Step 4: Extract TOC structure
            logger.info("Extracting table of contents")
            toc_entries = (
                self._extract_toc(book) if self.options.get("use_toc") else None
            )

            # Step 5: Extract content and detect chapters
            logger.info("Extracting content and detecting chapters")
            content, chapters = self._extract_content_and_chapters(book, toc_entries)

            # Step 6: Extract images (if enabled)
            images: List[ImageReference] = []
            if self.options.get("extract_images"):
                logger.info("Extracting images")
                try:
                    images = self.extract_images(file_path)
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    self._warnings.append(f"Image extraction failed: {e}")

            # Step 7: Clean text (if enabled)
            if self.options.get("clean_text"):
                logger.info("Cleaning text")
                content = self.clean_text(content)
                for chapter in chapters:
                    chapter.content = self.clean_text(chapter.content)

            # Step 8: Calculate statistics
            word_count = self._count_words(content)
            reading_time = self._estimate_reading_time(word_count)

            # Step 9: Create processing info
            processing_time = time.time() - self._start_time
            processing_info = ProcessingInfo(
                parser_used="EPUBParser",
                parser_version="1.0.0",
                processing_time=processing_time,
                timestamp=datetime.now(),
                warnings=self._warnings,
                options_used=self.options.copy(),
            )

            # Step 10: Create and return Document
            document = Document(
                document_id=str(uuid.uuid4()),
                content=content,
                chapters=chapters,
                images=images,
                metadata=metadata,
                processing_info=processing_info,
                word_count=word_count,
                estimated_reading_time=reading_time,
            )

            logger.info(
                f"EPUB parsing complete: {word_count} words, {len(chapters)} chapters, {len(images)} images"
            )
            return document

        except (FileReadError, ValidationError):
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"EPUB parsing failed: {e}")
            raise ParsingError(
                f"Failed to parse EPUB file: {e}", parser="EPUBParser", original_error=e
            )

    def _validate_epub(self, file_path: Path) -> None:
        """Validate EPUB file before parsing.

        Checks:
        - File exists
        - File is readable
        - File has .epub extension
        - File size is reasonable (not empty, not too large)

        Args:
            file_path: Path to EPUB file.

        Raises:
            FileReadError: If file doesn't exist or isn't readable.
            ValidationError: If file validation fails.
        """
        # Check file exists
        if not file_path.exists():
            raise FileReadError(f"File not found: {file_path}")

        # Check file is readable
        if not file_path.is_file():
            raise FileReadError(f"Not a file: {file_path}")

        # Check extension
        if not self.supports_format(file_path):
            raise ValidationError(f"Not an EPUB file: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"Empty file: {file_path}")

        # Warn if file is very large (>500MB)
        if file_size > 500 * 1024 * 1024:
            logger.warning(f"Large EPUB file ({file_size / 1024 / 1024:.1f} MB)")
            self._warnings.append(f"Large file size: {file_size / 1024 / 1024:.1f} MB")

    def _load_epub(self, file_path: Path) -> epub.EpubBook:
        """Load EPUB file using ebooklib.

        Args:
            file_path: Path to EPUB file.

        Returns:
            EpubBook object.

        Raises:
            ParsingError: If EPUB cannot be loaded.
        """
        try:
            book = epub.read_epub(str(file_path))
            return book
        except Exception as e:
            logger.error(f"Failed to load EPUB: {e}")
            raise ParsingError(
                f"Failed to load EPUB file: {e}", parser="EPUBParser", original_error=e
            )

    def _extract_metadata(self, book: epub.EpubBook, file_path: Path) -> Metadata:
        """Extract metadata from EPUB OPF file.

        Extracts standard Dublin Core metadata fields from the EPUB package
        document (OPF file).

        Args:
            book: EpubBook object.
            file_path: Path to EPUB file (for file_size).

        Returns:
            Metadata object with extracted fields.
        """

        # Helper function to safely extract first metadata value
        def get_first_metadata(namespace: str, name: str) -> Optional[str]:
            """Get first metadata value from book."""
            try:
                metadata_list = book.get_metadata(namespace, name)
                if metadata_list and len(metadata_list) > 0:
                    # Metadata returns list of tuples: [(value, attributes_dict)]
                    return metadata_list[0][0]
            except Exception as e:
                logger.debug(f"Failed to get metadata {namespace}:{name}: {e}")
            return None

        # Helper function to get all metadata values
        def get_all_metadata(namespace: str, name: str) -> List[str]:
            """Get all metadata values from book."""
            try:
                metadata_list = book.get_metadata(namespace, name)
                if metadata_list:
                    return [item[0] for item in metadata_list if item[0]]
            except Exception as e:
                logger.debug(f"Failed to get metadata list {namespace}:{name}: {e}")
            return []

        # Extract title
        title = get_first_metadata("DC", "title")

        # Extract authors (all contributors)
        authors = get_all_metadata("DC", "creator")
        # Primary author is first in list
        author = authors[0] if authors else None

        # Extract publisher
        publisher = get_first_metadata("DC", "publisher")

        # Extract and parse publication date
        publication_date: Optional[datetime] = None
        date_str = get_first_metadata("DC", "date")
        if date_str:
            # Try common date formats
            date_formats = [
                "%Y-%m-%d",  # 2023-01-15
                "%Y-%m-%dT%H:%M:%S",  # 2023-01-15T10:30:00
                "%Y-%m-%dT%H:%M:%SZ",  # 2023-01-15T10:30:00Z
                "%Y-%m-%dT%H:%M:%S%z",  # 2024-07-09T05:00:00+00:00
                "%Y",  # 2023
                "%Y-%m",  # 2023-01
            ]
            for fmt in date_formats:
                try:
                    publication_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            if publication_date is None:
                logger.warning(f"Could not parse publication date: {date_str}")
                self._warnings.append(f"Could not parse publication date: {date_str}")

        # Extract language
        language = get_first_metadata("DC", "language")

        # Extract ISBN from identifiers
        isbn: Optional[str] = None
        identifiers = get_all_metadata("DC", "identifier")
        for identifier in identifiers:
            # Look for ISBN in identifier string
            if identifier and "isbn" in identifier.lower():
                # Extract just the ISBN number (remove "ISBN:" prefix if present)
                isbn = (
                    identifier.replace("urn:isbn:", "")
                    .replace("ISBN:", "")
                    .replace("isbn:", "")
                    .strip()
                )
                break

        # Extract description
        description = get_first_metadata("DC", "description")

        # Extract tags/subjects
        tags = get_all_metadata("DC", "subject")

        # Calculate file size
        file_size = file_path.stat().st_size

        return Metadata(
            title=title,
            author=author,
            authors=authors,
            publisher=publisher,
            publication_date=publication_date,
            language=language,
            isbn=isbn,
            description=description,
            tags=tags,
            original_format="epub",
            file_size=file_size,
            custom_fields={},
        )

    def _extract_toc(self, book: epub.EpubBook) -> Optional[List[TocEntry]]:
        """Extract table of contents from EPUB.

        Parses the EPUB's table of contents structure and converts it to a flat
        list of TocEntry objects. Handles nested TOC structures by preserving
        hierarchy information via the level attribute.

        Args:
            book: EpubBook object.

        Returns:
            Flat list of TocEntry objects with level indicating hierarchy,
            or None if TOC is missing/empty.

        Note:
            The returned list is flattened - all TocEntry objects have empty
            children lists, but the level attribute indicates nesting depth
            (1=main chapter, 2=subsection, etc.).
        """
        try:
            toc = book.toc

            # Check if TOC is empty or None
            if not toc:
                logger.info("EPUB has no table of contents")
                return None

            # Parse TOC structure recursively
            flat_toc: List[TocEntry] = []
            self._parse_toc_item(toc, flat_toc, level=1)

            # Return None if parsing produced no entries
            if not flat_toc:
                logger.info("EPUB TOC parsing produced no entries")
                return None

            logger.info(f"Extracted {len(flat_toc)} TOC entries")
            return flat_toc

        except Exception as e:
            logger.warning(f"Failed to extract TOC: {e}")
            self._warnings.append(f"TOC extraction failed: {e}")
            return None

    def _parse_toc_item(
        self, items: Any, flat_toc: List[TocEntry], level: int = 1
    ) -> None:
        """Recursively parse TOC items into flat list.

        Handles various TOC structures from ebooklib:
        - Individual epub.Link objects
        - Tuples of (Section, [children])
        - Lists of Links or nested tuples

        Args:
            items: TOC item(s) to parse (Link, tuple, or list).
            flat_toc: Accumulator list for flattened TocEntry objects.
            level: Current hierarchy level (1=top-level, 2=subsection, etc.).
        """
        # Handle list of items
        if isinstance(items, list):
            for item in items:
                self._parse_toc_item(item, flat_toc, level)
            return

        # Handle tuple (Section, children)
        if isinstance(items, tuple):
            if len(items) >= 2:
                section, children = items[0], items[1]

                # Process section (could be Link or Section)
                if hasattr(section, "title") and hasattr(section, "href"):
                    # It's a Link
                    try:
                        title = section.title or "Untitled"
                        href = section.href or ""
                        flat_toc.append(TocEntry(title=title, href=href, level=level))
                    except Exception as e:
                        logger.warning(f"Failed to parse TOC Link: {e}")
                        self._warnings.append(f"Malformed TOC Link: {e}")
                elif hasattr(section, "title"):
                    # It's a Section (has title but maybe no href)
                    try:
                        title = section.title or "Untitled"
                        # Sections might not have href - use empty string
                        href = getattr(section, "href", "")
                        flat_toc.append(TocEntry(title=title, href=href, level=level))
                    except Exception as e:
                        logger.warning(f"Failed to parse TOC Section: {e}")
                        self._warnings.append(f"Malformed TOC Section: {e}")

                # Recursively process children at deeper level
                if children:
                    self._parse_toc_item(children, flat_toc, level + 1)
            return

        # Handle individual epub.Link
        if hasattr(items, "title") and hasattr(items, "href"):
            try:
                title = items.title or "Untitled"
                href = items.href or ""
                flat_toc.append(TocEntry(title=title, href=href, level=level))
            except Exception as e:
                logger.warning(f"Failed to parse TOC item: {e}")
                self._warnings.append(f"Malformed TOC item: {e}")
            return

        # Unknown structure - log warning
        logger.warning(f"Unknown TOC item structure: {type(items)}")
        self._warnings.append(f"Unknown TOC item type: {type(items).__name__}")

    def _extract_content_and_chapters(
        self, book: epub.EpubBook, toc_entries: Optional[List[TocEntry]]
    ) -> Tuple[str, List[Chapter]]:
        """Extract full content and detect chapters.

        Uses TOC-based detection if available, otherwise falls back to spine-based.
        Post-processes chapters to filter empty ones and handle duplicates.

        Args:
            book: EpubBook object.
            toc_entries: TOC entries if available, None otherwise.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        if toc_entries:
            logger.info("Using TOC-based chapter detection")
            content, chapters = self._extract_chapters_toc(book, toc_entries)
        else:
            logger.info("Using spine-based chapter detection (no TOC)")
            content, chapters = self._extract_chapters_spine(book)

        # Post-process chapters
        chapters = self._postprocess_chapters(chapters)

        return content, chapters

    def _extract_chapters_toc(
        self, book: epub.EpubBook, toc_entries: List[TocEntry]
    ) -> Tuple[str, List[Chapter]]:
        """Extract chapters using TOC-based detection.

        Maps TOC entries to spine items and creates chapter boundaries based on
        TOC structure. This is the preferred method as it respects the author's
        intended chapter divisions.

        Args:
            book: EpubBook object.
            toc_entries: List of TOC entries.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        from ..utils.html_extractor import HTMLTextExtractor

        # Get all spine items (reading order)
        spine_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        if not spine_items:
            logger.warning("No spine items found in EPUB")
            return "", []

        # Create mapping of href to spine items
        # Handle both "chapter.xhtml" and "chapter.xhtml#anchor" formats
        spine_map: Dict[str, epub.EpubHtml] = {}
        for item in spine_items:
            file_name = item.get_name()
            spine_map[file_name] = item

        # Extract text for all spine items and track positions
        extractor = HTMLTextExtractor()
        full_content_parts: List[str] = []
        cumulative_length = 0

        # Map of (file_name, anchor) -> position in full content
        position_map: Dict[Tuple[str, str], int] = {}

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

                # TODO: Handle anchors within the file
                # For now, we'll just track the file start position

                full_content_parts.append(text)
                cumulative_length += len(text)

                # Add spacing between spine items
                full_content_parts.append("\n\n")
                cumulative_length += 2

            except Exception as e:
                logger.warning(
                    f"Failed to extract content from spine item {item.get_id()}: {e}"
                )
                self._warnings.append(
                    f"Failed to extract content from {item.get_id()}: {e}"
                )

        # Join all content
        full_content = "".join(full_content_parts).strip()

        # Create chapters from TOC entries
        chapters: List[Chapter] = []
        chapter_id = 1

        for i, toc_entry in enumerate(toc_entries):
            try:
                # Parse href to get file name and anchor
                href = toc_entry.href
                if not href:
                    logger.warning(
                        f"TOC entry '{toc_entry.title}' has no href, skipping"
                    )
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
                self._warnings.append(
                    f"Failed to create chapter '{toc_entry.title}': {e}"
                )

        logger.info(
            f"Extracted {len(chapters)} chapters using TOC (total {len(full_content)} characters)"
        )
        return full_content, chapters

    def _extract_chapters_spine(self, book: epub.EpubBook) -> Tuple[str, List[Chapter]]:
        """Extract chapters using spine-based detection (fallback method).

        Creates one chapter per spine item when TOC is not available. This is a
        simple fallback that may not match the author's intended chapter structure.

        Args:
            book: EpubBook object.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        from ..utils.html_extractor import HTMLTextExtractor

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

                # Create title from item metadata or generate one
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
                self._warnings.append(
                    f"Failed to extract content from {item.get_id()}: {e}"
                )

        # Join all content
        full_content = "".join(full_content_parts).strip()

        logger.info(
            f"Extracted {len(chapters)} chapters using spine (total {len(full_content)} characters)"
        )
        return full_content, chapters

    def _postprocess_chapters(self, chapters: List[Chapter]) -> List[Chapter]:
        """Post-process chapters: filter empty ones and handle duplicates.

        Applies the following filters:
        - Remove chapters below min_chapter_length threshold
        - Disambiguate duplicate chapter titles

        Args:
            chapters: List of chapters to process.

        Returns:
            Filtered and cleaned chapter list.
        """
        min_length = self.options.get("min_chapter_length", 100)

        # Filter empty/short chapters
        filtered_chapters: List[Chapter] = []
        removed_count = 0

        for chapter in chapters:
            if chapter.word_count < min_length:
                logger.debug(
                    f"Filtering chapter '{chapter.title}' ({chapter.word_count} words < {min_length} minimum)"
                )
                self._warnings.append(
                    f"Filtered short chapter: '{chapter.title}' ({chapter.word_count} words)"
                )
                removed_count += 1
            else:
                filtered_chapters.append(chapter)

        if removed_count > 0:
            logger.info(
                f"Filtered {removed_count} short chapters (< {min_length} words)"
            )

        # Handle duplicate titles
        title_counts: Dict[str, int] = {}
        for chapter in filtered_chapters:
            title = chapter.title
            if title in title_counts:
                # Duplicate found - add disambiguation
                title_counts[title] += 1
                new_title = f"{title} ({title_counts[title]})"
                logger.debug(
                    f"Disambiguating duplicate title: '{title}' -> '{new_title}'"
                )
                chapter.title = new_title
            else:
                title_counts[title] = 1

        # Re-number chapter IDs to be sequential after filtering
        for i, chapter in enumerate(filtered_chapters, start=1):
            chapter.chapter_id = i

        return filtered_chapters

    def extract_images(self, file_path: Path) -> List[ImageReference]:
        """Extract images from EPUB file.

        Extracts all images from the EPUB, saves them to a temporary directory,
        and creates ImageReference objects with dimensions and format information.

        Args:
            file_path: Path to EPUB file.

        Returns:
            List of ImageReference objects.

        Raises:
            ParsingError: If EPUB loading fails.

        Note:
            - Uses temporary directory with context manager for safe cleanup
            - Sequential image IDs: img_001, img_002, etc.
            - Position set to 0 (exact position tracking not implemented)
            - Alt text set to None (HTML parsing not implemented)
        """
        try:
            # Load EPUB file
            logger.info(f"Loading EPUB for image extraction: {file_path}")
            book = self._load_epub(file_path)

            # Get all image items from EPUB
            image_items = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))

            if not image_items:
                logger.info("No images found in EPUB")
                return []

            logger.info(f"Found {len(image_items)} images in EPUB")

            # Use context manager for safe temporary directory cleanup
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                images: List[ImageReference] = []

                for idx, item in enumerate(image_items, start=1):
                    try:
                        # Get image metadata
                        image_name = item.get_name()  # e.g., "images/cover.jpg"
                        image_content = item.get_content()  # bytes

                        # Save to temp directory (preserve subdirectory structure)
                        image_path = temp_path / image_name
                        image_path.parent.mkdir(parents=True, exist_ok=True)

                        with open(image_path, "wb") as f:
                            f.write(image_content)

                        # Get image dimensions and format using PIL
                        width: Optional[int] = None
                        height: Optional[int] = None
                        format_name: str = "unknown"

                        try:
                            with Image.open(image_path) as img:
                                width, height = img.size
                                format_name = (
                                    img.format.lower() if img.format else "unknown"
                                )
                        except Exception as e:
                            logger.warning(f"Could not read image {image_name}: {e}")
                            self._warnings.append(
                                f"Could not read image {image_name}: {e}"
                            )

                        # Create ImageReference
                        image_ref = ImageReference(
                            image_id=f"img_{idx:03d}",
                            position=0,  # We don't track exact position
                            file_path=str(image_path),
                            alt_text=None,  # Would require HTML parsing
                            size=(width, height) if width and height else None,
                            format=format_name,
                        )

                        images.append(image_ref)
                        logger.debug(
                            f"Extracted image {idx}: {image_name} ({format_name}, {width}x{height})"
                        )

                    except Exception as e:
                        logger.warning(f"Failed to extract image {idx}: {e}")
                        self._warnings.append(f"Failed to extract image: {e}")
                        # Continue with next image - don't fail entire extraction

                logger.info(f"Successfully extracted {len(images)} images")
                return images

        except ParsingError:
            # Re-raise ParsingError from _load_epub
            raise
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            raise ParsingError(
                f"Failed to extract images from EPUB: {e}",
                parser="EPUBParser",
                original_error=e,
            )

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Text to count words in.

        Returns:
            Word count.
        """
        return len(text.split())

    def _estimate_reading_time(self, word_count: int) -> int:
        """Estimate reading time in minutes.

        Assumes average reading speed of 200-250 words per minute.
        Uses 225 WPM as middle ground.

        Args:
            word_count: Total word count.

        Returns:
            Estimated reading time in minutes.
        """
        return max(1, round(word_count / 225))
