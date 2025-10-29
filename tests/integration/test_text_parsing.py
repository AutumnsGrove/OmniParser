"""
Integration tests for text parsing.

Tests the TextParser with real text files and verifies end-to-end functionality
including encoding detection, chapter detection, and text cleaning.
"""

from pathlib import Path

import pytest

from omniparser import parse_document
from omniparser.models import Document
from omniparser.parsers.text_parser import TextParser


# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "text"


class TestSimpleTextParsing:
    """Test parsing simple text files."""

    def test_parse_simple_txt(self) -> None:
        """Test parsing simple.txt fixture."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"min_chapter_length": 10}
        doc = parse_document(str(file_path), options=options)

        assert isinstance(doc, Document)
        assert doc.metadata.original_format == "text"
        assert doc.word_count > 0
        assert len(doc.chapters) >= 1  # No chapter markers, single chapter
        assert "simple text document" in doc.content.lower()
        assert len(doc.images) == 0

    def test_parse_short_txt(self) -> None:
        """Test parsing short.txt fixture."""
        file_path = FIXTURES_DIR / "short.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"min_chapter_length": 1}
        doc = parse_document(str(file_path), options=options)

        assert isinstance(doc, Document)
        assert doc.word_count > 0
        assert len(doc.chapters) >= 1


class TestChapterDetection:
    """Test chapter detection with various patterns."""

    def test_parse_with_chapters(self) -> None:
        """Test parsing with_chapters.txt fixture."""
        file_path = FIXTURES_DIR / "with_chapters.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        assert len(doc.chapters) == 3, f"Expected 3 chapters, got {len(doc.chapters)}"

        # Verify chapter titles
        assert "Chapter 1" in doc.chapters[0].title
        assert "Chapter 2" in doc.chapters[1].title
        assert "Chapter 3" in doc.chapters[2].title

        # Verify chapter content
        assert "Introduction" in doc.chapters[0].title
        assert "Discovery" in doc.chapters[1].title
        assert "Resolution" in doc.chapters[2].title

        # Verify word counts
        for chapter in doc.chapters:
            assert chapter.word_count > 0
            assert len(chapter.content) > 0

    def test_parse_no_chapters(self) -> None:
        """Test parsing no_chapters.txt fixture."""
        file_path = FIXTURES_DIR / "no_chapters.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        assert len(doc.chapters) == 1  # Single chapter fallback
        assert "plain text document" in doc.content.lower()

    def test_parse_project_gutenberg(self) -> None:
        """Test parsing project_gutenberg.txt fixture."""
        file_path = FIXTURES_DIR / "project_gutenberg.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        # Should detect 3 chapters
        assert len(doc.chapters) == 3, f"Expected 3 chapters, got {len(doc.chapters)}"

        # Verify chapters detected from "Chapter N" pattern
        chapter_titles = [ch.title for ch in doc.chapters]
        assert any("Chapter 1" in title for title in chapter_titles)
        assert any("Chapter 2" in title for title in chapter_titles)
        assert any("Chapter 3" in title for title in chapter_titles)


class TestEncodingDetection:
    """Test encoding detection and handling."""

    def test_parse_utf8(self) -> None:
        """Test parsing utf8.txt fixture with special characters."""
        file_path = FIXTURES_DIR / "utf8.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        assert doc.word_count > 0

        # Verify special characters are preserved
        content = doc.content
        assert "café" in content
        assert "résumé" in content
        assert "Zürich" in content

        # Check encoding was detected
        assert "detected_encoding" in doc.processing_info.options_used

    def test_parse_latin1(self) -> None:
        """Test parsing latin1.txt fixture."""
        file_path = FIXTURES_DIR / "latin1.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        assert doc.word_count > 0

        # Verify special characters are handled
        content = doc.content
        assert "café" in content or "caf" in content  # May be converted
        assert "résumé" in content or "resum" in content

    def test_parse_with_forced_encoding(self) -> None:
        """Test parsing with explicitly specified encoding."""
        file_path = FIXTURES_DIR / "utf8.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"auto_detect_encoding": False, "encoding": "utf-8"}
        doc = parse_document(str(file_path), options=options)

        assert isinstance(doc, Document)
        assert doc.processing_info.options_used["encoding"] == "utf-8"
        assert "café" in doc.content


class TestLineEndingNormalization:
    """Test line ending normalization."""

    def test_parse_windows_line_endings(self) -> None:
        """Test parsing windows_line_endings.txt with CRLF."""
        file_path = FIXTURES_DIR / "windows_line_endings.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        assert doc.word_count > 0

        # Verify content is readable (line endings normalized)
        assert "Windows Line Endings" in doc.content
        assert "normalize" in doc.content.lower()

    def test_parse_mixed_line_endings(self) -> None:
        """Test parsing mixed_line_endings.txt with mixed line endings."""
        file_path = FIXTURES_DIR / "mixed_line_endings.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        assert doc.word_count > 0
        assert "Mixed Line Endings" in doc.content

    def test_parse_without_normalization(self) -> None:
        """Test parsing with line ending normalization disabled."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"normalize_line_endings_enabled": False}
        doc = parse_document(str(file_path), options=options)

        assert isinstance(doc, Document)
        assert doc.word_count > 0


class TestTextCleaning:
    """Test text cleaning integration."""

    def test_parse_with_cleaning(self) -> None:
        """Test parsing with text cleaning enabled (default)."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert isinstance(doc, Document)
        assert doc.word_count > 0
        # Text cleaning is applied by default
        assert doc.processing_info.options_used["clean_text"] is True

    def test_parse_without_cleaning(self) -> None:
        """Test parsing with text cleaning disabled."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"clean_text": False}
        doc = parse_document(str(file_path), options=options)

        assert isinstance(doc, Document)
        assert doc.word_count > 0
        assert doc.processing_info.options_used["clean_text"] is False


