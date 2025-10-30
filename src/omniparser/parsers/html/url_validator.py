"""
URL and format validation utilities for HTML parser.

This module provides validation functions to check if sources are supported
HTML formats or URLs.

Functions:
    supports_html_format: Check if source is a supported HTML format
    is_url: Check if source is an HTTP/HTTPS URL
"""

from pathlib import Path
from typing import Union
from urllib.parse import urlparse


def supports_html_format(file_path: Union[Path, str]) -> bool:
    """
    Check if source is a supported HTML format.

    Args:
        file_path: Path or URL to check.

    Returns:
        True if file is .html, .htm, or URL (http/https), False otherwise.
    """
    file_path_str = str(file_path).lower()

    # Check if URL
    if file_path_str.startswith("http://") or file_path_str.startswith("https://"):
        return True

    # Check file extension
    path_obj = Path(file_path_str)
    return path_obj.suffix.lower() in [".html", ".htm"]


def is_url(source: Union[Path, str]) -> bool:
    """
    Check if source is an HTTP/HTTPS URL.

    Uses urllib.parse for robust URL validation rather than simple
    string prefix checking.

    Args:
        source: Path or URL string to check.

    Returns:
        True if source is a valid HTTP(S) URL, False otherwise.

    Examples:
        >>> is_url("https://example.com")
        True
        >>> is_url("http://example.com/page")
        True
        >>> is_url("/path/to/file.html")
        False
        >>> is_url("ftp://example.com")
        False
    """
    try:
        result = urlparse(str(source))
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False
