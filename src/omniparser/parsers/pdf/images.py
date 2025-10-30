"""
PDF image extraction and processing.

This module provides functions for extracting images from PDF documents using
PyMuPDF (fitz). It handles image validation, filtering by size, saving to disk,
and creating ImageReference objects with metadata.

Functions:
    extract_pdf_images: Extract all images from a PDF document
    extract_page_images: Extract images from a single PDF page
"""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF

from ...models import ImageReference
from ...processors.image_extractor import (
    get_image_dimensions,
    save_image,
    validate_image_data,
)
from .utils import MIN_IMAGE_SIZE

logger = logging.getLogger(__name__)


def extract_pdf_images(
    doc: fitz.Document,
    output_dir: Optional[Path] = None,
    max_images: Optional[int] = None,
) -> List[ImageReference]:
    """
    Extract embedded images from PDF document.

    Process:
    1. Iterate through pages
    2. Get image list: page.get_images()
    3. Extract image data: doc.extract_image(xref)
    4. Validate using MIN_IMAGE_SIZE filter
    5. Save using shared image_extractor utility
    6. Create ImageReference objects

    Args:
        doc: PyMuPDF document object.
        output_dir: Directory for extracted images. If None, uses temp directory.
        max_images: Maximum number of images to extract. If None, extracts all.

    Returns:
        List of ImageReference objects with image metadata.

    Example:
        >>> import fitz
        >>> doc = fitz.open("document.pdf")
        >>> images = extract_pdf_images(doc, Path("/tmp/images"))
        >>> print(f"Extracted {len(images)} images")
        >>> doc.close()
    """
    images = []
    temp_dir_obj = None

    # Set up output directory
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Use temporary directory
        temp_dir_obj = tempfile.TemporaryDirectory()
        output_dir = Path(temp_dir_obj.name)

    try:
        image_counter = 0

        for page_num in range(len(doc)):
            # Check if we've reached the image limit
            if max_images and image_counter >= max_images:
                logger.info(
                    f"Reached max_images limit ({max_images}), stopping extraction"
                )
                break

            page = doc[page_num]
            page_images, image_counter = extract_page_images(
                page, page_num, output_dir, image_counter, doc, max_images
            )
            images.extend(page_images)

        logger.info(f"Extracted {len(images)} images")
        return images

    finally:
        # Clean up temp directory if created
        if temp_dir_obj:
            temp_dir_obj.cleanup()


def extract_page_images(
    page: fitz.Page,
    page_num: int,
    output_dir: Path,
    counter: int,
    doc: fitz.Document,
    max_images: Optional[int] = None,
) -> Tuple[List[ImageReference], int]:
    """
    Extract images from a single PDF page.

    Args:
        page: PyMuPDF page object.
        page_num: Page number (0-indexed).
        output_dir: Directory to save images.
        counter: Starting counter for image numbering.
        doc: PyMuPDF document object (for extract_image call).
        max_images: Maximum total images to extract (for limit checking).

    Returns:
        Tuple of (list of ImageReference objects, updated counter).

    Example:
        >>> page = doc[0]
        >>> images, new_counter = extract_page_images(
        ...     page, 0, Path("/tmp"), 0, doc
        ... )
        >>> print(f"Found {len(images)} images, counter now {new_counter}")
    """
    images = []
    image_list = page.get_images()

    for img_index, img in enumerate(image_list):
        # Check if we've reached the image limit
        if max_images and counter >= max_images:
            break

        try:
            xref = img[0]
            base_image = doc.extract_image(xref)

            if not base_image:
                continue

            image_data = base_image["image"]
            image_ext = base_image["ext"]

            # Validate image data using shared utility
            is_valid, error = validate_image_data(image_data, min_size=MIN_IMAGE_SIZE)
            if not is_valid:
                logger.debug(f"Skipping invalid image on page {page_num + 1}: {error}")
                continue

            # Increment counter
            counter += 1

            # Save image using shared utility
            image_path, format_name = save_image(
                image_data,
                output_dir,
                base_name="img",
                extension=image_ext,
                counter=counter,
            )

            # Get image dimensions using shared utility
            width, height, detected_format = get_image_dimensions(image_data)
            if detected_format != "unknown":
                format_name = detected_format

            # Create ImageReference
            img_ref = ImageReference(
                image_id=f"img_{counter:04d}",
                position=page_num * 1000 + img_index,  # Approximate position
                file_path=str(image_path),
                alt_text=f"Image on page {page_num + 1}",
                size=(width, height) if width and height else None,
                format=format_name,
            )

            images.append(img_ref)

        except Exception as e:
            logger.warning(
                f"Failed to extract image {img_index} on page {page_num + 1}: {e}"
            )

    return images, counter
