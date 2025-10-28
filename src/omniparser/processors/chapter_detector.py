"""
Chapter detection from markdown text based on heading hierarchy.

This module provides utilities for detecting chapters in markdown documents
by analyzing heading patterns (# through ######) and creating structured
Chapter objects with position tracking.

Functions:
    detect_chapters: Main function to detect chapters from markdown text.
    _extract_headings: Helper to extract all headings with metadata.
    _calculate_word_count: Helper to count words in text.
"""

import re
from typing import List, Tuple

from ..models import Chapter


def _extract_headings(text: str) -> List[Tuple[int, str, int]]:
    """Extract all markdown headings with level, title, and position.

    Finds all markdown headings (# through ######) and extracts their
    level (number of #), title text, and character position in the document.

    Args:
        text: Markdown text to analyze.

    Returns:
        List of tuples containing (level, title, position) for each heading.
        Level is 1-6 (corresponding to # through ######).

    Example:
        >>> text = "# Chapter 1\\n\\nContent\\n\\n## Section 1.1"
        >>> headings = _extract_headings(text)
        >>> headings[0]
        (1, 'Chapter 1', 0)
        >>> headings[1]
        (2, 'Section 1.1', 24)
    """
    headings = []
    # Pattern matches: start of line, 1-6 #, space(s), title text
    pattern = re.compile(r"^(#{1,6})\s+(.+?)$", re.MULTILINE)

    for match in pattern.finditer(text):
        level = len(match.group(1))  # Count # characters
        title = match.group(2).strip()  # Extract and clean title
        position = match.start()  # Character position in text
        headings.append((level, title, position))

    return headings


def _calculate_word_count(text: str) -> int:
    """Calculate word count for text content.

    Counts words by splitting on whitespace and filtering empty strings.
    This provides a simple but effective word count suitable for most
    document types.

    Args:
        text: Text content to count words in.

    Returns:
        Number of words in the text.

    Example:
        >>> _calculate_word_count("Hello world! This is a test.")
        6
        >>> _calculate_word_count("   ")
        0
    """
    words = [word for word in text.split() if word.strip()]
    return len(words)


def detect_chapters(text: str, min_level: int = 1, max_level: int = 2) -> List[Chapter]:
    """Detect chapters from markdown text based on heading hierarchy.

    Analyzes markdown headings (# through ######) and creates Chapter objects
    with proper position tracking and nesting levels. Only headings within
    the specified level range are treated as chapter boundaries.

    Features:
    - Detect headings from markdown (# = level 1, ## = level 2, etc.)
    - Extract chapter content between headings
    - Track start/end positions in original text
    - Calculate word counts per chapter
    - Support configurable heading levels (e.g., only H1-H2 are chapters)
    - Handle documents with no headings (single chapter)
    - Preserve heading hierarchy

    Args:
        text: Markdown text to analyze.
        min_level: Minimum heading level to consider as chapter (default 1).
        max_level: Maximum heading level to consider as chapter (default 2).

    Returns:
        List of Chapter objects with position tracking and metadata.

    Example:
        >>> markdown = '''
        ... # Introduction
        ...
        ... This is the intro content.
        ...
        ... ## Background
        ...
        ... Some background information.
        ...
        ... # Chapter 1
        ...
        ... Main content here.
        ... '''
        >>> chapters = detect_chapters(markdown, min_level=1, max_level=1)
        >>> len(chapters)
        2
        >>> chapters[0].title
        'Introduction'
        >>> chapters[0].level
        1
        >>> chapters[1].title
        'Chapter 1'
    """
    if not text or not text.strip():
        # Empty text: return empty list
        return []

    # Extract all headings from text
    all_headings = _extract_headings(text)

    # Filter headings by level range
    chapter_headings = [
        (level, title, position)
        for level, title, position in all_headings
        if min_level <= level <= max_level
    ]

    # No qualifying headings: treat entire document as single chapter
    if not chapter_headings:
        word_count = _calculate_word_count(text)
        return [
            Chapter(
                chapter_id=1,
                title="Full Document",
                content=text,
                start_position=0,
                end_position=len(text),
                word_count=word_count,
                level=1,
                metadata={"auto_generated": True},
            )
        ]

    # Build chapters from headings
    chapters = []
    for idx, (level, title, position) in enumerate(chapter_headings):
        # Determine chapter content range
        start_pos = position
        if idx + 1 < len(chapter_headings):
            # Content ends at next chapter heading
            end_pos = chapter_headings[idx + 1][2]
        else:
            # Last chapter: content to end of document
            end_pos = len(text)

        # Extract chapter content and calculate word count
        content = text[start_pos:end_pos]
        word_count = _calculate_word_count(content)

        # Create Chapter object
        chapter = Chapter(
            chapter_id=idx + 1,
            title=title,
            content=content,
            start_position=start_pos,
            end_position=end_pos,
            word_count=word_count,
            level=level,
        )
        chapters.append(chapter)

    return chapters
