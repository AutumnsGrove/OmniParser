"""Tests for validation utilities."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.omniparser.utils.validators import (
    validate_file_exists,
    validate_file_size,
    validate_format_supported,
)
from src.omniparser.exceptions import FileReadError, ValidationError


class TestValidateFileExists:
    """Tests for validate_file_exists function."""

    def test_existing_file(self, temp_file):
        """Test validation passes for existing file."""
        validate_file_exists(temp_file)  # Should not raise

    def test_nonexistent_file(self):
        """Test validation raises error for nonexistent file."""
        with pytest.raises(FileReadError, match="File not found"):
            validate_file_exists(Path("/nonexistent/file.txt"))

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_directory_not_file(self, mock_is_file, mock_exists):
        """Test validation raises error when path is directory."""
        mock_exists.return_value = True
        mock_is_file.return_value = False

        with pytest.raises(FileReadError, match="not a file"):
            validate_file_exists(Path("/some/directory"))

    @patch("pathlib.Path.exists")
    def test_path_does_not_exist(self, mock_exists):
        """Test validation raises error for non-existent path."""
        mock_exists.return_value = False

        with pytest.raises(FileReadError, match="File not found"):
            validate_file_exists(Path("/missing/file.txt"))


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_small_file_passes(self, temp_file):
        """Test validation passes for small file."""
        validate_file_size(temp_file, max_size_mb=1)  # Should not raise

    @patch("pathlib.Path.stat")
    def test_large_file_raises_error(self, mock_stat):
        """Test validation raises error for file exceeding size limit."""
        mock_stat.return_value = MagicMock(st_size=600 * 1024 * 1024)  # 600MB

        with pytest.raises(ValidationError, match="File too large"):
            validate_file_size(Path("large.txt"), max_size_mb=500)

    @patch("pathlib.Path.stat")
    def test_file_at_exact_limit(self, mock_stat):
        """Test validation passes for file at exact size limit."""
        mock_stat.return_value = MagicMock(st_size=500 * 1024 * 1024)  # Exactly 500MB
        validate_file_size(Path("exact.txt"), max_size_mb=500)  # Should not raise

    @patch("pathlib.Path.stat")
    def test_custom_size_limit(self, mock_stat):
        """Test validation with custom size limit."""
        mock_stat.return_value = MagicMock(st_size=100 * 1024 * 1024)  # 100MB

        # Should pass with 200MB limit
        validate_file_size(Path("file.txt"), max_size_mb=200)

        # Should fail with 50MB limit
        with pytest.raises(ValidationError):
            validate_file_size(Path("file.txt"), max_size_mb=50)

    @patch("pathlib.Path.stat")
    def test_default_size_limit(self, mock_stat):
        """Test validation uses default 500MB limit."""
        mock_stat.return_value = MagicMock(st_size=400 * 1024 * 1024)  # 400MB
        validate_file_size(Path("file.txt"))  # Should not raise with default 500MB

    @patch("pathlib.Path.stat")
    def test_very_small_file(self, mock_stat):
        """Test validation passes for very small file."""
        mock_stat.return_value = MagicMock(st_size=1024)  # 1KB
        validate_file_size(Path("tiny.txt"), max_size_mb=1)  # Should not raise

    @patch("pathlib.Path.stat")
    def test_error_message_includes_sizes(self, mock_stat):
        """Test error message includes actual and maximum sizes."""
        mock_stat.return_value = MagicMock(st_size=100 * 1024 * 1024)  # 100MB

        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(Path("file.txt"), max_size_mb=50)

        error_message = str(exc_info.value)
        assert "100" in error_message or "95" in error_message  # Allow for rounding
        assert "50" in error_message


class TestValidateFormatSupported:
    """Tests for validate_format_supported function."""

    def test_epub_supported(self):
        """Test EPUB format is supported."""
        validate_format_supported("epub")  # Should not raise

    def test_pdf_supported(self):
        """Test PDF format is supported."""
        validate_format_supported("pdf")  # Should not raise

    def test_docx_supported(self):
        """Test DOCX format is supported."""
        validate_format_supported("docx")  # Should not raise

    def test_html_supported(self):
        """Test HTML format is supported."""
        validate_format_supported("html")  # Should not raise

    def test_markdown_supported(self):
        """Test Markdown format is supported."""
        validate_format_supported("markdown")  # Should not raise

    def test_text_supported(self):
        """Test plain text format is supported."""
        validate_format_supported("text")  # Should not raise

    def test_unsupported_format_raises_error(self):
        """Test validation raises error for unsupported format."""
        with pytest.raises(ValidationError, match="Unsupported format"):
            validate_format_supported("xyz")

    def test_error_message_includes_supported_formats(self):
        """Test error message lists supported formats."""
        with pytest.raises(ValidationError) as exc_info:
            validate_format_supported("unknown")

        error_message = str(exc_info.value)
        assert "epub" in error_message
        assert "pdf" in error_message
        assert "docx" in error_message
        assert "html" in error_message
        assert "markdown" in error_message
        assert "text" in error_message

    def test_case_sensitive_format(self):
        """Test that format validation is case-sensitive."""
        with pytest.raises(ValidationError):
            validate_format_supported("EPUB")  # Uppercase should fail

    def test_empty_string_format(self):
        """Test that empty string format raises error."""
        with pytest.raises(ValidationError, match="Unsupported format"):
            validate_format_supported("")

    def test_whitespace_format(self):
        """Test that whitespace format raises error."""
        with pytest.raises(ValidationError, match="Unsupported format"):
            validate_format_supported("  ")
