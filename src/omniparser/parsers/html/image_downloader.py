"""
Image downloading and format detection for HTML parser.

This module handles downloading images from URLs and detecting their formats.

Functions:
    download_image: Download single image from URL
    get_image_format: Detect image format from file
"""

# Standard library
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

# Third-party
import requests
from PIL import Image

logger = logging.getLogger(__name__)


def download_image(
    image_url: str,
    output_path: Path,
    options: Optional[Dict[str, Any]] = None,
    apply_rate_limit: Optional[Callable[[], None]] = None,
    build_headers: Optional[Callable[[], Dict[str, str]]] = None,
) -> Optional[Tuple[int, int]]:
    """
    Download image from URL and save to output path.

    Features:
    - Use requests to download image
    - Timeout: use same timeout as HTML fetching
    - Use Pillow to get image dimensions
    - Handle download errors gracefully (log warning, return None)
    - Return image dimensions (width, height)

    Args:
        image_url: URL to download image from.
        output_path: Path to save downloaded image.
        options: Parser options dict containing timeout and verify_ssl settings
        apply_rate_limit: Callback function to apply rate limiting before request
        build_headers: Callback function to build HTTP headers

    Returns:
        Tuple of (width, height) if successful, None if failed.

    Example:
        >>> dims = download_image("https://example.com/image.jpg", Path("/tmp/img.jpg"))
        >>> if dims:
        ...     print(f"Image dimensions: {dims[0]}x{dims[1]}")
    """
    options = options or {}

    # Apply rate limiting if callback provided
    if apply_rate_limit:
        apply_rate_limit()

    timeout = options.get("timeout", 10)
    verify_ssl = options.get("verify_ssl", True)
    headers = build_headers() if build_headers else {}

    try:
        # Download image
        response = requests.get(
            image_url, timeout=timeout, headers=headers, stream=True, verify=verify_ssl
        )
        response.raise_for_status()

        # Save to file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Get dimensions using Pillow
        try:
            with Image.open(output_path) as img:
                width, height = img.size
                return (width, height)
        except Exception as e:
            logger.warning(f"Could not read image dimensions: {e}")
            # Image was downloaded but dimensions unknown
            return None

    except requests.exceptions.Timeout:
        logger.warning(f"Download timeout for image: {image_url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to download image {image_url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error processing image {image_url}: {e}")
        return None


def get_image_format(file_path: Path) -> str:
    """
    Detect image format from file.

    Uses Pillow to detect format (JPEG, PNG, GIF, WebP, etc.)

    Args:
        file_path: Path to image file.

    Returns:
        Image format string (lowercase, e.g., "jpeg", "png").

    Example:
        >>> format = get_image_format(Path("/tmp/image.jpg"))
        >>> print(format)
        jpeg
    """
    try:
        with Image.open(file_path) as img:
            return img.format.lower() if img.format else "unknown"
    except Exception as e:
        logger.warning(f"Could not detect image format for {file_path}: {e}")
        return "unknown"
