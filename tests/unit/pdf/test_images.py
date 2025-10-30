"""
Unit tests for PDF image extraction module.

Tests the extract_pdf_images and extract_page_images functions for extracting
images from PDF documents, including validation, filtering, and error handling.
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from omniparser.models import ImageReference
from omniparser.parsers.pdf.images import extract_page_images, extract_pdf_images


class TestExtractPDFImages:
    """Test extract_pdf_images function."""

    def test_extract_pdf_images_with_images(self) -> None:
        """Test extraction from PDF with images."""
        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (800, 600))
        img.save(img_bytes, format="PNG")
        valid_image_data = img_bytes.getvalue()

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page with images
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]
        mock_doc.__getitem__.return_value = mock_page

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": valid_image_data,
            "ext": "png",
        }

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            images = extract_pdf_images(mock_doc, output_dir)

            assert len(images) == 1
            assert images[0].image_id == "img_0001"
            assert images[0].format == "png"
            assert images[0].size == (800, 600)
            assert "Image on page 1" in images[0].alt_text

    def test_extract_pdf_images_no_images(self) -> None:
        """Test extraction from PDF without images."""
        # Mock document with no images
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_images.return_value = []
        mock_doc.__getitem__.return_value = mock_page

        images = extract_pdf_images(mock_doc)

        assert images == []

    def test_extract_pdf_images_no_output_dir(self) -> None:
        """Test extraction without specifying output directory (uses temp)."""
        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (400, 300))
        img.save(img_bytes, format="JPEG")
        valid_image_data = img_bytes.getvalue()

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page with images
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 400, 300, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]
        mock_doc.__getitem__.return_value = mock_page

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": valid_image_data,
            "ext": "jpg",
        }

        # Call without output_dir (should use temp)
        images = extract_pdf_images(mock_doc)

        assert len(images) == 1
        assert images[0].format == "jpeg"  # PIL detects JPEG format
        # Note: Can't check file existence as temp dir is cleaned up
        assert (
            "/tmp" in images[0].file_path.lower()
            or "temp" in images[0].file_path.lower()
        )

    def test_extract_pdf_images_small_images_filtered(self) -> None:
        """Test that small images are filtered out by MIN_IMAGE_SIZE."""
        # Create small image (50x50, below MIN_IMAGE_SIZE=100)
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (50, 50))
        img.save(img_bytes, format="PNG")
        small_image_data = img_bytes.getvalue()

        # Mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock page with small image
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 50, 50, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]
        mock_doc.__getitem__.return_value = mock_page

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": small_image_data,
            "ext": "png",
        }

        images = extract_pdf_images(mock_doc)

        # Small image should be filtered out
        assert len(images) == 0

    def test_extract_pdf_images_max_images_limit(self) -> None:
        """Test that max_images parameter limits extraction."""
        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (800, 600))
        img.save(img_bytes, format="PNG")
        valid_image_data = img_bytes.getvalue()

        # Mock document with 2 pages, each with an image
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Mock pages with images
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]
        mock_doc.__getitem__.return_value = mock_page

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": valid_image_data,
            "ext": "png",
        }

        # Limit to 1 image
        images = extract_pdf_images(mock_doc, max_images=1)

        # Should only extract 1 image despite 2 being available
        assert len(images) == 1

    def test_extract_pdf_images_multiple_pages(self) -> None:
        """Test extraction across multiple pages."""
        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (800, 600))
        img.save(img_bytes, format="PNG")
        valid_image_data = img_bytes.getvalue()

        # Mock document with 2 pages
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Mock pages with images
        mock_page1 = MagicMock()
        mock_page1.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]

        mock_page2 = MagicMock()
        mock_page2.get_images.return_value = [
            (2, 0, 600, 400, 8, "DeviceRGB", "", "Im2", "DCTDecode")
        ]

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": valid_image_data,
            "ext": "png",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            images = extract_pdf_images(mock_doc, Path(tmpdir))

            assert len(images) == 2
            assert images[0].image_id == "img_0001"
            assert images[1].image_id == "img_0002"


class TestExtractPageImages:
    """Test extract_page_images function."""

    def test_extract_page_images_success(self) -> None:
        """Test successful extraction from a single page."""
        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (800, 600))
        img.save(img_bytes, format="PNG")
        valid_image_data = img_bytes.getvalue()

        # Mock page
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.extract_image.return_value = {
            "image": valid_image_data,
            "ext": "png",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            images, new_counter = extract_page_images(
                mock_page, 0, output_dir, 0, mock_doc
            )

            assert len(images) == 1
            assert new_counter == 1
            assert images[0].image_id == "img_0001"
            assert images[0].position == 0  # page_num * 1000 + img_index

    def test_extract_page_images_invalid_image(self) -> None:
        """Test that invalid images are skipped."""
        # Mock page with image
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]

        # Mock document returning invalid image data
        mock_doc = MagicMock()
        mock_doc.extract_image.return_value = {
            "image": b"invalid_image_data",
            "ext": "png",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            images, new_counter = extract_page_images(
                mock_page, 0, output_dir, 0, mock_doc
            )

            # Invalid image should be skipped
            assert len(images) == 0
            assert new_counter == 0  # Counter not incremented

    def test_extract_page_images_save_error(self) -> None:
        """Test handling of save errors."""
        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (800, 600))
        img.save(img_bytes, format="PNG")
        valid_image_data = img_bytes.getvalue()

        # Mock page
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.extract_image.return_value = {
            "image": valid_image_data,
            "ext": "png",
        }

        # Use invalid output directory (will cause save to fail)
        invalid_dir = Path("/nonexistent/invalid/path")

        with patch("omniparser.parsers.pdf.images.logger") as mock_logger:
            images, new_counter = extract_page_images(
                mock_page, 0, invalid_dir, 0, mock_doc
            )

            # Error should be logged and image skipped
            assert len(images) == 0
            mock_logger.warning.assert_called()

    def test_extract_page_images_increments_counter(self) -> None:
        """Test that counter is properly incremented."""
        # Create valid image data
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (800, 600))
        img.save(img_bytes, format="PNG")
        valid_image_data = img_bytes.getvalue()

        # Mock page with 2 images
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode"),
            (2, 0, 600, 400, 8, "DeviceRGB", "", "Im2", "DCTDecode"),
        ]

        # Mock document
        mock_doc = MagicMock()
        mock_doc.extract_image.return_value = {
            "image": valid_image_data,
            "ext": "png",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            images, new_counter = extract_page_images(
                mock_page, 0, output_dir, 5, mock_doc
            )

            assert len(images) == 2
            assert new_counter == 7  # Started at 5, added 2
            assert images[0].image_id == "img_0006"
            assert images[1].image_id == "img_0007"

    def test_extract_page_images_no_images(self) -> None:
        """Test extraction from page with no images."""
        # Mock page with no images
        mock_page = MagicMock()
        mock_page.get_images.return_value = []

        mock_doc = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            images, new_counter = extract_page_images(
                mock_page, 0, output_dir, 0, mock_doc
            )

            assert images == []
            assert new_counter == 0

    def test_extract_page_images_empty_extraction(self) -> None:
        """Test handling of empty image extraction result."""
        # Mock page with image
        mock_page = MagicMock()
        mock_page.get_images.return_value = [
            (1, 0, 800, 600, 8, "DeviceRGB", "", "Im1", "DCTDecode")
        ]

        # Mock document returning None
        mock_doc = MagicMock()
        mock_doc.extract_image.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            images, new_counter = extract_page_images(
                mock_page, 0, output_dir, 0, mock_doc
            )

            # Should handle None gracefully
            assert len(images) == 0
            assert new_counter == 0
