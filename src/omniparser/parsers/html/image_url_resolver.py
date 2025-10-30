"""
URL resolution for image extraction.

This module handles resolution of relative image URLs to absolute URLs.

Functions:
    resolve_image_url: Resolve relative URLs to absolute URLs
"""

# Standard library
from typing import Optional
from urllib.parse import urljoin


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
