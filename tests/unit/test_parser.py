"""
Unit tests for the main parser module.

Tests the parse_document() function and format detection utilities.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omniparser import (
    parse_document,
    get_supported_formats,
    is_format_supported,
)
from omniparser.exceptions import FileReadError, UnsupportedFormatError
from omniparser.models import Document, Metadata, ProcessingInfo


class TestParseDocument:
    """Tests for parse_document() function."""

    def test_parse_document_accepts_string_path(self, tmp_path):
        """Test that parse_document accepts string paths."""
        # Create a test file
        test_file = tmp_path / "test.epub"
        test_file.write_text("dummy content")

        # Mock EPUBParser to avoid needing a real EPUB
        with patch("omniparser.parser.EPUBParser") as MockParser:
            mock_parser_instance = Mock()
            mock_doc = Mock(spec=Document)
            mock_parser_instance.parse.return_value = mock_doc
            MockParser.return_value = mock_parser_instance

            # Test with string path
            result = parse_document(str(test_file))

            # Verify parser was called with Path object
            assert mock_parser_instance.parse.called
            assert isinstance(mock_parser_instance.parse.call_args[0][0], Path)

    def test_parse_document_accepts_path_object(self, tmp_path):
        """Test that parse_document accepts Path objects."""
        # Create a test file
        test_file = tmp_path / "test.epub"
        test_file.write_text("dummy content")

        # Mock EPUBParser
        with patch("omniparser.parser.EPUBParser") as MockParser:
            mock_parser_instance = Mock()
            mock_doc = Mock(spec=Document)
            mock_parser_instance.parse.return_value = mock_doc
            MockParser.return_value = mock_parser_instance

            # Test with Path object
            result = parse_document(test_file)

            # Verify parser was called
            assert mock_parser_instance.parse.called
            assert isinstance(mock_parser_instance.parse.call_args[0][0], Path)

    def test_parse_document_file_not_found(self, tmp_path):
        """Test that parse_document raises FileReadError for non-existent files."""
        non_existent_file = tmp_path / "nonexistent.epub"

        with pytest.raises(FileReadError, match="File not found"):
            parse_document(non_existent_file)

    def test_parse_document_not_a_file(self, tmp_path):
        """Test that parse_document raises FileReadError for directories."""
        # tmp_path is a directory
        with pytest.raises(FileReadError, match="Not a file"):
            parse_document(tmp_path)

    def test_parse_document_epub_format(self, tmp_path):
        """Test that EPUB files are routed to EPUBParser."""
        test_file = tmp_path / "test.epub"
        test_file.write_text("dummy content")

        with patch("omniparser.parser.EPUBParser") as MockParser:
            mock_parser_instance = Mock()
            mock_doc = Mock(spec=Document)
            mock_parser_instance.parse.return_value = mock_doc
            MockParser.return_value = mock_parser_instance

            result = parse_document(test_file)

            # Verify EPUBParser was instantiated and used
            MockParser.assert_called_once_with(None)
            mock_parser_instance.parse.assert_called_once()
            assert result == mock_doc

    def test_parse_document_with_options(self, tmp_path):
        """Test that options are passed to parser."""
        test_file = tmp_path / "test.epub"
        test_file.write_text("dummy content")

        options = {"extract_images": False, "clean_text": True, "detect_chapters": True}

        with patch("omniparser.parser.EPUBParser") as MockParser:
            mock_parser_instance = Mock()
            mock_doc = Mock(spec=Document)
            mock_parser_instance.parse.return_value = mock_doc
            MockParser.return_value = mock_parser_instance

            result = parse_document(test_file, options=options)

            # Verify options were passed to EPUBParser
            MockParser.assert_called_once_with(options)

    def test_parse_document_unsupported_pdf(self, tmp_path):
        """Test that PDF files raise UnsupportedFormatError."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="PDF format not yet implemented"
        ):
            parse_document(test_file)

    def test_parse_document_unsupported_docx(self, tmp_path):
        """Test that DOCX files raise UnsupportedFormatError."""
        test_file = tmp_path / "test.docx"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="DOCX format not yet implemented"
        ):
            parse_document(test_file)

    def test_parse_document_unsupported_doc(self, tmp_path):
        """Test that DOC files raise UnsupportedFormatError."""
        test_file = tmp_path / "test.doc"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="DOCX format not yet implemented"
        ):
            parse_document(test_file)

    def test_parse_document_unsupported_html(self, tmp_path):
        """Test that HTML files raise UnsupportedFormatError."""
        test_file = tmp_path / "test.html"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="HTML format not yet implemented"
        ):
            parse_document(test_file)

    def test_parse_document_unsupported_htm(self, tmp_path):
        """Test that HTM files raise UnsupportedFormatError."""
        test_file = tmp_path / "test.htm"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="HTML format not yet implemented"
        ):
            parse_document(test_file)

    def test_parse_document_unsupported_markdown(self, tmp_path):
        """Test that Markdown files raise UnsupportedFormatError."""
        test_file = tmp_path / "test.md"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="Markdown format not yet implemented"
        ):
            parse_document(test_file)

    def test_parse_document_unsupported_txt(self, tmp_path):
        """Test that TXT files raise UnsupportedFormatError."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="Text format not yet implemented"
        ):
            parse_document(test_file)

    def test_parse_document_unknown_format(self, tmp_path):
        """Test that unknown file formats raise UnsupportedFormatError."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("dummy content")

        with pytest.raises(
            UnsupportedFormatError, match="Unsupported file format: .xyz"
        ):
            parse_document(test_file)

    def test_parse_document_case_insensitive_extension(self, tmp_path):
        """Test that file extensions are case-insensitive."""
        test_file = tmp_path / "test.EPUB"
        test_file.write_text("dummy content")

        with patch("omniparser.parser.EPUBParser") as MockParser:
            mock_parser_instance = Mock()
            mock_doc = Mock(spec=Document)
            mock_parser_instance.parse.return_value = mock_doc
            MockParser.return_value = mock_parser_instance

            result = parse_document(test_file)

            # Verify EPUBParser was used despite uppercase extension
            MockParser.assert_called_once()
            assert result == mock_doc


