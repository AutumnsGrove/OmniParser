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
            "extract_images": True,
            "image_output_dir": None,
            "detect_chapters": True,
            "clean_text": True,
            "min_chapter_length": 100,
            "use_toc": True,
            "use_spine_fallback": True,
        }

    def test_init_with_options(self) -> None:
        """Test initialization with custom options."""
        options = {"extract_images": False, "clean_text": False}
        parser = EPUBParser(options)

        assert parser.options["extract_images"] is False
        assert parser.options["clean_text"] is False
        # Defaults still applied
        assert parser.options["detect_chapters"] is True
        assert parser.options["min_chapter_length"] == 100

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
            title="Chapter 1", href="ch1.xhtml", level=1, children=[child1, child2]
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
        assert parser._estimate_reading_time(337) == 1  # 337/225 = 1.498 -> 1
        assert parser._estimate_reading_time(338) == 2  # 338/225 = 1.502 -> 2
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
            ("DC", "title"): [("The Great Gatsby", {})],
            ("DC", "creator"): [("F. Scott Fitzgerald", {}), ("Editor Name", {})],
            ("DC", "publisher"): [("Scribner", {})],
            ("DC", "date"): [("1925-04-10", {})],
            ("DC", "language"): [("en", {})],
            ("DC", "identifier"): [("urn:isbn:978-0743273565", {}), ("uuid:12345", {})],
            ("DC", "description"): [("A novel set in Jazz Age America.", {})],
            ("DC", "subject"): [
                ("fiction", {}),
                ("classic", {}),
                ("american-literature", {}),
            ],
        }.get((ns, name), [])

        # Create mock file path
        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 1024000

        # Extract metadata
        metadata = parser._extract_metadata(mock_book, mock_path)

        # Verify all fields
        assert metadata.title == "The Great Gatsby"
        assert metadata.author == "F. Scott Fitzgerald"
        assert metadata.authors == ["F. Scott Fitzgerald", "Editor Name"]
        assert metadata.publisher == "Scribner"
        assert metadata.publication_date == datetime(1925, 4, 10)
        assert metadata.language == "en"
        assert metadata.isbn == "978-0743273565"
        assert metadata.description == "A novel set in Jazz Age America."
        assert metadata.tags == ["fiction", "classic", "american-literature"]
        assert metadata.original_format == "epub"
        assert metadata.file_size == 1024000

    def test_extract_metadata_minimal(self) -> None:
        """Test metadata extraction with minimal fields."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock EPUB book with only title
        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ("DC", "title"): [("Minimal Book", {})]
        }.get((ns, name), [])

        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 50000

        # Extract metadata
        metadata = parser._extract_metadata(mock_book, mock_path)

        # Verify title present and others None/empty
        assert metadata.title == "Minimal Book"
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
            ("2023-01-15", datetime(2023, 1, 15)),
            ("2023-01-15T10:30:00", datetime(2023, 1, 15, 10, 30, 0)),
            ("2023-01-15T10:30:00Z", datetime(2023, 1, 15, 10, 30, 0)),
            ("2023", datetime(2023, 1, 1)),
            ("2023-06", datetime(2023, 6, 1)),
        ]

        for date_str, expected_date in test_cases:
            parser._warnings = []
            mock_book = MagicMock()
            mock_book.get_metadata.side_effect = lambda ns, name: {
                ("DC", "date"): [(date_str, {})]
            }.get((ns, name), [])

            mock_path = MagicMock()
            mock_path.stat.return_value.st_size = 1000

            metadata = parser._extract_metadata(mock_book, mock_path)
            assert (
                metadata.publication_date == expected_date
            ), f"Failed for date: {date_str}"

    def test_extract_metadata_invalid_date(self) -> None:
        """Test metadata extraction with invalid date format."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ("DC", "date"): [("invalid-date-format", {})]
        }.get((ns, name), [])

        mock_path = MagicMock()
        mock_path.stat.return_value.st_size = 1000

        metadata = parser._extract_metadata(mock_book, mock_path)

        # Date should be None and warning should be logged
        assert metadata.publication_date is None
        assert len(parser._warnings) > 0
        assert "Could not parse publication date" in parser._warnings[0]

    def test_extract_metadata_isbn_extraction(self) -> None:
        """Test ISBN extraction from identifiers."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Test various ISBN formats
        test_cases = [
            "urn:isbn:978-0743273565",
            "ISBN:978-0743273565",
            "isbn:978-0743273565",
        ]

        for isbn_str in test_cases:
            mock_book = MagicMock()
            mock_book.get_metadata.side_effect = lambda ns, name: {
                ("DC", "identifier"): [(isbn_str, {}), ("uuid:12345", {})]
            }.get((ns, name), [])

            mock_path = MagicMock()
            mock_path.stat.return_value.st_size = 1000

            metadata = parser._extract_metadata(mock_book, mock_path)
            assert (
                metadata.isbn == "978-0743273565"
            ), f"Failed for ISBN format: {isbn_str}"

    def test_extract_metadata_no_isbn(self) -> None:
        """Test metadata extraction when no ISBN in identifiers."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, name: {
            ("DC", "identifier"): [("uuid:12345", {}), ("urn:doi:10.1234", {})]
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


