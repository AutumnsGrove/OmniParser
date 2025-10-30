"""
Unit tests for PDF validation module.

Tests validate_pdf_file, load_pdf_document, and validate_and_load_pdf
functions for various success and error scenarios.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from omniparser.exceptions import FileReadError, ValidationError
from omniparser.parsers.pdf.validation import (
    load_pdf_document,
    validate_and_load_pdf,
    validate_pdf_file,
)


class TestValidatePdfFile:
    """Test validate_pdf_file function."""

    def test_validate_pdf_file_valid(self) -> None:
        """Test validation passes for valid PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Should not raise any exception
            validate_pdf_file(tmp_path)
        finally:
            tmp_path.unlink()

    def test_validate_pdf_file_not_exists(self) -> None:
        """Test validation fails for non-existent file."""
        with pytest.raises(ValidationError, match="File not found"):
            validate_pdf_file(Path("/nonexistent/path/document.pdf"))

    def test_validate_pdf_file_not_pdf(self) -> None:
        """Test validation fails for non-PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValidationError, match="Not a PDF file"):
                validate_pdf_file(tmp_path)
        finally:
            tmp_path.unlink()

    def test_validate_pdf_file_is_directory(self) -> None:
        """Test validation fails for directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            with pytest.raises(ValidationError, match="Not a file"):
                validate_pdf_file(dir_path)


class TestLoadPdfDocument:
    """Test load_pdf_document function."""

    @patch("omniparser.parsers.pdf.validation.fitz")
    def test_load_pdf_document_success(self, mock_fitz) -> None:
        """Test successful PDF loading."""
        # Mock fitz.open to return a document
        mock_doc = mock_fitz.open.return_value

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            result = load_pdf_document(tmp_path)

            # Verify fitz.open was called with correct path
            mock_fitz.open.assert_called_once_with(tmp_path)
            # Verify returned document
            assert result == mock_doc
        finally:
            tmp_path.unlink()

    @patch("omniparser.parsers.pdf.validation.fitz")
    def test_load_pdf_document_corrupted(self, mock_fitz) -> None:
        """Test loading fails for corrupted PDF."""
        # Mock fitz.open to raise exception
        mock_fitz.open.side_effect = Exception("PDF is corrupted")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(FileReadError, match="Failed to open PDF"):
                load_pdf_document(tmp_path)
        finally:
            tmp_path.unlink()


class TestValidateAndLoadPdf:
    """Test validate_and_load_pdf function."""

    @patch("omniparser.parsers.pdf.validation.fitz")
    def test_validate_and_load_pdf_success(self, mock_fitz) -> None:
        """Test combined validation and loading succeeds."""
        # Mock fitz.open to return a document
        mock_doc = mock_fitz.open.return_value

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            result = validate_and_load_pdf(tmp_path)

            # Verify document was returned
            assert result == mock_doc
            # Verify fitz.open was called
            mock_fitz.open.assert_called_once_with(tmp_path)
        finally:
            tmp_path.unlink()

    def test_validate_and_load_pdf_invalid(self) -> None:
        """Test combined operation fails for invalid file."""
        # Test with non-existent file
        with pytest.raises(ValidationError, match="File not found"):
            validate_and_load_pdf(Path("/nonexistent/file.pdf"))

    @patch("omniparser.parsers.pdf.validation.fitz")
    def test_validate_and_load_pdf_load_fails(self, mock_fitz) -> None:
        """Test combined operation fails when loading fails."""
        # Mock fitz.open to raise exception
        mock_fitz.open.side_effect = Exception("Cannot read PDF")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(FileReadError, match="Failed to open PDF"):
                validate_and_load_pdf(tmp_path)
        finally:
            tmp_path.unlink()
