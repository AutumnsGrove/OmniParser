"""
Photo parser module for OmniParser.

This module provides both functional and object-oriented interfaces to photo parsing:
- parse_photo(): Functional interface (recommended for new code)
- PhotoParser: Class-based interface (for backward compatibility and consistency)

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

    >>> # Class-based interface
    >>> parser = PhotoParser({"ai_analysis": True})
    >>> doc = parser.parse("photo.jpg")
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ...models import Document, ImageReference
from .metadata import (
    CameraInfo,
    ExposureInfo,
    GPSInfo,
    PhotoMetadata,
    extract_photo_metadata,
)
from .parser import parse_photo, supports_photo_format


class PhotoParser:
    """Parser for photo/image files with EXIF extraction and AI analysis.

    This is a thin wrapper around the functional parse_photo() implementation
    that provides a consistent class-based API matching other parsers.

    Features:
    - EXIF metadata extraction (camera, GPS, timestamps, exposure settings)
    - AI-powered image description and scene analysis
    - Sentiment/mood analysis
    - Caption generation for social media
    - Color palette extraction
    - Markdown output with YAML frontmatter

    Options:
        ai_analysis (bool): Enable AI analysis. Default: True
        ai_options (dict): AI provider options (see ai_config.py).
        include_sentiment (bool): Include sentiment/mood analysis. Default: True
        include_caption (bool): Generate social media caption. Default: True
        include_colors (bool): Extract color palette. Default: True
        output_format (str): Output format - "markdown" or "json". Default: "markdown"

    Example:
        >>> parser = PhotoParser({'ai_analysis': True, 'include_colors': True})
        >>> doc = parser.parse(Path('vacation.jpg'))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Sentiment: {doc.metadata.custom_fields.get('sentiment')}")

    Note:
        For new code, consider using the functional parse_photo() interface directly:
        >>> from omniparser.parsers.photo import parse_photo
        >>> doc = parse_photo('photo.jpg', ai_analysis=True)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize Photo parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        self.options = options or {}

        # Set default options
        self.options.setdefault("ai_analysis", True)
        self.options.setdefault("ai_options", {})
        self.options.setdefault("include_sentiment", True)
        self.options.setdefault("include_caption", True)
        self.options.setdefault("include_colors", True)
        self.options.setdefault("output_format", "markdown")

        # Initialize tracking (for consistency with other parsers)
        self._warnings: List[str] = []

    @classmethod
    def supports_format(cls, file_path: Union[Path, str]) -> bool:
        """Check if file is a supported photo format.

        Args:
            file_path: Path to check.

        Returns:
            True if format is supported, False otherwise.
        """
        return supports_photo_format(file_path)

    def parse(self, file_path: Union[Path, str]) -> Document:
        """Parse photo file and return Document object.

        This method delegates to the functional parse_photo() implementation,
        passing along the configured options.

        Args:
            file_path: Path to photo file.

        Returns:
            Document object with parsed content, metadata, and AI analysis.

        Raises:
            ValidationError: If file is not a valid photo format.
            ParsingError: If parsing fails.
        """
        # Delegate to functional implementation
        return parse_photo(file_path, **self.options)

    def extract_images(self, file_path: Union[Path, str]) -> List[ImageReference]:
        """Get image reference for the photo.

        For photos, this returns a single ImageReference for the photo itself.

        Args:
            file_path: Path to photo file.

        Returns:
            List containing single ImageReference for the photo.
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        metadata = extract_photo_metadata(path)

        return [
            ImageReference(
                image_id="photo_001",
                position=0,
                file_path=str(path.absolute()),
                alt_text=metadata.file_name,
                size=(metadata.width, metadata.height),
                format=metadata.format.lower(),
            )
        ]


__all__ = [
    # Class-based interface
    "PhotoParser",
    # Functional interface
    "parse_photo",
    "supports_photo_format",
    # Metadata classes
    "PhotoMetadata",
    "CameraInfo",
    "ExposureInfo",
    "GPSInfo",
    "extract_photo_metadata",
]
