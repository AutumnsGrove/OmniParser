"""
Unit tests for PDF table extraction and markdown conversion.

Tests the table extraction and markdown conversion functions including:
- extract_pdf_tables() with various scenarios
- table_to_markdown() with different table structures
- Edge cases and error handling
"""

from unittest.mock import MagicMock, patch

import pytest

from omniparser.parsers.pdf.tables import extract_pdf_tables, table_to_markdown


class TestTableToMarkdown:
    """Test table_to_markdown function."""

    def test_table_to_markdown_standard(self) -> None:
        """Test standard table with header and data rows."""
        table_data = [
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "SF"],
        ]

        result = table_to_markdown(table_data)

        assert "| Name | Age | City |" in result
        assert "| --- | --- | --- |" in result
        assert "| Alice | 30 | NYC |" in result
        assert "| Bob | 25 | SF |" in result

    def test_table_to_markdown_empty(self) -> None:
        """Test empty table returns empty string."""
        assert table_to_markdown([]) == ""

    def test_table_to_markdown_single_row(self) -> None:
        """Test single row table (header only) is discarded."""
        table_data = [["Header1", "Header2", "Header3"]]

        result = table_to_markdown(table_data)

        # Single-row tables should be discarded
        assert result == ""

    def test_table_to_markdown_no_header(self) -> None:
        """Test table with minimal data still formats correctly."""
        table_data = [
            ["A", "B"],
            ["C", "D"],
        ]

        result = table_to_markdown(table_data)

        assert "| A | B |" in result
        assert "| --- | --- |" in result
        assert "| C | D |" in result

    def test_table_to_markdown_special_chars(self) -> None:
        """Test table with special characters."""
        table_data = [
            ["Name", "Country"],
            ["Alice", "USA"],
            ["Bob", "UK"],
        ]

        result = table_to_markdown(table_data)

        assert "| Name | Country |" in result
        assert "| Alice | USA |" in result
        assert "| Bob | UK |" in result

    def test_table_to_markdown_none_cells(self) -> None:
        """Test table with None cells."""
        table_data = [
            ["A", None, "C"],
            ["D", "E", None],
        ]

        result = table_to_markdown(table_data)

        # None cells should be converted to empty strings
        assert "| A |  | C |" in result
        assert "| D | E |  |" in result

    def test_table_to_markdown_numeric_data(self) -> None:
        """Test table with numeric data."""
        table_data = [
            ["Product", "Price", "Quantity"],
            ["Widget", 19.99, 100],
            ["Gadget", 29.99, 50],
        ]

        result = table_to_markdown(table_data)

        assert "| Product | Price | Quantity |" in result
        assert "| Widget | 19.99 | 100 |" in result
        assert "| Gadget | 29.99 | 50 |" in result

    def test_table_to_markdown_empty_cells(self) -> None:
        """Test table with empty string cells."""
        table_data = [
            ["A", "B", "C"],
            ["", "Data", ""],
            ["X", "", "Y"],
        ]

        result = table_to_markdown(table_data)

        assert "|  | Data |  |" in result
        assert "| X |  | Y |" in result

    def test_table_to_markdown_large_table(self) -> None:
        """Test table with many rows and columns."""
        # Create 5x10 table
        header = [f"Col{i}" for i in range(5)]
        rows = [[f"R{row}C{col}" for col in range(5)] for row in range(10)]
        table_data = [header] + rows

        result = table_to_markdown(table_data)

        # Verify header
        assert "| Col0 | Col1 | Col2 | Col3 | Col4 |" in result
        # Verify separator
        assert "| --- | --- | --- | --- | --- |" in result
        # Verify first and last rows
        assert "| R0C0 | R0C1 | R0C2 | R0C3 | R0C4 |" in result
        assert "| R9C0 | R9C1 | R9C2 | R9C3 | R9C4 |" in result


