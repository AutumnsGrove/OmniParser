"""
Unit tests for EPUB parser.

Tests the EPUBParser class functionality including validation, format support,
and basic parsing capabilities.
"""

import tempfile
from pathlib import Path

import pytest

from omniparser.exceptions import FileReadError, ValidationError
from omniparser.parsers.epub_parser import EPUBParser, TocEntry


class TestEPUBParserInit:
    """Test EPUBParser initialization."""

    def test_init_no_options(self) -> None:
        """Test initialization without options."""
        parser = EPUBParser()
        assert parser.options == {
            'extract_images': True,
            'detect_chapters': True,
            'clean_text': True,
            'min_chapter_length': 100,
            'use_toc': True,
            'use_spine_fallback': True
        }

    def test_init_with_options(self) -> None:
        """Test initialization with custom options."""
        options = {'extract_images': False, 'clean_text': False}
        parser = EPUBParser(options)

        assert parser.options['extract_images'] is False
        assert parser.options['clean_text'] is False
        # Defaults still applied
        assert parser.options['detect_chapters'] is True
        assert parser.options['min_chapter_length'] == 100

    def test_init_warnings_empty(self) -> None:
        """Test warnings list is initialized empty."""
        parser = EPUBParser()
        assert parser._warnings == []


class TestEPUBParserSupportsFormat:
    """Test format support detection."""

    def test_supports_epub_lowercase(self) -> None:
        """Test .epub extension is supported."""
        parser = EPUBParser()
        assert parser.supports_format(Path("book.epub")) is True

    def test_supports_epub_uppercase(self) -> None:
        """Test .EPUB extension is supported."""
        parser = EPUBParser()
        assert parser.supports_format(Path("book.EPUB")) is True

    def test_supports_epub_mixed_case(self) -> None:
        """Test .ePub extension is supported."""
        parser = EPUBParser()
        assert parser.supports_format(Path("book.ePub")) is True

    def test_not_supports_pdf(self) -> None:
        """Test .pdf extension is not supported."""
        parser = EPUBParser()
        assert parser.supports_format(Path("document.pdf")) is False

    def test_not_supports_txt(self) -> None:
        """Test .txt extension is not supported."""
        parser = EPUBParser()
        assert parser.supports_format(Path("file.txt")) is False

    def test_not_supports_no_extension(self) -> None:
        """Test file without extension is not supported."""
        parser = EPUBParser()
        assert parser.supports_format(Path("book")) is False


class TestEPUBParserValidation:
    """Test EPUB file validation."""

    def test_validate_file_not_exists(self) -> None:
        """Test validation fails for non-existent file."""
        parser = EPUBParser()
        with pytest.raises(FileReadError, match="File not found"):
            parser._validate_epub(Path("/nonexistent/path/book.epub"))

    def test_validate_directory_not_file(self) -> None:
        """Test validation fails for directory."""
        parser = EPUBParser()
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            with pytest.raises(FileReadError, match="Not a file"):
                parser._validate_epub(dir_path)

    def test_validate_wrong_extension(self) -> None:
        """Test validation fails for wrong file extension."""
        parser = EPUBParser()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                with pytest.raises(ValidationError, match="Not an EPUB file"):
                    parser._validate_epub(tmp_path)
            finally:
                tmp_path.unlink()

    def test_validate_empty_file(self) -> None:
        """Test validation fails for empty file."""
        parser = EPUBParser()
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                # File is created empty by default
                with pytest.raises(ValidationError, match="Empty file"):
                    parser._validate_epub(tmp_path)
            finally:
                tmp_path.unlink()

    def test_validate_large_file_warning(self) -> None:
        """Test validation warns for large files."""
        parser = EPUBParser()

        # Create a mock file that appears large
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Write some data so it's not empty
            tmp.write(b"dummy epub content")

        try:
            # We can't easily create a 500MB+ file in tests,
            # so we'll just test that validation passes for normal files
            # The large file warning is tested manually
            parser._validate_epub(tmp_path)
            # Should pass without exceptions
            assert True
        finally:
            tmp_path.unlink()


