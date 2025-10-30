"""
HTML parser for OmniParser using Trafilatura with Readability fallback.

This module provides an HTML parser that can handle both local HTML files
and web URLs, extracting clean content while preserving structure and metadata.

Classes:
    HTMLParser: Parser for HTML files and URLs.
"""

# Standard library
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Local
from ...base.base_parser import BaseParser
from ...models import Document
from .content_extractor import extract_main_content
from .content_fetcher import ContentFetcher
from .document_builder import build_html_document
from .url_validator import is_url, supports_html_format

__all__ = ["HTMLParser"]

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
        self.content_fetcher = ContentFetcher(self.options)

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
        is_url_source = is_url(file_path)

        # Fetch HTML content
        if is_url_source:
            html_content = self.content_fetcher.fetch_url(file_path_str)
            source_identifier = file_path_str
        else:
            file_path_obj = Path(file_path) if isinstance(file_path, str) else file_path
            html_content = self.content_fetcher.read_file(file_path_obj)
            source_identifier = str(file_path_obj.absolute())

        # Extract main content (Trafilatura with Readability fallback)
        extracted_html, extraction_warnings = extract_main_content(
            html_content, self.options
        )
        warnings.extend(extraction_warnings)

        # Build and return Document
        document = build_html_document(
            content_html=extracted_html,
            full_html=html_content,
            source=source_identifier,
            warnings=warnings,
            options=self.options,
            apply_rate_limit=self.content_fetcher.apply_rate_limit,
            build_headers=self.content_fetcher.build_headers,
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
        return supports_html_format(file_path)
