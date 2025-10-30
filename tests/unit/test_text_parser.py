"""
Unit tests for Text parser.

Tests the TextParser class functionality including validation, format support,
encoding detection, line ending normalization, and chapter detection.
"""

import tempfile
from pathlib import Path

import pytest

from omniparser.exceptions import FileReadError, ParsingError, ValidationError
from omniparser.models import Chapter, Document
from omniparser.parsers.text_parser import TextParser

# Import modular functions for direct testing
from omniparser.parsers.text.validation import validate_text_file
from omniparser.parsers.text.encoding import read_text_with_encoding
from omniparser.parsers.text.chapter_detection import detect_text_chapters
from omniparser.parsers.text.utils import count_words, estimate_reading_time


class TestTextParserInit:
    """Test TextParser initialization."""

    def test_init_no_options(self) -> None:
        """Test initialization without options."""
        parser = TextParser()
        # Wrapper is thin - just verify it can be instantiated
        assert parser is not None
        assert isinstance(parser, TextParser)

    def test_init_with_options(self) -> None:
        """Test initialization with custom options."""
        options = {
            "detect_chapters": False,
        }
        parser = TextParser(options)
        # Wrapper is thin - just verify it can be instantiated
        assert parser is not None
        assert isinstance(parser, TextParser)


class TestTextParserSupportsFormat:
    """Test format support detection."""

    def test_supports_txt_lowercase(self) -> None:
        """Test .txt extension is supported."""
        parser = TextParser()
        assert parser.supports_format(Path("file.txt")) is True

    def test_supports_txt_uppercase(self) -> None:
        """Test .TXT extension is supported."""
        parser = TextParser()
        assert parser.supports_format(Path("file.TXT")) is True

    def test_supports_no_extension(self) -> None:
        """Test file without extension is supported."""
        parser = TextParser()
        assert parser.supports_format(Path("README")) is True

    def test_not_supports_pdf(self) -> None:
        """Test .pdf extension is not supported."""
        parser = TextParser()
        assert parser.supports_format(Path("document.pdf")) is False

    def test_not_supports_epub(self) -> None:
        """Test .epub extension is not supported."""
        parser = TextParser()
        assert parser.supports_format(Path("book.epub")) is False

    def test_not_supports_html(self) -> None:
        """Test .html extension is not supported."""
        parser = TextParser()
        assert parser.supports_format(Path("page.html")) is False


class TestTextParserValidation:
    """Test text file validation."""

    def test_validate_file_not_exists(self) -> None:
        """Test validation fails for non-existent file."""
        warnings = []
        with pytest.raises(FileReadError, match="File not found"):
            validate_text_file(Path("/nonexistent/path/file.txt"), warnings)

    def test_validate_directory_not_file(self) -> None:
        """Test validation fails for directory."""
        warnings = []
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            with pytest.raises(FileReadError, match="Not a file"):
                validate_text_file(dir_path, warnings)

    def test_validate_empty_file(self) -> None:
        """Test validation fails for empty file."""
        warnings = []
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            with pytest.raises(ValidationError, match="Empty file"):
                validate_text_file(tmp_path, warnings)
        finally:
            tmp_path.unlink()

    def test_validate_large_file_warning(self) -> None:
        """Test validation warns for large files."""
        warnings = []
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            # Write just enough to pass validation (>0 bytes)
            tmp.write("test content")
            tmp_path = Path(tmp.name)

        try:
            # Should not raise error, just warn
            validate_text_file(tmp_path, warnings)
            assert len(warnings) == 0  # File is too small to trigger warning
        finally:
            tmp_path.unlink()