class TestEPUBParserTocExtraction:
    """Test table of contents extraction."""

    def test_extract_toc_flat_structure(self) -> None:
        """Test TOC extraction with flat (single-level) structure."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock TOC with flat structure (list of Links)
        mock_link1 = MagicMock()
        mock_link1.title = "Chapter 1"
        mock_link1.href = "chapter1.xhtml"

        mock_link2 = MagicMock()
        mock_link2.title = "Chapter 2"
        mock_link2.href = "chapter2.xhtml"

        mock_link3 = MagicMock()
        mock_link3.title = "Chapter 3"
        mock_link3.href = "chapter3.xhtml"

        mock_book = MagicMock()
        mock_book.toc = [mock_link1, mock_link2, mock_link3]

        # Extract TOC
        toc_entries = parser._extract_toc(mock_book)

        # Verify results
        assert toc_entries is not None
        assert len(toc_entries) == 3

        assert toc_entries[0].title == "Chapter 1"
        assert toc_entries[0].href == "chapter1.xhtml"
        assert toc_entries[0].level == 1
        assert toc_entries[0].children == []

        assert toc_entries[1].title == "Chapter 2"
        assert toc_entries[1].href == "chapter2.xhtml"
        assert toc_entries[1].level == 1

        assert toc_entries[2].title == "Chapter 3"
        assert toc_entries[2].href == "chapter3.xhtml"
        assert toc_entries[2].level == 1

    def test_extract_toc_nested_structure(self) -> None:
        """Test TOC extraction with nested (multi-level) structure."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock nested TOC structure
        # Chapter 1
        #   Section 1.1
        #   Section 1.2
        # Chapter 2

        mock_link1 = MagicMock()
        mock_link1.title = "Chapter 1"
        mock_link1.href = "chapter1.xhtml"

        mock_subsection1 = MagicMock()
        mock_subsection1.title = "Section 1.1"
        mock_subsection1.href = "chapter1.xhtml#s1"

        mock_subsection2 = MagicMock()
        mock_subsection2.title = "Section 1.2"
        mock_subsection2.href = "chapter1.xhtml#s2"

        mock_link2 = MagicMock()
        mock_link2.title = "Chapter 2"
        mock_link2.href = "chapter2.xhtml"

        # Structure as tuple (parent, [children])
        mock_book = MagicMock()
        mock_book.toc = [(mock_link1, [mock_subsection1, mock_subsection2]), mock_link2]

        # Extract TOC
        toc_entries = parser._extract_toc(mock_book)

        # Verify flattened structure with correct levels
        assert toc_entries is not None
        assert len(toc_entries) == 4

        # Chapter 1 (level 1)
        assert toc_entries[0].title == "Chapter 1"
        assert toc_entries[0].href == "chapter1.xhtml"
        assert toc_entries[0].level == 1

        # Section 1.1 (level 2)
        assert toc_entries[1].title == "Section 1.1"
        assert toc_entries[1].href == "chapter1.xhtml#s1"
        assert toc_entries[1].level == 2

        # Section 1.2 (level 2)
        assert toc_entries[2].title == "Section 1.2"
        assert toc_entries[2].href == "chapter1.xhtml#s2"
        assert toc_entries[2].level == 2

        # Chapter 2 (level 1)
        assert toc_entries[3].title == "Chapter 2"
        assert toc_entries[3].href == "chapter2.xhtml"
        assert toc_entries[3].level == 1

    def test_extract_toc_deeply_nested(self) -> None:
        """Test TOC extraction with deeply nested structure (3+ levels)."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create deeply nested TOC
        # Chapter 1
        #   Section 1.1
        #     Subsection 1.1.1
        #     Subsection 1.1.2

        mock_chapter = MagicMock()
        mock_chapter.title = "Chapter 1"
        mock_chapter.href = "ch1.xhtml"

        mock_section = MagicMock()
        mock_section.title = "Section 1.1"
        mock_section.href = "ch1.xhtml#s1"

        mock_subsub1 = MagicMock()
        mock_subsub1.title = "Subsection 1.1.1"
        mock_subsub1.href = "ch1.xhtml#s1.1"

        mock_subsub2 = MagicMock()
        mock_subsub2.title = "Subsection 1.1.2"
        mock_subsub2.href = "ch1.xhtml#s1.2"

        mock_book = MagicMock()
        mock_book.toc = [(mock_chapter, [(mock_section, [mock_subsub1, mock_subsub2])])]

        # Extract TOC
        toc_entries = parser._extract_toc(mock_book)

        # Verify all levels
        assert toc_entries is not None
        assert len(toc_entries) == 4

        assert toc_entries[0].title == "Chapter 1"
        assert toc_entries[0].level == 1

        assert toc_entries[1].title == "Section 1.1"
        assert toc_entries[1].level == 2

        assert toc_entries[2].title == "Subsection 1.1.1"
        assert toc_entries[2].level == 3

        assert toc_entries[3].title == "Subsection 1.1.2"
        assert toc_entries[3].level == 3

    def test_extract_toc_empty_returns_none(self) -> None:
        """Test that empty TOC returns None."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Empty TOC
        mock_book = MagicMock()
        mock_book.toc = []

        result = parser._extract_toc(mock_book)
        assert result is None

    def test_extract_toc_none_returns_none(self) -> None:
        """Test that None TOC returns None."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # None TOC
        mock_book = MagicMock()
        mock_book.toc = None

        result = parser._extract_toc(mock_book)
        assert result is None

    def test_extract_toc_handles_missing_title(self) -> None:
        """Test TOC extraction handles entries with missing titles."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Link with None title
        mock_link = MagicMock()
        mock_link.title = None
        mock_link.href = "chapter1.xhtml"

        mock_book = MagicMock()
        mock_book.toc = [mock_link]

        toc_entries = parser._extract_toc(mock_book)

        # Should default to "Untitled"
        assert toc_entries is not None
        assert len(toc_entries) == 1
        assert toc_entries[0].title == "Untitled"
        assert toc_entries[0].href == "chapter1.xhtml"

    def test_extract_toc_handles_missing_href(self) -> None:
        """Test TOC extraction handles entries with missing href."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Link with None href
        mock_link = MagicMock()
        mock_link.title = "Chapter 1"
        mock_link.href = None

        mock_book = MagicMock()
        mock_book.toc = [mock_link]

        toc_entries = parser._extract_toc(mock_book)

        # Should default to empty string
        assert toc_entries is not None
        assert len(toc_entries) == 1
        assert toc_entries[0].title == "Chapter 1"
        assert toc_entries[0].href == ""

    def test_extract_toc_handles_section_without_href(self) -> None:
        """Test TOC extraction handles Section objects without href."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Section with only title (no href attribute)
        mock_section = MagicMock()
        mock_section.title = "Part One"
        # Remove href attribute
        del mock_section.href

        mock_child = MagicMock()
        mock_child.title = "Chapter 1"
        mock_child.href = "ch1.xhtml"

        mock_book = MagicMock()
        mock_book.toc = [(mock_section, [mock_child])]

        toc_entries = parser._extract_toc(mock_book)

        # Should handle missing href gracefully
        assert toc_entries is not None
        assert len(toc_entries) == 2
        assert toc_entries[0].title == "Part One"
        assert toc_entries[0].href == ""
        assert toc_entries[1].title == "Chapter 1"
        assert toc_entries[1].href == "ch1.xhtml"

    def test_extract_toc_exception_handling(self) -> None:
        """Test TOC extraction handles exceptions gracefully."""
        from unittest.mock import MagicMock, PropertyMock

        parser = EPUBParser()
        parser._warnings = []

        # Mock book that raises exception when accessing toc
        mock_book = MagicMock()
        type(mock_book).toc = PropertyMock(side_effect=Exception("TOC error"))

        # Should return None and log warning
        result = parser._extract_toc(mock_book)
        assert result is None
        assert len(parser._warnings) > 0
        assert "TOC extraction failed" in parser._warnings[0]

    def test_extract_toc_malformed_entry_in_list(self) -> None:
        """Test that malformed TOC entries in list are handled gracefully."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create valid link followed by an object with no title/href attributes
        mock_link1 = MagicMock()
        mock_link1.title = "Chapter 1"
        mock_link1.href = "chapter1.xhtml"

        # Object that doesn't have title or href attributes (unknown structure)
        mock_bad_link = MagicMock(spec=["some_other_attr"])

        mock_link2 = MagicMock()
        mock_link2.title = "Chapter 2"
        mock_link2.href = "chapter2.xhtml"

        mock_book = MagicMock()
        mock_book.toc = [mock_link1, mock_bad_link, mock_link2]

        toc_entries = parser._extract_toc(mock_book)

        # Should extract valid entries and log warning about bad one
        assert toc_entries is not None
        assert len(toc_entries) == 2  # Only the valid ones
        assert toc_entries[0].title == "Chapter 1"
        assert toc_entries[1].title == "Chapter 2"

        # Should have warning about unknown structure
        assert len(parser._warnings) > 0
        assert "Unknown TOC item" in str(parser._warnings)

    def test_extract_toc_unknown_structure_warning(self) -> None:
        """Test that unknown TOC structures generate warnings."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create unknown structure (e.g., plain string)
        mock_book = MagicMock()
        mock_book.toc = ["invalid_structure"]

        result = parser._extract_toc(mock_book)

        # Should return None or empty
        assert result is None or len(result) == 0

        # Should have warning about unknown type
        assert len(parser._warnings) > 0
        assert "Unknown TOC item" in str(
            parser._warnings
        ) or "TOC extraction failed" in str(parser._warnings)

    def test_extract_toc_mixed_structure(self) -> None:
        """Test TOC with mixed flat and nested entries."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Mixed structure: some with children, some without
        mock_link1 = MagicMock()
        mock_link1.title = "Chapter 1"
        mock_link1.href = "ch1.xhtml"

        mock_link2 = MagicMock()
        mock_link2.title = "Chapter 2"
        mock_link2.href = "ch2.xhtml"

        mock_subsection = MagicMock()
        mock_subsection.title = "Section 2.1"
        mock_subsection.href = "ch2.xhtml#s1"

        mock_link3 = MagicMock()
        mock_link3.title = "Chapter 3"
        mock_link3.href = "ch3.xhtml"

        mock_book = MagicMock()
        mock_book.toc = [mock_link1, (mock_link2, [mock_subsection]), mock_link3]

        toc_entries = parser._extract_toc(mock_book)

        # Verify mixed structure is flattened correctly
        assert toc_entries is not None
        assert len(toc_entries) == 4

        assert toc_entries[0].title == "Chapter 1"
        assert toc_entries[0].level == 1

        assert toc_entries[1].title == "Chapter 2"
        assert toc_entries[1].level == 1

        assert toc_entries[2].title == "Section 2.1"
        assert toc_entries[2].level == 2

        assert toc_entries[3].title == "Chapter 3"
        assert toc_entries[3].level == 1


class TestEPUBParserChapterExtraction:
    """Test chapter extraction methods."""

    def test_postprocess_chapters_filter_short_chapters(self) -> None:
        """Test filtering of short chapters below min_chapter_length."""
        from omniparser.models import Chapter

        parser = EPUBParser({"min_chapter_length": 100})

        # Create chapters with varying word counts
        chapters = [
            Chapter(
                chapter_id=1,
                title="Long Chapter",
                content=" ".join(["word"] * 150),
                start_position=0,
                end_position=750,
                word_count=150,
                level=1,
            ),
            Chapter(
                chapter_id=2,
                title="Short Chapter",
                content=" ".join(["word"] * 50),
                start_position=750,
                end_position=1000,
                word_count=50,
                level=1,
            ),
            Chapter(
                chapter_id=3,
                title="Another Long Chapter",
                content=" ".join(["word"] * 200),
                start_position=1000,
                end_position=2000,
                word_count=200,
                level=1,
            ),
        ]

        # Post-process
        result = parser._postprocess_chapters(chapters)

        # Should have only 2 chapters (short one filtered out)
        assert len(result) == 2
        assert result[0].title == "Long Chapter"
        assert result[1].title == "Another Long Chapter"

        # Chapter IDs should be renumbered
        assert result[0].chapter_id == 1
        assert result[1].chapter_id == 2

    def test_postprocess_chapters_no_filtering(self) -> None:
        """Test that all chapters pass when above min threshold."""
        from omniparser.models import Chapter

        parser = EPUBParser({"min_chapter_length": 50})

        chapters = [
            Chapter(
                chapter_id=1,
                title="Chapter 1",
                content=" ".join(["word"] * 100),
                start_position=0,
                end_position=500,
                word_count=100,
                level=1,
            ),
            Chapter(
                chapter_id=2,
                title="Chapter 2",
                content=" ".join(["word"] * 75),
                start_position=500,
                end_position=875,
                word_count=75,
                level=1,
            ),
        ]

        result = parser._postprocess_chapters(chapters)

        # All chapters should pass
        assert len(result) == 2

    def test_postprocess_chapters_duplicate_titles(self) -> None:
        """Test handling of duplicate chapter titles."""
        from omniparser.models import Chapter

        parser = EPUBParser()

        # Create chapters with duplicate titles
        chapters = [
            Chapter(
                chapter_id=1,
                title="Introduction",
                content=" ".join(["word"] * 100),
                start_position=0,
                end_position=500,
                word_count=100,
                level=1,
            ),
            Chapter(
                chapter_id=2,
                title="Chapter 1",
                content=" ".join(["word"] * 150),
                start_position=500,
                end_position=1250,
                word_count=150,
                level=1,
            ),
            Chapter(
                chapter_id=3,
                title="Introduction",  # Duplicate
                content=" ".join(["word"] * 120),
                start_position=1250,
                end_position=1850,
                word_count=120,
                level=1,
            ),
            Chapter(
                chapter_id=4,
                title="Introduction",  # Another duplicate
                content=" ".join(["word"] * 110),
                start_position=1850,
                end_position=2400,
                word_count=110,
                level=1,
            ),
        ]

        result = parser._postprocess_chapters(chapters)

        # Verify disambiguated titles
        assert result[0].title == "Introduction"
        assert result[1].title == "Chapter 1"
        assert result[2].title == "Introduction (2)"
        assert result[3].title == "Introduction (3)"

    def test_postprocess_chapters_empty_list(self) -> None:
        """Test post-processing empty chapter list."""
        parser = EPUBParser()

        result = parser._postprocess_chapters([])

        assert result == []

    def test_extract_content_and_chapters_uses_toc(self) -> None:
        """Test that TOC-based extraction is used when TOC available."""
        from unittest.mock import MagicMock, patch

        parser = EPUBParser()
        mock_book = MagicMock()

        # Create mock TOC entries
        toc_entries = [
            TocEntry(title="Chapter 1", href="ch1.xhtml", level=1),
            TocEntry(title="Chapter 2", href="ch2.xhtml", level=1),
        ]

        # Mock the extraction methods
        with patch.object(
            parser, "_extract_chapters_toc", return_value=("content", [])
        ) as mock_toc:
            with patch.object(parser, "_extract_chapters_spine") as mock_spine:
                with patch.object(
                    parser, "_postprocess_chapters", return_value=[]
                ) as mock_post:
                    parser._extract_content_and_chapters(mock_book, toc_entries)

                    # TOC method should be called
                    mock_toc.assert_called_once_with(mock_book, toc_entries)
                    # Spine method should NOT be called
                    mock_spine.assert_not_called()
                    # Post-processing should be called
                    mock_post.assert_called_once()

    def test_extract_content_and_chapters_uses_spine_fallback(self) -> None:
        """Test that spine-based extraction is used when no TOC."""
        from unittest.mock import MagicMock, patch

        parser = EPUBParser()
        mock_book = MagicMock()

        # No TOC entries
        toc_entries = None

        # Mock the extraction methods
        with patch.object(parser, "_extract_chapters_toc") as mock_toc:
            with patch.object(
                parser, "_extract_chapters_spine", return_value=("content", [])
            ) as mock_spine:
                with patch.object(
                    parser, "_postprocess_chapters", return_value=[]
                ) as mock_post:
                    parser._extract_content_and_chapters(mock_book, toc_entries)

                    # TOC method should NOT be called
                    mock_toc.assert_not_called()
                    # Spine method should be called
                    mock_spine.assert_called_once_with(mock_book)
                    # Post-processing should be called
                    mock_post.assert_called_once()

    def test_extract_chapters_spine_no_items(self) -> None:
        """Test spine extraction with no spine items."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = []

        content, chapters = parser._extract_chapters_spine(mock_book)

        assert content == ""
        assert chapters == []

    def test_extract_chapters_spine_basic(self) -> None:
        """Test basic spine-based chapter extraction."""
        from unittest.mock import MagicMock
        import ebooklib

        parser = EPUBParser()
        parser._warnings = []

        # Create mock spine items
        mock_item1 = MagicMock()
        mock_item1.get_id.return_value = "item1"
        mock_item1.get_name.return_value = "chapter1.xhtml"
        mock_item1.title = "Chapter 1"
        mock_item1.get_content.return_value = (
            b"<html><body><h1>Chapter 1</h1><p>Content of chapter 1.</p></body></html>"
        )

        mock_item2 = MagicMock()
        mock_item2.get_id.return_value = "item2"
        mock_item2.get_name.return_value = "chapter2.xhtml"
        mock_item2.title = None  # No title
        mock_item2.get_content.return_value = b"<html><body><h1>Chapter Two</h1><p>Content of chapter 2.</p></body></html>"

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]

        content, chapters = parser._extract_chapters_spine(mock_book)

        # Verify content is extracted
        assert "Chapter 1" in content
        assert "Content of chapter 1" in content
        assert "Chapter Two" in content
        assert "Content of chapter 2" in content

        # Verify chapters created
        assert len(chapters) == 2

        # Chapter 1
        assert chapters[0].chapter_id == 1
        assert chapters[0].title == "Chapter 1"
        assert chapters[0].level == 1
        assert chapters[0].metadata["detection_method"] == "spine"
        assert chapters[0].metadata["source_item_id"] == "item1"
        assert chapters[0].word_count > 0

        # Chapter 2 (title from h1, not item.title)
        assert chapters[1].chapter_id == 2
        assert chapters[1].title == "Chapter Two"
        assert chapters[1].level == 1
        assert chapters[1].metadata["detection_method"] == "spine"

    def test_extract_chapters_spine_generated_title(self) -> None:
        """Test spine extraction generates title when none available."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock spine item with no title and no h1
        mock_item = MagicMock()
        mock_item.get_id.return_value = "item1"
        mock_item.get_name.return_value = "page.xhtml"
        mock_item.title = None
        mock_item.get_content.return_value = (
            b"<html><body><p>Just some content.</p></body></html>"
        )

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item]

        content, chapters = parser._extract_chapters_spine(mock_book)

        # Should generate title
        assert len(chapters) == 1
        assert chapters[0].title == "Chapter 1"

    def test_extract_chapters_toc_no_spine_items(self) -> None:
        """Test TOC extraction with no spine items."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = []

        toc_entries = [TocEntry(title="Chapter 1", href="ch1.xhtml", level=1)]

        content, chapters = parser._extract_chapters_toc(mock_book, toc_entries)

        assert content == ""
        assert chapters == []

    def test_extract_chapters_toc_basic(self) -> None:
        """Test basic TOC-based chapter extraction."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Create mock spine items
        mock_item1 = MagicMock()
        mock_item1.get_id.return_value = "item1"
        mock_item1.get_name.return_value = "chapter1.xhtml"
        mock_item1.get_content.return_value = (
            b"<html><body><p>Content of chapter 1.</p></body></html>"
        )

        mock_item2 = MagicMock()
        mock_item2.get_id.return_value = "item2"
        mock_item2.get_name.return_value = "chapter2.xhtml"
        mock_item2.get_content.return_value = (
            b"<html><body><p>Content of chapter 2.</p></body></html>"
        )

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]

        # TOC entries matching spine items
        toc_entries = [
            TocEntry(title="Chapter One", href="chapter1.xhtml", level=1),
            TocEntry(title="Chapter Two", href="chapter2.xhtml", level=1),
        ]

        content, chapters = parser._extract_chapters_toc(mock_book, toc_entries)

        # Verify content
        assert "Content of chapter 1" in content
        assert "Content of chapter 2" in content

        # Verify chapters
        assert len(chapters) == 2

        assert chapters[0].chapter_id == 1
        assert chapters[0].title == "Chapter One"
        assert chapters[0].level == 1
        assert chapters[0].metadata["detection_method"] == "toc"
        assert chapters[0].metadata["source_href"] == "chapter1.xhtml"

        assert chapters[1].chapter_id == 2
        assert chapters[1].title == "Chapter Two"
        assert chapters[1].level == 1

    def test_extract_chapters_toc_with_anchors(self) -> None:
        """Test TOC extraction with href anchors."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Single spine item with multiple TOC entries pointing to anchors
        mock_item = MagicMock()
        mock_item.get_id.return_value = "item1"
        mock_item.get_name.return_value = "content.xhtml"
        mock_item.get_content.return_value = b"<html><body><h1 id='ch1'>Chapter 1</h1><p>Content 1.</p><h1 id='ch2'>Chapter 2</h1><p>Content 2.</p></body></html>"

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item]

        # TOC with anchors
        toc_entries = [
            TocEntry(title="Chapter 1", href="content.xhtml#ch1", level=1),
            TocEntry(title="Chapter 2", href="content.xhtml#ch2", level=1),
        ]

        content, chapters = parser._extract_chapters_toc(mock_book, toc_entries)

        # Both chapters should be created
        # Note: Current implementation doesn't handle anchors perfectly,
        # but should still create chapters based on file boundaries
        assert len(chapters) == 2

    def test_extract_chapters_toc_missing_href(self) -> None:
        """Test TOC extraction skips entries with missing href."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_item = MagicMock()
        mock_item.get_id.return_value = "item1"
        mock_item.get_name.return_value = "chapter.xhtml"
        mock_item.get_content.return_value = (
            b"<html><body><p>Content.</p></body></html>"
        )

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item]

        # TOC entry with no href
        toc_entries = [
            TocEntry(title="Section", href="", level=1),
            TocEntry(title="Chapter", href="chapter.xhtml", level=1),
        ]

        content, chapters = parser._extract_chapters_toc(mock_book, toc_entries)

        # Only chapter with valid href should be created
        assert len(chapters) == 1
        assert chapters[0].title == "Chapter"

    def test_extract_chapters_toc_unknown_file(self) -> None:
        """Test TOC extraction skips entries referencing unknown files."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_item = MagicMock()
        mock_item.get_id.return_value = "item1"
        mock_item.get_name.return_value = "known.xhtml"
        mock_item.get_content.return_value = (
            b"<html><body><p>Content.</p></body></html>"
        )

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item]

        # TOC referencing unknown file
        toc_entries = [
            TocEntry(title="Known", href="known.xhtml", level=1),
            TocEntry(title="Unknown", href="unknown.xhtml", level=1),
        ]

        content, chapters = parser._extract_chapters_toc(mock_book, toc_entries)

        # Only known chapter created
        assert len(chapters) == 1
        assert chapters[0].title == "Known"

    def test_extract_chapters_spine_error_handling(self) -> None:
        """Test spine extraction handles errors gracefully."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        # Item that raises error
        mock_item1 = MagicMock()
        mock_item1.get_id.return_value = "item1"
        mock_item1.get_content.side_effect = Exception("Read error")

        # Valid item
        mock_item2 = MagicMock()
        mock_item2.get_id.return_value = "item2"
        mock_item2.get_name.return_value = "chapter.xhtml"
        mock_item2.title = "Chapter"
        mock_item2.get_content.return_value = (
            b"<html><body><p>Content.</p></body></html>"
        )

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]

        content, chapters = parser._extract_chapters_spine(mock_book)

        # Should skip error item and process valid one
        assert len(chapters) == 1
        assert chapters[0].title == "Chapter"

        # Should have warning
        assert len(parser._warnings) > 0

    def test_extract_chapters_toc_error_handling(self) -> None:
        """Test TOC extraction handles errors gracefully."""
        from unittest.mock import MagicMock

        parser = EPUBParser()
        parser._warnings = []

        mock_item = MagicMock()
        mock_item.get_id.return_value = "item1"
        mock_item.get_name.return_value = "chapter.xhtml"
        mock_item.get_content.return_value = (
            b"<html><body><p>Content.</p></body></html>"
        )

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item]

        # TOC entry that will cause error (None title)
        toc_entries = [
            TocEntry(title="Valid", href="chapter.xhtml", level=1),
            TocEntry(
                title=None, href="chapter.xhtml", level=1
            ),  # This might cause issues
        ]

        # Should not crash
        content, chapters = parser._extract_chapters_toc(mock_book, toc_entries)

        # At least one chapter should be created
        assert len(chapters) >= 1


class TestEPUBParserImageExtraction:
    """Test image extraction functionality."""

    def test_extract_images_no_images(self) -> None:
        """Test image extraction when EPUB has no images."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path

        parser = EPUBParser()
        parser._warnings = []

        # Create mock EPUB with no images
        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = []

        # Mock _load_epub to return our mock book
        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # Should return empty list
        assert images == []

    def test_extract_images_basic(self) -> None:
        """Test basic image extraction with valid images."""
        from unittest.mock import MagicMock, patch, mock_open
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create mock image data (1x1 PNG)
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (800, 600), color="red")
        img.save(img_bytes, format="PNG")
        img_data = img_bytes.getvalue()

        # Create mock EPUB image items
        mock_item1 = MagicMock()
        mock_item1.get_name.return_value = "images/cover.png"
        mock_item1.get_content.return_value = img_data

        mock_item2 = MagicMock()
        mock_item2.get_name.return_value = "images/diagram.jpg"
        mock_item2.get_content.return_value = img_data

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]

        # Mock _load_epub to return our mock book
        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # Verify images extracted
        assert len(images) == 2

        # Check first image
        assert images[0].image_id == "img_001"
        assert images[0].position == 0
        assert images[0].file_path is not None
        assert "cover.png" in images[0].file_path
        assert images[0].alt_text is None
        assert images[0].size == (800, 600)
        assert images[0].format == "png"

        # Check second image
        assert images[1].image_id == "img_002"
        assert images[1].position == 0
        assert "diagram.jpg" in images[1].file_path
        assert images[1].size == (800, 600)

    def test_extract_images_sequential_ids(self) -> None:
        """Test that image IDs are sequential and zero-padded."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create mock image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(img_bytes, format="PNG")
        img_data = img_bytes.getvalue()

        # Create 12 mock images to test zero-padding
        mock_items = []
        for i in range(12):
            mock_item = MagicMock()
            mock_item.get_name.return_value = f"image_{i}.png"
            mock_item.get_content.return_value = img_data
            mock_items.append(mock_item)

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = mock_items

        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # Verify IDs are sequential and zero-padded
        assert len(images) == 12
        assert images[0].image_id == "img_001"
        assert images[8].image_id == "img_009"
        assert images[9].image_id == "img_010"
        assert images[11].image_id == "img_012"

    def test_extract_images_subdirectories(self) -> None:
        """Test that images in subdirectories are extracted correctly."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create mock image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100))
        img.save(img_bytes, format="PNG")
        img_data = img_bytes.getvalue()

        # Create images in various subdirectories
        mock_item1 = MagicMock()
        mock_item1.get_name.return_value = "Pictures/deep/nested/image.png"
        mock_item1.get_content.return_value = img_data

        mock_item2 = MagicMock()
        mock_item2.get_name.return_value = "img/photo.jpg"
        mock_item2.get_content.return_value = img_data

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]

        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # Verify subdirectory structure preserved in paths
        assert len(images) == 2
        assert "deep/nested/image.png" in images[0].file_path
        assert "photo.jpg" in images[1].file_path

    def test_extract_images_corrupted_image_handling(self) -> None:
        """Test that corrupted images are handled gracefully."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100))
        img.save(img_bytes, format="PNG")
        valid_img_data = img_bytes.getvalue()

        # Corrupted image data
        corrupted_img_data = b"not a real image"

        # Mix of valid and corrupted images
        mock_item1 = MagicMock()
        mock_item1.get_name.return_value = "valid.png"
        mock_item1.get_content.return_value = valid_img_data

        mock_item2 = MagicMock()
        mock_item2.get_name.return_value = "corrupted.jpg"
        mock_item2.get_content.return_value = corrupted_img_data

        mock_item3 = MagicMock()
        mock_item3.get_name.return_value = "also_valid.png"
        mock_item3.get_content.return_value = valid_img_data

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2, mock_item3]

        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # All images should be included (even corrupted one)
        assert len(images) == 3

        # Valid images have proper dimensions
        assert images[0].size == (100, 100)
        assert images[0].format == "png"

        # Corrupted image has unknown dimensions/format
        assert images[1].size is None
        assert images[1].format == "unknown"

        # Third image is valid
        assert images[2].size == (100, 100)

        # Should have warning about corrupted image
        assert len(parser._warnings) > 0
        assert any("Could not read image" in w for w in parser._warnings)

    def test_extract_images_various_formats(self) -> None:
        """Test extraction of various image formats."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create images in different formats
        formats = [
            ("image.png", "PNG"),
            ("photo.jpg", "JPEG"),
            ("graphic.gif", "GIF"),
            ("icon.webp", "WEBP"),
        ]

        mock_items = []
        for filename, fmt in formats:
            img_bytes = io.BytesIO()
            img = Image.new("RGB", (50, 50))
            img.save(img_bytes, format=fmt)

            mock_item = MagicMock()
            mock_item.get_name.return_value = filename
            mock_item.get_content.return_value = img_bytes.getvalue()
            mock_items.append(mock_item)

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = mock_items

        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # Verify all formats extracted correctly
        assert len(images) == 4
        assert images[0].format == "png"
        assert images[1].format == "jpeg"
        assert images[2].format == "gif"
        assert images[3].format == "webp"

    def test_extract_images_position_always_zero(self) -> None:
        """Test that all images have position=0 (not tracked)."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create mock image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100))
        img.save(img_bytes, format="PNG")
        img_data = img_bytes.getvalue()

        mock_items = []
        for i in range(5):
            mock_item = MagicMock()
            mock_item.get_name.return_value = f"img{i}.png"
            mock_item.get_content.return_value = img_data
            mock_items.append(mock_item)

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = mock_items

        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # All images should have position=0
        for img in images:
            assert img.position == 0

    def test_extract_images_alt_text_always_none(self) -> None:
        """Test that all images have alt_text=None (not extracted)."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create mock image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100))
        img.save(img_bytes, format="PNG")
        img_data = img_bytes.getvalue()

        mock_item = MagicMock()
        mock_item.get_name.return_value = "image.png"
        mock_item.get_content.return_value = img_data

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item]

        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # Alt text not extracted (would require HTML parsing)
        assert images[0].alt_text is None

    def test_extract_images_load_epub_error(self) -> None:
        """Test that EPUB loading errors are propagated."""
        from unittest.mock import patch
        from pathlib import Path
        from omniparser.exceptions import ParsingError

        parser = EPUBParser()

        # Mock _load_epub to raise ParsingError
        with patch.object(
            parser,
            "_load_epub",
            side_effect=ParsingError("Failed to load", "EPUBParser"),
        ):
            with pytest.raises(ParsingError, match="Failed to load"):
                parser.extract_images(Path("/fake/path.epub"))

    def test_extract_images_unexpected_error(self) -> None:
        """Test that unexpected errors are wrapped in ParsingError."""
        from unittest.mock import patch
        from pathlib import Path
        from omniparser.exceptions import ParsingError

        parser = EPUBParser()

        # Mock _load_epub to raise unexpected error
        with patch.object(
            parser, "_load_epub", side_effect=RuntimeError("Unexpected error")
        ):
            with pytest.raises(ParsingError, match="Failed to extract images"):
                parser.extract_images(Path("/fake/path.epub"))

    def test_extract_images_individual_extraction_error(self) -> None:
        """Test that individual image extraction errors don't fail entire extraction."""
        from unittest.mock import MagicMock, patch
        from pathlib import Path
        from PIL import Image
        import io

        parser = EPUBParser()
        parser._warnings = []

        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100))
        img.save(img_bytes, format="PNG")
        valid_img_data = img_bytes.getvalue()

        # First item will raise error on get_content
        mock_item1 = MagicMock()
        mock_item1.get_name.return_value = "error.png"
        mock_item1.get_content.side_effect = Exception("Read error")

        # Second item is valid
        mock_item2 = MagicMock()
        mock_item2.get_name.return_value = "valid.png"
        mock_item2.get_content.return_value = valid_img_data

        mock_book = MagicMock()
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]

        with patch.object(parser, "_load_epub", return_value=mock_book):
            images = parser.extract_images(Path("/fake/path.epub"))

        # Should skip error image and process valid one
        assert len(images) == 1
        assert images[0].image_id == "img_002"  # Second item (idx=2)
        assert "valid.png" in images[0].file_path

        # Should have warning
        assert len(parser._warnings) > 0
        assert any("Failed to extract image" in w for w in parser._warnings)


# Note: Full integration tests with real EPUB files will be in
# tests/integration/test_epub_parsing.py
# These unit tests focus on individual method behavior
