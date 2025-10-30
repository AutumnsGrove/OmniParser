"""
Markdown content processing and normalization.

This module provides utilities for normalizing markdown content and
processing chapters. It uses shared processors where available to avoid
code duplication (DRY principle).

Functions:
    normalize_markdown_content: Normalize markdown formatting and structure.
    process_markdown_chapters: Detect chapters from markdown headings.
"""

import re
from pathlib import Path
from typing import List

from ...models import Chapter
from ...processors.chapter_detector import detect_chapters


def normalize_markdown_content(content: str) -> str:
    """
    Normalize markdown format and clean up content.

    Normalizations applied:
    - Convert underline-style headings (=== and ---) to # style
    - Standardize list markers (convert * to -)
    - Remove excessive blank lines (3+ consecutive -> 2)
    - Preserve markdown formatting (links, images, code blocks, etc.)

    Args:
        content: Original markdown text to normalize.

    Returns:
        Normalized markdown content with standardized formatting.

    Example:
        >>> content = "Title\\n===\\n\\nPara 1\\n\\n\\n\\nPara 2"
        >>> normalized = normalize_markdown_content(content)
        >>> print(normalized)
        # Title

        Para 1

        Para 2
    """
    if not content:
        return content

    # Convert underline-style H1 (===) to # style
    # Pattern: text on one line, followed by line of ===
    content = re.sub(
        r"^(.+)\n=+\s*$",
        r"# \1",
        content,
        flags=re.MULTILINE,
    )

    # Convert underline-style H2 (---) to ## style
    # Pattern: text on one line, followed by line of ---
    # Only match if underline length is similar to text length (avoid horizontal rules)
    def replace_h2(match: re.Match[str]) -> str:
        title = match.group(1)
        underline = match.group(2)
        # Check if underline length is within 50% of title length
        # This avoids matching horizontal rules (---)
        if len(underline) >= 3 and abs(len(title) - len(underline)) <= len(title) * 0.5:
            return f"## {title}"
        return match.group(0)

    content = re.sub(
        r"^(.+)\n(-{3,})\s*$",
        replace_h2,
        content,
        flags=re.MULTILINE,
    )

    # Normalize list markers: convert * to -
    content = re.sub(
        r"^(\s*)\*\s+",
        r"\1- ",
        content,
        flags=re.MULTILINE,
    )

    # Remove excessive blank lines (3+ newlines -> 2 newlines)
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content


def process_markdown_chapters(
    content: str, file_path: Path, min_level: int = 1, max_level: int = 2
) -> List[Chapter]:
    """
    Process markdown content and detect chapters using shared chapter detector.

    Uses the shared `chapter_detector.detect_chapters()` function for
    heading-based chapter detection. This follows the DRY principle by
    reusing existing chapter detection logic.

    Features:
    - Detect chapters from markdown headings (# through ######)
    - Configurable heading level range (min_level to max_level)
    - Handle documents with no headings (creates single chapter)
    - Preserve heading hierarchy
    - Calculate word counts per chapter

    Args:
        content: Markdown content to process.
        file_path: Source file path (used for logging/debugging).
        min_level: Minimum heading level to consider as chapter (default: 1).
        max_level: Maximum heading level to consider as chapter (default: 2).

    Returns:
        List of Chapter objects with position tracking and metadata.

    Example:
        >>> content = "# Introduction\\n\\nText\\n\\n# Chapter 1\\n\\nMore text"
        >>> chapters = process_markdown_chapters(content, Path("doc.md"))
        >>> len(chapters)
        2
        >>> chapters[0].title
        'Introduction'
    """
    if not content or not content.strip():
        # Empty content: return empty list
        return []

    # Use shared chapter detector (DRY principle)
    # The detect_chapters function handles:
    # - Heading extraction (# through ######)
    # - Level filtering (min_level to max_level)
    # - Content extraction between headings
    # - Position tracking
    # - Word counting
    # - Edge case: no headings found (creates single chapter)
    chapters = detect_chapters(content, min_level=min_level, max_level=max_level)

    return chapters
