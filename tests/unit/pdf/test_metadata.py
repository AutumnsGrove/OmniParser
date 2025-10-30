"""
Unit tests for PDF metadata extraction utilities.

Tests the metadata extraction functions including date parsing, keyword parsing,
and custom field extraction.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from omniparser.parsers.pdf.metadata import (
    build_custom_fields,
    extract_pdf_metadata,
    parse_keywords_to_tags,
    parse_pdf_date,
)


class TestExtractPDFMetadata:
    """Test extract_pdf_metadata function."""

    def test_extract_pdf_metadata_complete(self) -> None:
        """Test metadata extraction with all fields present."""
        # Mock document with full metadata
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Test PDF Document",
            "author": "John Doe",
            "subject": "Test Subject",
            "keywords": "pdf, test, document",
            "creator": "Test Creator",
            "producer": "Test Producer",
            "creationDate": "D:20240101120000",
            "format": "PDF 1.7",
        }
        mock_doc.__len__.return_value = 10

        # Create temporary file for file_path
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"fake pdf content for testing")
            tmp_path = Path(tmp.name)

        try:
            metadata = extract_pdf_metadata(mock_doc, tmp_path)

            assert metadata.title == "Test PDF Document"
            assert metadata.author == "John Doe"
            assert metadata.description == "Test Subject"
            assert metadata.tags == ["pdf", "test", "document"]
            assert metadata.original_format == "pdf"
            assert metadata.publication_date == datetime(2024, 1, 1, 12, 0, 0)
            assert metadata.custom_fields["page_count"] == 10
            assert metadata.custom_fields["creator"] == "Test Creator"
            assert metadata.custom_fields["producer"] == "Test Producer"
            assert metadata.custom_fields["pdf_version"] == "PDF 1.7"
            assert metadata.file_size > 0
        finally:
            tmp_path.unlink()

    def test_extract_pdf_metadata_minimal(self) -> None:
        """Test metadata extraction with minimal metadata."""
        # Mock document with minimal metadata
        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "Minimal PDF"}
        mock_doc.__len__.return_value = 5

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            metadata = extract_pdf_metadata(mock_doc, tmp_path)

            assert metadata.title == "Minimal PDF"
            assert metadata.author is None
            assert metadata.description is None
            assert metadata.tags == []
            assert metadata.publication_date is None
            assert metadata.custom_fields["page_count"] == 5
            assert metadata.custom_fields["creator"] is None
            assert metadata.custom_fields["producer"] is None
        finally:
            tmp_path.unlink()

    def test_extract_pdf_metadata_no_metadata(self) -> None:
        """Test metadata extraction with no metadata (empty dict)."""
        # Mock document with no metadata
        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.__len__.return_value = 1

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", prefix="test_document_", delete=False
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            metadata = extract_pdf_metadata(mock_doc, tmp_path)

            # Should use filename when no title
            assert tmp_path.stem in metadata.title
            assert metadata.author is None
            assert metadata.description is None
            assert metadata.custom_fields["page_count"] == 1
        finally:
            tmp_path.unlink()

    def test_extract_pdf_metadata_none_metadata(self) -> None:
        """Test metadata extraction when doc.metadata is None."""
        # Mock document with None metadata
        mock_doc = MagicMock()
        mock_doc.metadata = None
        mock_doc.__len__.return_value = 1

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            metadata = extract_pdf_metadata(mock_doc, tmp_path)

            # Should handle None metadata gracefully
            assert metadata.title == tmp_path.stem
            assert metadata.author is None
        finally:
            tmp_path.unlink()


class TestParsePDFDate:
    """Test parse_pdf_date function."""

    def test_parse_pdf_date_valid(self) -> None:
        """Test parsing valid PDF date format."""
        date_str = "D:20240101120000"
        result = parse_pdf_date(date_str)

        assert result == datetime(2024, 1, 1, 12, 0, 0)

    def test_parse_pdf_date_valid_with_timezone(self) -> None:
        """Test parsing PDF date with timezone info (timezone is ignored)."""
        date_str = "D:20240315143000+05'00'"
        result = parse_pdf_date(date_str)

        # Only parses up to seconds (YYYYMMDDHHmmSS = 14 chars after D:)
        assert result == datetime(2024, 3, 15, 14, 30, 0)

    def test_parse_pdf_date_invalid(self) -> None:
        """Test parsing invalid date format."""
        date_str = "invalid_date"
        result = parse_pdf_date(date_str)

        assert result is None

    def test_parse_pdf_date_none(self) -> None:
        """Test parsing None input."""
        result = parse_pdf_date(None)

        assert result is None

    def test_parse_pdf_date_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_pdf_date("")

        assert result is None

    def test_parse_pdf_date_no_prefix(self) -> None:
        """Test parsing date without D: prefix."""
        date_str = "20240101120000"
        result = parse_pdf_date(date_str)

        # Should return None because it doesn't start with "D:"
        assert result is None

    def test_parse_pdf_date_short_date(self) -> None:
        """Test parsing date with insufficient characters."""
        date_str = "D:2024"
        result = parse_pdf_date(date_str)

        # Should return None because there aren't enough characters
        assert result is None


class TestParseKeywordsToTags:
    """Test parse_keywords_to_tags function."""

    def test_parse_keywords_to_tags(self) -> None:
        """Test parsing comma-separated keywords."""
        keywords = "pdf, document, test"
        result = parse_keywords_to_tags(keywords)

        assert result == ["pdf", "document", "test"]

    def test_parse_keywords_to_tags_no_spaces(self) -> None:
        """Test parsing keywords without spaces."""
        keywords = "pdf,document,test"
        result = parse_keywords_to_tags(keywords)

        assert result == ["pdf", "document", "test"]

    def test_parse_keywords_to_tags_extra_spaces(self) -> None:
        """Test parsing keywords with extra whitespace."""
        keywords = "  pdf  ,  document  ,  test  "
        result = parse_keywords_to_tags(keywords)

        assert result == ["pdf", "document", "test"]

    def test_parse_keywords_to_tags_empty(self) -> None:
        """Test parsing empty keywords string."""
        result = parse_keywords_to_tags("")

        assert result == []

    def test_parse_keywords_to_tags_none(self) -> None:
        """Test parsing None keywords."""
        result = parse_keywords_to_tags(None)

        assert result == []

    def test_parse_keywords_to_tags_single_keyword(self) -> None:
        """Test parsing single keyword."""
        keywords = "pdf"
        result = parse_keywords_to_tags(keywords)

        assert result == ["pdf"]

    def test_parse_keywords_to_tags_with_empty_entries(self) -> None:
        """Test parsing keywords with empty entries (multiple commas)."""
        keywords = "pdf, , document, , test"
        result = parse_keywords_to_tags(keywords)

        # Empty entries should be filtered out
        assert result == ["pdf", "document", "test"]


class TestBuildCustomFields:
    """Test build_custom_fields function."""

    def test_build_custom_fields(self) -> None:
        """Test building custom fields with all metadata."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 42

        meta = {
            "creator": "Adobe Acrobat",
            "producer": "Adobe PDF Library",
            "format": "PDF 1.6",
        }

        result = build_custom_fields(mock_doc, meta)

        assert result["page_count"] == 42
        assert result["creator"] == "Adobe Acrobat"
        assert result["producer"] == "Adobe PDF Library"
        assert result["pdf_version"] == "PDF 1.6"

    def test_build_custom_fields_minimal(self) -> None:
        """Test building custom fields with minimal metadata."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        meta = {}

        result = build_custom_fields(mock_doc, meta)

        assert result["page_count"] == 1
        assert result["creator"] is None
        assert result["producer"] is None
        assert result["pdf_version"] == "Unknown"

    def test_build_custom_fields_partial(self) -> None:
        """Test building custom fields with partial metadata."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 10

        meta = {
            "creator": "Microsoft Word",
            # No producer or format
        }

        result = build_custom_fields(mock_doc, meta)

        assert result["page_count"] == 10
        assert result["creator"] == "Microsoft Word"
        assert result["producer"] is None
        assert result["pdf_version"] == "Unknown"
