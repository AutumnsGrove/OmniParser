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
FRANKENSTEIN_EPUB = FIXTURES_DIR / "frankenstein.epub"
PRIDE_AND_PREJUDICE_EPUB = FIXTURES_DIR / "pride-and-prejudice.epub"


class TestEPUBParsingFrankenstein:
    """Integration tests with Frankenstein EPUB (public domain)."""

    @pytest.fixture
    def epub_path(self) -> Path:
        """Return path to test EPUB file."""
        assert FRANKENSTEIN_EPUB.exists(), "Test EPUB file missing"
        return FRANKENSTEIN_EPUB

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
        assert "Frankenstein" in doc.metadata.title

        # Author
        assert doc.metadata.author == "Mary Wollstonecraft Shelley"

        # Language
        assert doc.metadata.language == "en"

        # Date (may or may not be present in public domain books)
        # Just verify it's accessible (can be None)
        _ = doc.metadata.publication_date

    def test_parse_epub_chapters(self, epub_path: Path) -> None:
        """Test chapter detection."""
        doc = parse_document(epub_path)

        # Should have detected chapters
        assert len(doc.chapters) > 0
        assert len(doc.chapters) >= 10  # At least 10 chapters
        # Frankenstein has 30 chapters
        assert len(doc.chapters) == 30

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
        # Frankenstein has ~78k words
        assert doc.word_count > 70000  # At least 70k words
        assert doc.word_count < 85000  # Less than 85k words

        # Chapter word counts should sum to approximately total
        # (may differ slightly due to spacing/cleaning)
        chapter_words = sum(ch.word_count for ch in doc.chapters)
        difference = abs(doc.word_count - chapter_words)
        # Allow up to 10% difference
        assert difference < doc.word_count * 0.1

    def test_parse_epub_images(self, epub_path: Path) -> None:
        """Test image extraction (or lack thereof)."""
        doc = parse_document(epub_path)

        # Frankenstein has no images (plain text public domain version)
        # This tests that parsing works correctly with image-free EPUBs
        assert len(doc.images) == 0

    def test_parse_epub_performance(self, epub_path: Path) -> None:
        """Test parsing performance."""
        start = time.time()
        doc = parse_document(epub_path)
        elapsed = time.time() - start

        # Should parse in reasonable time
        assert elapsed < 5.0, f"Parsing took {elapsed:.2f}s (should be <5s)"

        # For Frankenstein (~465KB), should be fast
        assert elapsed < 1.0, f"Parsing took {elapsed:.2f}s (expected <1s for 465KB)"

    def test_parse_epub_warnings(self, epub_path: Path) -> None:
        """Test that parsing warnings are reasonable."""
        doc = parse_document(epub_path)

        # Frankenstein has 2 warnings about filtered short chapters (title page, TOC)
        # This is expected behavior - short chapters are filtered by min_chapter_length
        assert len(doc.processing_info.warnings) <= 5  # Allow up to 5 warnings

        # All warnings should be about short chapters (informational, not errors)
        for warning in doc.processing_info.warnings:
            assert "Filtered short chapter" in warning or "chapter" in warning.lower()

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
        # 78k words at 225 WPM = ~347 minutes
        assert doc.estimated_reading_time > 300
        assert doc.estimated_reading_time < 400

    def test_parse_epub_with_custom_options(self, epub_path: Path) -> None:
        """Test parsing with custom options."""
        # Parse without images (Frankenstein has none anyway)
        doc = parse_document(epub_path, options={"extract_images": False})
        assert len(doc.images) == 0

        # Parse without text cleaning
        doc = parse_document(epub_path, options={"clean_text": False})
        assert doc.content is not None
        # Should still have parsed successfully
        assert len(doc.chapters) > 0

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


class TestEPUBParsingPrideAndPrejudice:
    """Integration tests with Pride and Prejudice EPUB (image-heavy)."""

    @pytest.fixture
    def epub_path(self) -> Path:
        """Return path to Pride and Prejudice EPUB."""
        assert PRIDE_AND_PREJUDICE_EPUB.exists(), "Test EPUB file missing"
        return PRIDE_AND_PREJUDICE_EPUB

    def test_parse_epub_with_images(self, epub_path: Path) -> None:
        """Test image extraction with image-heavy EPUB."""
        doc = parse_document(epub_path)

        # Pride and Prejudice has 163 images
        assert len(doc.images) > 150
        assert len(doc.images) <= 170  # Allow some variance

        # Check image references are valid
        for image in doc.images:
            assert image.image_id is not None
            assert image.file_path is not None
            # Position tracking not implemented yet
            assert image.position == 0

    def test_parse_epub_metadata_complete(self, epub_path: Path) -> None:
        """Test metadata extraction from well-formed EPUB."""
        doc = parse_document(epub_path)

        assert doc.metadata.title == "Pride and Prejudice"
        assert doc.metadata.author == "Jane Austen"
        assert doc.metadata.language == "en"

    def test_parse_large_epub_performance(self, epub_path: Path) -> None:
        """Test performance with large EPUB (24MB)."""
        start = time.time()
        doc = parse_document(epub_path)
        elapsed = time.time() - start

        # Should still parse in reasonable time despite 24MB size
        assert elapsed < 10.0, f"Parsing took {elapsed:.2f}s (should be <10s)"

    def test_parse_epub_large_word_count(self, epub_path: Path) -> None:
        """Test word count with large book."""
        doc = parse_document(epub_path)

        # Pride and Prejudice has ~132k words
        assert doc.word_count > 125000
        assert doc.word_count < 140000


class TestEPUBParsingEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_nonexistent_file(self) -> None:
        """Test error handling for missing file."""
        with pytest.raises(FileReadError):
            parse_document(Path("nonexistent.epub"))

    def test_parse_invalid_file_type(self) -> None:
        """Test error handling for wrong file type (non-EPUB)."""
        # Create a temporary file with unsupported extension for EPUB parser
        import tempfile
        from omniparser.parsers.epub_parser import EPUBParser

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"Not an EPUB file")
            tmp_path = Path(tmp.name)

        try:
            # Test that EPUBParser rejects non-EPUB files
            parser = EPUBParser()
            with pytest.raises(UnsupportedFormatError):
                parser.parse(tmp_path)
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
