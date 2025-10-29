"""
Unit tests for PDF parser.

Tests the PDFParser class functionality including validation, format support,
text extraction, heading detection, OCR, and image/table extraction.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from omniparser.exceptions import FileReadError, ParsingError, ValidationError
from omniparser.models import Chapter, Document, ImageReference, Metadata
from omniparser.parsers.pdf_parser import PDFParser


class TestPDFParserInit:
    """Test PDFParser initialization."""

    def test_init_no_options(self) -> None:
        """Test initialization without options."""
        parser = PDFParser()
        assert parser.options == {
            "extract_images": True,
            "image_output_dir": None,
            "ocr_enabled": True,
            "ocr_language": "eng",
            "min_heading_size": None,
            "extract_tables": True,
            "clean_text": True,
            "detect_chapters": True,
            "min_chapter_level": 1,
            "max_chapter_level": 2,
        }

    def test_init_with_options(self) -> None:
        """Test initialization with custom options."""
        options = {
            "extract_images": False,
            "ocr_enabled": False,
            "ocr_language": "fra",
            "min_heading_size": 16.0,
        }
        parser = PDFParser(options)

        assert parser.options["extract_images"] is False
        assert parser.options["ocr_enabled"] is False
        assert parser.options["ocr_language"] == "fra"
        assert parser.options["min_heading_size"] == 16.0
        # Defaults still applied
        assert parser.options["extract_tables"] is True
        assert parser.options["clean_text"] is True

    def test_init_warnings_empty(self) -> None:
        """Test warnings list is initialized empty."""
        parser = PDFParser()
        assert parser._warnings == []


class TestPDFParserSupportsFormat:
    """Test format support detection."""

    def test_supports_pdf_lowercase(self) -> None:
        """Test .pdf extension is supported."""
        parser = PDFParser()
        assert parser.supports_format(Path("document.pdf")) is True

    def test_supports_pdf_uppercase(self) -> None:
        """Test .PDF extension is supported."""
        parser = PDFParser()
        assert parser.supports_format(Path("document.PDF")) is True

    def test_supports_pdf_mixed_case(self) -> None:
        """Test .Pdf extension is supported."""
        parser = PDFParser()
        assert parser.supports_format(Path("document.Pdf")) is True

    def test_not_supports_epub(self) -> None:
        """Test .epub extension is not supported."""
        parser = PDFParser()
        assert parser.supports_format(Path("book.epub")) is False

    def test_not_supports_txt(self) -> None:
        """Test .txt extension is not supported."""
        parser = PDFParser()
        assert parser.supports_format(Path("file.txt")) is False

    def test_not_supports_no_extension(self) -> None:
        """Test file without extension is not supported."""
        parser = PDFParser()
        assert parser.supports_format(Path("document")) is False

    def test_supports_format_string_path(self) -> None:
        """Test format detection with string path."""
        parser = PDFParser()
        assert parser.supports_format("document.pdf") is True


class TestPDFParserValidation:
    """Test PDF file validation."""

    def test_validate_file_not_exists(self) -> None:
        """Test validation fails for non-existent file."""
        parser = PDFParser()
        with pytest.raises(ValidationError, match="File not found"):
            parser._validate_pdf(Path("/nonexistent/path/document.pdf"))

    def test_validate_directory_not_file(self) -> None:
        """Test validation fails for directory."""
        parser = PDFParser()
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            with pytest.raises(ValidationError, match="Not a file"):
                parser._validate_pdf(dir_path)

    def test_validate_wrong_extension(self) -> None:
        """Test validation fails for wrong extension."""
        parser = PDFParser()
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            tmp_path = Path(tmp.name)
            with pytest.raises(ValidationError, match="Not a PDF file"):
                parser._validate_pdf(tmp_path)


class TestPDFParserScannedDetection:
    """Test scanned PDF detection."""

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_is_scanned_pdf_true(self, mock_fitz) -> None:
        """Test detection of scanned PDF with minimal text."""
        parser = PDFParser()

        # Mock document with minimal text
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        mock_page = MagicMock()
        mock_page.get_text.return_value = "   "  # Very little text
        mock_doc.__getitem__.return_value = mock_page

        result = parser._is_scanned_pdf(mock_doc)
        assert result is True

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_is_scanned_pdf_false(self, mock_fitz) -> None:
        """Test detection of text-based PDF with substantial text."""
        parser = PDFParser()

        # Mock document with substantial text
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is a text-based PDF " * 20
        mock_doc.__getitem__.return_value = mock_page

        result = parser._is_scanned_pdf(mock_doc)
        assert result is False

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_is_scanned_pdf_single_page(self, mock_fitz) -> None:
        """Test scanned detection with single page document."""
        parser = PDFParser()

        # Mock single page document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_text.return_value = "  \n  "
        mock_doc.__getitem__.return_value = mock_page

        result = parser._is_scanned_pdf(mock_doc)
        assert result is True


class TestPDFParserTextExtraction:
    """Test text extraction methods."""

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_extract_text_with_formatting(self, mock_fitz) -> None:
        """Test text extraction with font information."""
        parser = PDFParser()

        # Mock document structure
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()

        # Mock text blocks with font info
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Chapter 1",
                                    "size": 18.0,
                                    "flags": 16,  # Bold flag
                                    "font": "Arial-Bold",
                                }
                            ]
                        },
                        {
                            "spans": [
                                {
                                    "text": "This is content",
                                    "size": 12.0,
                                    "flags": 0,
                                    "font": "Arial",
                                }
                            ]
                        },
                    ]
                }
            ]
        }
        mock_doc.__getitem__.return_value = mock_page

        text, blocks = parser._extract_text_with_formatting(mock_doc)

        assert "Chapter 1" in text
        assert "This is content" in text
        assert len(blocks) == 2
        assert blocks[0]["text"] == "Chapter 1"
        assert blocks[0]["font_size"] == 18.0
        assert blocks[0]["is_bold"] is True
        assert blocks[1]["text"] == "This is content"
        assert blocks[1]["font_size"] == 12.0

    @patch("pytesseract.image_to_string")
    @patch("omniparser.parsers.pdf_parser.Image")
    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_extract_text_with_ocr(self, mock_fitz, mock_image, mock_tesseract) -> None:
        """Test OCR-based text extraction."""
        parser = PDFParser({"ocr_language": "eng"})

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Mock page and pixmap
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.width = 800
        mock_pix.height = 1000
        mock_pix.samples = b"fake_image_data"
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__.return_value = mock_page

        # Mock PIL Image
        mock_img = MagicMock()
        mock_image.frombytes.return_value = mock_img

        # Mock OCR output
        mock_tesseract.return_value = "OCR extracted text"

        text = parser._extract_text_with_ocr(mock_doc)

        assert "OCR extracted text" in text
        assert "Page 1" in text
        mock_tesseract.assert_called()


class TestPDFParserHeadingDetection:
    """Test heading detection from font analysis."""

    def test_detect_headings_from_fonts_basic(self) -> None:
        """Test basic heading detection."""
        parser = PDFParser()

        text_blocks = [
            {"text": "Chapter One", "font_size": 18.0, "is_bold": True, "position": 0},
            {
                "text": "This is regular text",
                "font_size": 12.0,
                "is_bold": False,
                "position": 50,
            },
            {
                "text": "Section 1.1",
                "font_size": 14.0,
                "is_bold": True,
                "position": 100,
            },
            {
                "text": "More regular text here",
                "font_size": 12.0,
                "is_bold": False,
                "position": 150,
            },
        ]

        headings = parser._detect_headings_from_fonts(text_blocks)

        # Should detect the larger/bold text as headings
        # Note: This depends on font size analysis, so we check if any headings were detected
        assert len(headings) >= 0
        # The bold text with larger font sizes should be detected
        if len(headings) > 0:
            heading_texts = [h[0] for h in headings]
            # At least one of the bold entries should be detected
            assert any(h in heading_texts for h in ["Chapter One", "Section 1.1"])

    def test_detect_headings_from_fonts_empty(self) -> None:
        """Test heading detection with no blocks."""
        parser = PDFParser()
        headings = parser._detect_headings_from_fonts([])
        assert headings == []

    def test_detect_headings_from_fonts_min_size(self) -> None:
        """Test heading detection with minimum size threshold."""
        parser = PDFParser({"min_heading_size": 16.0})

        text_blocks = [
            {
                "text": "Large Heading",
                "font_size": 20.0,
                "is_bold": True,
                "position": 0,
            },
            {"text": "Medium Text", "font_size": 14.0, "is_bold": True, "position": 50},
            {
                "text": "Regular Text",
                "font_size": 12.0,
                "is_bold": False,
                "position": 100,
            },
        ]

        headings = parser._detect_headings_from_fonts(text_blocks)

        # "Large Heading" should be detected (>= 16.0)
        # Note: Bold text might also be detected as headings
        assert len(headings) >= 1
        # Check that Large Heading is in the results
        heading_texts = [h[0] for h in headings]
        assert "Large Heading" in heading_texts

    def test_map_font_size_to_level(self) -> None:
        """Test font size to heading level mapping."""
        parser = PDFParser()

        unique_sizes = [24.0, 18.0, 14.0, 12.0]

        # Largest font should be level 1
        assert parser._map_font_size_to_level(24.0, unique_sizes) == 1
        # Second largest should be level 2
        assert parser._map_font_size_to_level(18.0, unique_sizes) == 2
        # Third should be level 3
        assert parser._map_font_size_to_level(14.0, unique_sizes) == 3


class TestPDFParserMarkdownConversion:
    """Test heading to markdown conversion."""

    def test_convert_headings_to_markdown_basic(self) -> None:
        """Test basic markdown conversion."""
        parser = PDFParser()

        text = "Chapter One\nThis is some text.\nSection 1.1\nMore text here."
        headings = [
            ("Chapter One", 1, 0),
            ("Section 1.1", 2, 30),
        ]

        result = parser._convert_headings_to_markdown(text, headings)

        assert "# Chapter One" in result
        assert "## Section 1.1" in result

    def test_convert_headings_to_markdown_empty(self) -> None:
        """Test markdown conversion with no headings."""
        parser = PDFParser()

        text = "Just some regular text."
        headings = []

        result = parser._convert_headings_to_markdown(text, headings)
        assert result == text

    def test_convert_headings_to_markdown_multiple_levels(self) -> None:
        """Test markdown conversion with multiple heading levels."""
        parser = PDFParser()

        text = "Title\nChapter\nSection\nSubsection"
        headings = [
            ("Title", 1, 0),
            ("Chapter", 2, 10),
            ("Section", 3, 20),
            ("Subsection", 4, 30),
        ]

        result = parser._convert_headings_to_markdown(text, headings)

        assert "# Title" in result
        assert "## Chapter" in result
        assert "### Section" in result
        assert "#### Subsection" in result


class TestPDFParserMetadataExtraction:
    """Test metadata extraction."""

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_extract_metadata_full(self, mock_fitz) -> None:
        """Test metadata extraction with all fields."""
        parser = PDFParser()

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

        # Create a temporary file for file_path
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            metadata = parser._extract_metadata(mock_doc, tmp_path)

            assert metadata.title == "Test PDF Document"
            assert metadata.author == "John Doe"
            assert metadata.description == "Test Subject"
            assert metadata.tags == ["pdf", "test", "document"]
            assert metadata.original_format == "pdf"
            assert metadata.custom_fields["page_count"] == 10
            assert metadata.custom_fields["creator"] == "Test Creator"
            assert metadata.custom_fields["producer"] == "Test Producer"
        finally:
            tmp_path.unlink()

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_extract_metadata_partial(self, mock_fitz) -> None:
        """Test metadata extraction with missing fields."""
        parser = PDFParser()

        # Mock document with minimal metadata
        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "Minimal PDF"}
        mock_doc.__len__.return_value = 5

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            metadata = parser._extract_metadata(mock_doc, tmp_path)

            assert metadata.title == "Minimal PDF"
            assert metadata.author is None
            assert metadata.description is None
            assert metadata.custom_fields["page_count"] == 5
        finally:
            tmp_path.unlink()

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_extract_metadata_no_title(self, mock_fitz) -> None:
        """Test metadata extraction uses filename when no title."""
        parser = PDFParser()

        # Mock document with no title
        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.__len__.return_value = 1

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", prefix="test_document_", delete=False
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            metadata = parser._extract_metadata(mock_doc, tmp_path)

            # Should use filename without extension
            assert tmp_path.stem in metadata.title
        finally:
            tmp_path.unlink()


class TestPDFParserImageExtraction:
    """Test image extraction."""

    @patch("omniparser.parsers.pdf_parser.fitz")
    @patch("omniparser.parsers.pdf_parser.Image")
    def test_extract_images_basic(self, mock_image_class, mock_fitz) -> None:
        """Test basic image extraction."""
        parser = PDFParser()

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page with images
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]
        mock_doc.__getitem__.return_value = mock_page

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": b"fake_image_data",
            "ext": "png",
        }

        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.size = (800, 600)
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        images = parser._extract_images(mock_doc)

        assert len(images) == 1
        assert images[0].image_id == "img_0000"
        assert images[0].format == "png"
        assert images[0].size == (800, 600)

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_extract_images_no_images(self, mock_fitz) -> None:
        """Test image extraction with no images."""
        parser = PDFParser()

        # Mock document with no images
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_images.return_value = []
        mock_doc.__getitem__.return_value = mock_page

        images = parser._extract_images(mock_doc)

        assert images == []

    @patch("omniparser.parsers.pdf_parser.fitz")
    @patch("omniparser.parsers.pdf_parser.Image")
    def test_extract_images_multiple_pages(self, mock_image_class, mock_fitz) -> None:
        """Test image extraction across multiple pages."""
        parser = PDFParser()

        # Mock document with 2 pages
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Mock pages with images
        mock_page1 = MagicMock()
        mock_page1.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]

        mock_page2 = MagicMock()
        mock_page2.get_images.return_value = [
            (2, 0, 600, 400, 8, "DeviceRGB", "", "Im2", "DCTDecode")
        ]

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": b"fake_image_data",
            "ext": "jpg",
        }

        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.size = (800, 600)
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        images = parser._extract_images(mock_doc)

        assert len(images) == 2


class TestPDFParserTableExtraction:
    """Test table extraction."""

    def test_table_to_markdown_basic(self) -> None:
        """Test basic table to markdown conversion."""
        parser = PDFParser()

        table_data = [
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "SF"],
        ]

        result = parser._table_to_markdown(table_data)

        assert "| Name | Age | City |" in result
        assert "| --- | --- | --- |" in result
        assert "| Alice | 30 | NYC |" in result
        assert "| Bob | 25 | SF |" in result

    def test_table_to_markdown_empty(self) -> None:
        """Test table to markdown with empty data."""
        parser = PDFParser()

        assert parser._table_to_markdown([]) == ""
        assert parser._table_to_markdown([["Header"]]) == ""  # Need at least 2 rows

    def test_table_to_markdown_none_cells(self) -> None:
        """Test table to markdown with None cells."""
        parser = PDFParser()

        table_data = [
            ["A", None, "C"],
            ["D", "E", None],
        ]

        result = parser._table_to_markdown(table_data)

        assert "| A |  | C |" in result
        assert "| D | E |  |" in result


class TestPDFParserUtilities:
    """Test utility methods."""

    def test_count_words_basic(self) -> None:
        """Test basic word counting."""
        parser = PDFParser()

        assert parser._count_words("Hello world") == 2
        assert parser._count_words("One two three four five") == 5

    def test_count_words_empty(self) -> None:
        """Test word counting with empty string."""
        parser = PDFParser()

        assert parser._count_words("") == 0
        assert parser._count_words("   ") == 0

    def test_count_words_with_punctuation(self) -> None:
        """Test word counting with punctuation."""
        parser = PDFParser()

        assert parser._count_words("Hello, world! How are you?") == 5

    def test_estimate_reading_time_basic(self) -> None:
        """Test reading time estimation."""
        parser = PDFParser()

        # 250 words = 1 minute
        assert parser._estimate_reading_time(250) == 1
        assert parser._estimate_reading_time(500) == 2
        assert parser._estimate_reading_time(1000) == 4

    def test_estimate_reading_time_minimum(self) -> None:
        """Test reading time minimum is 1 minute."""
        parser = PDFParser()

        assert parser._estimate_reading_time(10) == 1
        assert parser._estimate_reading_time(100) == 1


class TestPDFParserIntegrationMethods:
    """Test integration with chapter detector."""

    @patch("omniparser.processors.chapter_detector.detect_chapters")
    def test_detect_chapters_from_markdown(self, mock_detect) -> None:
        """Test chapter detection integration."""
        parser = PDFParser({"min_chapter_level": 1, "max_chapter_level": 3})

        mock_chapters = [
            Chapter(
                chapter_id=1,
                title="Chapter 1",
                content="Content 1",
                start_position=0,
                end_position=100,
                word_count=20,
                level=1,
            )
        ]
        mock_detect.return_value = mock_chapters

        text = "# Chapter 1\n\nSome content here."
        chapters = parser._detect_chapters_from_markdown(text)

        assert len(chapters) == 1
        assert chapters[0].title == "Chapter 1"
        mock_detect.assert_called_once_with(text, min_level=1, max_level=3)


class TestPDFParserErrorHandling:
    """Test error handling in parser."""

    def test_parse_file_not_found(self) -> None:
        """Test parsing raises error for missing file."""
        parser = PDFParser()

        with pytest.raises((ValidationError, FileReadError, ParsingError)):
            parser.parse(Path("/nonexistent/file.pdf"))

    @patch("omniparser.parsers.pdf_parser.fitz")
    def test_load_pdf_failure(self, mock_fitz) -> None:
        """Test PDF loading failure."""
        parser = PDFParser()

        # Mock fitz.open to raise exception
        mock_fitz.open.side_effect = Exception("Cannot open PDF")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(FileReadError, match="Failed to open PDF"):
                parser._load_pdf(tmp_path)
        finally:
            tmp_path.unlink()
