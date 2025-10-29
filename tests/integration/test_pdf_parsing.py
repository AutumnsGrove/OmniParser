"""
Integration tests for PDF parsing with real PDF files.

Tests the complete parsing pipeline from PDF file to Document object
using real-world PDF files.
"""

import time
from pathlib import Path

import pytest

from omniparser import parse_document
from omniparser.exceptions import FileReadError, ValidationError
from omniparser.models import Document


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pdf"


class TestPDFParsingSimple:
    """Integration tests with simple text-based PDF."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to simple test PDF file."""
        simple_pdf = FIXTURES_DIR / "simple.pdf"
        if not simple_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return simple_pdf

    def test_parse_pdf_successfully(self, pdf_path: Path) -> None:
        """Test that PDF parses without errors."""
        doc = parse_document(pdf_path)

        assert isinstance(doc, Document)
        assert doc.content is not None
        assert len(doc.content) > 0

    def test_parse_pdf_metadata(self, pdf_path: Path) -> None:
        """Test metadata extraction."""
        doc = parse_document(pdf_path)

        # Should have metadata
        assert doc.metadata is not None
        assert doc.metadata.original_format == "pdf"

        # Should have page count in custom fields
        assert "page_count" in doc.metadata.custom_fields
        assert doc.metadata.custom_fields["page_count"] > 0

    def test_parse_pdf_word_count(self, pdf_path: Path) -> None:
        """Test word count calculation."""
        doc = parse_document(pdf_path)

        # Should have reasonable word count
        assert doc.word_count > 0

    def test_parse_pdf_processing_info(self, pdf_path: Path) -> None:
        """Test processing information."""
        doc = parse_document(pdf_path)

        assert doc.processing_info.parser_used == "PDFParser"
        assert doc.processing_info.parser_version == "1.0.0"
        assert doc.processing_info.processing_time > 0
        assert doc.processing_info.timestamp is not None


class TestPDFParsingWithHeadings:
    """Integration tests with PDF containing headings."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to PDF with headings."""
        headings_pdf = FIXTURES_DIR / "with_headings.pdf"
        if not headings_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return headings_pdf

    def test_parse_pdf_chapters(self, pdf_path: Path) -> None:
        """Test chapter detection from headings."""
        doc = parse_document(pdf_path)

        # Should have detected chapters
        assert len(doc.chapters) > 0

        # All chapters should have content
        for chapter in doc.chapters:
            assert len(chapter.content) > 0
            assert chapter.word_count > 0
            assert chapter.start_position >= 0
            assert chapter.end_position > chapter.start_position

    def test_parse_pdf_chapter_structure(self, pdf_path: Path) -> None:
        """Test chapter hierarchy."""
        doc = parse_document(pdf_path)

        # Chapters should have titles
        for chapter in doc.chapters:
            assert chapter.title is not None
            assert len(chapter.title) > 0

        # Chapters should be ordered by position
        for i in range(len(doc.chapters) - 1):
            assert doc.chapters[i].start_position < doc.chapters[i + 1].start_position


class TestPDFParsingWithImages:
    """Integration tests with PDF containing images."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to PDF with images."""
        images_pdf = FIXTURES_DIR / "with_images.pdf"
        if not images_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return images_pdf

    def test_parse_pdf_extract_images(self, pdf_path: Path) -> None:
        """Test image extraction."""
        doc = parse_document(pdf_path, {"extract_images": True})

        # Should have extracted images
        assert len(doc.images) > 0

        # All images should have valid metadata
        for img in doc.images:
            assert img.image_id is not None
            assert img.format is not None
            assert img.file_path is not None
            # Verify file exists
            assert Path(img.file_path).exists()

    def test_parse_pdf_without_images(self, pdf_path: Path) -> None:
        """Test parsing without image extraction."""
        doc = parse_document(pdf_path, {"extract_images": False})

        # Should not have extracted images
        assert len(doc.images) == 0


class TestPDFParsingWithTables:
    """Integration tests with PDF containing tables."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to PDF with tables."""
        tables_pdf = FIXTURES_DIR / "with_tables.pdf"
        if not tables_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return tables_pdf

    def test_parse_pdf_extract_tables(self, pdf_path: Path) -> None:
        """Test table extraction."""
        doc = parse_document(pdf_path, {"extract_tables": True})

        # Content should contain markdown table markers
        assert "|" in doc.content

    def test_parse_pdf_without_tables(self, pdf_path: Path) -> None:
        """Test parsing without table extraction."""
        doc = parse_document(pdf_path, {"extract_tables": False})

        # Should still parse successfully
        assert doc.content is not None


class TestPDFParsingScanned:
    """Integration tests with scanned (OCR-needed) PDF."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to scanned PDF."""
        scanned_pdf = FIXTURES_DIR / "scanned.pdf"
        if not scanned_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return scanned_pdf

    def test_parse_scanned_pdf_with_ocr(self, pdf_path: Path) -> None:
        """Test OCR-based parsing."""
        # This test requires Tesseract to be installed
        try:
            import pytesseract
        except ImportError:
            pytest.skip("Tesseract not available")

        doc = parse_document(pdf_path, {"ocr_enabled": True})

        # Should have extracted some text via OCR
        assert doc.content is not None
        assert len(doc.content) > 0

    def test_parse_scanned_pdf_without_ocr(self, pdf_path: Path) -> None:
        """Test parsing scanned PDF without OCR."""
        doc = parse_document(pdf_path, {"ocr_enabled": False})

        # Should still parse but with minimal text
        assert doc.content is not None


