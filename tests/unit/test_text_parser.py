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


class TestTextParserInit:
    """Test TextParser initialization."""

    def test_init_no_options(self) -> None:
        """Test initialization without options."""
        parser = TextParser()
        assert parser.options == {
            "auto_detect_encoding": True,
            "encoding": None,
            "normalize_line_endings_enabled": True,
            "attempt_chapter_detection": True,
            "clean_text": True,
            "min_chapter_length": 50,
        }

    def test_init_with_options(self) -> None:
        """Test initialization with custom options."""
        options = {
            "auto_detect_encoding": False,
            "encoding": "utf-8",
            "clean_text": False,
        }
        parser = TextParser(options)

        assert parser.options["auto_detect_encoding"] is False
        assert parser.options["encoding"] == "utf-8"
        assert parser.options["clean_text"] is False
        # Defaults still applied
        assert parser.options["normalize_line_endings_enabled"] is True
        assert parser.options["min_chapter_length"] == 50

    def test_init_warnings_empty(self) -> None:
        """Test warnings list is initialized empty."""
        parser = TextParser()
        assert parser._warnings == []

    def test_init_chapter_patterns_loaded(self) -> None:
        """Test chapter detection patterns are loaded."""
        parser = TextParser()
        assert len(parser.chapter_patterns) > 0
        assert any("Chapter" in pattern[0] for pattern in parser.chapter_patterns)


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
        parser = TextParser()
        with pytest.raises(FileReadError, match="File not found"):
            parser._validate_text_file(Path("/nonexistent/path/file.txt"))

    def test_validate_directory_not_file(self) -> None:
        """Test validation fails for directory."""
        parser = TextParser()
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            with pytest.raises(FileReadError, match="Not a file"):
                parser._validate_text_file(dir_path)

    def test_validate_empty_file(self) -> None:
        """Test validation fails for empty file."""
        parser = TextParser()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            with pytest.raises(ValidationError, match="Empty file"):
                parser._validate_text_file(tmp_path)
        finally:
            tmp_path.unlink()

    def test_validate_large_file_warning(self) -> None:
        """Test validation warns for large files."""
        parser = TextParser()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            # Write just enough to pass validation (>0 bytes)
            tmp.write("test content")
            tmp_path = Path(tmp.name)

        try:
            # Should not raise error, just warn
            parser._validate_text_file(tmp_path)
            assert len(parser._warnings) == 0  # File is too small to trigger warning
        finally:
            tmp_path.unlink()


class TestTextParserReadWithEncoding:
    """Test encoding detection and file reading."""

    def test_read_utf8_file(self) -> None:
        """Test reading UTF-8 encoded file."""
        parser = TextParser({"auto_detect_encoding": True})
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write("Hello World! café résumé")
            tmp_path = Path(tmp.name)

        try:
            text = parser._read_with_encoding(tmp_path)
            assert "Hello World!" in text
            assert "café" in text
            assert "résumé" in text
            assert parser._detected_encoding is not None
        finally:
            tmp_path.unlink()

    def test_read_with_specified_encoding(self) -> None:
        """Test reading with specified encoding."""
        parser = TextParser({"auto_detect_encoding": False, "encoding": "utf-8"})
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write("Test content")
            tmp_path = Path(tmp.name)

        try:
            text = parser._read_with_encoding(tmp_path)
            assert "Test content" in text
            assert parser._detected_encoding == "utf-8"
        finally:
            tmp_path.unlink()

    def test_read_nonexistent_file(self) -> None:
        """Test reading non-existent file raises error."""
        parser = TextParser()
        with pytest.raises(FileReadError):
            parser._read_with_encoding(Path("/nonexistent/file.txt"))