class TestGetSupportedFormats:
    """Tests for get_supported_formats() function."""

    def test_get_supported_formats_returns_list(self):
        """Test that get_supported_formats returns a list."""
        formats = get_supported_formats()
        assert isinstance(formats, list)

    def test_get_supported_formats_contains_epub(self):
        """Test that EPUB is in supported formats."""
        formats = get_supported_formats()
        assert ".epub" in formats

    def test_get_supported_formats_only_epub_for_now(self):
        """Test that only EPUB is supported currently."""
        formats = get_supported_formats()
        assert formats == [".epub"]


class TestIsFormatSupported:
    """Tests for is_format_supported() function."""

    def test_is_format_supported_with_string_path(self):
        """Test is_format_supported with string path."""
        assert is_format_supported("test.epub") is True
        assert is_format_supported("test.pdf") is False

    def test_is_format_supported_with_path_object(self):
        """Test is_format_supported with Path object."""
        assert is_format_supported(Path("test.epub")) is True
        assert is_format_supported(Path("test.pdf")) is False

    def test_is_format_supported_case_insensitive(self):
        """Test that extension checking is case-insensitive."""
        assert is_format_supported("test.EPUB") is True
        assert is_format_supported("test.Epub") is True
        assert is_format_supported("test.ePuB") is True

    def test_is_format_supported_various_formats(self):
        """Test is_format_supported with various formats."""
        # Supported
        assert is_format_supported("book.epub") is True

        # Unsupported (but planned)
        assert is_format_supported("doc.pdf") is False
        assert is_format_supported("doc.docx") is False
        assert is_format_supported("page.html") is False
        assert is_format_supported("readme.md") is False
        assert is_format_supported("notes.txt") is False

        # Unknown
        assert is_format_supported("file.xyz") is False


class TestImports:
    """Tests for package imports."""

    def test_import_parse_document(self):
        """Test that parse_document can be imported from package."""
        from omniparser import parse_document

        assert callable(parse_document)

    def test_import_models(self):
        """Test that models can be imported from package."""
        from omniparser import (
            Document,
            Chapter,
            Metadata,
            ImageReference,
            ProcessingInfo,
        )

        assert Document is not None
        assert Chapter is not None
        assert Metadata is not None
        assert ImageReference is not None
        assert ProcessingInfo is not None

    def test_import_exceptions(self):
        """Test that exceptions can be imported from package."""
        from omniparser import (
            OmniparserError,
            UnsupportedFormatError,
            ParsingError,
            FileReadError,
            NetworkError,
            ValidationError,
        )

        assert issubclass(UnsupportedFormatError, OmniparserError)
        assert issubclass(ParsingError, OmniparserError)
        assert issubclass(FileReadError, OmniparserError)
        assert issubclass(NetworkError, OmniparserError)
        assert issubclass(ValidationError, OmniparserError)

    def test_import_parser(self):
        """Test that EPUBParser can be imported from package."""
        from omniparser import EPUBParser

        assert EPUBParser is not None

    def test_import_version(self):
        """Test that version can be imported from package."""
        from omniparser import __version__

        assert isinstance(__version__, str)
        assert __version__ == "1.0.0"

    def test_import_utility_functions(self):
        """Test that utility functions can be imported."""
        from omniparser import get_supported_formats, is_format_supported

        assert callable(get_supported_formats)
        assert callable(is_format_supported)
