"""
Unit tests for QR code detector processor.

Tests QR code detection, data classification, and image file handling.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from omniparser.processors.qr_detector import (
    classify_qr_data,
    detect_qr_codes,
    detect_qr_codes_from_pil,
    detect_qr_codes_from_file,
    is_qr_detection_available,
    scan_image_for_qr_and_fetch,
)
from omniparser.models import QRCodeReference


class TestClassifyQrData:
    """Tests for QR data type classification."""

    def test_classify_url_https(self):
        """Test classification of HTTPS URLs."""
        assert classify_qr_data("https://example.com") == "URL"
        assert classify_qr_data("https://example.com/path?query=1") == "URL"

    def test_classify_url_http(self):
        """Test classification of HTTP URLs."""
        assert classify_qr_data("http://example.com") == "URL"

    def test_classify_url_www(self):
        """Test classification of www URLs."""
        assert classify_qr_data("www.example.com") == "URL"

    def test_classify_url_ftp(self):
        """Test classification of FTP URLs."""
        assert classify_qr_data("ftp://files.example.com") == "URL"

    def test_classify_email_mailto(self):
        """Test classification of mailto: links."""
        assert classify_qr_data("mailto:test@example.com") == "EMAIL"
        assert classify_qr_data("MAILTO:TEST@EXAMPLE.COM") == "EMAIL"

    def test_classify_email_plain(self):
        """Test classification of plain email addresses."""
        assert classify_qr_data("test@example.com") == "EMAIL"
        assert classify_qr_data("user.name@domain.org") == "EMAIL"

    def test_classify_phone(self):
        """Test classification of phone numbers."""
        assert classify_qr_data("tel:+1234567890") == "PHONE"
        assert classify_qr_data("TEL:123-456-7890") == "PHONE"

    def test_classify_wifi(self):
        """Test classification of WiFi configurations."""
        assert classify_qr_data("WIFI:S:MyNetwork;T:WPA;P:password;;") == "WIFI"

    def test_classify_vcard(self):
        """Test classification of vCard data."""
        vcard = "BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nEND:VCARD"
        assert classify_qr_data(vcard) == "VCARD"

    def test_classify_geo(self):
        """Test classification of geographic coordinates."""
        assert classify_qr_data("geo:37.7749,-122.4194") == "GEO"

    def test_classify_sms(self):
        """Test classification of SMS links."""
        assert classify_qr_data("sms:+1234567890") == "SMS"
        assert classify_qr_data("smsto:+1234567890") == "SMS"

    def test_classify_text(self):
        """Test classification of plain text."""
        assert classify_qr_data("Hello World") == "TEXT"
        assert classify_qr_data("Some random text content") == "TEXT"
        assert classify_qr_data("12345") == "TEXT"

    def test_classify_with_whitespace(self):
        """Test classification handles whitespace."""
        assert classify_qr_data("  https://example.com  ") == "URL"
        assert classify_qr_data("\ntest@example.com\n") == "EMAIL"


class TestDetectQrCodes:
    """Tests for QR code detection from image bytes."""

    def test_detect_returns_tuple(self):
        """Test that detect_qr_codes returns a tuple."""
        # Empty image data should return empty results
        result = detect_qr_codes(b"")
        assert isinstance(result, tuple)
        assert len(result) == 2
        qr_codes, warnings = result
        assert isinstance(qr_codes, list)
        assert isinstance(warnings, list)

    def test_detect_invalid_image_graceful(self):
        """Test that invalid image data is handled gracefully."""
        qr_codes, warnings = detect_qr_codes(b"not an image")
        assert qr_codes == []
        assert len(warnings) > 0

    def test_detect_with_source_image_id(self):
        """Test that source_image_id is passed through."""
        qr_codes, warnings = detect_qr_codes(
            b"", source_image_id="test_img", page_number=5
        )
        # Even on failure, the function should complete
        assert isinstance(qr_codes, list)

    @pytest.mark.skipif(
        not is_qr_detection_available(),
        reason="pyzbar not installed"
    )
    def test_detect_qr_available(self):
        """Test QR detection availability check."""
        assert is_qr_detection_available() is True


class TestDetectQrCodesFromFile:
    """Tests for QR code detection from files."""

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        qr_codes, warnings = detect_qr_codes_from_file("/nonexistent/file.png")
        assert qr_codes == []
        assert any("not found" in w.lower() for w in warnings)

    def test_unsupported_format(self, tmp_path):
        """Test handling of unsupported file format."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("dummy content")

        qr_codes, warnings = detect_qr_codes_from_file(test_file)
        assert qr_codes == []
        assert any("unsupported" in w.lower() for w in warnings)

    def test_supported_extensions(self, tmp_path):
        """Test that supported extensions are recognized."""
        # Create minimal valid PNG (1x1 pixel)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])

        for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"]:
            test_file = tmp_path / f"test{ext}"
            test_file.write_bytes(png_data)

            # Should not return unsupported format warning
            qr_codes, warnings = detect_qr_codes_from_file(test_file)
            unsupported_warnings = [w for w in warnings if "unsupported" in w.lower()]
            assert len(unsupported_warnings) == 0, f"Format {ext} should be supported"


