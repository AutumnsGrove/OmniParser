"""Tests for encoding utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import sys

# Mock the chardet module before importing encoding
sys.modules["chardet"] = MagicMock()

from src.omniparser.utils.encoding import (
    detect_encoding,
    normalize_to_utf8,
    normalize_line_endings,
)


class TestDetectEncoding:
    """Tests for detect_encoding function."""

    @patch("builtins.open", new_callable=mock_open, read_data=b"UTF-8 content")
    @patch("src.omniparser.utils.encoding.chardet.detect")
    def test_detect_utf8(self, mock_detect, mock_file):
        """Test UTF-8 detection."""
        mock_detect.return_value = {"encoding": "utf-8"}
        result = detect_encoding(Path("test.txt"))
        assert result == "utf-8"

    @patch("builtins.open", new_callable=mock_open, read_data=b"Latin-1 content")
    @patch("src.omniparser.utils.encoding.chardet.detect")
    def test_detect_latin1(self, mock_detect, mock_file):
        """Test Latin-1 detection."""
        mock_detect.return_value = {"encoding": "latin-1"}
        result = detect_encoding(Path("test.txt"))
        assert result == "latin-1"

    @patch("builtins.open", new_callable=mock_open, read_data=b"ISO-8859-1 content")
    @patch("src.omniparser.utils.encoding.chardet.detect")
    def test_detect_iso88591(self, mock_detect, mock_file):
        """Test ISO-8859-1 detection."""
        mock_detect.return_value = {"encoding": "iso-8859-1"}
        result = detect_encoding(Path("test.txt"))
        assert result == "iso-8859-1"

    @patch("builtins.open", new_callable=mock_open, read_data=b"")
    @patch("src.omniparser.utils.encoding.chardet.detect")
    def test_detect_fallback_to_utf8(self, mock_detect, mock_file):
        """Test fallback to UTF-8 when detection returns None."""
        mock_detect.return_value = {"encoding": None}
        result = detect_encoding(Path("test.txt"))
        assert result == "utf-8"

    @patch("builtins.open", new_callable=mock_open, read_data=b"ASCII content")
    @patch("src.omniparser.utils.encoding.chardet.detect")
    def test_detect_ascii(self, mock_detect, mock_file):
        """Test ASCII detection."""
        mock_detect.return_value = {"encoding": "ascii"}
        result = detect_encoding(Path("test.txt"))
        assert result == "ascii"

    @patch("builtins.open", new_callable=mock_open, read_data=b"Windows content")
    @patch("src.omniparser.utils.encoding.chardet.detect")
    def test_detect_windows1252(self, mock_detect, mock_file):
        """Test Windows-1252 detection."""
        mock_detect.return_value = {"encoding": "windows-1252"}
        result = detect_encoding(Path("test.txt"))
        assert result == "windows-1252"


class TestNormalizeToUtf8:
    """Tests for normalize_to_utf8 function."""

    def test_ascii_text(self):
        """Test normalizing ASCII text."""
        text = "Hello World"
        result = normalize_to_utf8(text)
        assert result == "Hello World"

    def test_utf8_text(self):
        """Test normalizing UTF-8 text."""
        text = "Hello 世界"
        result = normalize_to_utf8(text)
        assert result == "Hello 世界"

    def test_special_characters(self):
        """Test normalizing text with special characters."""
        text = "Café résumé"
        result = normalize_to_utf8(text)
        assert result == "Café résumé"

    def test_emoji(self):
        """Test normalizing text with emoji."""
        text = "Hello 👋"
        result = normalize_to_utf8(text)
        assert result == "Hello 👋"

    def test_empty_string(self):
        """Test normalizing empty string."""
        result = normalize_to_utf8("")
        assert result == ""

    def test_numbers_and_symbols(self):
        """Test normalizing text with numbers and symbols."""
        text = "Price: $100.50 (20% off!)"
        result = normalize_to_utf8(text)
        assert result == "Price: $100.50 (20% off!)"

    def test_mixed_scripts(self):
        """Test normalizing text with mixed scripts."""
        text = "English English, 日本語 Japanese, Русский Russian"
        result = normalize_to_utf8(text)
        assert "English" in result
        assert "日本語" in result or "Japanese" in result


class TestNormalizeLineEndings:
    """Tests for normalize_line_endings function."""

    def test_windows_line_endings(self):
        """Test normalizing Windows line endings (CRLF)."""
        text = "Line 1\r\nLine 2\r\nLine 3"
        result = normalize_line_endings(text)
        assert result == "Line 1\nLine 2\nLine 3"
        assert "\r\n" not in result

    def test_mac_line_endings(self):
        """Test normalizing old Mac line endings (CR)."""
        text = "Line 1\rLine 2\rLine 3"
        result = normalize_line_endings(text)
        assert result == "Line 1\nLine 2\nLine 3"
        assert "\r" not in result

    def test_unix_line_endings(self):
        """Test Unix line endings are preserved."""
        text = "Line 1\nLine 2\nLine 3"
        result = normalize_line_endings(text)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_mixed_line_endings(self):
        """Test normalizing mixed line endings."""
        text = "Line 1\r\nLine 2\nLine 3\rLine 4"
        result = normalize_line_endings(text)
        assert result == "Line 1\nLine 2\nLine 3\nLine 4"
        assert "\r" not in result

    def test_empty_string(self):
        """Test normalizing empty string."""
        result = normalize_line_endings("")
        assert result == ""

    def test_single_line_no_endings(self):
        """Test normalizing single line with no line endings."""
        text = "Single line without line ending"
        result = normalize_line_endings(text)
        assert result == "Single line without line ending"

    def test_multiple_consecutive_line_endings(self):
        """Test normalizing multiple consecutive line endings."""
        text = "Line 1\r\n\r\nLine 2"
        result = normalize_line_endings(text)
        assert result == "Line 1\n\nLine 2"

    def test_trailing_line_ending(self):
        """Test normalizing text with trailing line ending."""
        text = "Line 1\r\nLine 2\r\n"
        result = normalize_line_endings(text)
        assert result == "Line 1\nLine 2\n"

    def test_leading_line_ending(self):
        """Test normalizing text with leading line ending."""
        text = "\r\nLine 1\r\nLine 2"
        result = normalize_line_endings(text)
        assert result == "\nLine 1\nLine 2"
