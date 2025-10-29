"""
Unit tests for image extraction utilities.

Tests the shared image_extractor module functions:
- save_image
- get_image_dimensions
- validate_image_data
- extract_format_from_content_type
"""

import io
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from omniparser.processors.image_extractor import (
    extract_format_from_content_type,
    get_image_dimensions,
    save_image,
    validate_image_data,
)


# Helper function to create test images
def create_test_image(width: int, height: int, format: str = "PNG") -> bytes:
    """Create a test image in memory and return as bytes."""
    img = Image.new("RGB", (width, height), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    return img_bytes.getvalue()


class TestSaveImage:
    """Test suite for save_image function."""

    def test_save_image_basic(self):
        """Test basic image saving with auto-numbering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            image_data = create_test_image(100, 100, "PNG")

            # Save image
            path, fmt = save_image(image_data, output_dir, "test", "png", counter=1)

            # Verify file exists
            assert path.exists()
            assert path.name == "test_001.png"
            assert fmt == "png"

            # Verify file content
            with open(path, "rb") as f:
                saved_data = f.read()
            assert saved_data == image_data

    def test_save_image_auto_detect_format(self):
        """Test auto-detection of image format when extension not provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            image_data = create_test_image(100, 100, "JPEG")

            # Save without providing extension
            path, fmt = save_image(image_data, output_dir, "test", counter=1)

            # Format should be auto-detected
            assert path.exists()
            assert fmt == "jpeg"
            assert path.suffix in [".jpeg", ".jpg"]

    def test_save_image_preserve_subdirs(self):
        """Test preserving subdirectory structure from original path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            image_data = create_test_image(100, 100, "PNG")

            # Save with subdirectory preservation
            path, fmt = save_image(
                image_data,
                output_dir,
                preserve_subdirs=True,
                original_path="images/subfolder/cover.png",
            )

            # Verify subdirectory structure is preserved
            assert path.exists()
            assert path.name == "cover.png"
            assert "images" in path.parts
            assert "subfolder" in path.parts

    def test_save_image_creates_output_dir(self):
        """Test that save_image creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use non-existent subdirectory
            output_dir = Path(temp_dir) / "new_dir" / "subdir"
            image_data = create_test_image(100, 100, "PNG")

            # Should create directory automatically
            path, fmt = save_image(image_data, output_dir, counter=1)

            assert output_dir.exists()
            assert path.exists()

    def test_save_image_empty_data_raises_error(self):
        """Test that empty image data raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with pytest.raises(ValueError, match="Image data is empty"):
                save_image(b"", output_dir)

    def test_save_image_counter_formatting(self):
        """Test that counter is formatted with zero-padding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            image_data = create_test_image(100, 100, "PNG")

            # Test various counter values
            path1, _ = save_image(image_data, output_dir, "img", "png", counter=1)
            path2, _ = save_image(image_data, output_dir, "img", "png", counter=42)
            path3, _ = save_image(image_data, output_dir, "img", "png", counter=999)

            assert path1.name == "img_001.png"
            assert path2.name == "img_042.png"
            assert path3.name == "img_999.png"

    def test_save_image_different_formats(self):
        """Test saving images in different formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            formats = [("PNG", "png"), ("JPEG", "jpeg"), ("GIF", "gif")]

            for pil_format, expected_ext in formats:
                image_data = create_test_image(100, 100, pil_format)
                path, fmt = save_image(
                    image_data, output_dir, "test", expected_ext, counter=1
                )

                assert path.exists()
                assert path.suffix == f".{expected_ext}"


class TestGetImageDimensions:
    """Test suite for get_image_dimensions function."""

    def test_get_dimensions_png(self):
        """Test extracting dimensions from PNG image."""
        image_data = create_test_image(1920, 1080, "PNG")
        width, height, fmt = get_image_dimensions(image_data)

        assert width == 1920
        assert height == 1080
        assert fmt == "png"

    def test_get_dimensions_jpeg(self):
        """Test extracting dimensions from JPEG image."""
        image_data = create_test_image(800, 600, "JPEG")
        width, height, fmt = get_image_dimensions(image_data)

        assert width == 800
        assert height == 600
        assert fmt == "jpeg"

    def test_get_dimensions_various_sizes(self):
        """Test extracting dimensions from images of various sizes."""
        test_cases = [(100, 100), (1, 1), (5000, 3000), (320, 240)]

        for w, h in test_cases:
            image_data = create_test_image(w, h, "PNG")
            width, height, fmt = get_image_dimensions(image_data)

            assert width == w
            assert height == h
            assert fmt == "png"

    def test_get_dimensions_invalid_data(self):
        """Test that invalid data returns None dimensions."""
        invalid_data = b"not an image"
        width, height, fmt = get_image_dimensions(invalid_data)

        assert width is None
        assert height is None
        assert fmt == "unknown"

    def test_get_dimensions_empty_data(self):
        """Test that empty data returns None dimensions."""
        width, height, fmt = get_image_dimensions(b"")

        assert width is None
        assert height is None
        assert fmt == "unknown"


class TestValidateImageData:
    """Test suite for validate_image_data function."""

    def test_validate_valid_image(self):
        """Test validation of valid image data."""
        image_data = create_test_image(200, 200, "PNG")
        is_valid, error = validate_image_data(image_data)

        assert is_valid is True
        assert error is None

    def test_validate_empty_data(self):
        """Test validation rejects empty data."""
        is_valid, error = validate_image_data(b"")

        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_invalid_data(self):
        """Test validation rejects invalid image data."""
        invalid_data = b"This is not an image"
        is_valid, error = validate_image_data(invalid_data)

        assert is_valid is False
        assert "invalid" in error.lower()

    def test_validate_image_too_small(self):
        """Test validation rejects images below minimum size."""
        # Create 50x50 image (below default 100px minimum)
        image_data = create_test_image(50, 50, "PNG")
        is_valid, error = validate_image_data(image_data, min_size=100)

        assert is_valid is False
        assert "too small" in error.lower()
        assert "50x50" in error

    def test_validate_image_meets_minimum(self):
        """Test validation accepts images at exact minimum size."""
        # Create 100x100 image (exactly at minimum)
        image_data = create_test_image(100, 100, "PNG")
        is_valid, error = validate_image_data(image_data, min_size=100)

        assert is_valid is True
        assert error is None

    def test_validate_custom_min_size(self):
        """Test validation with custom minimum size."""
        image_data = create_test_image(150, 150, "PNG")

        # Should pass with min_size=100
        is_valid, _ = validate_image_data(image_data, min_size=100)
        assert is_valid is True

        # Should fail with min_size=200
        is_valid, error = validate_image_data(image_data, min_size=200)
        assert is_valid is False
        assert "too small" in error.lower()

    def test_validate_image_too_large(self):
        """Test validation rejects images exceeding max file size."""
        # Create a reasonably sized image
        image_data = create_test_image(1000, 1000, "PNG")

        # Set unreasonably small max_size to trigger validation
        is_valid, error = validate_image_data(image_data, max_size=1000)  # 1KB

        assert is_valid is False
        assert "too large" in error.lower()

    def test_validate_different_formats(self):
        """Test validation works with different image formats."""
        formats = ["PNG", "JPEG", "GIF", "BMP"]

        for fmt in formats:
            image_data = create_test_image(200, 200, fmt)
            is_valid, error = validate_image_data(image_data)

            assert is_valid is True, f"Validation failed for {fmt}: {error}"
            assert error is None

    def test_validate_rectangular_images(self):
        """Test validation with non-square images."""
        # Wide image
        wide_image = create_test_image(500, 100, "PNG")
        is_valid, _ = validate_image_data(wide_image, min_size=100)
        assert is_valid is True

        # Tall image
        tall_image = create_test_image(100, 500, "PNG")
        is_valid, _ = validate_image_data(tall_image, min_size=100)
        assert is_valid is True

        # Both dimensions below minimum
        small_image = create_test_image(50, 80, "PNG")
        is_valid, error = validate_image_data(small_image, min_size=100)
        assert is_valid is False
        assert "too small" in error.lower()


class TestExtractFormatFromContentType:
    """Test suite for extract_format_from_content_type function."""

    def test_extract_jpeg_formats(self):
        """Test extraction of JPEG format variants."""
        assert extract_format_from_content_type("image/jpeg") == "jpg"
        assert extract_format_from_content_type("image/jpg") == "jpg"

    def test_extract_png_format(self):
        """Test extraction of PNG format."""
        assert extract_format_from_content_type("image/png") == "png"

    def test_extract_gif_format(self):
        """Test extraction of GIF format."""
        assert extract_format_from_content_type("image/gif") == "gif"

    def test_extract_bmp_format(self):
        """Test extraction of BMP format."""
        assert extract_format_from_content_type("image/bmp") == "bmp"

    def test_extract_webp_format(self):
        """Test extraction of WebP format."""
        assert extract_format_from_content_type("image/webp") == "webp"

    def test_extract_tiff_formats(self):
        """Test extraction of TIFF format variants."""
        assert extract_format_from_content_type("image/tiff") == "tiff"
        assert extract_format_from_content_type("image/tif") == "tiff"

    def test_extract_unknown_format(self):
        """Test that unknown formats default to PNG."""
        assert extract_format_from_content_type("image/unknown") == "png"
        assert extract_format_from_content_type("application/octet-stream") == "png"
        assert extract_format_from_content_type("") == "png"

    def test_extract_case_insensitive(self):
        """Test that format extraction is case-insensitive."""
        assert extract_format_from_content_type("IMAGE/JPEG") == "jpg"
        assert extract_format_from_content_type("Image/Png") == "png"
        assert extract_format_from_content_type("IMAGE/GIF") == "gif"


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_workflow(self):
        """Test complete workflow: validate, save, verify."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Create test image
            image_data = create_test_image(500, 300, "PNG")

            # Validate
            is_valid, error = validate_image_data(image_data)
            assert is_valid is True

            # Get dimensions
            width, height, fmt = get_image_dimensions(image_data)
            assert width == 500
            assert height == 300

            # Save
            path, saved_fmt = save_image(image_data, output_dir, "test", fmt, counter=1)
            assert path.exists()

            # Verify saved file
            with open(path, "rb") as f:
                saved_data = f.read()

            # Validate saved data
            is_valid, error = validate_image_data(saved_data)
            assert is_valid is True

            # Check dimensions of saved file
            width2, height2, fmt2 = get_image_dimensions(saved_data)
            assert width2 == 500
            assert height2 == 300

    def test_batch_save_with_counters(self):
        """Test saving multiple images with sequential counters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Save 10 images
            for i in range(1, 11):
                image_data = create_test_image(100, 100, "PNG")
                path, _ = save_image(image_data, output_dir, "img", "png", counter=i)

                expected_name = f"img_{i:03d}.png"
                assert path.name == expected_name
                assert path.exists()

            # Verify all files exist
            saved_files = list(output_dir.glob("img_*.png"))
            assert len(saved_files) == 10
