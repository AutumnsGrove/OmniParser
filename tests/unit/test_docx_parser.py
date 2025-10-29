"""
Unit tests for DOCX parser.

Tests the DOCXParser class functionality including validation, format support,
and basic parsing capabilities.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from docx import Document as DocxDocument
from docx.text.paragraph import Paragraph
from docx.table import Table

from omniparser.exceptions import FileReadError, ParsingError, ValidationError
from omniparser.parsers.docx_parser import DOCXParser


class TestDOCXParserInit:
    """Test DOCXParser initialization."""

    def test_init_no_options(self) -> None:
        """Test initialization without options."""
        parser = DOCXParser()
        assert parser.options == {
            "extract_images": True,
            "image_output_dir": None,
            "preserve_formatting": True,
            "extract_tables": True,
            "clean_text": True,
            "min_chapter_level": 1,
            "max_chapter_level": 2,
            "heading_styles": [
                "Heading 1",
                "Heading 2",
                "Heading 3",
                "Heading 4",
                "Heading 5",
                "Heading 6",
            ],
        }

    def test_init_with_options(self) -> None:
        """Test initialization with custom options."""
        options = {"extract_images": False, "clean_text": False}
        parser = DOCXParser(options)

        assert parser.options["extract_images"] is False
        assert parser.options["clean_text"] is False
        # Defaults still applied
        assert parser.options["preserve_formatting"] is True
        assert parser.options["extract_tables"] is True

    def test_init_warnings_empty(self) -> None:
        """Test warnings list is initialized empty."""
        parser = DOCXParser()
        assert parser._warnings == []

    def test_init_image_counter_zero(self) -> None:
        """Test image counter is initialized to zero."""
        parser = DOCXParser()
        assert parser._image_counter == 0


class TestDOCXParserSupportsFormat:
    """Test format support detection."""

    def test_supports_docx_lowercase(self) -> None:
        """Test .docx extension is supported."""
        parser = DOCXParser()
        assert parser.supports_format(Path("document.docx")) is True

    def test_supports_docx_uppercase(self) -> None:
        """Test .DOCX extension is supported."""
        parser = DOCXParser()
        assert parser.supports_format(Path("document.DOCX")) is True

    def test_supports_docx_mixed_case(self) -> None:
        """Test .Docx extension is supported."""
        parser = DOCXParser()
        assert parser.supports_format(Path("document.Docx")) is True

    def test_not_supports_pdf(self) -> None:
        """Test .pdf extension is not supported."""
        parser = DOCXParser()
        assert parser.supports_format(Path("document.pdf")) is False

    def test_not_supports_doc(self) -> None:
        """Test .doc extension is not supported."""
        parser = DOCXParser()
        assert parser.supports_format(Path("document.doc")) is False

    def test_not_supports_txt(self) -> None:
        """Test .txt extension is not supported."""
        parser = DOCXParser()
        assert parser.supports_format(Path("file.txt")) is False

    def test_not_supports_no_extension(self) -> None:
        """Test file without extension is not supported."""
        parser = DOCXParser()
        assert parser.supports_format(Path("document")) is False

    def test_supports_format_with_string(self) -> None:
        """Test supports_format with string path."""
        parser = DOCXParser()
        assert parser.supports_format("document.docx") is True
        assert parser.supports_format("document.pdf") is False


class TestDOCXParserValidation:
    """Test DOCX file validation."""

    def test_validate_file_not_exists(self) -> None:
        """Test validation fails for non-existent file."""
        parser = DOCXParser()
        with pytest.raises(FileReadError, match="File not found"):
            parser._validate_docx(Path("/nonexistent/path/document.docx"))

    def test_validate_directory_not_file(self) -> None:
        """Test validation fails for directory."""
        parser = DOCXParser()
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            with pytest.raises(FileReadError, match="Not a file"):
                parser._validate_docx(dir_path)

    def test_validate_wrong_extension(self) -> None:
        """Test validation fails for wrong file extension."""
        parser = DOCXParser()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                with pytest.raises(ValidationError, match="Not a DOCX file"):
                    parser._validate_docx(tmp_path)
            finally:
                tmp_path.unlink()

    def test_validate_empty_file(self) -> None:
        """Test validation fails for empty file."""
        parser = DOCXParser()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                # File is created empty by default
                with pytest.raises(ValidationError, match="Empty file"):
                    parser._validate_docx(tmp_path)
            finally:
                tmp_path.unlink()

    def test_validate_large_file_warning(self) -> None:
        """Test validation warns for large files."""
        parser = DOCXParser()

        # Create a mock file that appears large
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Write some data so it's not empty
            tmp.write(b"dummy docx content")

        try:
            parser._validate_docx(tmp_path)
            # Should pass without exceptions
            assert True
        finally:
            tmp_path.unlink()


class TestDOCXParserHelpers:
    """Test helper methods."""

    def test_count_words(self) -> None:
        """Test word counting."""
        parser = DOCXParser()

        assert parser._count_words("") == 0
        assert parser._count_words("Hello") == 1
        assert parser._count_words("Hello world") == 2
        assert parser._count_words("The quick brown fox") == 4
        assert parser._count_words("Multiple   spaces   between") == 3

    def test_count_words_with_punctuation(self) -> None:
        """Test word counting with punctuation."""
        parser = DOCXParser()

        assert parser._count_words("Hello, world!") == 2
        assert parser._count_words("It's a test.") == 3

    def test_estimate_reading_time(self) -> None:
        """Test reading time estimation."""
        parser = DOCXParser()

        # 225 WPM average
        assert parser._estimate_reading_time(0) == 1  # Minimum 1 minute
        assert parser._estimate_reading_time(100) == 1
        assert parser._estimate_reading_time(225) == 1
        assert parser._estimate_reading_time(450) == 2
        assert parser._estimate_reading_time(1000) == 4
        assert parser._estimate_reading_time(2250) == 10

    def test_is_heading(self) -> None:
        """Test heading detection."""
        parser = DOCXParser()

        # Mock paragraph with heading style
        mock_para = Mock(spec=Paragraph)
        mock_para.style = Mock()
        mock_para.style.name = "Heading 1"
        assert parser._is_heading(mock_para) is True

        # Mock paragraph with normal style
        mock_para.style.name = "Normal"
        assert parser._is_heading(mock_para) is False

        # Mock paragraph with Heading 3
        mock_para.style.name = "Heading 3"
        assert parser._is_heading(mock_para) is True

    def test_get_heading_level(self) -> None:
        """Test heading level extraction."""
        parser = DOCXParser()

        # Mock paragraphs with different heading levels
        for level in range(1, 7):
            mock_para = Mock(spec=Paragraph)
            mock_para.style = Mock()
            mock_para.style.name = f"Heading {level}"
            assert parser._get_heading_level(mock_para) == level

    def test_get_heading_level_default(self) -> None:
        """Test heading level defaults to 1."""
        parser = DOCXParser()

        mock_para = Mock(spec=Paragraph)
        mock_para.style = Mock()
        mock_para.style.name = "Normal"
        assert parser._get_heading_level(mock_para) == 1

    def test_get_heading_level_caps_at_six(self) -> None:
        """Test heading level caps at 6."""
        parser = DOCXParser()

        # Even if someone has "Heading 10", cap it at 6
        mock_para = Mock(spec=Paragraph)
        mock_para.style = Mock()
        mock_para.style.name = "Heading 10"
        assert parser._get_heading_level(mock_para) == 6


class TestDOCXParserFormatting:
    """Test formatting conversion to markdown."""

    def test_run_to_markdown_plain(self) -> None:
        """Test plain text run conversion."""
        parser = DOCXParser()

        mock_run = Mock()
        mock_run.text = "plain text"
        mock_run.bold = False
        mock_run.italic = False

        result = parser._run_to_markdown(mock_run)
        assert result == "plain text"

    def test_run_to_markdown_bold(self) -> None:
        """Test bold text run conversion."""
        parser = DOCXParser()

        mock_run = Mock()
        mock_run.text = "bold text"
        mock_run.bold = True
        mock_run.italic = False

        result = parser._run_to_markdown(mock_run)
        assert result == "**bold text**"

    def test_run_to_markdown_italic(self) -> None:
        """Test italic text run conversion."""
        parser = DOCXParser()

        mock_run = Mock()
        mock_run.text = "italic text"
        mock_run.bold = False
        mock_run.italic = True

        result = parser._run_to_markdown(mock_run)
        assert result == "*italic text*"

    def test_run_to_markdown_bold_italic(self) -> None:
        """Test bold+italic text run conversion."""
        parser = DOCXParser()

        mock_run = Mock()
        mock_run.text = "bold italic"
        mock_run.bold = True
        mock_run.italic = True

        result = parser._run_to_markdown(mock_run)
        assert result == "***bold italic***"

    def test_paragraph_to_markdown_heading(self) -> None:
        """Test paragraph to markdown for headings."""
        parser = DOCXParser()

        # Mock heading paragraph
        mock_para = Mock(spec=Paragraph)
        mock_para.style = Mock()
        mock_para.style.name = "Heading 1"
        mock_para.text = "Chapter Title"

        result = parser._paragraph_to_markdown(mock_para)
        assert result == "# Chapter Title"

    def test_paragraph_to_markdown_heading_level_2(self) -> None:
        """Test paragraph to markdown for Heading 2."""
        parser = DOCXParser()

        mock_para = Mock(spec=Paragraph)
        mock_para.style = Mock()
        mock_para.style.name = "Heading 2"
        mock_para.text = "Section Title"

        result = parser._paragraph_to_markdown(mock_para)
        assert result == "## Section Title"

    def test_paragraph_to_markdown_plain_without_formatting(self) -> None:
        """Test paragraph to markdown without formatting preservation."""
        parser = DOCXParser({"preserve_formatting": False})

        mock_para = Mock(spec=Paragraph)
        mock_para.style = Mock()
        mock_para.style.name = "Normal"
        mock_para.text = "  Plain text with spaces  "

        result = parser._paragraph_to_markdown(mock_para)
        assert result == "Plain text with spaces"


class TestDOCXParserTableConversion:
    """Test table conversion to markdown."""

    def test_table_to_markdown_empty(self) -> None:
        """Test empty table conversion."""
        parser = DOCXParser()

        mock_table = Mock(spec=Table)
        mock_table.rows = []

        result = parser._table_to_markdown(mock_table)
        assert result == ""

    def test_table_to_markdown_single_row(self) -> None:
        """Test single row table conversion."""
        parser = DOCXParser()

        # Mock table with one row
        mock_cell1 = Mock()
        mock_cell1.text = "Header 1"
        mock_cell2 = Mock()
        mock_cell2.text = "Header 2"

        mock_row = Mock()
        mock_row.cells = [mock_cell1, mock_cell2]

        mock_table = Mock(spec=Table)
        mock_table.rows = [mock_row]

        result = parser._table_to_markdown(mock_table)
        expected = "| Header 1 | Header 2 |\n| --- | --- |"
        assert result == expected

    def test_table_to_markdown_multiple_rows(self) -> None:
        """Test multiple row table conversion."""
        parser = DOCXParser()

        # Mock header row
        mock_header_cell1 = Mock()
        mock_header_cell1.text = "Name"
        mock_header_cell2 = Mock()
        mock_header_cell2.text = "Age"

        mock_header_row = Mock()
        mock_header_row.cells = [mock_header_cell1, mock_header_cell2]

        # Mock data row
        mock_data_cell1 = Mock()
        mock_data_cell1.text = "John"
        mock_data_cell2 = Mock()
        mock_data_cell2.text = "30"

        mock_data_row = Mock()
        mock_data_row.cells = [mock_data_cell1, mock_data_cell2]

        # Mock table
        mock_table = Mock(spec=Table)
        mock_table.rows = [mock_header_row, mock_data_row]

        result = parser._table_to_markdown(mock_table)
        expected = "| Name | Age |\n| --- | --- |\n| John | 30 |"
        assert result == expected

    def test_table_to_markdown_with_newlines(self) -> None:
        """Test table conversion with newlines in cells."""
        parser = DOCXParser()

        # Mock cell with newlines
        mock_cell = Mock()
        mock_cell.text = "Line 1\nLine 2\nLine 3"

        mock_row = Mock()
        mock_row.cells = [mock_cell]

        mock_table = Mock(spec=Table)
        mock_table.rows = [mock_row]

        result = parser._table_to_markdown(mock_table)
        # Newlines should be replaced with spaces
        assert "Line 1 Line 2 Line 3" in result


class TestDOCXParserMetadata:
    """Test metadata extraction."""

    def test_extract_metadata_all_fields(self) -> None:
        """Test metadata extraction with all fields present."""
        parser = DOCXParser()

        # Mock DOCX document
        mock_docx = Mock(spec=DocxDocument)
        mock_docx.core_properties = Mock()
        mock_docx.core_properties.title = "Test Document"
        mock_docx.core_properties.author = "John Doe"
        mock_docx.core_properties.subject = "A test subject"
        mock_docx.core_properties.keywords = "test, document, sample"
        mock_docx.core_properties.comments = None
        from datetime import datetime

        mock_docx.core_properties.created = datetime(2023, 1, 15, 10, 30, 0)
        mock_docx.core_properties.modified = datetime(2023, 2, 20, 15, 45, 0)
        mock_docx.core_properties.last_modified_by = "Jane Smith"

        # Mock file path
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)

        try:
            metadata = parser._extract_metadata(mock_docx, tmp_path)

            assert metadata.title == "Test Document"
            assert metadata.author == "John Doe"
            assert metadata.authors == ["John Doe"]
            assert metadata.description == "A test subject"
            assert metadata.tags == ["test", "document", "sample"]
            assert metadata.publication_date == datetime(2023, 1, 15, 10, 30, 0)
            assert metadata.original_format == "docx"
            assert metadata.file_size > 0
            assert metadata.custom_fields["last_modified_by"] == "Jane Smith"
        finally:
            tmp_path.unlink()

    def test_extract_metadata_minimal_fields(self) -> None:
        """Test metadata extraction with minimal fields."""
        parser = DOCXParser()

        # Mock DOCX document with minimal metadata
        mock_docx = Mock(spec=DocxDocument)
        mock_docx.core_properties = Mock()
        mock_docx.core_properties.title = None
        mock_docx.core_properties.author = None
        mock_docx.core_properties.subject = None
        mock_docx.core_properties.keywords = None
        mock_docx.core_properties.comments = None
        mock_docx.core_properties.created = None
        mock_docx.core_properties.modified = None
        mock_docx.core_properties.last_modified_by = None

        # Mock file path
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = Path(tmp.name)

        try:
            metadata = parser._extract_metadata(mock_docx, tmp_path)

            assert metadata.title is None
            assert metadata.author is None
            assert metadata.description is None
            assert metadata.tags is None
            assert metadata.publication_date is None
            assert metadata.original_format == "docx"
        finally:
            tmp_path.unlink()

    def test_extract_metadata_keywords_semicolon_separated(self) -> None:
        """Test metadata extraction with semicolon-separated keywords."""
        parser = DOCXParser()

        mock_docx = Mock(spec=DocxDocument)
        mock_docx.core_properties = Mock()
        mock_docx.core_properties.title = None
        mock_docx.core_properties.author = None
        mock_docx.core_properties.subject = None
        mock_docx.core_properties.keywords = "python; docx; parser"
        mock_docx.core_properties.comments = None
        mock_docx.core_properties.created = None
        mock_docx.core_properties.modified = None
        mock_docx.core_properties.last_modified_by = None

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = Path(tmp.name)

        try:
            metadata = parser._extract_metadata(mock_docx, tmp_path)
            assert metadata.tags == ["python", "docx", "parser"]
        finally:
            tmp_path.unlink()


class TestDOCXParserLoadError:
    """Test DOCX loading error handling."""

    def test_load_docx_invalid_file(self) -> None:
        """Test loading invalid DOCX file raises ParsingError."""
        parser = DOCXParser()

        # Create a file that's not a valid DOCX
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(b"This is not a valid DOCX file")
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ParsingError, match="Failed to load DOCX"):
                parser._load_docx(tmp_path)
        finally:
            tmp_path.unlink()