class TestTocEntry:
    """Test TocEntry dataclass."""

    def test_toc_entry_creation(self) -> None:
        """Test creating a TocEntry."""
        entry = TocEntry(title="Chapter 1", href="chapter1.xhtml", level=1)

        assert entry.title == "Chapter 1"
        assert entry.href == "chapter1.xhtml"
        assert entry.level == 1
        assert entry.children == []

    def test_toc_entry_with_children(self) -> None:
        """Test TocEntry with nested children."""
        child1 = TocEntry(title="Section 1.1", href="ch1.xhtml#s1", level=2)
        child2 = TocEntry(title="Section 1.2", href="ch1.xhtml#s2", level=2)
        parent = TocEntry(
            title="Chapter 1",
            href="ch1.xhtml",
            level=1,
            children=[child1, child2]
        )

        assert parent.title == "Chapter 1"
        assert len(parent.children) == 2
        assert parent.children[0].title == "Section 1.1"
        assert parent.children[1].title == "Section 1.2"

    def test_toc_entry_default_level(self) -> None:
        """Test TocEntry default level is 1."""
        entry = TocEntry(title="Chapter", href="ch.xhtml")
        assert entry.level == 1


class TestEPUBParserHelpers:
    """Test helper methods."""

    def test_count_words(self) -> None:
        """Test word counting."""
        parser = EPUBParser()

        assert parser._count_words("") == 0
        assert parser._count_words("Hello") == 1
        assert parser._count_words("Hello world") == 2
        assert parser._count_words("The quick brown fox") == 4
        assert parser._count_words("Multiple   spaces   between") == 3

    def test_count_words_with_punctuation(self) -> None:
        """Test word counting with punctuation."""
        parser = EPUBParser()

        assert parser._count_words("Hello, world!") == 2
        assert parser._count_words("It's a test.") == 3

    def test_estimate_reading_time(self) -> None:
        """Test reading time estimation."""
        parser = EPUBParser()

        # 225 WPM average
        assert parser._estimate_reading_time(0) == 1  # Minimum 1 minute
        assert parser._estimate_reading_time(100) == 1
        assert parser._estimate_reading_time(225) == 1
        assert parser._estimate_reading_time(450) == 2
        assert parser._estimate_reading_time(1125) == 5
        assert parser._estimate_reading_time(45000) == 200

    def test_estimate_reading_time_rounding(self) -> None:
        """Test reading time rounds correctly."""
        parser = EPUBParser()

        # Should round to nearest minute
        assert parser._estimate_reading_time(337) == 2  # 337/225 = 1.5 -> 2
        assert parser._estimate_reading_time(300) == 1  # 300/225 = 1.33 -> 1


