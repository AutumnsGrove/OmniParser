"""
Image extraction module for Markdown parser.

This module provides functions for extracting image references from Markdown
content. It handles both inline images and reference-style images, resolves
relative paths, and creates ImageReference objects with metadata.

Functions:
    extract_image_references: Extract all image references from markdown content
    resolve_image_path: Resolve relative image paths to absolute

Usage:
    >>> from pathlib import Path
    >>> content = "![alt text](image.png)\\n![photo](../images/photo.jpg)"
    >>> images = extract_image_references(content, Path("/docs/readme.md"))
    >>> print(f"Found {len(images)} images")
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from ...models import ImageReference

logger = logging.getLogger(__name__)

# Markdown image patterns
# Inline: ![alt text](image.png "optional title")
_IMAGE_INLINE_PATTERN = re.compile(
    r'!\[([^\]]*)\]\(([^\s\)]+)(?:\s+"([^"]*)")?\)', re.MULTILINE
)

# Reference-style: ![alt text][ref_id]
_IMAGE_REFERENCE_PATTERN = re.compile(r"!\[([^\]]*)\]\[([^\]]+)\]", re.MULTILINE)

# Reference definition: [ref_id]: url "optional title"
_REFERENCE_DEF_PATTERN = re.compile(
    r'^\[([^\]]+)\]:\s+([^\s]+)(?:\s+"([^"]*)")?', re.MULTILINE
)

# URL pattern to detect absolute URLs
_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

# Data URI pattern (base64 encoded images)
_DATA_URI_PATTERN = re.compile(r"^data:image/(\w+)", re.IGNORECASE)


def extract_image_references(content: str, file_path: Path) -> List[ImageReference]:
    """
    Extract all image references from markdown content.

    Supports:
    - Inline images: ![alt](path "title")
    - Reference-style images: ![alt][ref] with [ref]: path
    - URLs (http://, https://)
    - Data URIs (data:image/png;base64,...)
    - Relative paths (resolved relative to markdown file)
    - Absolute paths

    Process:
    1. Find all reference definitions ([ref]: path)
    2. Find all inline images
    3. Find all reference-style images
    4. Resolve relative paths
    5. Remove duplicates (keep first occurrence)
    6. Create ImageReference objects

    Args:
        content: Markdown content to extract images from.
        file_path: Path to source markdown file (for resolving relative paths).

    Returns:
        List of ImageReference objects with image metadata.

    Example:
        >>> content = "![Logo](logo.png)\\n![Icon](../icons/star.svg)"
        >>> images = extract_image_references(content, Path("docs/readme.md"))
        >>> print(f"Found {len(images)} images")
    """
    if not content:
        return []

    images: List[ImageReference] = []
    seen_paths: set[str] = set()  # Track unique paths
    counter = 0

    # Step 1: Parse reference definitions
    references = _parse_reference_definitions(content)
    logger.debug(f"Found {len(references)} reference definitions")

    # Step 2: Extract inline images
    for match in _IMAGE_INLINE_PATTERN.finditer(content):
        alt_text = match.group(1).strip() or None
        image_path = match.group(2).strip()
        title = match.group(3).strip() if match.group(3) else None
        position = match.start()

        # Resolve path
        resolved_path = resolve_image_path(image_path, file_path)

        # Skip duplicates
        if resolved_path in seen_paths:
            continue
        seen_paths.add(resolved_path)

        counter += 1
        image_ref = _create_image_reference(
            counter, resolved_path, position, alt_text or title
        )
        images.append(image_ref)
        logger.debug(f"Found inline image: {resolved_path}")

    # Step 3: Extract reference-style images
    for match in _IMAGE_REFERENCE_PATTERN.finditer(content):
        alt_text = match.group(1).strip() or None
        ref_id = match.group(2).strip()
        position = match.start()

        # Look up reference
        if ref_id.lower() not in references:
            logger.debug(f"Reference not found: {ref_id}")
            continue

        image_path, title = references[ref_id.lower()]

        # Resolve path
        resolved_path = resolve_image_path(image_path, file_path)

        # Skip duplicates
        if resolved_path in seen_paths:
            continue
        seen_paths.add(resolved_path)

        counter += 1
        image_ref = _create_image_reference(
            counter, resolved_path, position, alt_text or title
        )
        images.append(image_ref)
        logger.debug(f"Found reference-style image: {resolved_path}")

    logger.info(f"Extracted {len(images)} unique image references")
    return images


def resolve_image_path(image_path: str, markdown_file: Path) -> str:
    """
    Resolve image path to absolute path or URL.

    Handles:
    - URLs (http://, https://) -> return as-is
    - Data URIs (data:image/...) -> return as-is
    - Absolute paths -> return as-is
    - Relative paths -> resolve relative to markdown file directory

    Args:
        image_path: Image path from markdown (relative, absolute, or URL).
        markdown_file: Path to markdown file (used for resolving relative paths).

    Returns:
        Resolved path as string (absolute path or URL).

    Example:
        >>> resolve_image_path("logo.png", Path("/docs/readme.md"))
        '/docs/logo.png'
        >>> resolve_image_path("https://example.com/img.png", Path("/docs/readme.md"))
        'https://example.com/img.png'
        >>> resolve_image_path("../images/icon.svg", Path("/docs/guide/page.md"))
        '/docs/images/icon.svg'
    """
    # URLs: return as-is
    if _URL_PATTERN.match(image_path):
        return image_path

    # Data URIs: return as-is
    if _DATA_URI_PATTERN.match(image_path):
        return image_path

    # Convert to Path for resolution
    path = Path(image_path)

    # Absolute paths: return as string
    if path.is_absolute():
        return str(path)

    # Relative paths: resolve relative to markdown file directory
    markdown_dir = markdown_file.parent
    resolved = (markdown_dir / path).resolve()
    return str(resolved)


def _parse_reference_definitions(content: str) -> dict[str, tuple[str, Optional[str]]]:
    """
    Parse markdown reference definitions.

    Reference definition format:
    [ref_id]: url "optional title"

    Args:
        content: Markdown content.

    Returns:
        Dictionary mapping ref_id (lowercase) to (url, title) tuple.

    Example:
        >>> content = '[logo]: logo.png "Company Logo"\\n[icon]: icon.svg'
        >>> refs = _parse_reference_definitions(content)
        >>> refs['logo']
        ('logo.png', 'Company Logo')
    """
    references: dict[str, tuple[str, Optional[str]]] = {}

    for match in _REFERENCE_DEF_PATTERN.finditer(content):
        ref_id = match.group(1).strip().lower()
        url = match.group(2).strip()
        title = match.group(3).strip() if match.group(3) else None

        references[ref_id] = (url, title)

    return references


def _create_image_reference(
    counter: int, path: str, position: int, alt_text: Optional[str]
) -> ImageReference:
    """
    Create ImageReference object for markdown image.

    Args:
        counter: Image counter for unique ID.
        path: Resolved image path or URL.
        position: Character position in markdown content.
        alt_text: Alt text or title from markdown.

    Returns:
        ImageReference object with metadata.
    """
    # Extract format from path
    format_name = _extract_image_format(path)

    return ImageReference(
        image_id=f"img_{counter:03d}",
        position=position,
        file_path=path,
        alt_text=alt_text,
        size=None,  # Size not available without fetching/reading image
        format=format_name,
    )


def _extract_image_format(path: str) -> str:
    """
    Extract image format from path or URL.

    Handles:
    - Data URIs: data:image/png;base64,... -> png
    - Query parameters: image.jpg?format=webp -> webp
    - File extensions: image.png -> png
    - Unknown: -> unknown

    Args:
        path: Image path, URL, or data URI.

    Returns:
        Image format (e.g., 'png', 'jpg', 'svg') or 'unknown'.

    Example:
        >>> _extract_image_format("logo.png")
        'png'
        >>> _extract_image_format("data:image/jpeg;base64,...")
        'jpeg'
        >>> _extract_image_format("photo.jpg?w=800&format=webp")
        'webp'
    """
    # Data URIs
    data_match = _DATA_URI_PATTERN.match(path)
    if data_match:
        return data_match.group(1).lower()

    # Check for format in query parameters
    if "?" in path:
        query_part = path.split("?", 1)[1]
        format_match = re.search(r"(?:format|fmt)=(\w+)", query_part, re.IGNORECASE)
        if format_match:
            return format_match.group(1).lower()

    # Extract from file extension
    # Remove query parameters first
    clean_path = path.split("?")[0]
    # Get filename from path (handle URLs with /)
    filename = clean_path.split("/")[-1]

    if "." in filename:
        ext = filename.split(".")[-1].lower()
        # Common image extensions
        if ext in ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico", "tiff"]:
            return ext
        # Return extension even if not common
        return ext

    return "unknown"
