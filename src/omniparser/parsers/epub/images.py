"""
Image extraction for EPUB files.

This module handles extracting images from EPUB archives and saving them
with proper validation, dimension detection, and format handling.

Functions:
    extract_epub_images: Main entry point for image extraction from EPUB files
    extract_images_from_book: Extract images from loaded EpubBook object
    extract_images_to_directory: Extract images to specified directory
"""

import logging
import tempfile
from pathlib import Path
from typing import Any, List, Optional

import ebooklib

from ...models import ImageReference
from ...processors.image_extractor import (
    get_image_dimensions,
    save_image,
    validate_image_data,
)

logger = logging.getLogger(__name__)


def extract_epub_images(
    book: Any,
    output_dir: Optional[Path],
    warnings: List[str],
) -> List[ImageReference]:
    """Extract images from loaded EPUB book object.

    Extracts all images from the EPUB and saves them to either a temporary
    directory (default) or a persistent directory if output_dir is set.

    Args:
        book: Loaded EpubBook object from ebooklib.
        output_dir: Directory to save images. If None, uses temp directory
            (auto-cleanup). If set, saves to persistent directory.
        warnings: List to append warning messages to.

    Returns:
        List of ImageReference objects.

    Note:
        - If output_dir is None: uses temp directory (auto-cleanup)
        - If output_dir is set: saves to persistent directory
        - Sequential image IDs: img_001, img_002, etc.
        - Position set to 0 (exact position tracking not implemented)
        - Alt text set to None (HTML parsing not implemented)
        - Preserves EPUB internal directory structure (e.g., images/cover.jpg)
    """
    try:
        # Get all image items from EPUB
        image_items = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))

        if not image_items:
            logger.info("No images found in EPUB")
            return []

        logger.info(f"Found {len(image_items)} images in EPUB")

        # Determine output directory
        use_persistent_dir = output_dir is not None

        if use_persistent_dir:
            # Create persistent directory
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving images to persistent directory: {output_dir}")

            # Extract images to persistent directory
            images = extract_images_to_directory(image_items, output_dir, warnings)
            logger.info(f"Successfully extracted {len(images)} images to {output_dir}")
            return images
        else:
            # Use temporary directory with context manager for safe cleanup
            logger.info("Saving images to temporary directory (will be deleted)")
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                images = extract_images_to_directory(image_items, temp_path, warnings)
                logger.info(f"Successfully extracted {len(images)} images")
                return images

    except Exception as e:
        logger.error(f"Image extraction failed: {e}")
        raise


def extract_images_to_directory(
    image_items: List, output_path: Path, warnings: List[str]
) -> List[ImageReference]:
    """Extract images to specified directory.

    Performs the actual image extraction and saves to the provided directory
    path. Uses shared image_extractor utilities for validation and saving.

    Args:
        image_items: List of EPUB image items from ebooklib.
        output_path: Directory path to save images to.
        warnings: List to append warning messages to.

    Returns:
        List of ImageReference objects with file paths pointing to saved images.
    """
    images: List[ImageReference] = []

    for idx, item in enumerate(image_items, start=1):
        try:
            # Get image metadata
            image_name = item.get_name()  # e.g., "images/cover.jpg"
            image_content = item.get_content()  # bytes

            # Validate image data (no minimum size for EPUB - icons can be small)
            is_valid, error = validate_image_data(image_content, min_size=1)
            if not is_valid:
                logger.warning(f"Skipping invalid image {image_name}: {error}")
                warnings.append(f"Skipped invalid image {image_name}: {error}")
                continue

            # Save image (preserves subdirectory structure)
            image_path, format_name = save_image(
                image_content,
                output_path,
                preserve_subdirs=True,
                original_path=image_name,
                counter=idx,
            )

            # Get image dimensions
            width, height, detected_format = get_image_dimensions(image_content)
            if detected_format != "unknown":
                format_name = detected_format

            # Create ImageReference
            image_ref = ImageReference(
                image_id=f"img_{idx:03d}",
                position=0,  # We don't track exact position
                file_path=str(image_path),
                alt_text=None,  # Would require HTML parsing
                size=(width, height) if width and height else None,
                format=format_name,
            )

            images.append(image_ref)
            logger.debug(
                f"Extracted image {idx}: {image_name} ({format_name}, {width}x{height})"
            )

        except Exception as e:
            logger.warning(f"Failed to extract image {idx}: {e}")
            warnings.append(f"Failed to extract image: {e}")
            # Continue with next image - don't fail entire extraction

    return images
