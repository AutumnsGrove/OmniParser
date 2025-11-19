"""
PDF image extraction and processing.

This module provides functions for extracting images from PDF documents using
PyMuPDF (fitz). It handles image validation, filtering by size, saving to disk,
and creating ImageReference objects with metadata.

Functions:
    extract_pdf_images: Extract all images from a PDF document
    extract_page_images: Extract images from a single PDF page
    scan_pdf_for_qr_codes: Scan all PDF pages for QR codes
"""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

from ...models import ImageReference, QRCodeReference
from ...processors.image_extractor import (
    get_image_dimensions,
    save_image,
    validate_image_data,
)
from ...processors.qr_detector import detect_qr_codes_from_pil, is_qr_detection_available
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


def scan_pdf_for_qr_codes(
    doc: fitz.Document,
    dpi: int = 150,
) -> Tuple[List[QRCodeReference], List[str]]:
    """
    Scan all PDF pages for QR codes.

    Renders each page as an image and scans for QR codes. This method
    catches QR codes both in embedded images and rendered on pages.

    Args:
        doc: PyMuPDF document object.
        dpi: Resolution for page rendering (higher = more accurate but slower).

    Returns:
        Tuple of (list of QRCodeReference objects, list of warning messages).

    Example:
        >>> import fitz
        >>> doc = fitz.open("document.pdf")
        >>> qr_codes, warnings = scan_pdf_for_qr_codes(doc)
        >>> print(f"Found {len(qr_codes)} QR codes")
        >>> doc.close()
    """
    qr_codes: List[QRCodeReference] = []
    warnings: List[str] = []

    if not is_qr_detection_available():
        warnings.append(
            "QR detection unavailable: pyzbar not installed. "
            "Install with: pip install pyzbar"
        )
        return qr_codes, warnings

    # Calculate zoom factor for desired DPI (default PDF is 72 DPI)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    qr_counter = 0

    for page_num in range(len(doc)):
        try:
            page = doc[page_num]

            # Render page to pixmap
            pixmap = page.get_pixmap(matrix=matrix)

            # Convert to PIL Image
            img_data = pixmap.tobytes("png")
            pil_image = Image.open(BytesIO(img_data))

            # Scan for QR codes
            page_qr_codes, page_warnings = detect_qr_codes_from_pil(
                pil_image,
                source_image_id=f"page_{page_num + 1}",
                page_number=page_num + 1,
                qr_id_prefix=f"qr_p{page_num + 1}",
            )

            # Update QR IDs to be globally unique
            for qr in page_qr_codes:
                qr.qr_id = f"qr_{qr_counter:03d}"
                qr_counter += 1

            qr_codes.extend(page_qr_codes)
            warnings.extend(page_warnings)

            if page_qr_codes:
                logger.debug(
                    f"Found {len(page_qr_codes)} QR code(s) on page {page_num + 1}"
                )

        except Exception as e:
            warning_msg = f"QR scan failed for page {page_num + 1}: {str(e)}"
            warnings.append(warning_msg)
            logger.warning(warning_msg)

    logger.info(f"QR scan complete: found {len(qr_codes)} QR code(s)")
    return qr_codes, warnings
