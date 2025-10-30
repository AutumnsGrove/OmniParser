"""
HTML parser for OmniParser using Trafilatura with Readability fallback.

This module provides an HTML parser that can handle both local HTML files
and web URLs, extracting clean content while preserving structure and metadata.

Classes:
    HTMLParser: Parser for HTML files and URLs.
"""

# Standard library
import logging
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

# Third-party
import requests
import trafilatura
from readability import Document as ReadabilityDocument

# Local
from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, NetworkError, ParsingError
from ..models import Document, ImageReference, Metadata, ProcessingInfo
from ..processors.chapter_detector import detect_chapters
from ..processors.markdown_converter import html_to_markdown
from ..processors.metadata_extractor import extract_html_metadata
from .html.image_extractor import extract_images

logger = logging.getLogger(__name__)


class HTMLParser(BaseParser):
    """
    Parser for HTML files and URLs using Trafilatura with Readability fallback.

    Supports:
    - Local HTML files (.html, .htm)
    - Live URLs (HTTP/HTTPS) with timeout
    - Main content extraction (removes nav, ads, scripts)
    - Metadata extraction (OpenGraph, Dublin Core, standard meta)
    - Chapter detection based on headings
    - Image extraction with alt text
    - Readability-lxml fallback when Trafilatura fails

    Example:
        >>> parser = HTMLParser()
        >>> doc = parser.parse("article.html")
        >>> print(doc.metadata.title, len(doc.chapters))

        >>> doc = parser.parse("https://example.com/article")
        >>> print(doc.content[:100])
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize HTMLParser with rate limiting support.

        Args:
            options: Parser configuration dict including:
                - rate_limit_delay: Minimum seconds between requests (default: 0.0)
                - timeout: Request timeout in seconds (default: 10)
                - extract_images: Whether to extract images (default: True)
                - detect_chapters: Whether to detect chapters (default: True)
                - user_agent: Custom User-Agent string
                - max_image_workers: Max concurrent image downloads (default: 5)
        """
        super().__init__(options)
        self._last_request_time: float = 0.0
        self._rate_limit_lock = threading.Lock()

    def parse(self, file_path: Union[Path, str]) -> Document:
        """
        Parse HTML file or URL and return Document object.

        Args:
            file_path: Path to local HTML file or URL string.

        Returns:
            Document object with parsed content and metadata.

        Raises:
            NetworkError: If URL fetch fails.
            FileReadError: If local file cannot be read.
            ParsingError: If both Trafilatura and Readability fail.
        """
        start_time = time.time()
        warnings = []

        # Determine if URL or local file
        file_path_str = str(file_path)
        is_url = file_path_str.startswith("http://") or file_path_str.startswith(
            "https://"
        )

        # Fetch HTML content
        if is_url:
            html_content = self._fetch_url(file_path_str)
            source_identifier = file_path_str
        else:
            file_path_obj = Path(file_path) if isinstance(file_path, str) else file_path
            html_content = self._read_local_file(file_path_obj)
            source_identifier = str(file_path_obj.absolute())

        # Extract main content with Trafilatura
        extracted_html = self._extract_content_trafilatura(html_content)

        # Fallback to Readability if Trafilatura fails or returns too little
        if not extracted_html or len(extracted_html.strip()) < 100:
            if extracted_html and len(extracted_html.strip()) > 0:
                warnings.append(
                    "Trafilatura extraction returned minimal content, "
                    "using Readability fallback"
                )
            else:
                warnings.append(
                    "Trafilatura extraction failed, using Readability fallback"
                )

            extracted_html = self._extract_content_readability(html_content)

            # If both fail, raise error
            if not extracted_html or len(extracted_html.strip()) < 50:
                raise ParsingError(
                    "Both Trafilatura and Readability failed to extract content",
                    parser="HTMLParser",
                )

        # Build and return Document
        document = self._build_document(
            extracted_html, html_content, source_identifier, warnings
        )

        # Update processing time
        processing_time = time.time() - start_time
        document.processing_info.processing_time = processing_time

        return document

    def supports_format(self, file_path: Union[Path, str]) -> bool:
        """
        Check if this parser supports the file format.

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
            >>> parser = HTMLParser(rate_limit_delay=1.0)
            >>> parser._apply_rate_limit()  # First call returns immediately
            >>> parser._apply_rate_limit()  # Second call waits ~1 second
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

    def _fetch_url(self, url: str) -> str:
        """
        Fetch HTML content from URL.

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
            return cast(str, response.text)
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request timeout after {timeout} seconds: {url}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Failed to fetch URL: {url} - {str(e)}") from e

    def _read_local_file(self, file_path: Path) -> str:
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

    def _extract_content_trafilatura(self, html: str) -> Optional[str]:
        """
        Extract main content using Trafilatura.

        Args:
            html: HTML string to extract content from.

        Returns:
            Extracted HTML content or None if extraction fails.
        """
        try:
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=False,
                output_format="html",
            )
            return cast(Optional[str], extracted)
        except Exception:
            # Trafilatura can fail on malformed HTML
            return None

    def _extract_content_readability(self, html: str) -> str:
        """
        Extract main content using Readability as fallback.

        Args:
            html: HTML string to extract content from.

        Returns:
            Extracted HTML content.

        Raises:
            ParsingError: If Readability extraction fails.
        """
        try:
            doc = ReadabilityDocument(html)
            return cast(str, doc.summary())
        except Exception as e:
            raise ParsingError(
                f"Readability extraction failed: {str(e)}", parser="HTMLParser"
            ) from e

    def _build_document(
        self,
        content_html: str,
        original_html: str,
        source_identifier: str,
        warnings: list,
    ) -> Document:
        """
        Build Document object from extracted HTML.

        Args:
            content_html: Extracted HTML content.
            original_html: Original HTML (for metadata extraction).
            source_identifier: File path or URL.
            warnings: List of warnings from processing.

        Returns:
            Complete Document object.
        """
        # Convert HTML to Markdown
        markdown_content = html_to_markdown(content_html)

        # Extract metadata from original HTML (better meta tag access)
        url = source_identifier if source_identifier.startswith("http") else None
        metadata = extract_html_metadata(original_html, url=url)

        # Extract images from ORIGINAL HTML (before processing strips them)
        images: List[ImageReference] = []
        if self.options.get("extract_images", True):
            try:
                base_url = (
                    source_identifier if source_identifier.startswith("http") else None
                )
                images = extract_images(
                    original_html,
                    base_url=base_url,
                    options=self.options,
                    apply_rate_limit=self._apply_rate_limit,
                    build_headers=self._build_headers,
                )
                if images:
                    logger.info(f"Extracted {len(images)} images from HTML")
            except Exception as e:
                warning_msg = f"Image extraction failed: {str(e)}"
                warnings.append(warning_msg)
                logger.warning(warning_msg)

        # Detect chapters if enabled
        chapters = []
        if self.options.get("detect_chapters", True):
            min_level = self.options.get("min_chapter_level", 1)
            max_level = self.options.get("max_chapter_level", 2)
            chapters = detect_chapters(markdown_content, min_level, max_level)

        # Calculate word count and reading time
        word_count = len(markdown_content.split())
        estimated_reading_time = max(
            1, round(word_count / 225)
        )  # 225 WPM, minimum 1 minute

        # Create processing info
        processing_info = ProcessingInfo(
            parser_used="HTMLParser",
            parser_version="0.1.0",
            processing_time=0.0,  # Will be updated by caller
            timestamp=datetime.now(),
            warnings=warnings,
            options_used=dict(self.options),
        )

        # Generate document ID
        document_id = str(uuid.uuid4())

        # Build and return Document
        return Document(
            document_id=document_id,
            content=markdown_content,
            chapters=chapters,
            images=images,
            metadata=metadata,
            processing_info=processing_info,
            word_count=word_count,
            estimated_reading_time=estimated_reading_time,
        )
