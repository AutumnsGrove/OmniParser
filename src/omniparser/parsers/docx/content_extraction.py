"""
DOCX content extraction orchestration module.

This module orchestrates the extraction of all content from a DOCX document,
coordinating paragraph, table, and heading extraction to produce the final
markdown output.

Extracted from the monolithic DOCXParser as part of the modularization effort.
This module serves as the main orchestrator that brings together all the
specialized extraction modules.

Functions:
    extract_content: Main orchestrator for extracting all document content
"""

from typing import Any, List, Optional

from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from .paragraphs import convert_paragraph
from .tables import convert_table


def extract_content(
    docx: Any,
    preserve_formatting: bool = True,
    heading_styles: Optional[List[str]] = None,
    extract_tables: bool = True,
) -> str:
    """Extract all content from DOCX document as markdown.

    Orchestrates extraction of:
    - Paragraphs (with formatting if preserve_formatting=True)
    - Tables (as markdown tables if extract_tables=True)
    - Headings (as markdown headings # ## ###)

    Note: Lists and hyperlinks will be added in Phase 3.

    The function iterates through all document elements in order, processing
    paragraphs and tables sequentially to preserve document structure.

    Args:
        docx: python-docx Document object
        preserve_formatting: Whether to preserve bold/italic formatting.
            Default: True
        heading_styles: Optional list of heading style names to recognize.
            If None, uses default heading styles (Heading 1-6).
        extract_tables: Whether to extract and convert tables to markdown.
            Default: True

    Returns:
        Full document content as markdown string with paragraphs and tables
        separated by double newlines

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> markdown = extract_content(doc)
        >>> print(markdown)
        # Report Title

        This is a paragraph with **bold** text.

        | Name | Value |
        |------|-------|
        | Item | 100   |
    """
    markdown_parts: List[str] = []

    # Iterate through all document elements (paragraphs and tables)
    for element in docx.element.body:
        # Check if it's a paragraph
        if isinstance(element, CT_P):
            para = Paragraph(element, docx)
            markdown_text = convert_paragraph(
                para,
                heading_styles=heading_styles,
                preserve_formatting=preserve_formatting,
            )
            if markdown_text.strip():  # Skip empty paragraphs
                markdown_parts.append(markdown_text)

        # Check if it's a table
        elif isinstance(element, CT_Tbl):
            if extract_tables:
                table = Table(element, docx)
                markdown_table = convert_table(table)
                if markdown_table.strip():
                    markdown_parts.append(markdown_table)
                    markdown_parts.append("")  # Add blank line after table

        # TODO: Phase 3 - Add list handling
        # TODO: Phase 3 - Add hyperlink extraction

    # Join all parts with double newlines
    return "\n\n".join(markdown_parts)
