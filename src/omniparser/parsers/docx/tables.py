"""
DOCX table conversion module.

This module provides functions for converting python-docx Table objects
to markdown format. Extracted from the monolithic DOCXParser as part of
the modularization effort.

Features:
- Table to markdown conversion
- Cell formatting and escape handling
- Row processing with header detection

Functions:
    convert_table: Main entry point for table conversion
    format_cell: Format individual table cell content
"""

from typing import List


def format_cell(cell_text: str) -> str:
    """
    Format table cell content for markdown.

    Handles:
    - Newline replacement with spaces
    - Pipe character escaping (|) to prevent table format breaking
    - Whitespace normalization

    Args:
        cell_text: Raw cell text content

    Returns:
        Formatted cell text suitable for markdown table
    """
    # Handle None case for empty cells
    text = (cell_text or "").strip()

    # Replace newlines with spaces to keep cell content on one line
    text = text.replace("\n", " ")

    # Escape pipe characters to prevent breaking table formatting
    text = text.replace("|", "\\|")

    return text


def convert_table(table: any) -> str:
    """
    Convert python-docx Table object to markdown table format.

    Markdown table format:
    | Header 1 | Header 2 |
    |----------|----------|
    | Cell 1   | Cell 2   |

    The first row is treated as a header row with a separator line
    added automatically.

    Args:
        table: python-docx Table object with rows and cells

    Returns:
        Markdown-formatted table string. Empty string if table has no rows.

    Example:
        >>> from docx import Document
        >>> doc = Document("example.docx")
        >>> table = doc.tables[0]
        >>> markdown = convert_table(table)
        >>> print(markdown)
        | Name | Age |
        |------|-----|
        | John | 30  |
    """
    if not table.rows:
        return ""

    markdown_rows: List[str] = []

    # Process each row
    for row_idx, row in enumerate(table.rows):
        cells = []
        for cell in row.cells:
            # Format cell content
            cell_text = format_cell(cell.text)
            cells.append(cell_text)

        # Create markdown row with pipes
        markdown_row = "| " + " | ".join(cells) + " |"
        markdown_rows.append(markdown_row)

        # Add separator after first row (header)
        if row_idx == 0:
            separator = "| " + " | ".join(["---"] * len(cells)) + " |"
            markdown_rows.append(separator)

    return "\n".join(markdown_rows)
