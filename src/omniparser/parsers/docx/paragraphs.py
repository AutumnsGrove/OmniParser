"""
Paragraph and run conversion for DOCX documents.

This module provides utilities for converting DOCX paragraphs and text runs to
markdown format. It handles:
- Heading detection and conversion (# ## ###)
- Text formatting (bold, italic, bold+italic)
- Plain text extraction

Functions:
    convert_run: Convert DOCX run to markdown with formatting
    convert_paragraph: Convert DOCX paragraph to markdown
"""

from typing import Any

from .headings import get_heading_level, is_heading


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

    # TODO: Handle hyperlinks - they're complex in DOCX XML structure
    # Hyperlinks are stored in the document's relationships, not directly
    # in runs. Future implementation needed to extract and convert them.

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

    Not Yet Implemented (TODO):
    - Hyperlinks -> [text](url)
    - Lists -> - item or 1. item

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
