"""
Unit tests for photo parser module.

Tests the photo parser functionality:
- EXIF metadata extraction
- Photo parsing (without AI)
- Format support detection
- Markdown output generation
- Color palette extraction
- Integration with main parser
"""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from omniparser.parser import parse_document, get_supported_formats, is_format_supported
from omniparser.parsers.photo import (
    parse_photo,
    supports_photo_format,
    extract_photo_metadata,
    PhotoMetadata,
    CameraInfo,
    ExposureInfo,
    GPSInfo,
)
from omniparser.exceptions import ValidationError


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "images"


class TestSupportsPhotoFormat:
    """Test suite for supports_photo_format function."""

    def test_supports_jpeg(self):
        """Test JPEG format support."""
        assert supports_photo_format("photo.jpg") is True
        assert supports_photo_format("photo.jpeg") is True
        assert supports_photo_format("photo.JPG") is True
        assert supports_photo_format("photo.JPEG") is True

    def test_supports_png(self):
        """Test PNG format support."""
        assert supports_photo_format("image.png") is True
        assert supports_photo_format("image.PNG") is True

    def test_supports_gif(self):
        """Test GIF format support."""
        assert supports_photo_format("animation.gif") is True
        assert supports_photo_format("animation.GIF") is True

    def test_supports_webp(self):
        """Test WebP format support."""
        assert supports_photo_format("modern.webp") is True
        assert supports_photo_format("modern.WEBP") is True

    def test_supports_bmp(self):
        """Test BMP format support."""
        assert supports_photo_format("legacy.bmp") is True

    def test_supports_tiff(self):
        """Test TIFF format support."""
        assert supports_photo_format("scan.tiff") is True
        assert supports_photo_format("scan.tif") is True

    def test_rejects_unsupported_formats(self):
        """Test that unsupported formats are rejected."""
        assert supports_photo_format("document.pdf") is False
        assert supports_photo_format("video.mp4") is False
        assert supports_photo_format("text.txt") is False
        assert supports_photo_format("archive.zip") is False

    def test_supports_path_objects(self):
        """Test with Path objects."""
        assert supports_photo_format(Path("photo.jpg")) is True
        assert supports_photo_format(Path("/path/to/image.png")) is True
        assert supports_photo_format(Path("document.pdf")) is False


