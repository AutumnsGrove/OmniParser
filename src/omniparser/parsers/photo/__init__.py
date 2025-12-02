"""
Photo parser module for OmniParser.

This module provides parsing capabilities for standalone photo/image files,
including EXIF metadata extraction, AI-powered analysis, and markdown output.

Supported formats:
    - JPEG (.jpg, .jpeg)
    - PNG (.png)
    - GIF (.gif)
    - WebP (.webp)
    - BMP (.bmp)
    - TIFF (.tiff, .tif)

Example:
    >>> from omniparser.parsers.photo import parse_photo
    >>> doc = parse_photo("vacation.jpg")
    >>> print(doc.metadata.title)
    >>> print(doc.content)  # Markdown formatted

    >>> # With AI analysis
    >>> doc = parse_photo(
    ...     "photo.jpg",
    ...     ai_options={"ai_provider": "anthropic"}
    ... )
    >>> print(doc.metadata.custom_fields["sentiment"])
"""

from .metadata import (
    CameraInfo,
    ExposureInfo,
    GPSInfo,
    PhotoMetadata,
    extract_photo_metadata,
)
from .parser import parse_photo, supports_photo_format

__all__ = [
    # Main parser function
    "parse_photo",
    "supports_photo_format",
    # Metadata classes
    "PhotoMetadata",
    "CameraInfo",
    "ExposureInfo",
    "GPSInfo",
    "extract_photo_metadata",
]
