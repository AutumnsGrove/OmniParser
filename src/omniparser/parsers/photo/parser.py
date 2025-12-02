"""
Photo parser for standalone image files.

This module provides a parser for photo/image files that extracts comprehensive
metadata (EXIF), generates AI-powered descriptions, sentiment analysis, and
captions, and outputs everything as a Document object.

Supported formats: JPEG, PNG, GIF, WebP, BMP, TIFF

Features:
    - EXIF metadata extraction (camera, GPS, timestamps, exposure settings)
    - AI-powered image description and scene analysis
    - Sentiment/mood analysis (happy, sad, peaceful, dramatic, etc.)
    - Caption generation for social media
    - Color palette extraction
    - Markdown output with YAML frontmatter
"""

import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from ...exceptions import ParsingError, ValidationError
from ...models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from .metadata import PhotoMetadata, extract_photo_metadata

logger = logging.getLogger(__name__)

# Supported photo formats
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


def parse_photo(file_path: Union[Path, str], **options: Any) -> Document:
    """Parse a photo file and return a Document object.

    This is the main entry point for photo parsing. It extracts metadata,
    performs AI analysis if enabled, and returns a Document with all
    information formatted for easy access.

    Args:
        file_path: Path to the photo file.
        **options: Parser configuration options:
            ai_analysis (bool): Enable AI analysis. Default: True
            ai_options (dict): AI provider options (see ai_config.py).
            include_sentiment (bool): Include sentiment/mood analysis. Default: True
            include_caption (bool): Generate social media caption. Default: True
            include_colors (bool): Extract color palette. Default: True
            output_format (str): Output format - "markdown" or "json". Default: "markdown"

    Returns:
        Document object with parsed content, metadata, and AI analysis.

    Raises:
        ValidationError: If file is not a valid photo format.
        ParsingError: If parsing fails.

    Example:
        >>> doc = parse_photo("vacation.jpg")
        >>> print(doc.metadata.title)  # File name
        >>> print(doc.content)  # Markdown formatted content
        >>> print(doc.metadata.custom_fields["sentiment"])  # AI sentiment

        >>> # With specific AI provider
        >>> doc = parse_photo(
        ...     "photo.jpg",
        ...     ai_options={
        ...         "ai_provider": "anthropic",
        ...         "ai_model": "claude-3-5-sonnet-20241022"
        ...     }
        ... )
    """
    start_time = time.time()
    warnings: List[str] = []

    # Convert to Path
    path = Path(file_path) if isinstance(file_path, str) else file_path

    # Validate file
    _validate_photo_file(path)

    try:
        # Extract metadata
        logger.info(f"Extracting metadata from: {path}")
        photo_metadata = extract_photo_metadata(path)

        # Build configuration
        config = _build_config(options)

        # Perform AI analysis if enabled
        ai_analysis: Dict[str, Any] = {}
        if config.get("ai_analysis", True):
            try:
                ai_analysis = _perform_ai_analysis(path, photo_metadata, config)
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")
                warnings.append(f"AI analysis failed: {e}")

        # Extract colors if enabled
        colors: List[str] = []
        if config.get("include_colors", True):
            try:
                colors = _extract_dominant_colors(path)
            except Exception as e:
                logger.warning(f"Color extraction failed: {e}")
                warnings.append(f"Color extraction failed: {e}")

        # Build Document metadata
        metadata = _build_metadata(photo_metadata, ai_analysis, colors)

        # Generate content (markdown by default)
        content = _generate_content(photo_metadata, ai_analysis, colors, config)

        # Create ImageReference for the photo itself
        images = [
            ImageReference(
                image_id="photo_001",
                position=0,
                file_path=str(path.absolute()),
                alt_text=ai_analysis.get("alt_text", photo_metadata.file_name),
                size=(photo_metadata.width, photo_metadata.height),
                format=photo_metadata.format.lower(),
            )
        ]

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create processing info
        processing_info = ProcessingInfo(
            parser_used="PhotoParser",
            parser_version="1.0.0",
            processing_time=processing_time,
            timestamp=datetime.now(),
            warnings=warnings,
            options_used=config.copy(),
        )

        # Create Document
        document = Document(
            document_id=str(uuid.uuid4()),
            content=content,
            chapters=[],  # Photos don't have chapters
            images=images,
            metadata=metadata,
            processing_info=processing_info,
            word_count=len(content.split()),
            estimated_reading_time=1,  # Minimal reading time for photo metadata
        )

        logger.info(
            f"Photo parsing complete: {photo_metadata.width}x{photo_metadata.height}, "
            f"format={photo_metadata.format} (took {processing_time:.2f}s)"
        )

        return document

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Photo parsing failed: {e}")
        raise ParsingError(
            f"Failed to parse photo: {e}", parser="PhotoParser", original_error=e
        )