class TestExtractPhotoMetadata:
    """Test suite for extract_photo_metadata function."""

    def test_extract_basic_metadata(self):
        """Test extracting basic metadata from a photo."""
        # Use existing test fixture
        photo_path = FIXTURES_DIR / "salmon.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        metadata = extract_photo_metadata(photo_path)

        # Verify basic properties
        assert metadata.file_name == "salmon.jpg"
        assert metadata.width > 0
        assert metadata.height > 0
        assert metadata.format.upper() == "JPEG"
        assert metadata.file_size > 0

    def test_extract_dimensions(self):
        """Test extracting image dimensions."""
        photo_path = FIXTURES_DIR / "MeadowInHimalayanMountains.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        metadata = extract_photo_metadata(photo_path)

        assert metadata.width > 0
        assert metadata.height > 0
        assert metadata.megapixels > 0
        assert metadata.aspect_ratio > 0

    def test_file_not_found_raises_error(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            extract_photo_metadata("/nonexistent/photo.jpg")

    def test_invalid_image_raises_error(self):
        """Test that invalid image data raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"not an image")
            f.flush()

            with pytest.raises(ValueError, match="Failed to read image"):
                extract_photo_metadata(f.name)

            Path(f.name).unlink()

    def test_metadata_properties(self):
        """Test computed properties of PhotoMetadata."""
        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img = Image.new("RGB", (1920, 1080), color="blue")
            img.save(f.name)

            metadata = extract_photo_metadata(f.name)

            # Test computed properties
            assert metadata.megapixels == pytest.approx(2.0736, rel=0.01)
            assert metadata.aspect_ratio == pytest.approx(16/9, rel=0.01)

            Path(f.name).unlink()


class TestParsePhoto:
    """Test suite for parse_photo function."""

    def test_parse_photo_basic(self):
        """Test basic photo parsing without AI."""
        photo_path = FIXTURES_DIR / "salmon.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        # Parse without AI analysis
        doc = parse_photo(photo_path, ai_analysis=False)

        # Verify Document structure
        assert doc.document_id is not None
        assert doc.content is not None
        assert doc.metadata is not None
        assert doc.processing_info is not None
        assert doc.processing_info.parser_used == "PhotoParser"

        # Verify metadata
        assert doc.metadata.title == "salmon.jpg"
        assert doc.metadata.original_format == "jpeg"
        assert doc.metadata.file_size > 0

    def test_parse_photo_returns_markdown_content(self):
        """Test that photo parsing returns markdown formatted content."""
        photo_path = FIXTURES_DIR / "HouseWithBicycle.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False)

        # Verify markdown structure
        assert "# " in doc.content  # Has title
        assert "## " in doc.content  # Has sections
        assert "**" in doc.content  # Has bold text
        assert "Technical Details" in doc.content

    def test_parse_photo_includes_image_reference(self):
        """Test that parsed photo includes ImageReference."""
        photo_path = FIXTURES_DIR / "Toadstools.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False)

        # Should have one image reference (the photo itself)
        assert len(doc.images) == 1
        assert doc.images[0].image_id == "photo_001"
        assert doc.images[0].file_path is not None
        assert doc.images[0].size is not None
        assert doc.images[0].format in ["jpeg", "jpg"]

    def test_parse_photo_custom_fields(self):
        """Test that custom_fields contains expected data."""
        photo_path = FIXTURES_DIR / "MarathonFinish.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False)

        custom = doc.metadata.custom_fields
        assert custom is not None
        assert "width" in custom
        assert "height" in custom
        assert "megapixels" in custom
        assert "aspect_ratio" in custom

    def test_parse_photo_extracts_colors(self):
        """Test that color palette is extracted."""
        photo_path = FIXTURES_DIR / "HeartShapedAppetizers.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False, include_colors=True)

        custom = doc.metadata.custom_fields
        assert "color_palette" in custom
        assert isinstance(custom["color_palette"], list)
        # Colors should be hex codes
        for color in custom["color_palette"]:
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB

    def test_parse_photo_validation_error(self):
        """Test that invalid file raises ValidationError."""
        with pytest.raises(ValidationError):
            parse_photo("/nonexistent/photo.jpg", ai_analysis=False)

    def test_parse_photo_unsupported_format(self):
        """Test that unsupported format raises ValidationError."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"fake pdf content")
            f.flush()

            with pytest.raises(ValidationError, match="Unsupported format"):
                parse_photo(f.name, ai_analysis=False)

            Path(f.name).unlink()


class TestGPSInfo:
    """Test suite for GPSInfo class."""

    def test_gps_decimal_string(self):
        """Test GPS decimal string formatting."""
        gps = GPSInfo(latitude=40.7128, longitude=-74.0060)
        result = gps.to_decimal_string()
        assert result == "40.712800, -74.006000"

    def test_gps_dms_string(self):
        """Test GPS DMS string formatting."""
        gps = GPSInfo(latitude=40.7128, longitude=-74.0060)
        result = gps.to_dms_string()
        assert "40°" in result
        assert "N" in result
        assert "W" in result

    def test_gps_no_coordinates(self):
        """Test GPS with no coordinates."""
        gps = GPSInfo()
        assert gps.to_decimal_string() is None
        assert gps.to_dms_string() is None


class TestPhotoMetadataProperties:
    """Test PhotoMetadata computed properties."""

    def test_orientation_descriptions(self):
        """Test orientation description lookup."""
        metadata = PhotoMetadata(
            file_path="/test.jpg",
            file_name="test.jpg",
            file_size=1000,
            width=100,
            height=100,
            format="JPEG",
            mode="RGB",
            orientation=1,
        )
        assert metadata.orientation_description == "Normal"

        metadata.orientation = 6
        assert metadata.orientation_description == "Rotated 90° CW"

        metadata.orientation = None
        assert metadata.orientation_description == "Normal"


class TestIntegrationWithMainParser:
    """Integration tests with main parse_document function."""

    def test_parse_document_supports_photos(self):
        """Test that parse_document can parse photos."""
        photo_path = FIXTURES_DIR / "salmon.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        # Parse using main entry point
        doc = parse_document(photo_path, options={"ai_analysis": False})

        assert doc is not None
        assert doc.processing_info.parser_used == "PhotoParser"
        assert doc.metadata.original_format == "jpeg"

    def test_get_supported_formats_includes_photos(self):
        """Test that get_supported_formats includes photo formats."""
        formats = get_supported_formats()

        photo_formats = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"]
        for fmt in photo_formats:
            assert fmt in formats, f"{fmt} should be in supported formats"

    def test_is_format_supported_for_photos(self):
        """Test is_format_supported for photo formats."""
        assert is_format_supported("photo.jpg") is True
        assert is_format_supported("image.png") is True
        assert is_format_supported("picture.webp") is True
        assert is_format_supported(Path("test.tiff")) is True


class TestParseMultiplePhotos:
    """Test parsing multiple photos."""

    def test_parse_all_fixture_photos(self):
        """Test parsing all photos in fixtures directory."""
        photo_files = list(FIXTURES_DIR.glob("*.jpg"))

        if not photo_files:
            pytest.skip("No photo fixtures available")

        for photo_path in photo_files:
            doc = parse_photo(photo_path, ai_analysis=False)

            assert doc is not None
            assert doc.document_id is not None
            assert doc.metadata.title == photo_path.name
            assert len(doc.images) == 1

    def test_parse_different_formats(self):
        """Test parsing photos of different formats."""
        # Create test images in different formats
        formats = [
            ("test.jpg", "JPEG"),
            ("test.png", "PNG"),
            ("test.gif", "GIF"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for filename, pil_format in formats:
                path = Path(temp_dir) / filename
                img = Image.new("RGB", (200, 200), color="red")
                img.save(path, format=pil_format)

                doc = parse_photo(path, ai_analysis=False)

                assert doc is not None
                assert doc.metadata.title == filename
                assert len(doc.images) == 1


class TestColorExtraction:
    """Test color palette extraction."""

    def test_extract_colors_from_solid_image(self):
        """Test extracting colors from a solid color image."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create solid red image
            img = Image.new("RGB", (100, 100), color=(255, 0, 0))
            img.save(f.name)

            doc = parse_photo(f.name, ai_analysis=False, include_colors=True)

            colors = doc.metadata.custom_fields.get("color_palette", [])
            assert len(colors) > 0
            # Should contain red-ish colors
            assert any("ff" in c.lower()[:3] for c in colors)

            Path(f.name).unlink()

    def test_disable_color_extraction(self):
        """Test disabling color extraction."""
        photo_path = FIXTURES_DIR / "salmon.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False, include_colors=False)

        colors = doc.metadata.custom_fields.get("color_palette", [])
        assert colors == []


class TestMarkdownOutput:
    """Test markdown output generation."""

    def test_markdown_has_title(self):
        """Test that markdown output has title."""
        photo_path = FIXTURES_DIR / "salmon.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False)

        assert doc.content.startswith("# salmon.jpg")

    def test_markdown_has_technical_details(self):
        """Test that markdown output has technical details section."""
        photo_path = FIXTURES_DIR / "salmon.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False)

        assert "## Technical Details" in doc.content
        assert "Dimensions:" in doc.content
        assert "Megapixels:" in doc.content
        assert "Format:" in doc.content
        assert "File Size:" in doc.content

    def test_markdown_has_color_palette(self):
        """Test that markdown output has color palette section."""
        photo_path = FIXTURES_DIR / "salmon.jpg"
        if not photo_path.exists():
            pytest.skip("Test fixture not available")

        doc = parse_photo(photo_path, ai_analysis=False, include_colors=True)

        assert "## Color Palette" in doc.content
        # Should have hex color codes
        assert "`#" in doc.content
