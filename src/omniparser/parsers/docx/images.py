"""
Image extraction module for DOCX parser.

This module provides functions for extracting and saving images from Microsoft
Word DOCX files. It handles image validation, dimension extraction, format
detection, and file saving.

Functions:
    extract_images: Extract and save images from DOCX document
    extract_images_to_directory: Helper for actual image extraction

Usage:
    >>> from pathlib import Path
    >>> from docx import Document
    >>> docx = Document("report.docx")
    >>> images = extract_images(docx, True, Path("/output/images"), Path("report.docx"))
    >>> print(f"Extracted {len(images)} images")
"""

import logging
from pathlib import Path
from typing import Any, List, Optional

from ...models import ImageReference
from ...processors.image_extractor import (
    extract_format_from_content_type,
    get_image_dimensions,
    save_image,
    validate_image_data,
)

logger = logging.getLogger(__name__)

# Security: Maximum size for individual images (50MB)
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB


def extract_images(
    docx: Any,
    extract_images_flag: bool,
    image_output_dir: Optional[Path],
    file_path: Path,
    warnings_list: Optional[List[str]] = None,
) -> tuple[List[ImageReference], int]:
    """
    Extract and save images from DOCX document.

    IMPORTANT: Images are only extracted when image_output_dir is specified.
    If image_output_dir is None, images are not extracted and an empty list
    is returned. This prevents creating ImageReference objects with invalid
    file paths to deleted temporary directories.

    Process:
    1. Check if image_output_dir is specified
    2. If not, return empty list
    3. Access document relationships (docx.part.rels)
    4. Find image relationships (rId)
    5. Extract image data
    6. Validate with shared utilities
    7. Save to output directory
    8. Create ImageReference objects

    Args:
        docx: python-docx Document object
        extract_images_flag: Whether to extract images
        image_output_dir: Output directory for images (must be specified)
        file_path: Source DOCX file path (for error messages)
        warnings_list: Optional list to append warnings to

    Returns:
        Tuple of (images_list, image_counter) where:
        - images_list: List of ImageReference objects (empty if image_output_dir is None)
        - image_counter: Number of images processed (for tracking)

    Example:
        >>> from pathlib import Path
        >>> from docx import Document
        >>> docx = Document("report.docx")
        >>> images, count = extract_images(
        ...     docx,
        ...     True,
        ...     Path("/output/images"),
        ...     Path("report.docx")
        ... )
        >>> print(f"Extracted {len(images)} images")
    """
    if warnings_list is None:
        warnings_list = []

    # Only extract images if a persistent output directory is specified
    if not extract_images_flag or image_output_dir is None:
        logger.info(
            "Skipping image extraction: no image_output_dir specified. "
            "Set image_output_dir option to extract images."
        )
        return [], 0

    try:
        # Ensure output directory exists
        output_path = Path(image_output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving images to persistent directory: {output_path}")

        # Extract images to directory
        images, counter = extract_images_to_directory(docx, output_path, warnings_list)

        logger.info(f"Successfully extracted {len(images)} images")
        return images, counter

    except Exception as e:
        logger.error(f"Image extraction failed: {e}")
        warnings_list.append(f"Image extraction failed: {e}")
        return [], 0


def extract_images_to_directory(
    docx: Any, output_path: Path, warnings_list: Optional[List[str]] = None
) -> tuple[List[ImageReference], int]:
    """
    Extract images to specified directory.

    Helper function that performs the actual image extraction and saves to
    the provided directory path. Uses shared image_extractor utilities for
    validation, saving, and dimension extraction.

    Args:
        docx: python-docx Document object
        output_path: Directory path to save images to
        warnings_list: Optional list to append warnings to

    Returns:
        Tuple of (images_list, image_counter) where:
        - images_list: List of ImageReference objects
        - image_counter: Number of images processed

    Raises:
        Exception: If critical error occurs during extraction (logged but not raised)
    """
    if warnings_list is None:
        warnings_list = []

    images: List[ImageReference] = []
    image_counter = 0

    # Access document relationships to find images
    try:
        # Get all image parts from document relationships
        for rel in docx.part.rels.values():
            if "image" in rel.target_ref:
                image_counter += 1
                image_ref = process_single_image(
                    rel, image_counter, output_path, warnings_list
                )
                if image_ref:
                    images.append(image_ref)

    except Exception as e:
        logger.warning(f"Error accessing document relationships: {e}")
        warnings_list.append(f"Error accessing document relationships: {e}")

    return images, image_counter


def process_single_image(
    rel: Any, counter: int, output_path: Path, warnings_list: List[str]
) -> Optional[ImageReference]:
    """
    Process and save a single image from document relationship.

    Args:
        rel: Document relationship object containing image
        counter: Current image counter for numbering
        output_path: Directory to save image to
        warnings_list: List to append warnings to

    Returns:
        ImageReference object if successful, None if extraction failed
    """
    try:
        # Extract image data
        image_part = rel.target_part
        image_bytes = image_part.blob

        # Validate image data using shared utility
        # Note: No minimum size for DOCX - icons and small graphics are valid
        is_valid, error = validate_image_data(
            image_bytes, min_size=1, max_size=MAX_IMAGE_SIZE
        )
        if not is_valid:
            logger.warning(f"Skipping image {counter}: {error}")
            warnings_list.append(f"Skipped invalid/oversized image: {error}")
            return None

        # Determine image format from content type
        content_type = image_part.content_type
        format_ext = extract_format_from_content_type(content_type)

        # Save image using shared utility
        image_path, format_name = save_image(
            image_bytes,
            output_path,
            base_name="image",
            extension=format_ext,
            counter=counter,
        )

        # Get image dimensions using shared utility
        width, height, detected_format = get_image_dimensions(image_bytes)
        if detected_format != "unknown":
            format_name = detected_format

        # Create ImageReference
        image_ref = ImageReference(
            image_id=f"img_{counter:03d}",
            position=0,  # We don't track exact position in DOCX
            file_path=str(image_path),
            alt_text=None,  # DOCX doesn't easily expose alt text
            size=(width, height) if width and height else None,
            format=format_name,
        )

        logger.debug(
            f"Extracted image {counter}: {image_path.name} "
            f"({format_name}, {width}x{height})"
        )
        return image_ref

    except Exception as e:
        logger.warning(f"Failed to extract image {counter}: {e}")
        warnings_list.append(f"Failed to extract image: {e}")
        return None