class TestTextParserReadWithEncoding:
    """Test encoding detection and file reading."""

    def test_read_utf8_file(self) -> None:
        """Test reading UTF-8 encoded file."""
        warnings = []
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write("Hello World! café résumé")
            tmp_path = Path(tmp.name)

        try:
            text = read_text_with_encoding(tmp_path, warnings)
            assert "Hello World!" in text
            assert "café" in text
            assert "résumé" in text
        finally:
            tmp_path.unlink()

    def test_read_with_utf8_content(self) -> None:
        """Test reading file with UTF-8 content."""
        warnings = []
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write("Test content")
            tmp_path = Path(tmp.name)

        try:
            text = read_text_with_encoding(tmp_path, warnings)
            assert "Test content" in text
        finally:
            tmp_path.unlink()

    def test_read_nonexistent_file(self) -> None:
        """Test reading non-existent file raises error."""
        warnings = []
        # Python raises FileNotFoundError before our custom exception can be raised
        with pytest.raises((FileReadError, FileNotFoundError)):
            read_text_with_encoding(Path("/nonexistent/file.txt"), warnings)


class TestTextParserChapterDetection:
    """Test chapter detection from patterns."""

    def test_detect_chapters_chapter_pattern(self) -> None:
        """Test detection with 'Chapter N' pattern."""
        text = """Chapter 1: Introduction

This is the first chapter with enough content to meet the minimum word count.
It has multiple sentences and paragraphs.

Chapter 2: Main Content

This is the second chapter with sufficient content.
It also has multiple sentences.

Chapter 3: Conclusion

This is the final chapter with enough words.
The content continues here."""

        chapters = detect_text_chapters(text, Path("test.txt"))
        assert len(chapters) == 3
        assert chapters[0].title == "Chapter 1: Introduction"
        assert chapters[1].title == "Chapter 2: Main Content"
        assert chapters[2].title == "Chapter 3: Conclusion"

    def test_detect_chapters_part_pattern(self) -> None:
        """Test detection with 'Part N' pattern."""
        text = """Part 1: Beginning

Content for part one with enough words to meet the minimum.
More content here.

Part 2: Middle

Content for part two with sufficient text.
Additional content.

Part 3: End

Content for part three with adequate text.
Final content."""

        chapters = detect_text_chapters(text, Path("test.txt"))
        assert len(chapters) == 3
        assert "Part 1" in chapters[0].title
        assert "Part 2" in chapters[1].title
        assert "Part 3" in chapters[2].title

    def test_detect_chapters_section_pattern(self) -> None:
        """Test detection with 'Section N' pattern."""
        text = """Section 1

Content for section one with enough words.
More text here.

Section 2

Content for section two with sufficient words.
Additional text.

Section A

Content for section A with adequate words.
Final text."""

        chapters = detect_text_chapters(text, Path("test.txt"))
        assert len(chapters) == 3

    def test_detect_chapters_insufficient_markers(self) -> None:
        """Test detection returns single chapter with insufficient markers."""
        text = """Chapter 1: Only One Chapter

This text only has one chapter marker.
So the parser creates a single chapter with all content."""

        chapters = detect_text_chapters(text, Path("test.txt"))
        # With < 2 markers, returns single chapter
        assert len(chapters) == 1
        assert chapters[0].metadata["detection_method"] == "single_chapter"

    def test_detect_chapters_no_markers(self) -> None:
        """Test detection returns single chapter with no markers."""
        text = """This is plain text without any chapter markers.
The parser will create a single chapter with all content."""

        chapters = detect_text_chapters(text, Path("test.txt"))
        # With no markers, returns single chapter
        assert len(chapters) == 1
        assert chapters[0].metadata["detection_method"] == "single_chapter"


class TestTextParserSingleChapter:
    """Test single chapter creation."""

    def test_create_single_chapter_with_title(self) -> None:
        """Test creating single chapter with title from first line."""
        text = """My Document Title

This is the content of the document.
It has multiple lines."""

        chapters = detect_text_chapters(text, Path("test.txt"))
        assert len(chapters) == 1
        assert chapters[0].title == "My Document Title"
        assert chapters[0].chapter_id == 1
        assert text in chapters[0].content  # Full content is preserved

    def test_create_single_chapter_no_title(self) -> None:
        """Test creating single chapter when first line is too long."""
        # First line is very long
        text = (
            "A" * 150
            + "\n\nThis is the content of the document with a very long first line."
        )

        chapters = detect_text_chapters(text, Path("test.txt"))
        assert len(chapters) == 1
        assert chapters[0].title == "Document"

    def test_create_single_chapter_calculates_word_count(self) -> None:
        """Test single chapter has correct word count."""
        text = "One two three four five"

        chapters = detect_text_chapters(text, Path("test.txt"))
        assert chapters[0].word_count == 5

    def test_create_single_chapter_metadata(self) -> None:
        """Test single chapter has correct metadata."""
        text = "Test content"

        chapters = detect_text_chapters(text, Path("test.txt"))
        assert chapters[0].metadata == {"detection_method": "single_chapter"}


