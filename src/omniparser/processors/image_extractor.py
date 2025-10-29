"""
Shared image extraction utilities for all parsers.

This module provides reusable functions for extracting and saving images
from various document formats (EPUB, PDF, DOCX). It handles common operations
like file naming, directory management, format detection, and PIL validation.

Functions:
    save_image: Save image bytes to disk with automatic numbering
    get_image_dimensions: Extract dimensions and format from image data
    validate_image_data: Validate image data using PIL
"""

import io
import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

# Constants
MIN_IMAGE_SIZE = 100  # Minimum image dimension in pixels
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB maximum file size


def save_image(
    image_data: bytes,
    output_dir: Path,
    base_name: str = "image",
    extension: Optional[str] = None,
    counter: int = 1,
    preserve_subdirs: bool = False,
    original_path: Optional[str] = None,
) -> Tuple[Path, str]:
    """
    Save image data to file with auto-numbering.

    Args:
        image_data: Raw image bytes to save.
        output_dir: Directory to save images in.
        base_name: Base filename (e.g., "image", "img"). Default: "image"
        extension: File extension (e.g., "png", "jpg"). If None, auto-detect.
        counter: Starting counter for auto-numbering. Default: 1
        preserve_subdirs: If True and original_path provided, preserve directory structure.
        original_path: Original file path (e.g., "images/cover.jpg") for preserving structure.

    Returns:
        Tuple of (absolute_path, format_name) where:
        - absolute_path: Path object pointing to saved image file
        - format_name: Detected image format (e.g., "png", "jpeg", "gif")

    Raises:
        ValueError: If image_data is empty or invalid
        IOError: If file cannot be written

    Example:
        >>> image_bytes = b"\\x89PNG..."
        >>> path, fmt = save_image(image_bytes, Path("/tmp/images"), "photo", counter=5)
        >>> print(path)
        /tmp/images/photo_005.png
        >>> print(fmt)
        png
    """
    if not image_data:
        raise ValueError("Image data is empty")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Auto-detect extension if not provided
    if extension is None:
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                extension = img.format.lower() if img.format else "png"
        except Exception as e:
            logger.warning(f"Could not detect image format: {e}, defaulting to png")
            extension = "png"

    # Determine output path
    if preserve_subdirs and original_path:
        # Preserve original directory structure (e.g., "images/cover.jpg")
        image_path = output_dir / original_path
        image_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Use auto-numbered filename
        image_filename = f"{base_name}_{counter:03d}.{extension}"
        image_path = output_dir / image_filename

    # Save image to disk
    try:
        with open(image_path, "wb") as f:
            f.write(image_data)
    except IOError as e:
        logger.error(f"Failed to save image to {image_path}: {e}")
        raise

    # Get actual format name
    format_name = extension

    logger.debug(f"Saved image to {image_path} (format: {format_name})")
    return image_path, format_name


def get_image_dimensions(image_data: bytes) -> Tuple[Optional[int], Optional[int], str]:
    """
    Extract dimensions and format from image data using PIL.

    Args:
        image_data: Raw image bytes.

    Returns:
        Tuple of (width, height, format_name) where:
        - width: Image width in pixels, or None if cannot be determined
        - height: Image height in pixels, or None if cannot be determined
        - format_name: Image format (e.g., "png", "jpeg"), or "unknown"

    Example:
        >>> image_bytes = b"\\x89PNG..."
        >>> width, height, fmt = get_image_dimensions(image_bytes)
        >>> print(f"{width}x{height} {fmt}")
        1920x1080 png
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            width, height = img.size
            format_name = img.format.lower() if img.format else "unknown"
            return width, height, format_name
    except Exception as e:
        logger.warning(f"Could not read image dimensions: {e}")
        return None, None, "unknown"


def validate_image_data(
    image_data: bytes,
    min_size: int = MIN_IMAGE_SIZE,
    max_size: int = MAX_IMAGE_SIZE,
) -> Tuple[bool, Optional[str]]:
    """
    Validate image data using PIL and size constraints.

    Checks:
    - Image data is not empty
    - File size is within limits
    - PIL can open and verify the image
    - Image dimensions meet minimum requirements

    Args:
        image_data: Raw image bytes to validate.
        min_size: Minimum dimension (width or height) in pixels. Default: 100
        max_size: Maximum file size in bytes. Default: 50MB

    Returns:
        Tuple of (is_valid, error_message) where:
        - is_valid: True if image passes all validation checks
        - error_message: Description of validation failure, or None if valid

    Example:
        >>> image_bytes = b"\\x89PNG..."
        >>> is_valid, error = validate_image_data(image_bytes)
        >>> if not is_valid:
        ...     print(f"Invalid image: {error}")
    """
    # Check if data is empty
    if not image_data:
        return False, "Image data is empty"

    # Check file size
    if len(image_data) > max_size:
        size_mb = len(image_data) / 1024 / 1024
        max_mb = max_size / 1024 / 1024
        return False, f"Image too large ({size_mb:.1f} MB, max {max_mb:.0f} MB)"

    # Validate with PIL
    try:
        # First pass: verify image integrity
        with Image.open(io.BytesIO(image_data)) as img:
            img.verify()

        # Second pass: check dimensions (verify() closes the image)
        with Image.open(io.BytesIO(image_data)) as img:
            width, height = img.size

            # Check minimum dimensions
            if width < min_size or height < min_size:
                return (
                    False,
                    f"Image too small ({width}x{height}, min {min_size}x{min_size})",
                )

    except (IOError, OSError, Image.UnidentifiedImageError) as e:
        return False, f"Invalid image data: {e}"

    # All checks passed
    return True, None


def extract_format_from_content_type(content_type: str) -> str:
    """
    Extract file extension from MIME content type.

    Args:
        content_type: MIME type string (e.g., "image/jpeg", "image/png")

    Returns:
        File extension without dot (e.g., "jpg", "png", "gif")

    Example:
        >>> extract_format_from_content_type("image/jpeg")
        'jpg'
        >>> extract_format_from_content_type("image/png")
        'png'
    """
    # Normalize to lowercase for case-insensitive matching
    content_type_lower = content_type.lower()

    format_ext = "png"  # Default

    if "jpeg" in content_type_lower or "jpg" in content_type_lower:
        format_ext = "jpg"
    elif "png" in content_type_lower:
        format_ext = "png"
    elif "gif" in content_type_lower:
        format_ext = "gif"
    elif "bmp" in content_type_lower:
        format_ext = "bmp"
    elif "webp" in content_type_lower:
        format_ext = "webp"
    elif "tiff" in content_type_lower or "tif" in content_type_lower:
        format_ext = "tiff"

    return format_ext