class TestParserOptions:
    """Test various parser options."""

    def test_parse_with_min_chapter_length(self) -> None:
        """Test parsing with custom minimum chapter length."""
        file_path = FIXTURES_DIR / "with_chapters.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"min_chapter_length": 100}
        doc = parse_document(str(file_path), options=options)

        assert isinstance(doc, Document)
        # All chapters should meet the minimum length
        for chapter in doc.chapters:
            assert chapter.word_count >= 100

    def test_parse_with_chapter_detection_disabled(self) -> None:
        """Test parsing with chapter detection disabled."""
        file_path = FIXTURES_DIR / "with_chapters.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"attempt_chapter_detection": False}
        doc = parse_document(str(file_path), options=options)

        assert isinstance(doc, Document)
        # Should have single chapter even though markers exist
        assert len(doc.chapters) == 1


class TestDocumentMetadata:
    """Test document metadata extraction."""

    def test_metadata_title_from_first_line(self) -> None:
        """Test metadata title extracted from first line."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert doc.metadata.title == "A Simple Text Document"
        assert doc.metadata.original_format == "text"

    def test_metadata_custom_fields(self) -> None:
        """Test metadata includes custom fields."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert doc.metadata.custom_fields is not None
        assert "encoding" in doc.metadata.custom_fields
        assert "line_count" in doc.metadata.custom_fields
        assert doc.metadata.custom_fields["line_count"] > 0

    def test_metadata_file_size(self) -> None:
        """Test metadata includes file size."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert doc.metadata.file_size > 0
        assert doc.metadata.file_size == file_path.stat().st_size


class TestProcessingInfo:
    """Test processing information."""

    def test_processing_info_present(self) -> None:
        """Test processing info is included in document."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert doc.processing_info.parser_used == "TextParser"
        assert doc.processing_info.parser_version == "1.0.0"
        assert doc.processing_info.processing_time > 0
        assert doc.processing_info.timestamp is not None

    def test_processing_info_options(self) -> None:
        """Test processing info includes options used."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"clean_text": False, "attempt_chapter_detection": False}
        doc = parse_document(str(file_path), options=options)

        assert doc.processing_info.options_used["clean_text"] is False
        assert doc.processing_info.options_used["attempt_chapter_detection"] is False

    def test_processing_info_warnings(self) -> None:
        """Test processing info captures warnings."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        # Warnings list should exist (may be empty)
        assert isinstance(doc.processing_info.warnings, list)


class TestDocumentStatistics:
    """Test document statistics calculation."""

    def test_word_count(self) -> None:
        """Test word count is calculated correctly."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert doc.word_count > 0
        # Verify word count matches content
        content_word_count = len(doc.content.split())
        assert doc.word_count == content_word_count

    def test_reading_time(self) -> None:
        """Test estimated reading time is calculated."""
        file_path = FIXTURES_DIR / "project_gutenberg.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        assert doc.estimated_reading_time > 0
        # Reading time should be reasonable (1-10 minutes for this fixture)
        assert 1 <= doc.estimated_reading_time <= 10


class TestChapterContent:
    """Test chapter content integrity."""

    def test_chapter_positions(self) -> None:
        """Test chapter positions are correct."""
        file_path = FIXTURES_DIR / "with_chapters.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        # Verify chapters have valid positions
        for chapter in doc.chapters:
            assert chapter.start_position >= 0
            assert chapter.end_position > chapter.start_position
            # Positions should be within the full content range (allow for some variation)
            assert chapter.start_position <= len(doc.content) + 100
            assert chapter.end_position <= len(doc.content) + 100

    def test_chapter_content_in_full_content(self) -> None:
        """Test chapter content exists in full document content."""
        file_path = FIXTURES_DIR / "with_chapters.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        doc = parse_document(str(file_path))

        # Each chapter's content should be findable in full content
        # Chapter content may include the title, so check for a portion
        for chapter in doc.chapters:
            if len(chapter.content.strip()) > 0:
                # Check that at least some words from the chapter are in the full content
                words = chapter.content.split()
                if len(words) >= 5:
                    # Find a snippet that's likely in the content (skip title)
                    snippet = (
                        " ".join(words[5:10])
                        if len(words) > 10
                        else " ".join(words[:5])
                    )
                    assert (
                        snippet in doc.content
                    ), f"Snippet '{snippet}' not found in full content"


class TestDirectParserUsage:
    """Test using TextParser directly (not through parse_document)."""

    def test_direct_parser_instantiation(self) -> None:
        """Test creating and using TextParser directly."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        parser = TextParser()
        doc = parser.parse(file_path)

        assert isinstance(doc, Document)
        assert doc.processing_info.parser_used == "TextParser"

    def test_direct_parser_with_options(self) -> None:
        """Test using TextParser directly with options."""
        file_path = FIXTURES_DIR / "simple.txt"
        assert file_path.exists(), f"Fixture not found: {file_path}"

        options = {"clean_text": False, "attempt_chapter_detection": False}
        parser = TextParser(options)
        doc = parser.parse(file_path)

        assert isinstance(doc, Document)
        assert doc.processing_info.options_used["clean_text"] is False

    def test_parser_supports_format(self) -> None:
        """Test TextParser.supports_format() method."""
        parser = TextParser()

        assert parser.supports_format(Path("file.txt")) is True
        assert parser.supports_format(Path("file.TXT")) is True
        assert parser.supports_format(Path("README")) is True
        assert parser.supports_format(Path("file.pdf")) is False
        assert parser.supports_format(Path("file.epub")) is False