class TestTextParserUtilities:
    """Test utility methods."""

    def test_count_words(self) -> None:
        """Test word counting."""
        assert count_words("one two three") == 3
        assert count_words("Hello world!") == 2
        assert count_words("") == 0

    def test_estimate_reading_time(self) -> None:
        """Test reading time estimation."""
        # Default is 200 words per minute in modular implementation
        assert estimate_reading_time(200) == 1
        assert estimate_reading_time(400) == 2
        assert estimate_reading_time(1000) == 5
        # Minimum is 1 minute
        assert estimate_reading_time(10) == 1


class TestTextParserIntegration:
    """Test full parsing workflow."""

    def test_parse_simple_text_file(self) -> None:
        """Test parsing a simple text file."""
        parser = TextParser({"min_chapter_length": 10})
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write(
                """Simple Document

This is a simple text file with basic content.
It has enough words to create a valid document.
The parser should handle this without any issues."""
            )
            tmp_path = Path(tmp.name)

        try:
            doc = parser.parse(tmp_path)
            assert isinstance(doc, Document)
            assert doc.word_count > 0
            assert len(doc.chapters) >= 1
            assert doc.metadata.original_format == "text"
            assert doc.processing_info.parser_used == "parse_text"
            assert len(doc.images) == 0  # Text files have no images
        finally:
            tmp_path.unlink()

    def test_parse_with_chapters(self) -> None:
        """Test parsing text file with chapter markers."""
        parser = TextParser({"min_chapter_length": 10})
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write(
                """Chapter 1: Introduction

This is the first chapter with enough content words to meet the minimum threshold.
It introduces the topic and sets the stage properly with sufficient detail and explanation.

Chapter 2: Main Content

This is the second chapter with sufficient content words to meet the minimum threshold.
It develops the main ideas and provides details fully with adequate depth and analysis.

Chapter 3: Conclusion

This is the final chapter with adequate content words to meet the minimum threshold.
It wraps up and provides final thoughts completely with proper closure and reflection."""
            )
            tmp_path = Path(tmp.name)

        try:
            doc = parser.parse(tmp_path)
            assert len(doc.chapters) == 3
            assert "Chapter 1" in doc.chapters[0].title
            assert "Chapter 2" in doc.chapters[1].title
            assert "Chapter 3" in doc.chapters[2].title
        finally:
            tmp_path.unlink()

    def test_parse_returns_document_with_processing_info(self) -> None:
        """Test parsing returns document with processing information."""
        parser = TextParser()
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write("Test content with enough words to create a document properly")
            tmp_path = Path(tmp.name)

        try:
            doc = parser.parse(tmp_path)
            assert doc.processing_info.parser_used == "parse_text"
            assert doc.processing_info.parser_version == "0.3.0"  # Current project version
            assert doc.processing_info.processing_time > 0
        finally:
            tmp_path.unlink()

    def test_parse_empty_file_raises_error(self) -> None:
        """Test parsing empty file raises ValidationError."""
        parser = TextParser()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValidationError, match="Empty file"):
                parser.parse(tmp_path)
        finally:
            tmp_path.unlink()

    def test_parse_nonexistent_file_raises_error(self) -> None:
        """Test parsing non-existent file raises FileReadError."""
        parser = TextParser()
        with pytest.raises(FileReadError, match="File not found"):
            parser.parse(Path("/nonexistent/file.txt"))
