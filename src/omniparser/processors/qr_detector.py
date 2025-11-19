"""
QR code detection processor for OmniParser.

This module provides QR code detection capabilities using pyzbar as the primary
backend, with stubs for alternative backends (opencv, zxing) for future expansion.

Functions:
    detect_qr_codes: Detect QR codes in an image.
    classify_qr_data: Classify the type of data encoded in a QR code.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image

from omniparser.models import QRCodeReference

logger = logging.getLogger(__name__)

# Try to import pyzbar
try:
    from pyzbar import pyzbar
    from pyzbar.pyzbar import Decoded

    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    logger.warning(
        "pyzbar not available. QR code detection will be disabled. "
        "Install with: pip install pyzbar (also requires zbar system library)"
    )


def _process_pyzbar_results(
    decoded_objects: List,
    source_image_id: Optional[str],
    page_number: Optional[int],
    qr_id_prefix: str,
) -> Tuple[List[QRCodeReference], List[str]]:
    """Process decoded pyzbar objects into QRCodeReference objects.

    This is a shared helper function used by both detect_qr_codes()
    and detect_qr_codes_from_pil() to avoid code duplication.

    Args:
        decoded_objects: List of decoded objects from pyzbar.decode().
        source_image_id: Optional ID of the source image for reference.
        page_number: Optional page number where image was found.
        qr_id_prefix: Prefix for generated QR code IDs.

    Returns:
        Tuple of (list of QRCodeReference objects, list of warning messages).
    """
    warnings: List[str] = []
    qr_codes: List[QRCodeReference] = []

    for idx, obj in enumerate(decoded_objects):
        # Only process QR codes (not barcodes)
        if obj.type != "QRCODE":
            continue

        # Extract raw data
        try:
            raw_data = obj.data.decode("utf-8")
        except UnicodeDecodeError:
            raw_data = obj.data.decode("latin-1")
            warnings.append(
                f"QR code {idx} contained non-UTF-8 data, decoded as latin-1"
            )

        # Get position/bounding box
        rect = obj.rect
        position = {
            "x": rect.left,
            "y": rect.top,
            "width": rect.width,
            "height": rect.height,
        }

        # Classify data type
        data_type = classify_qr_data(raw_data)

        # Create QR code reference
        qr_ref = QRCodeReference(
            qr_id=f"{qr_id_prefix}_{idx:03d}",
            raw_data=raw_data,
            data_type=data_type,
            source_image=source_image_id,
            position=position,
            page_number=page_number,
            fetch_status="pending" if data_type == "URL" else "skipped",
            fetch_notes=[],
        )

        qr_codes.append(qr_ref)
        logger.debug(f"Detected QR code: {data_type} - {raw_data[:50]}...")

    return qr_codes, warnings


def detect_qr_codes(
    image_data: bytes,
    source_image_id: Optional[str] = None,
    page_number: Optional[int] = None,
    qr_id_prefix: str = "qr",
) -> Tuple[List[QRCodeReference], List[str]]:
    """Detect QR codes in an image.

    Args:
        image_data: Raw image bytes (PNG, JPG, etc.).
        source_image_id: Optional ID of the source image for reference.
        page_number: Optional page number where image was found.
        qr_id_prefix: Prefix for generated QR code IDs.

    Returns:
        Tuple of (list of QRCodeReference objects, list of warning messages).

    Example:
        >>> with open("image.png", "rb") as f:
        ...     image_data = f.read()
        >>> qr_codes, warnings = detect_qr_codes(image_data)
        >>> for qr in qr_codes:
        ...     print(f"Found QR: {qr.raw_data}")
    """
    warnings: List[str] = []
    qr_codes: List[QRCodeReference] = []

    if not PYZBAR_AVAILABLE:
        warnings.append(
            "QR detection unavailable: pyzbar not installed. "
            "Install with: pip install pyzbar"
        )
        return qr_codes, warnings

    try:
        # Load image from bytes
        from io import BytesIO

        image = Image.open(BytesIO(image_data))

        # Convert to RGB if necessary (pyzbar works best with RGB/grayscale)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Detect QR codes using pyzbar
        decoded_objects = pyzbar.decode(image)

        # Process results using shared helper
        qr_codes, process_warnings = _process_pyzbar_results(
            decoded_objects, source_image_id, page_number, qr_id_prefix
        )
        warnings.extend(process_warnings)

    except Exception as e:
        warnings.append(f"QR detection failed: {str(e)}")
        logger.error(f"QR detection error: {e}", exc_info=True)

    return qr_codes, warnings


def detect_qr_codes_from_pil(
    image: Image.Image,
    source_image_id: Optional[str] = None,
    page_number: Optional[int] = None,
    qr_id_prefix: str = "qr",
) -> Tuple[List[QRCodeReference], List[str]]:
    """Detect QR codes from a PIL Image object.

    Args:
        image: PIL Image object.
        source_image_id: Optional ID of the source image for reference.
        page_number: Optional page number where image was found.
        qr_id_prefix: Prefix for generated QR code IDs.

    Returns:
        Tuple of (list of QRCodeReference objects, list of warning messages).
    """
    warnings: List[str] = []
    qr_codes: List[QRCodeReference] = []

    if not PYZBAR_AVAILABLE:
        warnings.append(
            "QR detection unavailable: pyzbar not installed. "
            "Install with: pip install pyzbar"
        )
        return qr_codes, warnings

    try:
        # Convert to RGB if necessary
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Detect QR codes using pyzbar
        decoded_objects = pyzbar.decode(image)

        # Process results using shared helper
        qr_codes, process_warnings = _process_pyzbar_results(
            decoded_objects, source_image_id, page_number, qr_id_prefix
        )
        warnings.extend(process_warnings)

    except Exception as e:
        warnings.append(f"QR detection failed: {str(e)}")
        logger.error(f"QR detection error: {e}", exc_info=True)

    return qr_codes, warnings


def classify_qr_data(data: str) -> str:
    """Classify the type of data encoded in a QR code.

    Args:
        data: Raw string data from QR code.

    Returns:
        Data type classification (URL, EMAIL, PHONE, WIFI, VCARD, GEO, TEXT).

    Example:
        >>> classify_qr_data("https://example.com")
        'URL'
        >>> classify_qr_data("Hello World")
        'TEXT'
    """
    data_stripped = data.strip()

    # URL patterns
    url_pattern = re.compile(
        r"^(https?://|www\.|ftp://)", re.IGNORECASE
    )
    if url_pattern.match(data_stripped):
        return "URL"

    # Email pattern (mailto: or plain email)
    if data_stripped.lower().startswith("mailto:"):
        return "EMAIL"
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if email_pattern.match(data_stripped):
        return "EMAIL"

    # Phone pattern (tel:)
    if data_stripped.lower().startswith("tel:"):
        return "PHONE"

    # WiFi configuration
    if data_stripped.upper().startswith("WIFI:"):
        return "WIFI"

    # vCard
    if data_stripped.upper().startswith("BEGIN:VCARD"):
        return "VCARD"

    # Geographic location
    if data_stripped.lower().startswith("geo:"):
        return "GEO"

    # SMS
    if data_stripped.lower().startswith("sms:") or data_stripped.lower().startswith("smsto:"):
        return "SMS"

    # Default to text
    return "TEXT"


def is_qr_detection_available() -> bool:
    """Check if QR code detection is available.

    Returns:
        True if pyzbar is installed and functional, False otherwise.
    """
    return PYZBAR_AVAILABLE


# Stub for future OpenCV backend
def _detect_qr_codes_opencv(
    image_data: bytes,
) -> Tuple[List[QRCodeReference], List[str]]:
    """OpenCV-based QR detection (stub for future implementation).

    Args:
        image_data: Raw image bytes.

    Returns:
        Tuple of (empty list, warning message).
    """
    return [], ["OpenCV QR detection not yet implemented"]


# Stub for future ZXing backend
def _detect_qr_codes_zxing(
    image_data: bytes,
) -> Tuple[List[QRCodeReference], List[str]]:
    """ZXing-based QR detection (stub for future implementation).

    Args:
        image_data: Raw image bytes.

    Returns:
        Tuple of (empty list, warning message).
    """
    return [], ["ZXing QR detection not yet implemented"]


def detect_qr_codes_from_file(
    file_path: Union[str, Path],
    qr_id_prefix: str = "qr",
) -> Tuple[List[QRCodeReference], List[str]]:
    """Detect QR codes from an image file.

    Supports common image formats: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF.

    Args:
        file_path: Path to image file.
        qr_id_prefix: Prefix for generated QR code IDs.

    Returns:
        Tuple of (list of QRCodeReference objects, list of warning messages).

    Example:
        >>> qr_codes, warnings = detect_qr_codes_from_file("image.png")
        >>> for qr in qr_codes:
        ...     print(f"Found: {qr.raw_data}")
    """
    warnings: List[str] = []
    qr_codes: List[QRCodeReference] = []

    file_path = Path(file_path)

    if not file_path.exists():
        warnings.append(f"File not found: {file_path}")
        return qr_codes, warnings

    # Check file extension
    supported_formats = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
    if file_path.suffix.lower() not in supported_formats:
        warnings.append(
            f"Unsupported image format: {file_path.suffix}. "
            f"Supported: {', '.join(supported_formats)}"
        )
        return qr_codes, warnings

    try:
        # Load image
        with open(file_path, "rb") as f:
            image_data = f.read()

        # Detect QR codes
        qr_codes, detect_warnings = detect_qr_codes(
            image_data,
            source_image_id=file_path.name,
            qr_id_prefix=qr_id_prefix,
        )

        warnings.extend(detect_warnings)

    except Exception as e:
        warnings.append(f"Failed to process image {file_path}: {str(e)}")
        logger.error(f"Image processing error: {e}")

    return qr_codes, warnings


def scan_image_for_qr_and_fetch(
    file_path: Union[str, Path],
    fetch_urls: bool = True,
    timeout: int = 15,
) -> Tuple[List[QRCodeReference], List[str]]:
    """Scan an image file for QR codes and optionally fetch URL content.

    Convenience function that combines QR detection with URL fetching.

    Args:
        file_path: Path to image file.
        fetch_urls: Whether to fetch content from URL QR codes.
        timeout: Request timeout for URL fetching.

    Returns:
        Tuple of (list of processed QRCodeReference objects, list of warnings).

    Example:
        >>> qr_codes, warnings = scan_image_for_qr_and_fetch("recipe_qr.png")
        >>> for qr in qr_codes:
        ...     if qr.fetched_content:
        ...         print(f"Content from {qr.raw_data}:")
        ...         print(qr.fetched_content[:200])
    """
    # Import here to avoid circular imports
    from omniparser.processors.qr_content_merger import process_qr_codes

    qr_codes, warnings = detect_qr_codes_from_file(file_path)

    if qr_codes and fetch_urls:
        qr_codes = process_qr_codes(qr_codes, fetch_urls=True, timeout=timeout)

    return qr_codes, warnings
