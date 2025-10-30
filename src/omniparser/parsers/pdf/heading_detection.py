"""
PDF heading detection from font metadata and markdown conversion.

This module provides functions for:
- Detecting headings from PDF font size and weight analysis
- Mapping font sizes to heading levels (1-6)
- Converting detected headings to markdown format
- Detecting chapters from markdown headings

The heading detection algorithm analyzes font metadata (size, weight, boldness)
to identify potential headings, then converts them to markdown format for
consistent document structure.
"""

import logging
import statistics
from typing import Dict, List, Tuple

from ...models import Chapter
from ...processors.chapter_detector import detect_chapters
from .utils import DEFAULT_MAX_HEADING_WORDS, HEADING_SEARCH_WINDOW

logger = logging.getLogger(__name__)


def detect_headings_from_fonts(
    text_blocks: List[Dict], max_heading_words: int = DEFAULT_MAX_HEADING_WORDS
) -> List[Tuple[str, int, int]]:
    """
    Detect headings based on font size analysis.

    Algorithm:
    1. Calculate average font size across document
    2. Calculate standard deviation
    3. Threshold = average + (1.5 * std_dev)
    4. Blocks above threshold = headings
    5. Map font sizes to heading levels (1-6)

    Args:
        text_blocks: List of text blocks with font info (font_size, is_bold, text, position).
        max_heading_words: Maximum words in a heading (default: 25).

    Returns:
        List of (heading_text, level, position) tuples.

    Example:
        >>> text_blocks = [
        ...     {"text": "Chapter 1", "font_size": 18.0, "is_bold": True, "position": 0},
        ...     {"text": "Body text", "font_size": 12.0, "is_bold": False, "position": 10}
        ... ]
        >>> headings = detect_headings_from_fonts(text_blocks)
        >>> len(headings)
        1
    """
    if not text_blocks:
        return []

    # Calculate font size statistics
    font_sizes = [block["font_size"] for block in text_blocks]
    avg_size = statistics.mean(font_sizes)
    std_dev = statistics.stdev(font_sizes) if len(font_sizes) > 1 else 0.0

    # Determine heading threshold (configurable or auto-detect)
    min_heading_size = avg_size + (1.5 * std_dev)

    # Find headings
    headings = []
    unique_sizes = sorted(set(font_sizes), reverse=True)

    for block in text_blocks:
        # Refined heuristic: heading must meet one of these criteria:
        # 1. Font size above threshold
        # 2. Bold AND font size above average (not just any bold text)
        is_heading_candidate = block["font_size"] >= min_heading_size or (
            block["is_bold"] and block["font_size"] > avg_size
        )

        if is_heading_candidate:
            # Only consider lines with reasonable length for headings
            text = block["text"].strip()
            word_count = len(text.split())
            # Headings are typically 1-N words (configurable)
            if 1 <= word_count <= max_heading_words:
                # Map font size to heading level
                level = map_font_size_to_level(block["font_size"], unique_sizes)
                headings.append((text, level, block["position"]))

    logger.info(
        f"Font analysis: avg={avg_size:.1f}, std={std_dev:.1f}, "
        f"threshold={min_heading_size:.1f}, found {len(headings)} headings"
    )

    return headings


def map_font_size_to_level(font_size: float, unique_sizes: List[float]) -> int:
    """
    Map font size to heading level (1-6).

    Larger fonts get lower level numbers (1 is biggest).

    Args:
        font_size: Font size to map.
        unique_sizes: Sorted list of unique font sizes (descending).

    Returns:
        Heading level (1-6).

    Example:
        >>> unique_sizes = [24.0, 18.0, 14.0, 12.0]
        >>> map_font_size_to_level(18.0, unique_sizes)
        2
        >>> map_font_size_to_level(24.0, unique_sizes)
        1
    """
    # Find position in sorted sizes
    try:
        position = unique_sizes.index(font_size)
        # Map to level 1-6
        level = min(position + 1, 6)
        return level
    except ValueError:
        return 3  # Default to level 3 if not found


