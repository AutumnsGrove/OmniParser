"""
Chapter detection from plain text using pattern matching.

This module provides utilities for detecting chapters in plain text documents
by analyzing text patterns (Chapter 1, CHAPTER I, Part 1, etc.) and creating
structured Chapter objects with position tracking.

Features:
- Pattern-based chapter detection (Chapter 1, CHAPTER I, Part 1, etc.)
- Support for multiple numbering formats (1, I, One, etc.)
- Case-insensitive matching
- Fallback to single chapter if no patterns match
- Word count tracking per chapter

Functions:
    detect_text_chapters: Main function to detect chapters from plain text.
    _find_chapter_markers: Find chapter markers using regex patterns.
    _split_by_markers: Split text into chapters at marker positions.
    _create_chapter_object: Create Chapter object from text segment.
    _extract_title_from_first_line: Extract title from first line of text.
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple

from ...models import Chapter

logger = logging.getLogger(__name__)


# Chapter detection patterns (ordered by specificity)
# Each pattern is a tuple of (regex_pattern, chapter_type_name)
CHAPTER_PATTERNS = [
    # Chapter with Arabic numerals (Chapter 1, Chapter 2, etc.)
    (r"^Chapter\s+(\d+)", "Chapter"),
    # Chapter with number words (Chapter One, Chapter Two, etc.)
    (
        r"^Chapter\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|"
        r"Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|"
        r"Eighteen|Nineteen|Twenty)",
        "Chapter",
    ),
    # CHAPTER all caps with numbers (CHAPTER 1, CHAPTER I, etc.)
    (r"^CHAPTER\s+(\d+|[IVX]+)", "Chapter"),
    # Part with numbers (Part 1, Part I, Part One, etc.)
    (r"^Part\s+(\d+|[IVX]+|One|Two|Three|Four|Five)", "Part"),
    # Section with numbers or letters (Section 1, Section A, etc.)
    (r"^Section\s+(\d+|[A-Z])", "Section"),
    # Roman numerals at line start (I. Introduction, II. Methods, etc.)
    (r"^([IVX]+)\.\s+[A-Z]", "Section"),
    # Numbers at line start (1. Introduction, 2. Methods, etc.)
    (r"^(\d+)\.\s+[A-Z][a-z]+", "Chapter"),
]


def _find_chapter_markers(text: str) -> List[Tuple[int, str, str]]:
    """Find chapter markers in text using regex patterns.

    Applies each pattern from CHAPTER_PATTERNS to find potential chapter
    markers. Returns list of tuples containing line number, title, and
    chapter type for each detected marker.

    Args:
        text: Plain text content to scan for chapter markers.

    Returns:
        List of tuples (line_number, title, chapter_type) for each marker.
        Empty list if no markers found.

    Example:
        >>> text = "Chapter 1\\n\\nContent here\\n\\nChapter 2\\n\\nMore content"
        >>> markers = _find_chapter_markers(text)
        >>> len(markers)
        2
        >>> markers[0]
        (0, 'Chapter 1', 'Chapter')
    """
    lines = text.split("\n")
    markers = []

    for line_num, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Try each pattern (stop at first match)
        for pattern, chapter_type in CHAPTER_PATTERNS:
            match = re.match(pattern, line_stripped, re.IGNORECASE)
            if match:
                title = line_stripped
                markers.append((line_num, title, chapter_type))
                logger.debug(f"Found chapter marker at line {line_num}: {title}")
                break  # Only match first pattern per line

    return markers


def _split_by_markers(
    text: str, markers: List[Tuple[int, str, str]]
) -> List[Tuple[str, str, int, int, str]]:
    """Split text into chapters at marker positions.

    Takes the list of chapter markers and splits the full text into segments,
    one per chapter. Each segment includes the marker line and all content
    until the next marker.

    Args:
        text: Full text content.
        markers: List of (line_number, title, chapter_type) tuples.

    Returns:
        List of tuples (title, content, start_pos, end_pos, chapter_type)
        for each chapter segment.

    Example:
        >>> text = "Chapter 1\\nContent\\nChapter 2\\nMore content"
        >>> markers = [(0, 'Chapter 1', 'Chapter'), (2, 'Chapter 2', 'Chapter')]
        >>> segments = _split_by_markers(text, markers)
        >>> len(segments)
        2
        >>> segments[0][0]  # First chapter title
        'Chapter 1'
    """
    lines = text.split("\n")
    segments = []

    for i, (line_num, title, chapter_type) in enumerate(markers):
        # Determine start and end line numbers
        start_line = line_num
        if i + 1 < len(markers):
            end_line = markers[i + 1][0]
        else:
            end_line = len(lines)

        # Extract chapter content
        chapter_lines = lines[start_line:end_line]
        chapter_content = "\n".join(chapter_lines).strip()

        # Calculate positions in full text
        start_position = sum(len(lines[j]) + 1 for j in range(start_line))
        end_position = sum(len(lines[j]) + 1 for j in range(end_line))

        segments.append(
            (title, chapter_content, start_position, end_position, chapter_type)
        )

    return segments


def _create_chapter_object(
    chapter_id: int,
    title: str,
    content: str,
    start_position: int,
    end_position: int,
    chapter_type: str,
    line_number: int,
) -> Chapter:
    """Create Chapter object from text segment.

    Builds a Chapter object with proper metadata including word count,
    position tracking, and detection method information.

    Args:
        chapter_id: Sequential chapter number (1-indexed).
        title: Chapter title extracted from marker.
        content: Chapter content text.
        start_position: Character position where chapter starts.
        end_position: Character position where chapter ends.
        chapter_type: Type of chapter marker (Chapter, Part, Section).
        line_number: Line number where chapter marker was found.

    Returns:
        Chapter object with all fields populated.

    Example:
        >>> chapter = _create_chapter_object(
        ...     chapter_id=1,
        ...     title="Chapter 1",
        ...     content="Chapter 1\\n\\nContent here",
        ...     start_position=0,
        ...     end_position=100,
        ...     chapter_type="Chapter",
        ...     line_number=0
        ... )
        >>> chapter.title
        'Chapter 1'
        >>> chapter.chapter_id
        1
    """
    word_count = len(content.split())

    return Chapter(
        chapter_id=chapter_id,
        title=title,
        content=content,
        start_position=start_position,
        end_position=end_position,
        word_count=word_count,
        level=1,
        metadata={
            "detection_method": "pattern",
            "pattern_type": chapter_type,
            "line_number": line_number,
        },
    )


def _extract_title_from_first_line(text: str) -> str:
    """Extract title from first line of text.

    Attempts to use the first non-empty line as a title if it's short
    enough (<100 characters). Otherwise returns "Document" as default.

    Args:
        text: Text content to extract title from.

    Returns:
        Extracted title string or "Document" as fallback.

    Example:
        >>> _extract_title_from_first_line("My Great Novel\\n\\nContent here")
        'My Great Novel'
        >>> _extract_title_from_first_line("\\n\\nContent starts here")
        'Content starts here'
        >>> _extract_title_from_first_line("A" * 200)
        'Document'
    """
    lines = text.split("\n")
    first_line = lines[0].strip() if lines else ""

    # Use first line as title if it's short and not empty
    if first_line and len(first_line) < 100:
        return first_line
    else:
        return "Document"


def detect_text_chapters(content: str, file_path: Path) -> List[Chapter]:
    """Detect chapters from plain text using pattern matching.

    Analyzes text for common chapter markers (Chapter 1, CHAPTER I, Part 1,
    etc.) and creates Chapter objects with proper position tracking. Supports
    multiple numbering formats including Arabic numerals, Roman numerals, and
    number words.

    Features:
    - Pattern-based detection (Chapter 1, CHAPTER I, Part 1, etc.)
    - Support for multiple numbering formats (1, I, One, etc.)
    - Case-insensitive matching
    - Fallback to single chapter if no patterns match
    - Word count tracking per chapter
    - Position tracking in original text

    Args:
        content: Plain text content to analyze.
        file_path: Path to source file (used for metadata).

    Returns:
        List of Chapter objects. Returns single chapter if no markers found.

    Example:
        >>> text = "Chapter 1\\n\\nIntro content\\n\\nChapter 2\\n\\nMain content"
        >>> chapters = detect_text_chapters(text, Path("book.txt"))
        >>> len(chapters)
        2
        >>> chapters[0].title
        'Chapter 1'
        >>> chapters[0].word_count
        2

    Note:
        Requires at least 2 chapter markers to create structured chapters.
        With fewer than 2 markers, returns single chapter with entire content.
    """
    if not content or not content.strip():
        logger.warning("Empty content provided for chapter detection")
        return []

    # Find all chapter markers
    markers = _find_chapter_markers(content)

    # Need at least 2 markers to create meaningful chapters
    if len(markers) < 2:
        logger.info(
            f"Found {len(markers)} chapter markers, need at least 2. "
            "Creating single chapter instead."
        )

        # Create single chapter with entire content
        title = _extract_title_from_first_line(content)
        word_count = len(content.split())

        return [
            Chapter(
                chapter_id=1,
                title=title,
                content=content,
                start_position=0,
                end_position=len(content),
                word_count=word_count,
                level=1,
                metadata={"detection_method": "single_chapter"},
            )
        ]

    # Split text by markers
    segments = _split_by_markers(content, markers)

    # Create Chapter objects
    chapters = []
    for idx, (title, chapter_content, start_pos, end_pos, chapter_type) in enumerate(
        segments, start=1
    ):
        line_number = markers[idx - 1][0]  # Get original line number

        chapter = _create_chapter_object(
            chapter_id=idx,
            title=title,
            content=chapter_content,
            start_position=start_pos,
            end_position=end_pos,
            chapter_type=chapter_type,
            line_number=line_number,
        )

        chapters.append(chapter)
        logger.debug(f"Created chapter {idx}: '{title}' ({chapter.word_count} words)")

    logger.info(f"Detected {len(chapters)} chapters using pattern matching")
    return chapters