class TestTextParserChapterDetection:
    """Test chapter detection from patterns."""

    def test_detect_chapters_chapter_pattern(self) -> None:
        """Test detection with 'Chapter N' pattern."""
        parser = TextParser()
        text = """Chapter 1: Introduction

This is the first chapter with enough content to meet the minimum word count.
It has multiple sentences and paragraphs.

Chapter 2: Main Content

This is the second chapter with sufficient content.
It also has multiple sentences.

Chapter 3: Conclusion

This is the final chapter with enough words.
The content continues here."""

        chapters = parser._detect_chapters_from_patterns(text)
        assert len(chapters) == 3
        assert chapters[0].title == "Chapter 1: Introduction"
        assert chapters[1].title == "Chapter 2: Main Content"
        assert chapters[2].title == "Chapter 3: Conclusion"

    def test_detect_chapters_part_pattern(self) -> None:
        """Test detection with 'Part N' pattern."""
        parser = TextParser()
        text = """Part 1: Beginning

Content for part one with enough words to meet the minimum.
More content here.

Part 2: Middle

Content for part two with sufficient text.
Additional content.

Part 3: End

Content for part three with adequate text.
Final content."""

        chapters = parser._detect_chapters_from_patterns(text)
        assert len(chapters) == 3
        assert "Part 1" in chapters[0].title
        assert "Part 2" in chapters[1].title
        assert "Part 3" in chapters[2].title

    def test_detect_chapters_section_pattern(self) -> None:
        """Test detection with 'Section N' pattern."""
        parser = TextParser()
        text = """Section 1

Content for section one with enough words.
More text here.

Section 2

Content for section two with sufficient words.
Additional text.

Section A

Content for section A with adequate words.
Final text."""

        chapters = parser._detect_chapters_from_patterns(text)
        assert len(chapters) == 3

    def test_detect_chapters_insufficient_markers(self) -> None:
        """Test detection returns empty list with insufficient markers."""
        parser = TextParser()
        text = """Chapter 1: Only One Chapter

This text only has one chapter marker.
So the parser should return empty list.
And fall back to single chapter creation."""

        chapters = parser._detect_chapters_from_patterns(text)
        assert len(chapters) == 0

    def test_detect_chapters_no_markers(self) -> None:
        """Test detection returns empty list with no markers."""
        parser = TextParser()
        text = """This is plain text without any chapter markers.
It should return an empty list.
The parser will fall back to single chapter."""

        chapters = parser._detect_chapters_from_patterns(text)
        assert len(chapters) == 0


class TestTextParserSingleChapter:
    """Test single chapter creation."""

    def test_create_single_chapter_with_title(self) -> None:
        """Test creating single chapter with title from first line."""
        parser = TextParser()
        text = """My Document Title

This is the content of the document.
It has multiple lines."""

        chapters = parser._create_single_chapter(text)
        assert len(chapters) == 1
        assert chapters[0].title == "My Document Title"
        assert chapters[0].chapter_id == 1
        assert "This is the content" in chapters[0].content

    def test_create_single_chapter_no_title(self) -> None:
        """Test creating single chapter when first line is too long."""
        parser = TextParser()
        # First line is very long
        text = (
            "A" * 150
            + "\n\nThis is the content of the document with a very long first line."
        )

        chapters = parser._create_single_chapter(text)
        assert len(chapters) == 1
        assert chapters[0].title == "Document"

    def test_create_single_chapter_calculates_word_count(self) -> None:
        """Test single chapter has correct word count."""
        parser = TextParser()
        text = "One two three four five"

        chapters = parser._create_single_chapter(text)
        assert chapters[0].word_count == 5

    def test_create_single_chapter_metadata(self) -> None:
        """Test single chapter has correct metadata."""
        parser = TextParser()
        text = "Test content"

        chapters = parser._create_single_chapter(text)
        assert chapters[0].metadata == {"detection_method": "single_chapter"}


