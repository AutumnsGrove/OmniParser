"""
Image extraction module for HTML parser.

This module handles image extraction from HTML content, including:
- Parallel image downloads using ThreadPoolExecutor
- URL resolution (relative/absolute/protocol-relative)
- Image format detection using Pillow
- Alt text extraction
- Image dimensions extraction
- Thread-safe rate limiting support

Functions:
    extract_images: Main entry point for image extraction
    resolve_image_url: Resolve relative URLs to absolute URLs
    download_image: Download single image from URL
    get_image_format: Detect image format from file
"""

# Standard library
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

# Third-party
import requests
from bs4 import BeautifulSoup
from PIL import Image

# Local
from ...models import ImageReference

logger = logging.getLogger(__name__)


def extract_images(
    html: str,
    base_url: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    apply_rate_limit: Optional[Callable[[], None]] = None,
    build_headers: Optional[Callable[[], Dict[str, str]]] = None,
) -> List[ImageReference]:
    """
    Extract images from HTML content with parallel downloads.

    Features:
    - Find all <img> tags using BeautifulSoup
    - Download images from URLs in parallel using ThreadPoolExecutor
    - Handle relative image paths
    - Extract alt text
    - Get image dimensions (if possible)
    - Save to image_output_dir or temp directory
    - Generate sequential image IDs (img_001, img_002, etc.)
    - Thread-safe with rate limiting support

    Args:
        html: HTML content to extract images from.
        base_url: Base URL for resolving relative image paths (None for local files).
        options: Parser options dict containing:
            - image_output_dir: Directory to save images (None for temp dir)
            - max_image_workers: Max concurrent downloads (default: 5)
            - timeout: Request timeout in seconds (default: 10)
        apply_rate_limit: Callback function to apply rate limiting before requests
        build_headers: Callback function to build HTTP headers

    Returns:
        List of ImageReference objects.

    Example:
        >>> images = extract_images(html_content, base_url="https://example.com")
        >>> print(f"Found {len(images)} images")
    """
    images: List[ImageReference] = []
    options = options or {}

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")

    if not img_tags:
        logger.debug("No image tags found in HTML")
        return images

    # Set up output directory
    output_dir = options.get("image_output_dir")
    cleanup_temp = False

    if output_dir:
        # Persistent directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving images to persistent directory: {output_dir}")
    else:
        # Temporary directory
        output_dir = Path(tempfile.mkdtemp(prefix="omniparser_images_"))
        cleanup_temp = True
        logger.info(f"Saving images to temporary directory: {output_dir}")

    # Build list of download tasks (pre-process all img tags)
    download_tasks = []
    for idx, img_tag in enumerate(img_tags, start=1):
        try:
            # Get image source
            img_src = img_tag.get("src")
            if not img_src:
                logger.debug(f"Image {idx} has no src attribute, skipping")
                continue

            # Cast to string (BeautifulSoup returns str | AttributeValueList)
            img_src = str(img_src) if img_src else ""
            if not img_src:
                continue

            # Skip data URIs for now (inline base64 images)
            if img_src.startswith("data:"):
                logger.debug(f"Image {idx} is data URI, skipping")
                continue

            # Resolve image URL
            image_url = resolve_image_url(img_src, base_url)

            # Skip non-absolute URLs (local/relative paths)
            if not image_url.startswith(("http://", "https://")):
                logger.debug(
                    f"Image {idx} is local/relative reference, skipping: {img_src}"
                )
                continue

            # Determine file extension from URL
            parsed_url = urlparse(image_url)
            path_parts = parsed_url.path.split(".")
            extension = path_parts[-1].lower() if len(path_parts) > 1 else "jpg"

            # Limit extension to common formats
            if extension not in ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"]:
                extension = "jpg"

            # Extract alt text (cast to string)
            alt_text_raw = img_tag.get("alt")
            alt_text = str(alt_text_raw) if alt_text_raw else None

            # Add to download tasks
            download_tasks.append((image_url, extension, alt_text, idx))

        except Exception as e:
            logger.warning(f"Failed to process image {idx} metadata: {e}")
            continue

    if not download_tasks:
        logger.info("No downloadable images found")
        return images

    # Parallel download using ThreadPoolExecutor
    max_workers = options.get("max_image_workers", 5)
    logger.info(f"Downloading {len(download_tasks)} images with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_task = {}
        for task_idx, (image_url, extension, alt_text, original_idx) in enumerate(
            download_tasks, start=1
        ):
            # Generate output filename with sequential numbering
            output_filename = f"img_{task_idx:03d}.{extension}"
            output_path = output_dir / output_filename

            # Submit download task
            future = executor.submit(
                download_image,
                image_url,
                output_path,
                options,
                apply_rate_limit,
                build_headers,
            )
            future_to_task[future] = (
                task_idx,
                output_path,
                alt_text,
                original_idx,
                image_url,
            )

        # Collect results as they complete
        for future in as_completed(future_to_task):
            task_idx, output_path, alt_text, original_idx, image_url = future_to_task[
                future
            ]
            try:
                dimensions = future.result()
                if dimensions is None:
                    logger.warning(f"Failed to download image {task_idx}: {image_url}")
                    continue

                # Get image format
                img_format = get_image_format(output_path)

                # Create ImageReference
                image_ref = ImageReference(
                    image_id=f"img_{task_idx:03d}",
                    position=task_idx * 100,  # Simple sequential spacing
                    file_path=str(output_path),
                    alt_text=alt_text,
                    size=dimensions,
                    format=img_format,
                )

                images.append(image_ref)
                logger.debug(
                    f"Extracted image {task_idx}: {output_path.name} "
                    f"({img_format}, {dimensions})"
                )

            except Exception as e:
                logger.warning(f"Failed to process image {task_idx}: {e}")
                continue

    # Sort images by image_id to ensure consistent ordering
    images.sort(key=lambda img: img.image_id)

    logger.info(f"Successfully extracted {len(images)} images")
    return images


def resolve_image_url(img_src: str, base_url: Optional[str]) -> str:
    """
    Resolve relative image URLs to absolute URLs.

    Handles:
    - Absolute URLs: return as-is
    - Relative URLs with base_url: join with base_url
    - Protocol-relative URLs (//example.com/img.jpg)
    - Data URIs: return as-is (skip download)

    Args:
        img_src: Image src attribute value.
        base_url: Base URL from parsed page (None for local files).

    Returns:
        Resolved absolute URL or original src.

    Example:
        >>> url = resolve_image_url("/images/photo.jpg", "https://example.com/page")
        >>> print(url)
        https://example.com/images/photo.jpg
    """
    # Data URIs - return as-is
    if img_src.startswith("data:"):
        return img_src

    # Absolute URLs - return as-is
    if img_src.startswith("http://") or img_src.startswith("https://"):
        return img_src

    # Protocol-relative URLs
    if img_src.startswith("//"):
        # Use https by default
        return f"https:{img_src}"

    # Relative URLs - need base_url
    if base_url:
        return urljoin(base_url, img_src)

    # No base_url - return as-is (will fail download but logged)
    return img_src


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
        options: Parser options dict containing timeout setting
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
    headers = build_headers() if build_headers else {}

    try:
        # Download image
        response = requests.get(
            image_url, timeout=timeout, headers=headers, stream=True
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