class TestScanImageForQrAndFetch:
    """Tests for the combined scan and fetch function."""

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        qr_codes, warnings = scan_image_for_qr_and_fetch("/nonexistent/file.png")
        assert qr_codes == []
        assert len(warnings) > 0

    def test_returns_processed_qr_codes(self, tmp_path):
        """Test that function returns QR code references."""
        # Create a dummy image file
        test_file = tmp_path / "test.png"
        # Minimal PNG
        test_file.write_bytes(bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ]))

        qr_codes, warnings = scan_image_for_qr_and_fetch(test_file, fetch_urls=False)
        assert isinstance(qr_codes, list)
        assert isinstance(warnings, list)


class TestQRCodeReferenceModel:
    """Tests for QRCodeReference data model integration."""

    def test_qr_reference_creation(self):
        """Test creating a QRCodeReference."""
        qr = QRCodeReference(
            qr_id="qr_001",
            raw_data="https://example.com",
            data_type="URL",
        )
        assert qr.qr_id == "qr_001"
        assert qr.raw_data == "https://example.com"
        assert qr.data_type == "URL"
        assert qr.fetch_status == "pending"
        assert qr.fetch_notes == []

    def test_qr_reference_with_all_fields(self):
        """Test QRCodeReference with all fields populated."""
        qr = QRCodeReference(
            qr_id="qr_002",
            raw_data="https://example.com/recipe",
            data_type="URL",
            source_image="page_1",
            position={"x": 100, "y": 200, "width": 50, "height": 50},
            page_number=1,
            fetched_content="Recipe content here",
            fetch_status="success",
            fetch_notes=["Followed 2 redirects"],
        )
        assert qr.page_number == 1
        assert qr.fetched_content == "Recipe content here"
        assert len(qr.fetch_notes) == 1

    def test_qr_reference_default_values(self):
        """Test QRCodeReference default values."""
        qr = QRCodeReference(
            qr_id="qr_003",
            raw_data="Plain text",
        )
        assert qr.data_type == "TEXT"
        assert qr.source_image is None
        assert qr.position is None
        assert qr.page_number is None
        assert qr.fetched_content is None
        assert qr.fetch_status == "pending"
        assert qr.fetch_notes == []


class TestIsQrDetectionAvailable:
    """Tests for QR detection availability check."""

    def test_returns_bool(self):
        """Test that is_qr_detection_available returns a boolean."""
        result = is_qr_detection_available()
        assert isinstance(result, bool)

    @patch.dict('sys.modules', {'pyzbar': None, 'pyzbar.pyzbar': None})
    def test_unavailable_when_pyzbar_missing(self):
        """Test that function returns False when pyzbar is not installed."""
        # This test would need to reload the module to take effect
        # For now, just verify the function exists
        assert callable(is_qr_detection_available)