class TestTextParserPostProcess:
    """Test chapter post-processing."""

    def test_postprocess_filters_short_chapters(self) -> None:
        """Test filtering of chapters below minimum length."""
        parser = TextParser({"min_chapter_length": 10})
        chapters = [
            Chapter(
                chapter_id=1,
                title="Chapter 1",
                content="Short",
                start_position=0,
                end_position=5,
                word_count=1,
                level=1,
            ),
            Chapter(
                chapter_id=2,
                title="Chapter 2",
                content="This has enough words to pass the minimum threshold",
                start_position=5,
                end_position=60,
                word_count=10,
                level=1,
            ),
        ]

        filtered = parser._postprocess_chapters(chapters)
        assert len(filtered) == 1
        assert filtered[0].title == "Chapter 2"
        assert len(parser._warnings) > 0

    def test_postprocess_handles_duplicate_titles(self) -> None:
        """Test disambiguation of duplicate titles."""
        parser = TextParser({"min_chapter_length": 10})
        chapters = [
            Chapter(
                chapter_id=1,
                title="Chapter 1",
                content="First chapter " * 10,
                start_position=0,
                end_position=100,
                word_count=20,
                level=1,
            ),
            Chapter(
                chapter_id=2,
                title="Chapter 1",
                content="Duplicate title " * 10,
                start_position=100,
                end_position=200,
                word_count=20,
                level=1,
            ),
        ]

        processed = parser._postprocess_chapters(chapters)
        assert len(processed) == 2
        assert processed[0].title == "Chapter 1"
        assert processed[1].title == "Chapter 1 (2)"

    def test_postprocess_renumbers_chapter_ids(self) -> None:
        """Test chapter IDs are renumbered sequentially."""
        parser = TextParser({"min_chapter_length": 5})
        chapters = [
            Chapter(
                chapter_id=5,
                title="Chapter A",
                content="Content " * 10,
                start_position=0,
                end_position=100,
                word_count=10,
                level=1,
            ),
            Chapter(
                chapter_id=10,
                title="Chapter B",
                content="Content " * 10,
                start_position=100,
                end_position=200,
                word_count=10,
                level=1,
            ),
        ]

        processed = parser._postprocess_chapters(chapters)
        assert processed[0].chapter_id == 1
        assert processed[1].chapter_id == 2


class TestTextParserMetadata:
    """Test metadata creation."""

    def test_create_metadata_from_first_line(self) -> None:
        """Test metadata uses first line as title."""
        parser = TextParser()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            tmp_path = Path(tmp.name)

        text = "Document Title\n\nContent here"

        metadata = parser._create_metadata(tmp_path, text)
        assert metadata.title == "Document Title"
        assert metadata.original_format == "text"
        tmp_path.unlink()

    def test_create_metadata_from_filename(self) -> None:
        """Test metadata uses filename when first line is long."""
        parser = TextParser()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            tmp_path = Path(tmp.name)

        # Very long first line
        text = "A" * 150 + "\n\nContent"

        metadata = parser._create_metadata(tmp_path, text)
        assert metadata.title == tmp_path.stem
        tmp_path.unlink()

    def test_create_metadata_includes_encoding(self) -> None:
        """Test metadata includes detected encoding in custom fields."""
        parser = TextParser()
        parser._detected_encoding = "utf-8"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            tmp_path = Path(tmp.name)

        text = "Test content"

        metadata = parser._create_metadata(tmp_path, text)
        assert metadata.custom_fields is not None
        assert metadata.custom_fields["encoding"] == "utf-8"
        tmp_path.unlink()

    def test_create_metadata_includes_line_count(self) -> None:
        """Test metadata includes line count in custom fields."""
        parser = TextParser()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
            tmp_path = Path(tmp.name)

        text = "Line 1\nLine 2\nLine 3"

        metadata = parser._create_metadata(tmp_path, text)
        assert metadata.custom_fields is not None
        assert metadata.custom_fields["line_count"] == 3
        tmp_path.unlink()


class TestTextParserUtilities:
    """Test utility methods."""

    def test_count_words(self) -> None:
        """Test word counting."""
        parser = TextParser()
        assert parser._count_words("one two three") == 3
        assert parser._count_words("Hello world!") == 2
        assert parser._count_words("") == 0

    def test_estimate_reading_time(self) -> None:
        """Test reading time estimation."""
        parser = TextParser()
        # 225 words per minute
        assert parser._estimate_reading_time(225) == 1
        assert parser._estimate_reading_time(450) == 2
        assert parser._estimate_reading_time(1000) == 4
        # Minimum is 1 minute
        assert parser._estimate_reading_time(10) == 1


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
            assert doc.processing_info.parser_used == "TextParser"
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
            assert doc.processing_info.parser_used == "TextParser"
            assert doc.processing_info.parser_version == "1.0.0"
            assert doc.processing_info.processing_time > 0
            assert "detected_encoding" in doc.processing_info.options_used
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
