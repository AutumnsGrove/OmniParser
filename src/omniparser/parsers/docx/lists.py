"""
DOCX list detection and formatting module.

This module provides functions for detecting and formatting list items from
DOCX documents into markdown format. It handles:
- Bulleted lists (unordered)
- Numbered lists (ordered)
- Nested lists with multiple indentation levels
- Detection via both style names and paragraph numbering properties

The module uses a hybrid approach:
1. Check paragraph style name for list-related keywords
2. Check paragraph numbering properties (numPr) when available
3. Extract nesting level from ilvl property or style name

Extracted from the monolithic DOCXParser as part of the modularization effort.
This is a beta feature to improve DOCX parsing quality.

Functions:
    is_list_item: Check if a paragraph is a list item
    get_list_level: Get the nesting level of a list item
    is_numbered_list: Determine if a list is numbered or bulleted
    format_list_item: Convert a list paragraph to markdown format
"""

from typing import Any


def is_list_item(paragraph: Any) -> bool:
    """
    Check if a paragraph is a list item.

    Uses two detection methods:
    1. Style name contains list-related keywords (List, Bullet, Number)
    2. Paragraph has numbering properties (numPr) in XML structure

    Args:
        paragraph: python-docx Paragraph object

    Returns:
        True if the paragraph is a list item, False otherwise

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> if is_list_item(para):
        ...     print("This is a list item")
    """
    # Method 1: Check style name for list keywords
    if paragraph.style and paragraph.style.name:
        style_lower = paragraph.style.name.lower()
        list_keywords = ["list", "bullet", "number"]
        # Exclude "No List" style
        if "no list" not in style_lower:
            if any(keyword in style_lower for keyword in list_keywords):
                return True

    # Method 2: Check for numbering properties in XML
    try:
        if hasattr(paragraph, "_element") and paragraph._element is not None:
            pPr = paragraph._element.pPr
            if pPr is not None and hasattr(pPr, "numPr") and pPr.numPr is not None:
                return True
    except (AttributeError, TypeError):
        pass

    return False


def get_list_level(paragraph: Any) -> int:
    """
    Get the nesting level of a list item (0-based).

    Attempts to extract level from:
    1. Paragraph numbering properties (ilvl attribute)
    2. Style name (e.g., "List 2" -> level 1, "List Bullet 3" -> level 2)

    Args:
        paragraph: python-docx Paragraph object

    Returns:
        List nesting level (0, 1, 2, etc.), or -1 if not a list item
        Level 0 = first-level list
        Level 1 = first nested list
        Level 2 = second nested list, etc.

    Example:
        >>> level = get_list_level(paragraph)
        >>> if level >= 0:
        ...     indent = "  " * level
        ...     print(f"{indent}- Item")
    """
    if not is_list_item(paragraph):
        return -1

    # Method 1: Try to extract from numPr.ilvl
    try:
        if hasattr(paragraph, "_element") and paragraph._element is not None:
            pPr = paragraph._element.pPr
            if pPr is not None and hasattr(pPr, "numPr") and pPr.numPr is not None:
                numPr = pPr.numPr
                if hasattr(numPr, "ilvl") and numPr.ilvl is not None:
                    return int(numPr.ilvl.val)
    except (AttributeError, TypeError, ValueError):
        pass

    # Method 2: Try to extract from style name
    if paragraph.style and paragraph.style.name:
        style_name = paragraph.style.name
        # Look for patterns like "List 2", "List Bullet 3", "List Number 2"
        parts = style_name.split()
        for part in reversed(parts):  # Check from end
            if part.isdigit():
                level = int(part) - 1  # Convert to 0-based
                return max(0, level)

    # Default to level 0 for recognized list items
    return 0


def is_numbered_list(paragraph: Any) -> bool:
    """
    Determine if a list item is numbered or bulleted.

    Uses style name to distinguish between numbered and bulleted lists.
    If style name contains "number", assumes numbered list.
    Otherwise, assumes bulleted list (default).

    Note: This is a heuristic approach since python-docx doesn't easily
    expose the numbering format from numPr properties.

    Args:
        paragraph: python-docx Paragraph object

    Returns:
        True if numbered list, False if bulleted list

    Example:
        >>> if is_numbered_list(paragraph):
        ...     marker = "1."
        ... else:
        ...     marker = "-"
    """
    if paragraph.style and paragraph.style.name:
        style_lower = paragraph.style.name.lower()
        return "number" in style_lower
    return False


def format_list_item(paragraph: Any, text: str) -> str:
    """
    Format a paragraph as a markdown list item.

    Handles:
    - Bulleted lists: `- Item`
    - Numbered lists: `1. Item`
    - Nested lists with proper indentation (2 spaces per level)

    Args:
        paragraph: python-docx Paragraph object
        text: The paragraph text content

    Returns:
        Markdown-formatted list item string

    Example:
        >>> text = paragraph.text
        >>> if is_list_item(paragraph):
        ...     markdown = format_list_item(paragraph, text)
        ... else:
        ...     markdown = text

        # Level 0 bullet:  "- Item"
        # Level 1 bullet:  "  - Nested item"
        # Level 0 number:  "1. Item"
        # Level 1 number:  "  1. Nested item"
    """
    if not is_list_item(paragraph):
        return text

    level = get_list_level(paragraph)
    if level < 0:
        level = 0

    # Calculate indentation (2 spaces per level)
    indent = "  " * level

    # Determine marker
    if is_numbered_list(paragraph):
        marker = "1."
    else:
        marker = "-"

    return f"{indent}{marker} {text}"