class TestExtractPdfTables:
    """Test extract_pdf_tables function."""

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_with_tables(self, mock_fitz) -> None:
        """Test extraction with PDF containing tables."""
        # Mock PyMuPDF version check
        mock_fitz.version = ["1.18.0"]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page
        mock_page = MagicMock()

        # Mock table finder
        mock_table_finder = MagicMock()
        mock_table = MagicMock()
        mock_table.extract.return_value = [
            ["Name", "Age"],
            ["Alice", "30"],
            ["Bob", "25"],
        ]
        mock_table_finder.tables = [mock_table]
        mock_page.find_tables.return_value = mock_table_finder

        mock_doc.__getitem__.return_value = mock_page

        result = extract_pdf_tables(mock_doc)

        assert len(result) == 1
        assert "**Table from page 1**" in result[0]
        assert "| Name | Age |" in result[0]
        assert "| Alice | 30 |" in result[0]

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_no_tables(self, mock_fitz) -> None:
        """Test extraction with PDF without tables."""
        # Mock PyMuPDF version check
        mock_fitz.version = ["1.18.0"]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page with no tables
        mock_page = MagicMock()
        mock_table_finder = MagicMock()
        mock_table_finder.tables = []
        mock_page.find_tables.return_value = mock_table_finder

        mock_doc.__getitem__.return_value = mock_page

        result = extract_pdf_tables(mock_doc)

        assert result == []

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_empty_doc(self, mock_fitz) -> None:
        """Test extraction with empty PDF."""
        # Mock PyMuPDF version check
        mock_fitz.version = ["1.18.0"]

        # Mock empty document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 0

        result = extract_pdf_tables(mock_doc)

        assert result == []

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_multiple_pages(self, mock_fitz) -> None:
        """Test extraction across multiple pages."""
        # Mock PyMuPDF version check
        mock_fitz.version = ["1.18.0"]

        # Mock document with 2 pages
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Mock page 1 with table
        mock_page1 = MagicMock()
        mock_table_finder1 = MagicMock()
        mock_table1 = MagicMock()
        mock_table1.extract.return_value = [
            ["Col1", "Col2"],
            ["A", "B"],
        ]
        mock_table_finder1.tables = [mock_table1]
        mock_page1.find_tables.return_value = mock_table_finder1

        # Mock page 2 with table
        mock_page2 = MagicMock()
        mock_table_finder2 = MagicMock()
        mock_table2 = MagicMock()
        mock_table2.extract.return_value = [
            ["X", "Y"],
            ["1", "2"],
        ]
        mock_table_finder2.tables = [mock_table2]
        mock_page2.find_tables.return_value = mock_table_finder2

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]

        result = extract_pdf_tables(mock_doc)

        assert len(result) == 2
        assert "**Table from page 1**" in result[0]
        assert "**Table from page 2**" in result[1]

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_unsupported_version(self, mock_fitz) -> None:
        """Test extraction with unsupported PyMuPDF version."""
        # Mock old PyMuPDF version
        mock_fitz.version = ["1.17.0"]

        mock_doc = MagicMock()

        result = extract_pdf_tables(mock_doc)

        # Should return empty list for unsupported version
        assert result == []

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_single_row_discarded(self, mock_fitz) -> None:
        """Test that single-row tables are discarded."""
        # Mock PyMuPDF version check
        mock_fitz.version = ["1.18.0"]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page with single-row table
        mock_page = MagicMock()
        mock_table_finder = MagicMock()
        mock_table = MagicMock()
        mock_table.extract.return_value = [["Header1", "Header2"]]
        mock_table_finder.tables = [mock_table]
        mock_page.find_tables.return_value = mock_table_finder

        mock_doc.__getitem__.return_value = mock_page

        result = extract_pdf_tables(mock_doc)

        # Single-row table should be discarded
        assert result == []

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_attribute_error(self, mock_fitz) -> None:
        """Test handling of AttributeError during extraction."""
        # Mock PyMuPDF version check
        mock_fitz.version = ["1.18.0"]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page that raises AttributeError
        mock_page = MagicMock()
        mock_page.find_tables.side_effect = AttributeError("find_tables not available")

        mock_doc.__getitem__.return_value = mock_page

        result = extract_pdf_tables(mock_doc)

        # Should handle error and return empty list
        assert result == []

    @patch("omniparser.parsers.pdf.tables.fitz")
    def test_extract_pdf_tables_general_exception(self, mock_fitz) -> None:
        """Test handling of general exception during extraction."""
        # Mock PyMuPDF version check
        mock_fitz.version = ["1.18.0"]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page that raises exception
        mock_page = MagicMock()
        mock_page.find_tables.side_effect = RuntimeError("Table extraction failed")

        mock_doc.__getitem__.return_value = mock_page

        result = extract_pdf_tables(mock_doc)

        # Should handle error and return empty list
        assert result == []