def convert_headings_to_markdown(
    text: str, headings: List[Tuple[str, int, int]]
) -> str:
    """
    Convert detected headings to markdown format.

    Replace heading text in content with markdown headings:
    - Level 1: # Heading
    - Level 2: ## Heading
    - etc.

    Uses position-based replacement to avoid replacing wrong occurrences.

    Args:
        text: Original text.
        headings: Detected headings with levels (text, level, position).

    Returns:
        Text with markdown headings.

    Example:
        >>> text = "Chapter 1 This is the introduction."
        >>> headings = [("Chapter 1", 1, 0)]
        >>> result = convert_headings_to_markdown(text, headings)
        >>> "# Chapter 1" in result
        True
    """
    if not headings:
        return text

    # Sort headings by position (descending) to process from end to start
    # This avoids position offset issues when modifying the string
    sorted_headings = sorted(headings, key=lambda x: x[2], reverse=True)

    result = text
    for heading_text, level, approx_position in sorted_headings:
        # Create markdown heading
        markdown_heading = f"\n{'#' * level} {heading_text}\n"

        # Search for the heading text near the approximate position
        # Use a window around the position to account for minor discrepancies
        search_start = max(0, approx_position - HEADING_SEARCH_WINDOW)
        search_end = min(
            len(result), approx_position + len(heading_text) + HEADING_SEARCH_WINDOW
        )
        search_region = result[search_start:search_end]

        # Find the heading text in the search region
        heading_index = search_region.find(heading_text)

        if heading_index != -1:
            # Calculate actual position in the full text
            actual_position = search_start + heading_index

            # Replace at the specific position
            result = (
                result[:actual_position]
                + markdown_heading
                + result[actual_position + len(heading_text) :]
            )
        else:
            # Fallback: use simple replacement if position-based fails
            # This handles cases where spacing might have changed
            logger.debug(
                f"Position-based replacement failed for '{heading_text}', "
                f"using fallback"
            )
            result = result.replace(heading_text, markdown_heading, 1)

    return result


def detect_chapters_from_content(
    markdown_content: str, min_level: int = 1, max_level: int = 3
) -> List[Chapter]:
    """
    Detect chapters from markdown headings.

    Uses the shared chapter_detector processor to identify chapters
    based on markdown heading levels.

    Args:
        markdown_content: Markdown text with headings.
        min_level: Minimum heading level for chapters (default: 1).
        max_level: Maximum heading level for chapters (default: 3).

    Returns:
        List of Chapter objects.

    Example:
        >>> content = "# Chapter 1\\n\\nIntroduction text.\\n\\n# Chapter 2\\n\\nMore text."
        >>> chapters = detect_chapters_from_content(content)
        >>> len(chapters)
        2
    """
    chapters = detect_chapters(
        markdown_content, min_level=min_level, max_level=max_level
    )

    logger.info(f"Detected {len(chapters)} chapters")

    return chapters


def process_pdf_headings(
    text_blocks: List[Dict],
    content: str,
    max_heading_words: int = DEFAULT_MAX_HEADING_WORDS,
    min_chapter_level: int = 1,
    max_chapter_level: int = 3,
) -> Tuple[str, List[Chapter]]:
    """
    Main coordinator for PDF heading detection and processing.

    This function orchestrates the complete heading processing pipeline:
    1. Detect headings from font analysis
    2. Convert headings to markdown
    3. Detect chapters from markdown headings

    Args:
        text_blocks: List of text blocks with font info.
        content: Original text content.
        max_heading_words: Maximum words in a heading (default: 25).
        min_chapter_level: Minimum heading level for chapters (default: 1).
        max_chapter_level: Maximum heading level for chapters (default: 3).

    Returns:
        Tuple of (markdown_content, chapters).

    Example:
        >>> text_blocks = [
        ...     {"text": "Chapter 1", "font_size": 18.0, "is_bold": True, "position": 0},
        ...     {"text": "Body text", "font_size": 12.0, "is_bold": False, "position": 10}
        ... ]
        >>> content = "Chapter 1 Body text"
        >>> markdown, chapters = process_pdf_headings(text_blocks, content)
        >>> "# Chapter 1" in markdown
        True
        >>> len(chapters) > 0
        True
    """
    # Step 1: Detect headings from font analysis
    headings = detect_headings_from_fonts(
        text_blocks, max_heading_words=max_heading_words
    )

    # Step 2: Convert headings to markdown
    markdown_content = content
    if headings:
        logger.info(f"Found {len(headings)} headings")
        markdown_content = convert_headings_to_markdown(content, headings)

    # Step 3: Detect chapters from markdown
    chapters = detect_chapters_from_content(
        markdown_content, min_level=min_chapter_level, max_level=max_chapter_level
    )

    return markdown_content, chapters
