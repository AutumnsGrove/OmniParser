"""
Unit tests for PDF text extraction module.

Tests the text extraction functions including scanned PDF detection,
text extraction with formatting, OCR extraction, and the main coordinator.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from omniparser.exceptions import ParsingError
from omniparser.parsers.pdf.text_extraction import (
    extract_text_content,
    extract_text_with_formatting,
    extract_text_with_ocr,
    is_scanned_pdf,
)


class TestIsScannedPdf:
    """Test scanned PDF detection."""

    def test_is_scanned_pdf_true(self) -> None:
        """Test detection of scanned PDF with minimal text."""
        # Mock document with minimal text
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        mock_page = MagicMock()
        mock_page.get_text.return_value = "   "  # Very little text
        mock_doc.__getitem__.return_value = mock_page

        result = is_scanned_pdf(mock_doc)
        assert result is True

    def test_is_scanned_pdf_false(self) -> None:
        """Test detection of text-based PDF with substantial text."""
        # Mock document with substantial text
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is a text-based PDF " * 20
        mock_doc.__getitem__.return_value = mock_page

        result = is_scanned_pdf(mock_doc)
        assert result is False

    def test_is_scanned_pdf_single_page(self) -> None:
        """Test scanned detection with single page document."""
        # Mock single page document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_text.return_value = "  \n  "
        mock_doc.__getitem__.return_value = mock_page

        result = is_scanned_pdf(mock_doc)
        assert result is True

    def test_is_scanned_pdf_custom_threshold(self) -> None:
        """Test scanned detection with custom threshold."""
        # Mock document with moderate text
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Some text here"  # 14 chars
        mock_doc.__getitem__.return_value = mock_page

        # With low threshold, should be text-based
        result = is_scanned_pdf(mock_doc, threshold=10)
        assert result is False

        # With high threshold, should be scanned
        result = is_scanned_pdf(mock_doc, threshold=50)
        assert result is True

    def test_is_scanned_pdf_empty_document(self) -> None:
        """Test scanned detection with empty document."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 0

        result = is_scanned_pdf(mock_doc)
        # Empty document should be considered scanned (0 chars < threshold)
        assert result is True


