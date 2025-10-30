"""
Heading detection for DOCX documents.

This module provides utilities for detecting headings in DOCX documents based on
paragraph styles. It identifies heading paragraphs (Heading 1-6) and extracts
their level numbers.

Functions:
    is_heading: Check if a paragraph uses a heading style
    get_heading_level: Extract heading level (1-6) from style name
"""

import re
from typing import Any, List

# Default heading style names recognized by this module
DEFAULT_HEADING_STYLES = [
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Heading 5",
    "Heading 6",
]


def is_heading(paragraph: Any, heading_styles: List[str] = None) -> bool:
    """Check if paragraph is a heading based on style.

    Determines whether a paragraph uses one of the recognized heading styles
    (e.g., "Heading 1", "Heading 2", etc.).

    Args:
        paragraph: python-docx Paragraph object
        heading_styles: Optional list of style names to consider as headings.
            Defaults to DEFAULT_HEADING_STYLES if not provided.

    Returns:
        True if paragraph uses a heading style, False otherwise

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> if is_heading(para):
        ...     print(f"Found heading: {para.text}")
    """
    if heading_styles is None:
        heading_styles = DEFAULT_HEADING_STYLES

    style_name = paragraph.style.name if paragraph.style else ""
    return style_name in heading_styles


def get_heading_level(paragraph: Any) -> int:
    """Get heading level (1-6) from paragraph style.

    Extracts the numeric level from heading style names like "Heading 1",
    "Heading 2", etc. Returns 0 if the paragraph is not a heading.

    Args:
        paragraph: python-docx Paragraph object

    Returns:
        Heading level (1-6), or 0 if not a heading or level cannot be determined.
        Level is capped at 6 to match markdown heading limits.

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> level = get_heading_level(para)
        >>> if level > 0:
        ...     print(f"{'#' * level} {para.text}")
    """
    style_name = paragraph.style.name if paragraph.style else ""

    if "Heading" not in style_name:
        return 0

    # Extract number from "Heading 1", "Heading 2", etc.
    try:
        match = re.search(r"Heading (\d+)", style_name)
        if match:
            level = int(match.group(1))
            return min(level, 6)  # Cap at 6 (max markdown heading level)
    except (ValueError, AttributeError):
        pass

    return 0
