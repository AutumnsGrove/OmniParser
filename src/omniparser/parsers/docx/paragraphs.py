"""
Paragraph and run conversion for DOCX documents.

This module provides utilities for converting DOCX paragraphs and text runs to
markdown format. It handles:
- Heading detection and conversion (# ## ###)
- Text formatting (bold, italic, bold+italic)
- Hyperlink extraction and conversion (NEW: [text](url))
- Plain text extraction

Functions:
    convert_run: Convert DOCX run to markdown with formatting
    convert_paragraph: Convert DOCX paragraph to markdown
    convert_paragraph_with_hyperlinks: Convert paragraph including hyperlinks
"""

from typing import Any, Optional

from .headings import get_heading_level, is_heading
from .hyperlinks import apply_hyperlinks_to_paragraph


def convert_run(run: Any) -> str:
    """Convert DOCX run to markdown with formatting.

    Applies markdown formatting based on run properties:
    - Bold + Italic -> ***text***
    - Bold -> **text**
    - Italic -> *text*
    - Plain -> text

    Args:
        run: python-docx Run object with text and formatting properties

    Returns:
        Markdown formatted text string

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> for run in para.runs:
        ...     markdown = convert_run(run)
        ...     print(markdown)
    """
    text = str(run.text) if run.text else ""

    # Note: Hyperlinks are handled separately in convert_paragraph_with_hyperlinks()
    # They require access to document relationships, not available at run level

    # Apply formatting based on run properties
    if run.bold and run.italic:
        return f"***{text}***"
    elif run.bold:
        return f"**{text}**"
    elif run.italic:
        return f"*{text}*"
    else:
        return text


def convert_paragraph(
    paragraph: Any,
    heading_styles: list = None,
    preserve_formatting: bool = True,
) -> str:
    """Convert DOCX paragraph to markdown.

    Handles:
    - Heading styles -> markdown headings (# ## ###)
    - Bold text -> **text**
    - Italic text -> *text*
    - Plain text

    Note: This function does NOT handle hyperlinks. Use
    convert_paragraph_with_hyperlinks() for hyperlink support.

    Args:
        paragraph: python-docx Paragraph object
        heading_styles: Optional list of style names to treat as headings.
            If None, uses default heading styles from headings module.
        preserve_formatting: If True, preserves bold/italic formatting.
            If False, returns plain text only.

    Returns:
        Markdown-formatted paragraph text

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> markdown = convert_paragraph(para)
        >>> print(markdown)
    """
    # Check if it's a heading
    if is_heading(paragraph, heading_styles):
        level = get_heading_level(paragraph)
        heading_prefix = "#" * level
        text = paragraph.text.strip()
        return f"{heading_prefix} {text}"

    # Process runs with formatting
    if preserve_formatting:
        formatted_text = ""
        for run in paragraph.runs:
            formatted_text += convert_run(run)
        return formatted_text.strip()
    else:
        # Just return plain text
        return paragraph.text.strip()


def convert_paragraph_with_hyperlinks(
    paragraph: Any,
    docx: Any,
    heading_styles: list = None,
    preserve_formatting: bool = True,
    extract_hyperlinks: bool = True,
) -> str:
    """Convert DOCX paragraph to markdown with hyperlink support.

    This function extends convert_paragraph() by adding hyperlink extraction
    and conversion. Hyperlinks are formatted as markdown [text](url).

    Handles:
    - Hyperlinks -> [text](url) (NEW)
    - Heading styles -> markdown headings (# ## ###)
    - Bold text -> **text**
    - Italic text -> *text*
    - Plain text

    Args:
        paragraph: python-docx Paragraph object
        docx: python-docx Document object (required for hyperlink lookup)
        heading_styles: Optional list of style names to treat as headings.
            If None, uses default heading styles from headings module.
        preserve_formatting: If True, preserves bold/italic formatting.
            If False, returns plain text only.
        extract_hyperlinks: If True, extracts and formats hyperlinks.
            If False, treats hyperlink text as plain text.

    Returns:
        Markdown-formatted paragraph text with hyperlinks

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> markdown = convert_paragraph_with_hyperlinks(para, doc)
        >>> print(markdown)
        Visit [our website](https://example.com) for more info.
    """
    # Check if it's a heading (headings don't typically have hyperlinks)
    if is_heading(paragraph, heading_styles):
        level = get_heading_level(paragraph)
        heading_prefix = "#" * level
        text = paragraph.text.strip()
        return f"{heading_prefix} {text}"

    # Extract hyperlinks if requested
    if extract_hyperlinks and docx:
        # Use hyperlink-aware extraction
        return apply_hyperlinks_to_paragraph(paragraph, docx)
    else:
        # Fall back to standard conversion
        return convert_paragraph(paragraph, heading_styles, preserve_formatting)