class TestPDFParsingLarge:
    """Integration tests with large PDF."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to large PDF."""
        large_pdf = FIXTURES_DIR / "large.pdf"
        if not large_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return large_pdf

    def test_parse_large_pdf_successfully(self, pdf_path: Path) -> None:
        """Test that large PDF parses successfully."""
        doc = parse_document(pdf_path)

        assert isinstance(doc, Document)
        assert doc.content is not None

    def test_parse_large_pdf_performance(self, pdf_path: Path) -> None:
        """Test performance with large PDF."""
        start_time = time.time()
        doc = parse_document(pdf_path)
        end_time = time.time()

        processing_time = end_time - start_time

        # Should complete in reasonable time (adjust threshold as needed)
        # For 100+ page PDF, aim for < 30 seconds
        assert processing_time < 30.0

        # Verify processing time is tracked
        assert doc.processing_info.processing_time > 0


class TestPDFParsingOptions:
    """Test various parsing options."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to test PDF."""
        simple_pdf = FIXTURES_DIR / "simple.pdf"
        if not simple_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return simple_pdf

    def test_parse_with_text_cleaning(self, pdf_path: Path) -> None:
        """Test parsing with text cleaning enabled."""
        doc = parse_document(pdf_path, {"clean_text": True})

        assert doc.content is not None
        # Text should be cleaned (no excessive whitespace)
        assert "   " not in doc.content  # No triple spaces

    def test_parse_without_text_cleaning(self, pdf_path: Path) -> None:
        """Test parsing without text cleaning."""
        doc = parse_document(pdf_path, {"clean_text": False})

        assert doc.content is not None

    def test_parse_with_custom_heading_size(self, pdf_path: Path) -> None:
        """Test parsing with custom heading size threshold."""
        doc = parse_document(pdf_path, {"min_heading_size": 16.0})

        assert doc.content is not None

    def test_parse_with_chapter_detection_disabled(self, pdf_path: Path) -> None:
        """Test parsing without chapter detection."""
        doc = parse_document(pdf_path, {"detect_chapters": False})

        # Should have no chapters or single default chapter
        assert len(doc.chapters) <= 1


class TestPDFParsingErrorHandling:
    """Test error handling."""

    def test_parse_nonexistent_pdf(self) -> None:
        """Test parsing non-existent file."""
        with pytest.raises(FileReadError):
            parse_document("/nonexistent/path/document.pdf")

    def test_parse_corrupted_pdf(self) -> None:
        """Test parsing corrupted PDF."""
        # Create a fake PDF file
        corrupted_pdf = FIXTURES_DIR / "corrupted.pdf"
        if not corrupted_pdf.parent.exists():
            corrupted_pdf.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid PDF content
        with open(corrupted_pdf, "wb") as f:
            f.write(b"Not a valid PDF file")

        try:
            with pytest.raises((FileReadError, ValidationError)):
                parse_document(corrupted_pdf)
        finally:
            if corrupted_pdf.exists():
                corrupted_pdf.unlink()


class TestPDFParsingTextCleaning:
    """Test text cleaning integration."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to test PDF."""
        simple_pdf = FIXTURES_DIR / "simple.pdf"
        if not simple_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return simple_pdf

    def test_parse_with_cleaning(self, pdf_path: Path) -> None:
        """Test that text cleaning is applied."""
        doc_cleaned = parse_document(pdf_path, {"clean_text": True})
        doc_raw = parse_document(pdf_path, {"clean_text": False})

        # Both should have content
        assert doc_cleaned.content is not None
        assert doc_raw.content is not None

        # They might differ (cleaned version should be normalized)
        # Note: This test might need adjustment based on actual PDF content


class TestPDFParsingChapterDetection:
    """Test chapter detection integration."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to PDF with headings."""
        headings_pdf = FIXTURES_DIR / "with_headings.pdf"
        if not headings_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return headings_pdf

    def test_chapter_detection_levels(self, pdf_path: Path) -> None:
        """Test chapter detection with different heading levels."""
        # Only level 1 headings
        doc1 = parse_document(
            pdf_path, {"min_chapter_level": 1, "max_chapter_level": 1}
        )

        # Levels 1 and 2
        doc2 = parse_document(
            pdf_path, {"min_chapter_level": 1, "max_chapter_level": 2}
        )

        # doc2 should have more or equal chapters (includes level 2)
        assert len(doc2.chapters) >= len(doc1.chapters)


class TestPDFParsingReadingTime:
    """Test reading time estimation."""

    @pytest.fixture
    def pdf_path(self) -> Path:
        """Return path to test PDF."""
        simple_pdf = FIXTURES_DIR / "simple.pdf"
        if not simple_pdf.exists():
            pytest.skip("Test PDF fixture not available")
        return simple_pdf

    def test_reading_time_calculated(self, pdf_path: Path) -> None:
        """Test that reading time is estimated."""
        doc = parse_document(pdf_path)

        assert doc.estimated_reading_time > 0
        # Reading time should be proportional to word count
        # (approximately word_count / 250)
        expected_time = max(1, doc.word_count // 250)
        assert abs(doc.estimated_reading_time - expected_time) <= 1
