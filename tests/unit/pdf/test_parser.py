"""
Unit tests for PDF parser orchestrator.

Tests the main parse_pdf function that coordinates all PDF parsing operations.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from omniparser.exceptions import FileReadError, ValidationError
from omniparser.models import (
    Chapter,
    Document,
    ImageReference,
    Metadata,
    ProcessingInfo,
)
from omniparser.parsers.pdf.parser import parse_pdf


@pytest.fixture
def mock_pdf_document():
    """Create a mock PyMuPDF document."""
    doc = MagicMock()
    doc.metadata = {
        "title": "Test Document",
        "author": "Test Author",
        "subject": "Test Subject",
        "keywords": "test, pdf",
        "creationDate": "D:20240101120000",
    }
    doc.__len__.return_value = 10  # 10 pages
    doc.close = MagicMock()
    return doc


@pytest.fixture
def mock_metadata():
    """Create mock metadata."""
    return Metadata(
        title="Test Document",
        author="Test Author",
        description="Test Subject",
        tags=["test", "pdf"],
        original_format="pdf",
        file_size=1024,
        custom_fields={"page_count": 10},
    )


@pytest.fixture
def mock_chapters():
    """Create mock chapters."""
    return [
        Chapter(
            chapter_id=1,
            title="Chapter 1",
            content="Content 1",
            start_position=0,
            end_position=100,
            word_count=50,
            level=1,
        ),
        Chapter(
            chapter_id=2,
            title="Chapter 2",
            content="Content 2",
            start_position=100,
            end_position=200,
            word_count=50,
            level=1,
        ),
    ]


@pytest.fixture
def mock_images():
    """Create mock image references."""
    return [
        ImageReference(
            image_id="img_0001",
            position=50,
            file_path="/tmp/img_0001.png",
            alt_text="Test image",
            size=(800, 600),
            format="png",
        )
    ]


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "images"
    output_dir.mkdir()
    return output_dir


class TestParsePdfBasic:
    """Test basic PDF parsing functionality."""

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_metadata")
    @patch("omniparser.parsers.pdf.parser.extract_text_content")
    @patch("omniparser.parsers.pdf.parser.process_pdf_headings")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_tables")
    @patch("omniparser.parsers.pdf.parser.clean_text")
    def test_parse_pdf_basic(
        self,
        mock_clean,
        mock_tables,
        mock_headings,
        mock_text,
        mock_metadata,
        mock_validate,
        mock_pdf_document,
        tmp_path,
    ):
        """Test basic PDF parsing without images."""
        # Setup mocks
        mock_validate.return_value = mock_pdf_document
        mock_metadata.return_value = Metadata(title="Test", original_format="pdf")
        mock_text.return_value = ("Test content", [])
        mock_headings.return_value = ("# Test\n\nTest content", [])
        mock_tables.return_value = []
        mock_clean.return_value = "# Test\n\nTest content"

        # Parse PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        doc = parse_pdf(pdf_path)

        # Verify result
        assert isinstance(doc, Document)
        assert doc.content == "# Test\n\nTest content"
        assert doc.metadata.title == "Test"
        assert doc.processing_info.parser_used == "PDFParser"
        assert len(doc.images) == 0

        # Verify mocks called
        mock_validate.assert_called_once_with(pdf_path)
        mock_text.assert_called_once()
        mock_headings.assert_called_once()
        mock_pdf_document.close.assert_called_once()

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_metadata")
    @patch("omniparser.parsers.pdf.parser.extract_text_content")
    @patch("omniparser.parsers.pdf.parser.process_pdf_headings")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_images")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_tables")
    @patch("omniparser.parsers.pdf.parser.clean_text")
    def test_parse_pdf_with_images(
        self,
        mock_clean,
        mock_tables,
        mock_images_func,
        mock_headings,
        mock_text,
        mock_metadata_func,
        mock_validate,
        mock_pdf_document,
        mock_images,
        tmp_output_dir,
        tmp_path,
    ):
        """Test PDF parsing with image extraction."""
        # Setup mocks
        mock_validate.return_value = mock_pdf_document
        mock_metadata_func.return_value = Metadata(title="Test", original_format="pdf")
        mock_text.return_value = ("Test content", [])
        mock_headings.return_value = ("Test content", [])
        mock_tables.return_value = []
        mock_clean.return_value = "Test content"
        mock_images_func.return_value = mock_images

        # Parse PDF with output_dir
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        doc = parse_pdf(pdf_path, output_dir=tmp_output_dir)

        # Verify images extracted
        assert len(doc.images) == 1
        assert doc.images[0].image_id == "img_0001"
        mock_images_func.assert_called_once()


class TestParsePdfOptions:
    """Test PDF parsing with various options."""

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_metadata")
    @patch("omniparser.parsers.pdf.parser.extract_text_content")
    @patch("omniparser.parsers.pdf.parser.process_pdf_headings")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_tables")
    @patch("omniparser.parsers.pdf.parser.clean_text")
    def test_parse_pdf_with_ocr_options(
        self,
        mock_clean,
        mock_tables,
        mock_headings,
        mock_text,
        mock_metadata,
        mock_validate,
        mock_pdf_document,
        tmp_path,
    ):
        """Test PDF parsing with OCR options."""
        # Setup mocks
        mock_validate.return_value = mock_pdf_document
        mock_metadata.return_value = Metadata(title="Test", original_format="pdf")
        mock_text.return_value = ("OCR content", [])
        mock_headings.return_value = ("OCR content", [])
        mock_tables.return_value = []
        mock_clean.return_value = "OCR content"

        # Parse with OCR options
        pdf_path = tmp_path / "scanned.pdf"
        pdf_path.touch()
        options = {
            "use_ocr": True,
            "ocr_language": "fra",
            "ocr_timeout": 600,
            "max_pages": 5,
        }
        doc = parse_pdf(pdf_path, options=options)

        # Verify OCR options passed
        call_kwargs = mock_text.call_args[1]
        assert call_kwargs["use_ocr"] is True
        assert call_kwargs["ocr_language"] == "fra"
        assert call_kwargs["ocr_timeout"] == 600
        assert call_kwargs["max_pages"] == 5

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_metadata")
    @patch("omniparser.parsers.pdf.parser.extract_text_content")
    @patch("omniparser.parsers.pdf.parser.process_pdf_headings")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_tables")
    def test_parse_pdf_without_text_cleaning(
        self,
        mock_tables,
        mock_headings,
        mock_text,
        mock_metadata,
        mock_validate,
        mock_pdf_document,
        tmp_path,
    ):
        """Test PDF parsing without text cleaning."""
        # Setup mocks
        mock_validate.return_value = mock_pdf_document
        mock_metadata.return_value = Metadata(title="Test", original_format="pdf")
        mock_text.return_value = ("Raw content", [])
        mock_headings.return_value = ("Raw content", [])
        mock_tables.return_value = []

        # Parse without cleaning
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        options = {"clean_text": False}

        with patch("omniparser.parsers.pdf.parser.clean_text") as mock_clean:
            doc = parse_pdf(pdf_path, options=options)
            # clean_text should not be called
            mock_clean.assert_not_called()
            assert doc.content == "Raw content"


class TestParsePdfTables:
    """Test PDF parsing with table extraction."""

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_metadata")
    @patch("omniparser.parsers.pdf.parser.extract_text_content")
    @patch("omniparser.parsers.pdf.parser.process_pdf_headings")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_tables")
    @patch("omniparser.parsers.pdf.parser.clean_text")
    def test_parse_pdf_with_tables(
        self,
        mock_clean,
        mock_tables,
        mock_headings,
        mock_text,
        mock_metadata,
        mock_validate,
        mock_pdf_document,
        tmp_path,
    ):
        """Test PDF parsing with table extraction."""
        # Setup mocks
        mock_validate.return_value = mock_pdf_document
        mock_metadata.return_value = Metadata(title="Test", original_format="pdf")
        mock_text.return_value = ("Content", [])
        mock_headings.return_value = ("Content", [])
        mock_tables.return_value = ["**Table 1**\n| A | B |\n| --- | --- |"]
        mock_clean.return_value = (
            "Content\n\n## Extracted Tables\n\n**Table 1**\n| A | B |\n| --- | --- |"
        )

        # Parse PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        doc = parse_pdf(pdf_path)

        # Verify tables in content
        assert "## Extracted Tables" in doc.content
        assert "**Table 1**" in doc.content
        mock_tables.assert_called_once()


class TestParsePdfErrors:
    """Test PDF parsing error handling."""

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    def test_parse_pdf_invalid_file(self, mock_validate, tmp_path):
        """Test parsing invalid PDF file."""
        mock_validate.side_effect = ValidationError("Invalid PDF")

        pdf_path = tmp_path / "invalid.pdf"
        pdf_path.touch()

        with pytest.raises(ValidationError, match="Invalid PDF"):
            parse_pdf(pdf_path)

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    def test_parse_pdf_file_read_error(self, mock_validate, tmp_path):
        """Test parsing PDF with read error."""
        mock_validate.side_effect = FileReadError("Cannot read PDF")

        pdf_path = tmp_path / "corrupted.pdf"
        pdf_path.touch()

        with pytest.raises(FileReadError, match="Cannot read PDF"):
            parse_pdf(pdf_path)

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_metadata")
    def test_parse_pdf_closes_on_error(
        self, mock_metadata, mock_validate, mock_pdf_document, tmp_path
    ):
        """Test that PDF is closed even on error."""
        mock_validate.return_value = mock_pdf_document
        mock_metadata.side_effect = Exception("Metadata error")

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        with pytest.raises(Exception, match="Metadata error"):
            parse_pdf(pdf_path)

        # Verify PDF was closed
        mock_pdf_document.close.assert_called_once()


class TestParsePdfProcessingInfo:
    """Test ProcessingInfo generation."""

    @patch("omniparser.parsers.pdf.parser.validate_and_load_pdf")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_metadata")
    @patch("omniparser.parsers.pdf.parser.extract_text_content")
    @patch("omniparser.parsers.pdf.parser.process_pdf_headings")
    @patch("omniparser.parsers.pdf.parser.extract_pdf_tables")
    @patch("omniparser.parsers.pdf.parser.clean_text")
    def test_processing_info_populated(
        self,
        mock_clean,
        mock_tables,
        mock_headings,
        mock_text,
        mock_metadata,
        mock_validate,
        mock_pdf_document,
        tmp_path,
    ):
        """Test that ProcessingInfo is properly populated."""
        # Setup mocks
        mock_validate.return_value = mock_pdf_document
        mock_metadata.return_value = Metadata(title="Test", original_format="pdf")
        mock_text.return_value = ("Test content", [])
        mock_headings.return_value = ("Test content", [])
        mock_tables.return_value = []
        mock_clean.return_value = "Test content"

        # Parse PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        options = {"use_ocr": True, "max_pages": 10}
        doc = parse_pdf(pdf_path, options=options)

        # Verify ProcessingInfo
        assert doc.processing_info.parser_used == "PDFParser"
        assert doc.processing_info.parser_version == "1.0.0"
        assert doc.processing_info.processing_time > 0
        assert isinstance(doc.processing_info.timestamp, datetime)
        assert doc.processing_info.options_used == options