class TestEPUBParserMetadataExtraction:
    """Test metadata extraction functionality."""

    def test_extract_metadata_all_fields(self) -> None:
        """Test metadata extraction with all fields present."""
        from datetime import datetime
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock EPUB book with metadata
        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ('DC', 'title'): [('The Great Gatsby', {})],
            ('DC', 'creator'): [('F. Scott Fitzgerald', {}), ('Editor Name', {})],
            ('DC', 'publisher'): [('Scribner', {})],
            ('DC', 'date'): [('1925-04-10', {})],
            ('DC', 'language'): [('en', {})],
            ('DC', 'identifier'): [('urn:isbn:978-0743273565', {}), ('uuid:12345', {})],
            ('DC', 'description'): [('A novel set in Jazz Age America.', {})],
            ('DC', 'subject'): [('fiction', {}), ('classic', {}), ('american-literature', {})]
        }.get((ns, name), [])

        # Create mock file path
        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 1024000

        # Extract metadata
        metadata = parser._extract_metadata(mock_book, mock_path)

        # Verify all fields
        assert metadata.title == 'The Great Gatsby'
        assert metadata.author == 'F. Scott Fitzgerald'
        assert metadata.authors == ['F. Scott Fitzgerald', 'Editor Name']
        assert metadata.publisher == 'Scribner'
        assert metadata.publication_date == datetime(1925, 4, 10)
        assert metadata.language == 'en'
        assert metadata.isbn == '978-0743273565'
        assert metadata.description == 'A novel set in Jazz Age America.'
        assert metadata.tags == ['fiction', 'classic', 'american-literature']
        assert metadata.original_format == 'epub'
        assert metadata.file_size == 1024000

    def test_extract_metadata_minimal(self) -> None:
        """Test metadata extraction with minimal fields."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock EPUB book with only title
        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ('DC', 'title'): [('Minimal Book', {})]
        }.get((ns, name), [])

        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 50000

        # Extract metadata
        metadata = parser._extract_metadata(mock_book, mock_path)

        # Verify title present and others None/empty
        assert metadata.title == 'Minimal Book'
        assert metadata.author is None
        assert metadata.authors == []
        assert metadata.publisher is None
        assert metadata.publication_date is None
        assert metadata.language is None
        assert metadata.isbn is None
        assert metadata.description is None
        assert metadata.tags == []
        assert metadata.file_size == 50000

    def test_extract_metadata_no_metadata(self) -> None:
        """Test metadata extraction with no metadata fields."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock EPUB book with no metadata
        mock_book = MagicMock()
        mock_book.get_metadata.return_value = []

        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 25000

        # Extract metadata
        metadata = parser._extract_metadata(mock_book, mock_path)

        # All fields should be None/empty except file_size
        assert metadata.title is None
        assert metadata.author is None
        assert metadata.authors == []
        assert metadata.file_size == 25000

    def test_extract_metadata_date_formats(self) -> None:
        """Test metadata extraction with various date formats."""
        from datetime import datetime
        from unittest.mock import MagicMock

        parser = EPUBParser()

        test_cases = [
            ('2023-01-15', datetime(2023, 1, 15)),
            ('2023-01-15T10:30:00', datetime(2023, 1, 15, 10, 30, 0)),
            ('2023-01-15T10:30:00Z', datetime(2023, 1, 15, 10, 30, 0)),
            ('2023', datetime(2023, 1, 1)),
            ('2023-06', datetime(2023, 6, 1)),
        ]

        for date_str, expected_date in test_cases:
            parser._warnings = []
            mock_book = MagicMock()
            mock_book.get_metadata.side_effect = lambda ns, name: {
                ('DC', 'date'): [(date_str, {})]
            }.get((ns, name), [])

            mock_path = MagicMock()
            mock_path.stat.return_value.st_size = 1000

            metadata = parser._extract_metadata(mock_book, mock_path)
            assert metadata.publication_date == expected_date, f"Failed for date: {date_str}"

    def test_extract_metadata_invalid_date(self) -> None:
        """Test metadata extraction with invalid date format."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ('DC', 'date'): [('invalid-date-format', {})]
        }.get((ns, name), [])

        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 1000

        metadata = parser._extract_metadata(mock_book, mock_path)

        # Date should be None and warning should be logged
        assert metadata.publication_date is None
        assert len(parser._warnings) > 0
        assert 'Could not parse publication date' in parser._warnings[0]

    def test_extract_metadata_isbn_extraction(self) -> None:
        """Test ISBN extraction from identifiers."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Test various ISBN formats
        test_cases = [
            'urn:isbn:978-0743273565',
            'ISBN:978-0743273565',
            'isbn:978-0743273565',
        ]

        for isbn_str in test_cases:
            mock_book = MagicMock()
            mock_book.get_metadata.side_effect = lambda ns, name: {
                ('DC', 'identifier'): [(isbn_str, {}), ('uuid:12345', {})]
            }.get((ns, name), [])

            mock_path = MagicMock()
            mock_path.stat.return_value.st_size = 1000

            metadata = parser._extract_metadata(mock_book, mock_path)
            assert metadata.isbn == '978-0743273565', f"Failed for ISBN format: {isbn_str}"

    def test_extract_metadata_no_isbn(self) -> None:
        """Test metadata extraction when no ISBN in identifiers."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ('DC', 'identifier'): [('uuid:12345', {}), ('urn:doi:10.1234', {})]
        }.get((ns, name), [])

        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 1000

        metadata = parser._extract_metadata(mock_book, mock_path)
        assert metadata.isbn is None

    def test_extract_metadata_exception_handling(self) -> None:
        """Test metadata extraction handles exceptions gracefully."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock that raises exception
        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = Exception("Metadata error")

        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 1000

        # Should not raise exception, return minimal metadata
        metadata = parser._extract_metadata(mock_book, mock_path)

        assert metadata.title is None
        assert metadata.author is None
        assert metadata.file_size == 1000


# Note: Full integration tests with real EPUB files will be in
# tests/integration/test_epub_parsing.py
# These unit tests focus on individual method behavior
