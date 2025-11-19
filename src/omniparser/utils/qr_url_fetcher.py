"""
URL fetcher utility for QR code content retrieval.

This module provides URL fetching capabilities with aggressive redirect following,
URL pattern variations, and Wayback Machine fallback for retrieving content
from QR code URLs.

Functions:
    fetch_url_content: Fetch content from a URL with fallback strategies.
    try_url_variations: Try common URL pattern variations.
    fetch_from_wayback: Fetch content from Wayback Machine archive.
"""

import ipaddress
import logging
import re
import socket
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 15  # seconds
MAX_REDIRECTS = 10
MAX_CONTENT_LENGTH = 500000  # 500KB max content
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Private/reserved IP ranges to block (SSRF prevention)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),        # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),     # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),    # Private Class C
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local (includes cloud metadata)
    ipaddress.ip_network("0.0.0.0/8"),         # Current network
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]


def _is_safe_url(
    url: str,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """Validate that a URL is safe to fetch (SSRF prevention).

    Checks against:
    - Private IP ranges (10.x, 172.16-31.x, 192.168.x)
    - Localhost addresses (127.x, localhost, ::1)
    - Cloud metadata endpoints (169.254.169.254)
    - Link-local addresses
    - Non-HTTP schemes (file://, etc.)

    Args:
        url: URL to validate.
        allowed_domains: Optional list of allowed domains. If provided, only these
            domains are allowed.
        blocked_domains: Optional list of blocked domains.

    Returns:
        Tuple of (is_safe, reason). If not safe, reason explains why.

    Example:
        >>> is_safe, reason = _is_safe_url("https://example.com")
        >>> print(f"Safe: {is_safe}")
        Safe: True
        >>> is_safe, reason = _is_safe_url("http://169.254.169.254/metadata")
        >>> print(f"Safe: {is_safe}, Reason: {reason}")
        Safe: False, Reason: IP address is in blocked range (link-local/metadata)
    """
    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            return False, f"Blocked scheme: {parsed.scheme}"

        hostname = parsed.hostname
        if not hostname:
            return False, "No hostname in URL"

        # Check blocked domains list
        if blocked_domains:
            for blocked in blocked_domains:
                if hostname == blocked or hostname.endswith(f".{blocked}"):
                    return False, f"Domain is in blocklist: {hostname}"

        # Check allowed domains list (if provided, only these are allowed)
        if allowed_domains:
            is_allowed = False
            for allowed in allowed_domains:
                if hostname == allowed or hostname.endswith(f".{allowed}"):
                    is_allowed = True
                    break
            if not is_allowed:
                return False, f"Domain not in allowlist: {hostname}"

        # Resolve hostname to IP address(es)
        try:
            # Get all IP addresses for the hostname
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            ip_addresses = set()
            for info in addr_info:
                ip_str = info[4][0]
                ip_addresses.add(ip_str)
        except socket.gaierror as e:
            return False, f"DNS resolution failed: {e}"

        # Check each resolved IP against blocked ranges
        for ip_str in ip_addresses:
            try:
                ip_addr = ipaddress.ip_address(ip_str)
                for network in BLOCKED_IP_NETWORKS:
                    if ip_addr in network:
                        return False, f"IP address {ip_str} is in blocked range ({network})"
            except ValueError:
                # Invalid IP address format, skip
                continue

        return True, "URL is safe"

    except Exception as e:
        return False, f"URL validation error: {e}"


@dataclass
class FetchResult:
    """Result of URL fetch operation.

    Attributes:
        success: Whether content was successfully retrieved.
        content: Extracted text content (if successful).
        status: Status of fetch (success, partial, failed).
        notes: List of notes about the fetch process.
        final_url: Final URL after redirects.
        source: Source of content (original, variation, wayback).
    """

    success: bool
    content: Optional[str] = None
    status: str = "failed"
    notes: List[str] = field(default_factory=list)
    final_url: Optional[str] = None
    source: str = "original"


def fetch_url_content(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    try_variations: bool = True,
    try_wayback: bool = True,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
) -> FetchResult:
    """Fetch content from a URL with multiple fallback strategies.

    Attempts to fetch content using:
    1. Original URL with aggressive redirect following
    2. Common URL variations (print versions, mobile, etc.)
    3. Wayback Machine archive (last resort)

    Includes SSRF protection to block requests to private networks,
    localhost, and cloud metadata endpoints.

    Args:
        url: URL to fetch content from.
        timeout: Request timeout in seconds.
        try_variations: Whether to try URL pattern variations.
        try_wayback: Whether to fall back to Wayback Machine.
        allowed_domains: Optional list of allowed domains. If provided, only
            these domains can be fetched.
        blocked_domains: Optional list of blocked domains.

    Returns:
        FetchResult with content and status information.

    Example:
        >>> result = fetch_url_content("https://example.com/recipe")
        >>> if result.success:
        ...     print(result.content)
        ... else:
        ...     print(f"Failed: {result.notes}")
    """
    result = FetchResult(success=False, notes=[])

    # Normalize URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # SSRF protection: validate URL before fetching
    is_safe, reason = _is_safe_url(url, allowed_domains, blocked_domains)
    if not is_safe:
        logger.warning(f"URL blocked by security check: {url} - {reason}")
        result.notes.append(f"Security block: {reason}")
        result.status = "blocked"
        return result

    # Try original URL first
    logger.info(f"Fetching URL: {url}")
    fetch_result = _fetch_single_url(url, timeout)

    if fetch_result.success:
        return fetch_result

    result.notes.extend(fetch_result.notes)

    # Try URL variations
    if try_variations:
        variations = _generate_url_variations(url)
        for var_url in variations:
            # SSRF check for variation URLs
            is_safe, reason = _is_safe_url(var_url, allowed_domains, blocked_domains)
            if not is_safe:
                result.notes.append(f"Variation {var_url} blocked: {reason}")
                continue

            logger.debug(f"Trying variation: {var_url}")
            var_result = _fetch_single_url(var_url, timeout)
            if var_result.success:
                var_result.notes.insert(0, f"Original URL failed, used variation")
                var_result.source = "variation"
                return var_result
            result.notes.append(f"Variation {var_url} failed")

    # Try Wayback Machine as last resort
    if try_wayback:
        logger.info(f"Trying Wayback Machine for: {url}")
        wayback_result = fetch_from_wayback(url, timeout)
        if wayback_result.success:
            wayback_result.notes.insert(
                0, "Original URL unavailable, retrieved from Wayback Machine"
            )
            return wayback_result
        result.notes.extend(wayback_result.notes)

    result.status = "failed"
    result.notes.append("All fetch attempts failed")
    return result


def _fetch_single_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> FetchResult:
    """Fetch content from a single URL with redirect following.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        FetchResult with content and status.
    """
    result = FetchResult(success=False, notes=[])

    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # Session for cookie handling
        session = requests.Session()
        session.max_redirects = MAX_REDIRECTS

        response = session.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )

        # Track redirects
        if response.history:
            redirect_count = len(response.history)
            result.notes.append(f"Followed {redirect_count} redirect(s)")

        result.final_url = response.url

        # Check response status
        if response.status_code != 200:
            result.notes.append(f"HTTP {response.status_code}: {response.reason}")
            return result

        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            result.notes.append(f"Unexpected content type: {content_type}")
            # Still try to extract text

        # Read content with size limit
        content_chunks = []
        content_length = 0
        for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
            if chunk:
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8", errors="replace")
                content_chunks.append(chunk)
                content_length += len(chunk)
                if content_length > MAX_CONTENT_LENGTH:
                    result.notes.append(
                        f"Content truncated at {MAX_CONTENT_LENGTH} bytes"
                    )
                    break

        raw_content = "".join(content_chunks)

        # Extract text from HTML
        text_content = _extract_text_from_html(raw_content)

        if text_content and len(text_content.strip()) > 50:
            result.success = True
            result.content = text_content
            result.status = "success"
        else:
            result.notes.append("No meaningful content extracted")
            result.status = "partial"
            result.content = text_content if text_content else None

    except requests.exceptions.TooManyRedirects:
        result.notes.append(f"Too many redirects (max {MAX_REDIRECTS})")
    except requests.exceptions.Timeout:
        result.notes.append(f"Request timed out after {timeout}s")
    except requests.exceptions.ConnectionError as e:
        result.notes.append(f"Connection error: {str(e)[:100]}")
    except requests.exceptions.RequestException as e:
        result.notes.append(f"Request failed: {str(e)[:100]}")
    except Exception as e:
        result.notes.append(f"Unexpected error: {str(e)[:100]}")
        logger.error(f"Fetch error for {url}: {e}")

    return result


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML content.

    Args:
        html: Raw HTML string.

    Returns:
        Cleaned text content.
    """
    try:
        soup = BeautifulSoup(html, "lxml")

        # Remove script, style, and other non-content elements
        for element in soup(
            ["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]
        ):
            element.decompose()

        # Try to find main content
        main_content = None
        for selector in ["main", "article", '[role="main"]', ".content", "#content"]:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            # Fall back to body
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]
        text = "\n".join(lines)

        return text

    except Exception as e:
        logger.error(f"HTML extraction error: {e}")
        return ""


def _generate_url_variations(url: str) -> List[str]:
    """Generate common URL variations to try.

    Args:
        url: Original URL.

    Returns:
        List of URL variations to try.
    """
    variations = []
    parsed = urlparse(url)

    # Try print version
    if "/print" not in parsed.path:
        print_url = url.replace(parsed.path, parsed.path.rstrip("/") + "/print")
        variations.append(print_url)

    # Try removing tracking parameters
    if parsed.query:
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        variations.append(clean_url)

    # Try mobile version
    if not parsed.netloc.startswith("m."):
        mobile_url = url.replace(parsed.netloc, "m." + parsed.netloc)
        variations.append(mobile_url)

    # Try amp version
    if "/amp" not in parsed.path and "amp." not in parsed.netloc:
        amp_url = url.replace(parsed.path, parsed.path.rstrip("/") + "/amp")
        variations.append(amp_url)

    return variations


def fetch_from_wayback(url: str, timeout: int = DEFAULT_TIMEOUT) -> FetchResult:
    """Fetch content from Wayback Machine archive.

    Args:
        url: Original URL to look up in archive.
        timeout: Request timeout in seconds.

    Returns:
        FetchResult with archived content.
    """
    result = FetchResult(success=False, notes=[], source="wayback")

    try:
        # Query Wayback Machine availability API
        api_url = f"https://archive.org/wayback/available?url={url}"

        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        snapshots = data.get("archived_snapshots", {})
        closest = snapshots.get("closest", {})

        if not closest or not closest.get("available"):
            result.notes.append("No Wayback Machine snapshot available")
            return result

        # Get the archived URL
        archive_url = closest.get("url", "")
        if not archive_url:
            result.notes.append("Wayback Machine snapshot URL not found")
            return result

        # Fetch the archived content
        archive_timestamp = closest.get("timestamp", "unknown")
        result.notes.append(f"Using Wayback snapshot from {archive_timestamp}")

        archived_result = _fetch_single_url(archive_url, timeout)

        if archived_result.success:
            result.success = True
            result.content = archived_result.content
            result.status = "success"
            result.final_url = archive_url
            result.notes.extend(archived_result.notes)
        else:
            result.notes.append("Failed to fetch Wayback snapshot")
            result.notes.extend(archived_result.notes)

    except requests.exceptions.RequestException as e:
        result.notes.append(f"Wayback API error: {str(e)[:100]}")
    except Exception as e:
        result.notes.append(f"Wayback lookup failed: {str(e)[:100]}")
        logger.error(f"Wayback error for {url}: {e}")

    return result


def normalize_url(url: str) -> str:
    """Normalize a URL for consistent handling.

    Args:
        url: URL string to normalize.

    Returns:
        Normalized URL with scheme.
    """
    url = url.strip()

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        if url.startswith("www."):
            url = "https://" + url
        else:
            url = "https://" + url

    return url
