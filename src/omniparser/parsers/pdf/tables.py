"""
PDF table extraction and markdown conversion.

This module provides functions for extracting tables from PDF documents
and converting them to markdown format. It includes:
- Table detection using PyMuPDF's find_tables()
- Table data extraction
- Markdown table formatting
- Validation of table structure

The module requires PyMuPDF >= 1.18.0 for table extraction support.
"""

import logging
from typing import List

import fitz  # PyMuPDF

from .utils import MIN_TABLE_ROWS

logger = logging.getLogger(__name__)


def extract_pdf_tables(doc: fitz.Document) -> List[str]:
    """
    Extract tables from PDF and convert to markdown format.

    Iterates through all pages in the PDF document, detects tables using
    PyMuPDF's find_tables() method, and converts them to markdown strings.

    Args:
        doc: PyMuPDF document object.

    Returns:
        List of markdown-formatted table strings with page numbers.

    Note:
        Requires PyMuPDF >= 1.18.0 for table extraction support.
        Tables with fewer than MIN_TABLE_ROWS are discarded.

    Example:
        >>> import fitz
        >>> doc = fitz.open("document.pdf")
        >>> tables = extract_pdf_tables(doc)
        >>> print(tables[0])
        **Table from page 1**
        | Header1 | Header2 |
        | --- | --- |
        | Data1 | Data2 |
    """
    # Check PyMuPDF version for table extraction support
    fitz_version = tuple(map(int, fitz.version[0].split(".")))
    if fitz_version < (1, 18, 0):
        logger.debug(
            f"PyMuPDF version {fitz.version[0]} does not support table extraction"
        )
        return []

    tables = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        try:
            # Find tables on page
            table_finder = page.find_tables()

            if not table_finder or not table_finder.tables:
                continue

            for table in table_finder.tables:
                # Extract table data
                table_data = table.extract()

                if not table_data:
                    continue

                # Convert to markdown
                markdown_table = table_to_markdown(table_data)
                if markdown_table:
                    tables.append(
                        f"**Table from page {page_num + 1}**\n\n{markdown_table}"
                    )

        except AttributeError as e:
            # find_tables() not available in this PyMuPDF version
            logger.debug(
                f"Table extraction not supported or failed on page {page_num + 1}: {e}"
            )
        except Exception as e:
            # Log exception type for debugging
            logger.warning(
                f"Table extraction failed on page {page_num + 1} "
                f"({type(e).__name__}): {e}"
            )

    logger.info(f"Extracted {len(tables)} tables")
    return tables


def table_to_markdown(table_data: List[List]) -> str:
    """
    Convert table data to markdown format.

    Single-row tables (header only) are discarded as they likely represent
    formatting artifacts rather than actual data tables.

    Args:
        table_data: 2D list of table cells (rows x columns).

    Returns:
        Markdown-formatted table string, or empty string if invalid.

    Example:
        >>> table_data = [
        ...     ["Name", "Age"],
        ...     ["Alice", "30"],
        ...     ["Bob", "25"]
        ... ]
        >>> print(table_to_markdown(table_data))
        | Name | Age |
        | --- | --- |
        | Alice | 30 |
        | Bob | 25 |
    """
    if not table_data:
        return ""

    if len(table_data) < MIN_TABLE_ROWS:
        # Single-row table (just headers) - likely not a real table
        logger.debug(f"Discarding single-row table: {table_data[0]}")
        return ""

    lines = []

    # Header row
    header = table_data[0]
    lines.append("| " + " | ".join(str(cell or "") for cell in header) + " |")

    # Separator
    lines.append("| " + " | ".join("---" for _ in header) + " |")

    # Data rows
    for row in table_data[1:]:
        lines.append("| " + " | ".join(str(cell or "") for cell in row) + " |")

    return "\n".join(lines)
