"""
HTML parser for OmniParser using Trafilatura with Readability fallback.

This module provides an HTML parser that can handle both local HTML files
and web URLs, extracting clean content while preserving structure and metadata.

Classes:
    HTMLParser: Parser for HTML files and URLs.
"""

import logging
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urljoin, urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup
from PIL import Image
from readability import Document as ReadabilityDocument

from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, NetworkError, ParsingError
from ..models import Document, ImageReference, Metadata, ProcessingInfo
from ..processors.chapter_detector import detect_chapters
from ..processors.markdown_converter import html_to_markdown
from ..processors.metadata_extractor import extract_html_metadata

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
            "OmniParser/0.2.0 (+https://github.com/AutumnsGrove/omniparser)",
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
                images = self._extract_images(original_html, base_url=base_url)
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

    def _extract_images(
        self, html: str, base_url: Optional[str] = None
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

        Returns:
            List of ImageReference objects.

        Example:
            >>> parser = HTMLParser()
            >>> images = parser._extract_images(html_content, base_url="https://example.com")
            >>> print(f"Found {len(images)} images")
        """
        images: List[ImageReference] = []

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        img_tags = soup.find_all("img")

        if not img_tags:
            logger.debug("No image tags found in HTML")
            return images

        # Set up output directory
        output_dir = self.options.get("image_output_dir")
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
                image_url = self._resolve_image_url(img_src, base_url)

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
        max_workers = self.options.get("max_image_workers", 5)
        logger.info(
            f"Downloading {len(download_tasks)} images with {max_workers} workers"
        )

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
                future = executor.submit(self._download_image, image_url, output_path)
                future_to_task[future] = (
                    task_idx,
                    output_path,
                    alt_text,
                    original_idx,
                    image_url,
                )

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task_idx, output_path, alt_text, original_idx, image_url = (
                    future_to_task[future]
                )
                try:
                    dimensions = future.result()
                    if dimensions is None:
                        logger.warning(
                            f"Failed to download image {task_idx}: {image_url}"
                        )
                        continue

                    # Get image format
                    img_format = self._get_image_format(output_path)

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

    def _resolve_image_url(self, img_src: str, base_url: Optional[str]) -> str:
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
            >>> parser = HTMLParser()
            >>> url = parser._resolve_image_url("/images/photo.jpg", "https://example.com/page")
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

    def _download_image(
        self, image_url: str, output_path: Path
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

        Returns:
            Tuple of (width, height) if successful, None if failed.

        Example:
            >>> parser = HTMLParser()
            >>> dims = parser._download_image("https://example.com/image.jpg", Path("/tmp/img.jpg"))
            >>> if dims:
            ...     print(f"Image dimensions: {dims[0]}x{dims[1]}")
        """
        self._apply_rate_limit()
        timeout = self.options.get("timeout", 10)
        headers = self._build_headers()

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

    def _get_image_format(self, file_path: Path) -> str:
        """
        Detect image format from file.

        Uses Pillow to detect format (JPEG, PNG, GIF, WebP, etc.)

        Args:
            file_path: Path to image file.

        Returns:
            Image format string (lowercase, e.g., "jpeg", "png").

        Example:
            >>> parser = HTMLParser()
            >>> format = parser._get_image_format(Path("/tmp/image.jpg"))
            >>> print(format)
            jpeg
        """
        try:
            with Image.open(file_path) as img:
                return img.format.lower() if img.format else "unknown"
        except Exception as e:
            logger.warning(f"Could not detect image format for {file_path}: {e}")
            return "unknown"
