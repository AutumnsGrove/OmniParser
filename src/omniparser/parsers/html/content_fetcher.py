"""
Content fetching functionality for HTML parser.

This module handles fetching HTML content from URLs and reading local files,
with thread-safe rate limiting support.

Classes:
    ContentFetcher: Handles URL fetching and local file reading with rate limiting.
"""

# Standard library
import threading
import time
from pathlib import Path
from typing import Any, Dict

# Third-party
import requests

# Local
from ...exceptions import FileReadError, NetworkError


class ContentFetcher:
    """
    Handles fetching HTML content from URLs and reading local files.

    Features:
    - Thread-safe rate limiting for HTTP requests
    - Configurable User-Agent header
    - Request timeout support
    - Proper error handling for network and file operations

    Example:
        >>> fetcher = ContentFetcher({"rate_limit_delay": 1.0, "timeout": 10})
        >>> html = fetcher.fetch_url("https://example.com")
        >>> local_html = fetcher.read_file(Path("page.html"))
    """

    def __init__(self, options: Dict[str, Any]):
        """
        Initialize ContentFetcher with rate limiting.

        Args:
            options: Configuration dict including:
                - rate_limit_delay: Minimum seconds between requests (default: 0.0)
                - timeout: Request timeout in seconds (default: 10)
                - user_agent: Custom User-Agent string
        """
        self.options = options
        self._last_request_time: float = 0.0
        self._rate_limit_lock = threading.Lock()

    def fetch_url(self, url: str) -> str:
        """
        Fetch HTML content from URL with rate limiting.

        Args:
            url: URL to fetch.

        Returns:
            HTML content as string.

        Raises:
            NetworkError: If fetch fails or times out.
        """
        self._apply_rate_limit()
        timeout = self.options.get("timeout", 10)
        headers = self._build_headers()

        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request timeout after {timeout} seconds: {url}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Failed to fetch URL: {url} - {str(e)}") from e

    def read_file(self, file_path: Path) -> str:
        """
        Read HTML content from local file.

        Args:
            file_path: Path to local HTML file.

        Returns:
            HTML content as string.

        Raises:
            FileReadError: If file doesn't exist or cannot be read.
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise FileReadError(f"File not found: {file_path}") from e
        except PermissionError as e:
            raise FileReadError(f"Permission denied: {file_path}") from e
        except Exception as e:
            raise FileReadError(f"Failed to read file: {file_path} - {str(e)}") from e

    def _build_headers(self) -> Dict[str, str]:
        """
        Build HTTP headers for requests.

        Returns:
            Dictionary of HTTP headers including User-Agent.
        """
        user_agent = self.options.get(
            "user_agent",
            "OmniParser/0.2.1 (+https://github.com/AutumnsGrove/omniparser)",
        )
        return {"User-Agent": user_agent}

    def _apply_rate_limit(self) -> None:
        """
        Apply rate limiting by enforcing minimum delay between requests.

        Thread-safe implementation using a lock to coordinate across parallel downloads.
        Respects the 'rate_limit_delay' option (default: 0.0 = no rate limiting).

        The method uses a lock to ensure thread safety when multiple images are being
        downloaded in parallel. It calculates the elapsed time since the last request
        and sleeps if necessary to enforce the minimum delay.

        Example:
            >>> fetcher = ContentFetcher({"rate_limit_delay": 1.0})
            >>> fetcher._apply_rate_limit()  # First call returns immediately
            >>> fetcher._apply_rate_limit()  # Second call waits ~1 second
        """
        rate_limit_delay = self.options.get("rate_limit_delay", 0.0)

        if rate_limit_delay <= 0:
            return

        with self._rate_limit_lock:
            current_time = time.time()
            elapsed = current_time - self._last_request_time

            if elapsed < rate_limit_delay:
                sleep_time = rate_limit_delay - elapsed
                time.sleep(sleep_time)

            self._last_request_time = time.time()