def supports_photo_format(file_path: Union[Path, str]) -> bool:
    """Check if the file is a supported photo format.

    Args:
        file_path: Path to check.

    Returns:
        True if format is supported.
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    return path.suffix.lower() in SUPPORTED_FORMATS


def _validate_photo_file(path: Path) -> None:
    """Validate that the file exists and is a supported photo format.

    Args:
        path: Path to the photo file.

    Raises:
        ValidationError: If file is invalid.
    """
    if not path.exists():
        raise ValidationError(f"File not found: {path}")

    if not path.is_file():
        raise ValidationError(f"Not a file: {path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValidationError(
            f"Unsupported format: {path.suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    # Verify it's a valid image
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as e:
        raise ValidationError(f"Invalid image file: {e}")


def _build_config(options: Dict[str, Any]) -> Dict[str, Any]:
    """Build configuration with defaults.

    Args:
        options: User-provided options.

    Returns:
        Complete configuration dictionary.
    """
    return {
        "ai_analysis": options.get("ai_analysis", True),
        "ai_options": options.get("ai_options", {}),
        "include_sentiment": options.get("include_sentiment", True),
        "include_caption": options.get("include_caption", True),
        "include_colors": options.get("include_colors", True),
        "output_format": options.get("output_format", "markdown"),
    }


def _perform_ai_analysis(
    path: Path, metadata: PhotoMetadata, config: Dict[str, Any]
) -> Dict[str, Any]:
    """Perform AI-powered analysis on the photo.

    Args:
        path: Path to photo file.
        metadata: Extracted photo metadata.
        config: Parser configuration.

    Returns:
        Dictionary with AI analysis results.
    """
    from ...processors.ai_photo_analyzer import analyze_photo

    ai_options = config.get("ai_options", {})

    return analyze_photo(
        str(path),
        ai_options=ai_options,
        include_sentiment=config.get("include_sentiment", True),
        include_caption=config.get("include_caption", True),
    )


def _extract_dominant_colors(path: Path, num_colors: int = 5) -> List[str]:
    """Extract dominant colors from the photo.

    Uses a simple color quantization approach.

    Args:
        path: Path to photo file.
        num_colors: Number of colors to extract.

    Returns:
        List of hex color codes.
    """
    with Image.open(path) as img:
        # Resize for faster processing
        img_small = img.copy()
        img_small.thumbnail((150, 150))

        # Convert to RGB
        if img_small.mode != "RGB":
            img_small = img_small.convert("RGB")

        # Quantize to reduce colors
        quantized = img_small.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)

        # Get palette
        palette = quantized.getpalette()
        if not palette:
            return []

        # Convert to hex colors
        colors = []
        # Palette is flat RGB: [R1, G1, B1, R2, G2, B2, ...]
        # Get actual number of colors we can extract
        actual_colors = min(num_colors, len(palette) // 3)
        for i in range(actual_colors):
            rgb_slice = palette[i * 3 : i * 3 + 3]
            if len(rgb_slice) == 3:
                r, g, b = rgb_slice
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                colors.append(hex_color)

        return colors


def _build_metadata(
    photo_metadata: PhotoMetadata,
    ai_analysis: Dict[str, Any],
    colors: List[str],
) -> Metadata:
    """Build Document metadata from photo metadata and AI analysis.

    Args:
        photo_metadata: Extracted photo metadata.
        ai_analysis: AI analysis results.
        colors: Extracted color palette.

    Returns:
        Metadata object.
    """
    custom_fields: Dict[str, Any] = {
        # Photo dimensions
        "width": photo_metadata.width,
        "height": photo_metadata.height,
        "megapixels": round(photo_metadata.megapixels, 2),
        "aspect_ratio": round(photo_metadata.aspect_ratio, 3),
        "orientation": photo_metadata.orientation_description,
        # Colors
        "color_palette": colors,
    }

    # Camera info
    if photo_metadata.camera.make or photo_metadata.camera.model:
        custom_fields["camera"] = {
            "make": photo_metadata.camera.make,
            "model": photo_metadata.camera.model,
            "lens": photo_metadata.camera.lens_model,
            "software": photo_metadata.camera.software,
        }

    # Exposure info
    if any(
        [
            photo_metadata.exposure.aperture,
            photo_metadata.exposure.shutter_speed,
            photo_metadata.exposure.iso,
        ]
    ):
        custom_fields["exposure"] = {
            "aperture": f"f/{photo_metadata.exposure.aperture}"
            if photo_metadata.exposure.aperture
            else None,
            "shutter_speed": photo_metadata.exposure.shutter_speed,
            "iso": photo_metadata.exposure.iso,
            "focal_length": f"{photo_metadata.exposure.focal_length}mm"
            if photo_metadata.exposure.focal_length
            else None,
            "focal_length_35mm": f"{photo_metadata.exposure.focal_length_35mm}mm"
            if photo_metadata.exposure.focal_length_35mm
            else None,
            "flash": photo_metadata.exposure.flash,
            "metering_mode": photo_metadata.exposure.metering_mode,
            "white_balance": photo_metadata.exposure.white_balance,
        }

    # GPS info
    if photo_metadata.gps.latitude is not None:
        custom_fields["gps"] = {
            "coordinates": photo_metadata.gps.to_decimal_string(),
            "coordinates_dms": photo_metadata.gps.to_dms_string(),
            "altitude": f"{photo_metadata.gps.altitude}m"
            if photo_metadata.gps.altitude
            else None,
        }

    # AI analysis results
    if ai_analysis:
        if "sentiment" in ai_analysis:
            custom_fields["sentiment"] = ai_analysis["sentiment"]
        if "mood" in ai_analysis:
            custom_fields["mood"] = ai_analysis["mood"]
        if "caption" in ai_analysis:
            custom_fields["caption"] = ai_analysis["caption"]
        if "subjects" in ai_analysis:
            custom_fields["subjects"] = ai_analysis["subjects"]
        if "scene_type" in ai_analysis:
            custom_fields["scene_type"] = ai_analysis["scene_type"]

    return Metadata(
        title=photo_metadata.file_name,
        author=photo_metadata.artist or photo_metadata.copyright,
        publication_date=photo_metadata.date_taken,
        description=ai_analysis.get("description", photo_metadata.description),
        tags=ai_analysis.get("tags", []),
        original_format=photo_metadata.format.lower(),
        file_size=photo_metadata.file_size,
        custom_fields=custom_fields,
    )


def _generate_content(
    photo_metadata: PhotoMetadata,
    ai_analysis: Dict[str, Any],
    colors: List[str],
    config: Dict[str, Any],
) -> str:
    """Generate formatted content for the Document.

    Args:
        photo_metadata: Extracted photo metadata.
        ai_analysis: AI analysis results.
        colors: Extracted color palette.
        config: Parser configuration.

    Returns:
        Formatted content string (markdown).
    """
    output_format = config.get("output_format", "markdown")

    if output_format == "markdown":
        return _generate_markdown_content(photo_metadata, ai_analysis, colors)
    else:
        # Default to markdown
        return _generate_markdown_content(photo_metadata, ai_analysis, colors)


def _generate_markdown_content(
    photo_metadata: PhotoMetadata,
    ai_analysis: Dict[str, Any],
    colors: List[str],
) -> str:
    """Generate markdown-formatted content.

    Args:
        photo_metadata: Extracted photo metadata.
        ai_analysis: AI analysis results.
        colors: Extracted color palette.

    Returns:
        Markdown string.
    """
    lines = []

    # Title
    lines.append(f"# {photo_metadata.file_name}")
    lines.append("")

    # AI-generated caption (if available)
    if ai_analysis.get("caption"):
        lines.append(f"> {ai_analysis['caption']}")
        lines.append("")

    # Description
    if ai_analysis.get("description"):
        lines.append("## Description")
        lines.append("")
        lines.append(ai_analysis["description"])
        lines.append("")

    # Sentiment and Mood
    if ai_analysis.get("sentiment") or ai_analysis.get("mood"):
        lines.append("## Mood & Sentiment")
        lines.append("")
        if ai_analysis.get("sentiment"):
            lines.append(f"**Sentiment:** {ai_analysis['sentiment']}")
        if ai_analysis.get("mood"):
            moods = ai_analysis["mood"]
            if isinstance(moods, list):
                lines.append(f"**Mood:** {', '.join(moods)}")
            else:
                lines.append(f"**Mood:** {moods}")
        lines.append("")

    # Subjects
    if ai_analysis.get("subjects"):
        lines.append("## Subjects")
        lines.append("")
        subjects = ai_analysis["subjects"]
        if isinstance(subjects, list):
            for subject in subjects:
                lines.append(f"- {subject}")
        else:
            lines.append(f"- {subjects}")
        lines.append("")

    # Technical Details
    lines.append("## Technical Details")
    lines.append("")
    lines.append(f"- **Dimensions:** {photo_metadata.width} × {photo_metadata.height} px")
    lines.append(f"- **Megapixels:** {photo_metadata.megapixels:.1f} MP")
    lines.append(f"- **Format:** {photo_metadata.format}")
    lines.append(f"- **File Size:** {_format_file_size(photo_metadata.file_size)}")

    if photo_metadata.date_taken:
        lines.append(
            f"- **Date Taken:** {photo_metadata.date_taken.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    lines.append("")

    # Camera Info
    if photo_metadata.camera.make or photo_metadata.camera.model:
        lines.append("## Camera")
        lines.append("")
        if photo_metadata.camera.make:
            lines.append(f"- **Make:** {photo_metadata.camera.make}")
        if photo_metadata.camera.model:
            lines.append(f"- **Model:** {photo_metadata.camera.model}")
        if photo_metadata.camera.lens_model:
            lines.append(f"- **Lens:** {photo_metadata.camera.lens_model}")
        if photo_metadata.camera.software:
            lines.append(f"- **Software:** {photo_metadata.camera.software}")
        lines.append("")

    # Exposure Settings
    if any(
        [
            photo_metadata.exposure.aperture,
            photo_metadata.exposure.shutter_speed,
            photo_metadata.exposure.iso,
        ]
    ):
        lines.append("## Exposure Settings")
        lines.append("")
        if photo_metadata.exposure.aperture:
            lines.append(f"- **Aperture:** f/{photo_metadata.exposure.aperture}")
        if photo_metadata.exposure.shutter_speed:
            lines.append(f"- **Shutter Speed:** {photo_metadata.exposure.shutter_speed}")
        if photo_metadata.exposure.iso:
            lines.append(f"- **ISO:** {photo_metadata.exposure.iso}")
        if photo_metadata.exposure.focal_length:
            lines.append(f"- **Focal Length:** {photo_metadata.exposure.focal_length}mm")
        if photo_metadata.exposure.focal_length_35mm:
            lines.append(
                f"- **35mm Equivalent:** {photo_metadata.exposure.focal_length_35mm}mm"
            )
        if photo_metadata.exposure.exposure_mode:
            lines.append(f"- **Exposure Mode:** {photo_metadata.exposure.exposure_mode}")
        if photo_metadata.exposure.metering_mode:
            lines.append(f"- **Metering:** {photo_metadata.exposure.metering_mode}")
        if photo_metadata.exposure.flash:
            lines.append(f"- **Flash:** {photo_metadata.exposure.flash}")
        lines.append("")

    # GPS Location
    if photo_metadata.gps.latitude is not None:
        lines.append("## Location")
        lines.append("")
        lines.append(f"- **Coordinates:** {photo_metadata.gps.to_decimal_string()}")
        lines.append(f"- **DMS:** {photo_metadata.gps.to_dms_string()}")
        if photo_metadata.gps.altitude:
            lines.append(f"- **Altitude:** {photo_metadata.gps.altitude:.1f}m")
        lines.append("")

    # Color Palette
    if colors:
        lines.append("## Color Palette")
        lines.append("")
        lines.append(" ".join([f"`{c}`" for c in colors]))
        lines.append("")

    # Tags
    if ai_analysis.get("tags"):
        lines.append("## Tags")
        lines.append("")
        tags = ai_analysis["tags"]
        lines.append(" ".join([f"#{tag}" for tag in tags]))
        lines.append("")

    return "\n".join(lines)


def _format_file_size(size_bytes: int) -> str:
    """Format file size as human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string (e.g., "2.5 MB").
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
