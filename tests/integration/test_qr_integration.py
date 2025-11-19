"""
Integration tests for QR code detection and content fetching.

These tests verify the complete QR code processing pipeline including
detection, URL fetching, and document merging.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO

from PIL import Image

from omniparser.processors.qr_detector import (
    detect_qr_codes,
    detect_qr_codes_from_pil,
    detect_qr_codes_from_file,
    scan_image_for_qr_and_fetch,
    is_qr_detection_available,
)
from omniparser.processors.qr_content_merger import (
    process_qr_codes,
    merge_qr_content_to_document,
    format_qr_section,
    generate_qr_summary,
)
from omniparser.utils.qr_url_fetcher import (
    fetch_url_content,
    FetchResult,
)
from omniparser.models import (
    Document,
    Metadata,
    ProcessingInfo,
    QRCodeReference,
)
from datetime import datetime


# Skip all tests if pyzbar is not available
pytestmark = pytest.mark.skipif(
    not is_qr_detection_available(),
    reason="pyzbar not installed - QR detection unavailable"
)


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        document_id="test_doc",
        content="# Test Document\n\nThis is test content.",
        chapters=[],
        images=[],
        metadata=Metadata(
            title="Test Document",
            original_format="pdf",
        ),
        processing_info=ProcessingInfo(
            parser_used="TestParser",
            parser_version="1.0.0",
            processing_time=0.5,
            timestamp=datetime.now(),
        ),
        word_count=6,
        estimated_reading_time=1,
    )


@pytest.fixture
def sample_qr_codes():
    """Create sample QR code references for testing."""
    return [
        QRCodeReference(
            qr_id="qr_001",
            raw_data="https://example.com/recipe",
            data_type="URL",
            page_number=1,
            fetch_status="pending",
        ),
        QRCodeReference(
            qr_id="qr_002",
            raw_data="Plain text content",
            data_type="TEXT",
            page_number=2,
            fetch_status="skipped",
        ),
    ]


class TestQrDetectionIntegration:
    """Integration tests for QR code detection."""

    def test_detect_from_pil_image_no_qr(self):
        """Test detection on image without QR codes."""
        # Create a blank image
        img = Image.new("RGB", (100, 100), color="white")

        qr_codes, warnings = detect_qr_codes_from_pil(img)
        assert qr_codes == []
        # No errors expected for clean image
        assert not any("error" in w.lower() for w in warnings)

    def test_detect_from_bytes_no_qr(self):
        """Test detection from image bytes without QR codes."""
        # Create a minimal blank image
        img = Image.new("RGB", (100, 100), color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_data = buffer.getvalue()

        qr_codes, warnings = detect_qr_codes(image_data)
        assert qr_codes == []

    def test_detection_preserves_source_info(self):
        """Test that source image info is preserved."""
        img = Image.new("RGB", (100, 100), color="white")

        qr_codes, warnings = detect_qr_codes_from_pil(
            img,
            source_image_id="test_image.png",
            page_number=5,
            qr_id_prefix="test",
        )

        # Even with no QR codes, function should complete successfully
        assert isinstance(qr_codes, list)
        assert isinstance(warnings, list)


class TestQrContentMergerIntegration:
    """Integration tests for QR content merging."""

    def test_process_qr_codes_with_text(self, sample_qr_codes):
        """Test processing QR codes with text data type."""
        processed = process_qr_codes(sample_qr_codes, fetch_urls=False)

        # Text QR should be marked as skipped
        text_qr = next(qr for qr in processed if qr.data_type == "TEXT")
        assert text_qr.fetch_status == "skipped"

    @patch('omniparser.processors.qr_content_merger.fetch_url_content')
    def test_process_qr_codes_fetches_urls(self, mock_fetch, sample_qr_codes):
        """Test that URLs are fetched when enabled."""
        mock_fetch.return_value = FetchResult(
            success=True,
            content="Fetched recipe content",
            status="success",
            notes=["Followed 1 redirect"],
        )

        processed = process_qr_codes(sample_qr_codes, fetch_urls=True)

        # URL QR should have content
        url_qr = next(qr for qr in processed if qr.data_type == "URL")
        assert url_qr.fetched_content == "Fetched recipe content"
        assert url_qr.fetch_status == "success"

    def test_merge_qr_content_to_document(self, sample_document):
        """Test merging QR content into document."""
        # Save original word count before merge (since merge modifies in place)
        original_word_count = sample_document.word_count

        qr_codes = [
            QRCodeReference(
                qr_id="qr_001",
                raw_data="https://example.com",
                data_type="URL",
                fetched_content="Recipe: Mix ingredients together.",
                fetch_status="success",
                fetch_notes=["Success"],
            )
        ]

        updated_doc = merge_qr_content_to_document(
            sample_document, qr_codes, add_sections=True
        )

        # Check metadata
        assert updated_doc.metadata.custom_fields is not None
        assert "qr_codes" in updated_doc.metadata.custom_fields
        assert updated_doc.metadata.custom_fields["qr_code_count"] == 1

        # Check content was added
        assert "Recipe: Mix ingredients together" in updated_doc.content

        # Check word count was updated
        assert updated_doc.word_count > original_word_count

        # Check qr_codes attribute is set
        assert len(updated_doc.qr_codes) == 1
        assert updated_doc.qr_codes[0].qr_id == "qr_001"

    def test_merge_without_sections(self, sample_document):
        """Test merging QR content without adding sections."""
        qr_codes = [
            QRCodeReference(
                qr_id="qr_001",
                raw_data="https://example.com",
                data_type="URL",
                fetched_content="Content here",
                fetch_status="success",
            )
        ]

        original_content = sample_document.content
        updated_doc = merge_qr_content_to_document(
            sample_document, qr_codes, add_sections=False
        )

        # Content should not change
        assert updated_doc.content == original_content
        # But metadata should be updated
        assert "qr_codes" in updated_doc.metadata.custom_fields

    def test_format_qr_section(self):
        """Test formatting QR content as a section."""
        qr = QRCodeReference(
            qr_id="qr_001",
            raw_data="https://example.com/recipe",
            data_type="URL",
            page_number=2,
            fetched_content="Recipe content here",
            fetch_status="success",
            fetch_notes=["Followed 2 redirects"],
        )

        section = format_qr_section(qr)

        assert "## Content from QR Code qr_001" in section
        assert "(Page 2)" in section
        assert "Recipe content here" in section
        assert "https://example.com/recipe" in section
        assert "success" in section

    def test_generate_qr_summary(self, sample_qr_codes):
        """Test generating QR code summary."""
        summary = generate_qr_summary(sample_qr_codes)

        assert "2" in summary  # Total count
        assert "URL" in summary
        assert "TEXT" in summary

    def test_generate_qr_summary_empty(self):
        """Test generating summary with no QR codes."""
        summary = generate_qr_summary([])
        assert "no" in summary.lower()


class TestUrlFetchingIntegration:
    """Integration tests for URL fetching."""

    @patch('omniparser.utils.qr_url_fetcher._fetch_single_url')
    def test_fetch_url_content_success(self, mock_fetch):
        """Test successful URL content fetching."""
        mock_fetch.return_value = FetchResult(
            success=True,
            content="Page content",
            status="success",
            final_url="https://example.com",
        )

        result = fetch_url_content("https://example.com")

        assert result.success is True
        assert result.content == "Page content"

    @patch('omniparser.utils.qr_url_fetcher._fetch_single_url')
    @patch('omniparser.utils.qr_url_fetcher.fetch_from_wayback')
    def test_fetch_url_content_with_wayback_fallback(self, mock_wayback, mock_fetch):
        """Test URL fetching with Wayback Machine fallback."""
        mock_fetch.return_value = FetchResult(
            success=False,
            notes=["Original URL failed"],
        )
        mock_wayback.return_value = FetchResult(
            success=True,
            content="Archived content",
            status="success",
            source="wayback",
        )

        result = fetch_url_content(
            "https://example.com",
            try_variations=False,
            try_wayback=True,
        )

        assert result.success is True
        assert result.source == "wayback"
        assert "Archived content" in result.content


class TestEndToEndPipeline:
    """End-to-end integration tests for complete QR pipeline."""

    @patch('omniparser.processors.qr_content_merger.fetch_url_content')
    def test_complete_qr_pipeline(self, mock_fetch, sample_document):
        """Test complete QR code processing pipeline."""
        # Mock URL fetch
        mock_fetch.return_value = FetchResult(
            success=True,
            content="This is the recipe:\n1. Step one\n2. Step two",
            status="success",
            notes=["Followed 1 redirect"],
        )

        # Create QR codes
        qr_codes = [
            QRCodeReference(
                qr_id="qr_001",
                raw_data="https://example.com/recipe",
                data_type="URL",
                page_number=1,
            ),
            QRCodeReference(
                qr_id="qr_002",
                raw_data="Note: See instructions",
                data_type="TEXT",
                page_number=2,
            ),
        ]

        # Process QR codes
        processed = process_qr_codes(qr_codes, fetch_urls=True)

        # Merge into document
        final_doc = merge_qr_content_to_document(
            sample_document, processed, add_sections=True
        )

        # Verify results
        assert final_doc.metadata.custom_fields["qr_code_count"] == 2
        assert "recipe" in final_doc.content.lower()
        assert "Step one" in final_doc.content

        # Check QR summaries in metadata
        qr_summaries = final_doc.metadata.custom_fields["qr_codes"]
        assert len(qr_summaries) == 2

        # URL QR should have content
        url_summary = next(s for s in qr_summaries if s["data_type"] == "URL")
        assert url_summary["has_content"] is True

        # TEXT QR should not
        text_summary = next(s for s in qr_summaries if s["data_type"] == "TEXT")
        assert text_summary["has_content"] is False

    def test_graceful_failure_handling(self, sample_document):
        """Test that failures are handled gracefully."""
        qr_codes = [
            QRCodeReference(
                qr_id="qr_001",
                raw_data="https://unreachable.invalid",
                data_type="URL",
                fetch_status="failed",
                fetch_notes=["Connection refused"],
            ),
        ]

        # Should not raise exception
        final_doc = merge_qr_content_to_document(
            sample_document, qr_codes, add_sections=True
        )

        # Document should still be valid
        assert final_doc.document_id == "test_doc"
        assert "qr_codes" in final_doc.metadata.custom_fields

        # Failed QR should be recorded
        qr_summary = final_doc.metadata.custom_fields["qr_codes"][0]
        assert qr_summary["fetch_status"] == "failed"


class TestFileBasedDetection:
    """Integration tests for file-based QR detection."""

    def test_detect_from_nonexistent_file(self):
        """Test handling of non-existent files."""
        qr_codes, warnings = detect_qr_codes_from_file("/nonexistent/file.png")

        assert qr_codes == []
        assert len(warnings) > 0
        assert any("not found" in w.lower() for w in warnings)

    def test_detect_from_empty_image(self, tmp_path):
        """Test detection from empty/minimal image file."""
        # Create a minimal blank image
        img = Image.new("RGB", (100, 100), color="white")
        img_path = tmp_path / "blank.png"
        img.save(img_path)

        qr_codes, warnings = detect_qr_codes_from_file(img_path)

        assert qr_codes == []
        # No error warnings for valid image
        assert not any("error" in w.lower() for w in warnings)

    def test_scan_and_fetch_convenience_function(self, tmp_path):
        """Test the combined scan and fetch function."""
        # Create a minimal image
        img = Image.new("RGB", (100, 100), color="white")
        img_path = tmp_path / "test.png"
        img.save(img_path)

        qr_codes, warnings = scan_image_for_qr_and_fetch(
            img_path, fetch_urls=False
        )

        assert isinstance(qr_codes, list)
        assert isinstance(warnings, list)