class TestExtractTextWithFormatting:
    """Test text extraction with font information."""

    def test_extract_text_with_formatting_basic(self) -> None:
        """Test text extraction with font information."""
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

        text, blocks = extract_text_with_formatting(mock_doc)

        assert "Chapter 1" in text
        assert "This is content" in text
        assert len(blocks) == 2
        assert blocks[0]["text"] == "Chapter 1"
        assert blocks[0]["font_size"] == 18.0
        assert blocks[0]["is_bold"] is True
        assert blocks[1]["text"] == "This is content"
        assert blocks[1]["font_size"] == 12.0

    def test_extract_text_with_formatting_empty(self) -> None:
        """Test text extraction with empty PDF."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_text.return_value = {"blocks": []}
        mock_doc.__getitem__.return_value = mock_page

        text, blocks = extract_text_with_formatting(mock_doc)

        assert text == ""
        assert blocks == []

    def test_extract_text_with_formatting_max_pages(self) -> None:
        """Test text extraction with page limit."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Page text",
                                    "size": 12.0,
                                    "flags": 0,
                                    "font": "Arial",
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_doc.__getitem__.return_value = mock_page

        text, blocks = extract_text_with_formatting(mock_doc, max_pages=2)

        # Should only process 2 pages
        assert len(blocks) == 2
        assert blocks[0]["page_num"] == 1
        assert blocks[1]["page_num"] == 2

    def test_extract_text_with_formatting_page_breaks(self) -> None:
        """Test text extraction with page break markers."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Text",
                                    "size": 12.0,
                                    "flags": 0,
                                    "font": "Arial",
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_doc.__getitem__.return_value = mock_page

        text, _ = extract_text_with_formatting(mock_doc, include_page_breaks=True)

        assert "--- Page 1 ---" in text
        assert "--- Page 2 ---" in text

    def test_extract_text_with_formatting_position_tracking(self) -> None:
        """Test that position tracking is correct."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "First",
                                    "size": 12.0,
                                    "flags": 0,
                                    "font": "Arial",
                                }
                            ]
                        },
                        {
                            "spans": [
                                {
                                    "text": "Second",
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

        _, blocks = extract_text_with_formatting(mock_doc)

        # First block starts at position 0
        assert blocks[0]["position"] == 0
        # Second block starts after "First " (5 chars + 1 space = 6)
        assert blocks[1]["position"] == 6

    def test_extract_text_with_formatting_bold_detection(self) -> None:
        """Test bold detection from font flags and name."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()

        # Test both bold flag and Bold in name
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Bold by flag",
                                    "size": 12.0,
                                    "flags": 16,
                                    "font": "Arial",
                                }
                            ]
                        },
                        {
                            "spans": [
                                {
                                    "text": "Bold by name",
                                    "size": 12.0,
                                    "flags": 0,
                                    "font": "Arial-Bold",
                                }
                            ]
                        },
                        {
                            "spans": [
                                {
                                    "text": "Not bold",
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

        _, blocks = extract_text_with_formatting(mock_doc)

        assert blocks[0]["is_bold"] is True
        assert blocks[1]["is_bold"] is True
        assert blocks[2]["is_bold"] is False


class TestExtractTextWithOcr:
    """Test OCR-based text extraction."""

    @patch("pytesseract.image_to_string")
    @patch("omniparser.parsers.pdf.text_extraction.Image")
    def test_extract_text_with_ocr_success(self, mock_image, mock_tesseract) -> None:
        """Test successful OCR extraction."""
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

        text = extract_text_with_ocr(mock_doc)

        assert "OCR extracted text" in text
        mock_tesseract.assert_called()

    @patch("omniparser.parsers.pdf.text_extraction.extract_text_with_formatting")
    def test_extract_text_with_ocr_no_pytesseract(self, mock_extract) -> None:
        """Test OCR fallback when pytesseract not available."""
        mock_doc = MagicMock()
        mock_extract.return_value = ("Fallback text", [])

        # Mock import error by patching the import
        with patch.dict("sys.modules", {"pytesseract": None}):
            text = extract_text_with_ocr(mock_doc)

        # Should fall back to regular text extraction
        mock_extract.assert_called_once()

    @patch("pytesseract.image_to_string")
    @patch("omniparser.parsers.pdf.text_extraction.Image")
    def test_extract_text_with_ocr_timeout(self, mock_image, mock_tesseract) -> None:
        """Test OCR timeout handling."""
        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

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

        # Mock OCR to simulate timeout
        def slow_ocr(*args, **kwargs):
            import time

            time.sleep(10)
            return "text"

        mock_tesseract.side_effect = slow_ocr

        # Use very short timeout
        with pytest.raises(ParsingError, match="OCR processing exceeded timeout"):
            extract_text_with_ocr(mock_doc, timeout=1)

    @patch("pytesseract.image_to_string")
    @patch("omniparser.parsers.pdf.text_extraction.Image")
    def test_extract_text_with_ocr_page_breaks(
        self, mock_image, mock_tesseract
    ) -> None:
        """Test OCR with page break markers."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.width = 800
        mock_pix.height = 1000
        mock_pix.samples = b"fake_image_data"
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__.return_value = mock_page

        mock_img = MagicMock()
        mock_image.frombytes.return_value = mock_img
        mock_tesseract.return_value = "Page text"

        text = extract_text_with_ocr(mock_doc, include_page_breaks=True)

        assert "--- Page 1 ---" in text
        assert "--- Page 2 ---" in text

    @patch("pytesseract.image_to_string")
    @patch("omniparser.parsers.pdf.text_extraction.Image")
    def test_extract_text_with_ocr_custom_language(
        self, mock_image, mock_tesseract
    ) -> None:
        """Test OCR with custom language."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.width = 800
        mock_pix.height = 1000
        mock_pix.samples = b"fake_image_data"
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__.return_value = mock_page

        mock_img = MagicMock()
        mock_image.frombytes.return_value = mock_img
        mock_tesseract.return_value = "Texte francais"

        text = extract_text_with_ocr(mock_doc, language="fra")

        # Verify language was passed
        call_kwargs = mock_tesseract.call_args[1]
        assert call_kwargs.get("lang") == "fra"


class TestExtractTextContent:
    """Test main text extraction coordinator."""

    @patch("omniparser.parsers.pdf.text_extraction.extract_text_with_formatting")
    @patch("omniparser.parsers.pdf.text_extraction.is_scanned_pdf")
    def test_extract_text_content_normal_pdf(
        self, mock_is_scanned, mock_extract_formatting
    ) -> None:
        """Test normal PDF text extraction."""
        mock_doc = MagicMock()
        mock_is_scanned.return_value = False
        mock_extract_formatting.return_value = ("Normal text", [{"text": "test"}])

        text, blocks = extract_text_content(mock_doc)

        assert text == "Normal text"
        assert len(blocks) == 1
        mock_extract_formatting.assert_called_once()

    @patch("omniparser.parsers.pdf.text_extraction.extract_text_with_ocr")
    @patch("omniparser.parsers.pdf.text_extraction.is_scanned_pdf")
    def test_extract_text_content_scanned_pdf(
        self, mock_is_scanned, mock_extract_ocr
    ) -> None:
        """Test scanned PDF with OCR."""
        mock_doc = MagicMock()
        mock_is_scanned.return_value = True
        mock_extract_ocr.return_value = "OCR text"

        text, blocks = extract_text_content(mock_doc, use_ocr=True)

        assert text == "OCR text"
        assert blocks == []  # OCR doesn't return blocks
        mock_extract_ocr.assert_called_once()

    @patch("omniparser.parsers.pdf.text_extraction.extract_text_with_formatting")
    @patch("omniparser.parsers.pdf.text_extraction.is_scanned_pdf")
    def test_extract_text_content_ocr_disabled(
        self, mock_is_scanned, mock_extract_formatting
    ) -> None:
        """Test scanned PDF with OCR disabled."""
        mock_doc = MagicMock()
        mock_is_scanned.return_value = True
        mock_extract_formatting.return_value = ("Basic text", [])

        text, blocks = extract_text_content(mock_doc, use_ocr=False)

        # Should use formatting extraction even for scanned PDF
        assert text == "Basic text"
        mock_extract_formatting.assert_called_once()

    @patch("omniparser.parsers.pdf.text_extraction.extract_text_with_formatting")
    @patch("omniparser.parsers.pdf.text_extraction.is_scanned_pdf")
    def test_extract_text_content_custom_threshold(
        self, mock_is_scanned, mock_extract_formatting
    ) -> None:
        """Test text extraction with custom OCR threshold."""
        mock_doc = MagicMock()
        mock_is_scanned.return_value = False
        mock_extract_formatting.return_value = ("Text", [])

        extract_text_content(mock_doc, ocr_threshold=50)

        # Verify threshold was passed to is_scanned_pdf
        mock_is_scanned.assert_called_once_with(mock_doc, threshold=50)

    @patch("omniparser.parsers.pdf.text_extraction.extract_text_with_ocr")
    @patch("omniparser.parsers.pdf.text_extraction.is_scanned_pdf")
    def test_extract_text_content_passes_options(
        self, mock_is_scanned, mock_extract_ocr
    ) -> None:
        """Test that options are passed correctly."""
        mock_doc = MagicMock()
        mock_is_scanned.return_value = True
        mock_extract_ocr.return_value = "OCR text"

        extract_text_content(
            mock_doc,
            use_ocr=True,
            ocr_timeout=600,
            ocr_language="deu",
            max_pages=10,
            include_page_breaks=True,
        )

        # Verify options were passed to OCR function
        call_kwargs = mock_extract_ocr.call_args[1]
        assert call_kwargs["timeout"] == 600
        assert call_kwargs["language"] == "deu"
        assert call_kwargs["max_pages"] == 10
        assert call_kwargs["include_page_breaks"] is True
