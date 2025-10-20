"""
Integration tests for EPUB parsing with real EPUB files.

Tests the complete parsing pipeline from EPUB file to Document object
using real-world EPUB files.
"""

import time
from pathlib import Path

import pytest

from omniparser import parse_document
from omniparser.exceptions import FileReadError, ValidationError, UnsupportedFormatError
from omniparser.models import Document


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "epub"
SYSTEM_FOR_WRITING_EPUB = FIXTURES_DIR / "A System for Writing.epub"


class TestEPUBParsingSystemForWriting:
    """Integration tests with 'A System for Writing' EPUB."""

    @pytest.fixture
    def epub_path(self) -> Path:
        """Return path to test EPUB file."""
        assert SYSTEM_FOR_WRITING_EPUB.exists(), "Test EPUB file missing"
        return SYSTEM_FOR_WRITING_EPUB

    def test_parse_epub_successfully(self, epub_path: Path) -> None:
        """Test that EPUB parses without errors."""
        doc = parse_document(epub_path)

        assert isinstance(doc, Document)
        assert doc.content is not None
        assert len(doc.content) > 0

    def test_parse_epub_metadata(self, epub_path: Path) -> None:
        """Test metadata extraction."""
        doc = parse_document(epub_path)

        # Title should be extracted
        assert doc.metadata.title is not None
        assert "System for Writing" in doc.metadata.title

        # Author
        assert doc.metadata.author == "Bob Doto"

        # Publisher
        assert doc.metadata.publisher == "New Old Traditions"

        # Language
        assert doc.metadata.language == "en"

        # Date (should be parsed successfully now)
        assert doc.metadata.publication_date is not None

    def test_parse_epub_chapters(self, epub_path: Path) -> None:
        """Test chapter detection."""
        doc = parse_document(epub_path)

        # Should have detected chapters
        assert len(doc.chapters) > 0
        assert len(doc.chapters) >= 10  # At least 10 chapters

        # First chapter should be Introduction
        first_chapter = doc.chapters[0]
        assert "Introduction" in first_chapter.title

        # All chapters should have content
        for chapter in doc.chapters:
            assert len(chapter.content) > 0
            assert chapter.word_count > 0
            assert chapter.start_position >= 0
            assert chapter.end_position > chapter.start_position

    def test_parse_epub_word_count(self, epub_path: Path) -> None:
        """Test word count calculation."""
        doc = parse_document(epub_path)

        # Should have reasonable word count
        assert doc.word_count > 30000  # At least 30k words
        assert doc.word_count < 100000  # Less than 100k words

        # Chapter word counts should sum to approximately total
        # (may differ slightly due to spacing/cleaning)
        chapter_words = sum(ch.word_count for ch in doc.chapters)
        difference = abs(doc.word_count - chapter_words)
        # Allow up to 10% difference
        assert difference < doc.word_count * 0.1

    def test_parse_epub_images(self, epub_path: Path) -> None:
        """Test image extraction."""
        doc = parse_document(epub_path)

        # Should have extracted images
        assert len(doc.images) > 0
        assert len(doc.images) >= 50  # At least 50 images

        # Check image references
        for image in doc.images:
            assert image.image_id is not None
            assert image.file_path is not None
            # Position tracking not implemented yet
            assert image.position == 0

    def test_parse_epub_performance(self, epub_path: Path) -> None:
        """Test parsing performance."""
        start = time.time()
        doc = parse_document(epub_path)
        elapsed = time.time() - start

        # Should parse in reasonable time
        assert elapsed < 5.0, f"Parsing took {elapsed:.2f}s (should be <5s)"

        # For this ~5MB file, should be much faster
        assert elapsed < 1.0, f"Parsing took {elapsed:.2f}s (expected <1s for 5MB)"

    def test_parse_epub_no_warnings(self, epub_path: Path) -> None:
        """Test that parsing produces no warnings."""
        doc = parse_document(epub_path)

        # Should have no warnings
        assert len(doc.processing_info.warnings) == 0

    def test_parse_epub_processing_info(self, epub_path: Path) -> None:
        """Test processing info metadata."""
        doc = parse_document(epub_path)

        assert doc.processing_info.parser_used == "EPUBParser"
        assert doc.processing_info.parser_version == "1.0.0"
        assert doc.processing_info.processing_time > 0
        assert doc.processing_info.timestamp is not None
        assert "extract_images" in doc.processing_info.options_used

    def test_parse_epub_reading_time(self, epub_path: Path) -> None:
        """Test reading time estimation."""
        doc = parse_document(epub_path)

        # Should have reasonable reading time estimate
        # 40k words at 225 WPM = ~178 minutes
        assert doc.estimated_reading_time > 100
        assert doc.estimated_reading_time < 300

    def test_parse_epub_with_custom_options(self, epub_path: Path) -> None:
        """Test parsing with custom options."""
        # Parse without images
        doc = parse_document(epub_path, options={"extract_images": False})
        assert len(doc.images) == 0

        # Parse without text cleaning
        doc = parse_document(epub_path, options={"clean_text": False})
        assert doc.content is not None

    def test_parse_epub_chapter_hierarchy(self, epub_path: Path) -> None:
        """Test chapter hierarchy levels."""
        doc = parse_document(epub_path)

        # All chapters should have level set
        for chapter in doc.chapters:
            assert chapter.level >= 1
            assert chapter.level <= 3  # Typically 1-3 levels

    def test_parse_epub_content_completeness(self, epub_path: Path) -> None:
        """Test that all chapter content is in full document content."""
        doc = parse_document(epub_path)

        # Full content should contain all chapter content
        for chapter in doc.chapters:
            # Extract chapter from full content using positions
            chapter_from_doc = doc.content[
                chapter.start_position : chapter.end_position
            ]
            # Should be similar (may have minor whitespace differences)
            assert len(chapter_from_doc) > 0
            # Check a sample of words from chapter appear
            chapter_words = chapter.content.split()[:10]
            for word in chapter_words:
                if len(word) > 3:  # Skip very short words
                    assert word in chapter_from_doc or word in doc.content


class TestEPUBParsingEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_nonexistent_file(self) -> None:
        """Test error handling for missing file."""
        with pytest.raises(FileReadError):
            parse_document(Path("nonexistent.epub"))

    def test_parse_invalid_file_type(self) -> None:
        """Test error handling for wrong file type."""
        # Create a temporary text file with .txt extension
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"Not an EPUB file")
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(UnsupportedFormatError):
                parse_document(tmp_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_parse_empty_file(self) -> None:
        """Test error handling for empty file."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValidationError):
                parse_document(tmp_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
