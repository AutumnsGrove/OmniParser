"""Tests for format detection utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Mock the magic module before importing format_detector
sys.modules["magic"] = MagicMock()

from src.omniparser.utils.format_detector import detect_format
from src.omniparser.exceptions import UnsupportedFormatError


class TestDetectFormat:
    """Tests for detect_format function."""

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_detect_epub_by_mime(self, mock_magic):
        """Test EPUB detection via MIME type."""
        mock_magic.return_value = "application/epub+zip"
        result = detect_format(Path("test.epub"))
        assert result == "epub"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_detect_pdf_by_mime(self, mock_magic):
        """Test PDF detection via MIME type."""
        mock_magic.return_value = "application/pdf"
        result = detect_format(Path("test.pdf"))
        assert result == "pdf"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_detect_docx_by_mime(self, mock_magic):
        """Test DOCX detection via MIME type."""
        mock_magic.return_value = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        result = detect_format(Path("test.docx"))
        assert result == "docx"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_detect_html_by_mime(self, mock_magic):
        """Test HTML detection via MIME type."""
        mock_magic.return_value = "text/html"
        result = detect_format(Path("test.html"))
        assert result == "html"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_detect_markdown_by_mime(self, mock_magic):
        """Test Markdown detection via MIME type."""
        mock_magic.return_value = "text/markdown"
        result = detect_format(Path("test.md"))
        assert result == "markdown"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_detect_text_by_mime(self, mock_magic):
        """Test plain text detection via MIME type."""
        mock_magic.return_value = "text/plain"
        result = detect_format(Path("test.txt"))
        assert result == "text"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_fallback_to_extension_markdown(self, mock_magic):
        """Test fallback to .md extension."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.md"))
        assert result == "markdown"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_fallback_to_extension_markdown_full(self, mock_magic):
        """Test fallback to .markdown extension."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.markdown"))
        assert result == "markdown"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_fallback_to_extension_txt(self, mock_magic):
        """Test fallback to .txt extension."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.txt"))
        assert result == "text"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_fallback_to_extension_html(self, mock_magic):
        """Test fallback to .html extension."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.html"))
        assert result == "html"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_fallback_to_extension_epub(self, mock_magic):
        """Test fallback to .epub extension."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.epub"))
        assert result == "epub"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_fallback_to_extension_pdf(self, mock_magic):
        """Test fallback to .pdf extension."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.pdf"))
        assert result == "pdf"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_fallback_to_extension_docx(self, mock_magic):
        """Test fallback to .docx extension."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.docx"))
        assert result == "docx"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_unsupported_format_raises_error(self, mock_magic):
        """Test that unsupported format raises UnsupportedFormatError."""
        mock_magic.return_value = "application/unknown"
        with pytest.raises(UnsupportedFormatError):
            detect_format(Path("test.xyz"))

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_unsupported_extension_raises_error(self, mock_magic):
        """Test that unsupported extension raises UnsupportedFormatError."""
        mock_magic.side_effect = Exception("Magic failed")
        with pytest.raises(UnsupportedFormatError, match="Unsupported file format"):
            detect_format(Path("test.unknown"))

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_case_insensitive_extension(self, mock_magic):
        """Test that extension matching is case insensitive."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.MD"))
        assert result == "markdown"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_case_insensitive_pdf_extension(self, mock_magic):
        """Test that PDF extension matching is case insensitive."""
        mock_magic.side_effect = Exception("Magic failed")
        result = detect_format(Path("test.PDF"))
        assert result == "pdf"

    @patch("src.omniparser.utils.format_detector.magic.from_file")
    def test_unknown_mime_type_falls_back_to_extension(self, mock_magic):
        """Test that unknown MIME type falls back to extension detection."""
        mock_magic.return_value = "application/unknown-type"
        result = detect_format(Path("test.txt"))
        assert result == "text"
