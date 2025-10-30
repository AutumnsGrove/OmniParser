"""
Document builder for HTML parser.

This module constructs the final Document object from extracted HTML content,
integrating markdown conversion, metadata extraction, and chapter detection.
"""

# Standard library
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Local
from ...models import Document, ImageReference, Metadata, ProcessingInfo
from ...processors.chapter_detector import detect_chapters
from ...processors.markdown_converter import html_to_markdown
from ...processors.metadata_extractor import extract_html_metadata
from .image_extractor import extract_images

logger = logging.getLogger(__name__)


def build_html_document(
    content_html: str,
    full_html: str,
    source: str,
    warnings: List[str],
    options: Dict[str, Any],
    apply_rate_limit: Callable[[], None],
    build_headers: Callable[[], Dict[str, str]],
) -> Document:
    """
    Build complete Document object from extracted HTML content.

    This function orchestrates the final document construction by:
    1. Converting HTML to Markdown
    2. Extracting metadata from original HTML
    3. Extracting images (if enabled)
    4. Detecting chapters based on headings (if enabled)
    5. Calculating word count and reading time
    6. Creating ProcessingInfo with warnings

    Args:
        content_html: Extracted HTML content (main content only).
        full_html: Original HTML with all elements (for metadata/images).
        source: File path or URL identifier.
        warnings: List of warnings accumulated during processing.
        options: Parser configuration dict including:
            - extract_images: Whether to extract images (default: True)
            - detect_chapters: Whether to detect chapters (default: True)
            - min_chapter_level: Minimum heading level for chapters (default: 1)
            - max_chapter_level: Maximum heading level for chapters (default: 2)
        apply_rate_limit: Callback for rate limiting (from ContentFetcher).
        build_headers: Callback for building HTTP headers (from ContentFetcher).

    Returns:
        Complete Document object with all fields populated.

    Example:
        >>> from html.content_fetcher import ContentFetcher
        >>> fetcher = ContentFetcher(options)
        >>> doc = build_html_document(
        ...     extracted_html,
        ...     original_html,
        ...     "https://example.com",
        ...     [],
        ...     options,
        ...     fetcher._apply_rate_limit,
        ...     fetcher._build_headers,
        ... )
    """
    # Convert HTML to Markdown
    markdown_content = html_to_markdown(content_html)

    # Extract metadata from original HTML (better meta tag access)
    url = source if source.startswith("http") else None
    metadata = extract_html_metadata(full_html, url=url)

    # Extract images from ORIGINAL HTML (before processing strips them)
    images: List[ImageReference] = []
    if options.get("extract_images", True):
        try:
            base_url = source if source.startswith("http") else None
            images = extract_images(
                full_html,
                base_url=base_url,
                options=options,
                apply_rate_limit=apply_rate_limit,
                build_headers=build_headers,
            )
            if images:
                logger.info(f"Extracted {len(images)} images from HTML")
        except Exception as e:
            warning_msg = f"Image extraction failed: {str(e)}"
            warnings.append(warning_msg)
            logger.warning(warning_msg)

    # Detect chapters if enabled
    chapters = []
    if options.get("detect_chapters", True):
        min_level = options.get("min_chapter_level", 1)
        max_level = options.get("max_chapter_level", 2)
        chapters = detect_chapters(markdown_content, min_level, max_level)

    # Calculate word count and reading time
    word_count = len(markdown_content.split())
    estimated_reading_time = max(
        1, round(word_count / 225)
    )  # 225 WPM, minimum 1 minute

    # Create processing info
    processing_info = ProcessingInfo(
        parser_used="html",
        parser_version="0.1.0",
        processing_time=0.0,  # Will be updated by caller
        timestamp=datetime.now(),
        warnings=warnings,
        options_used=dict(options),
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
