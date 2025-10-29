"""
HTML parser for OmniParser using Trafilatura with Readability fallback.

This module provides an HTML parser that can handle both local HTML files
and web URLs, extracting clean content while preserving structure and metadata.

Classes:
    HTMLParser: Parser for HTML files and URLs.
"""

import logging
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union, cast
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
        timeout = self.options.get("timeout", 10)

        try:
            response = requests.get(url, timeout=timeout)
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
        Extract images from HTML content.

        Features:
        - Find all <img> tags using BeautifulSoup
        - Download images from URLs (if base_url provided)
        - Handle relative image paths
        - Extract alt text
        - Get image dimensions (if possible)
        - Save to image_output_dir or temp directory
        - Generate sequential image IDs (img_001, img_002, etc.)

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

        # Extract each image
        img_counter = 0  # Counter for successfully extracted images
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

                # Determine file extension from URL
                parsed_url = urlparse(image_url)
                path_parts = parsed_url.path.split(".")
                extension = path_parts[-1].lower() if len(path_parts) > 1 else "jpg"

                # Limit extension to common formats
                if extension not in ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"]:
                    extension = "jpg"

                # Increment counter for this successfully processed image
                img_counter += 1

                # Generate output filename
                output_filename = f"img_{img_counter:03d}.{extension}"
                output_path = output_dir / output_filename

                # Download image if it's an absolute URL
                dimensions = None
                if image_url.startswith(("http://", "https://")):
                    # Download from URL (works for both URL sources and local files with absolute URLs)
                    dimensions = self._download_image(image_url, output_path)
                    if dimensions is None:
                        logger.warning(f"Failed to download image {img_counter}: {image_url}")
                        img_counter -= 1  # Decrement counter on failure
                        continue
                else:
                    # Local/relative path - skip for now
                    # Would need original HTML file path to resolve relative paths properly
                    logger.debug(f"Image {idx} is local/relative reference, skipping: {img_src}")
                    img_counter -= 1  # Decrement counter since we're skipping
                    continue

                # Get image format
                img_format = self._get_image_format(output_path)

                # Extract alt text (cast to string)
                alt_text_raw = img_tag.get("alt")
                alt_text = str(alt_text_raw) if alt_text_raw else None

                # Create ImageReference
                image_ref = ImageReference(
                    image_id=f"img_{img_counter:03d}",
                    position=img_counter * 100,  # Simple sequential spacing
                    file_path=str(output_path),
                    alt_text=alt_text,
                    size=dimensions,
                    format=img_format,
                )

                images.append(image_ref)
                logger.debug(
                    f"Extracted image {img_counter}: {output_filename} "
                    f"({img_format}, {dimensions})"
                )

            except Exception as e:
                logger.warning(f"Failed to extract image {idx}: {e}")
                # Continue with next image

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
        timeout = self.options.get("timeout", 10)

        try:
            # Download image
            response = requests.get(image_url, timeout=timeout, stream=True)
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
