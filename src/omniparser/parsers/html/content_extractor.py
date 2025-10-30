"""
Content extraction for HTML documents.

This module provides content extraction functionality using Readability
with Trafilatura as a fallback, orchestrating the extraction pipeline.

Functions:
    extract_main_content: Main orchestrator for content extraction
    extract_with_readability: Primary extraction using Readability
    extract_with_trafilatura: Fallback extraction using Trafilatura
"""

from typing import List, Optional, Tuple, cast

import trafilatura
from readability import Document as ReadabilityDocument

from ...exceptions import ParsingError

# Content length thresholds for extraction validation
MIN_CONTENT_LENGTH_READABILITY = (
    100  # Min chars for Readability to be considered successful
)
MIN_CONTENT_LENGTH_TRAFILATURA = (
    100  # Min chars for Trafilatura to be considered successful
)
MIN_CONTENT_LENGTH_TOTAL = 50  # Min chars for any extraction to be considered valid


def extract_main_content(html: str, options: dict) -> Tuple[str, List[str]]:
    """
    Extract main content from HTML with automatic fallback.

    Tries Readability first (preserves heading structure), falls back to Trafilatura
    if Readability fails or returns minimal content (<100 chars).

    Args:
        html: Raw HTML string to extract content from.
        options: Parser options dict (unused currently, for future features).

    Returns:
        Tuple of (extracted_html, warnings):
            - extracted_html: Clean HTML content
            - warnings: List of warning messages from extraction

    Raises:
        ParsingError: If both extraction methods fail to produce usable content.

    Example:
        >>> html = '<html><body><p>Article text</p></body></html>'
        >>> content, warnings = extract_main_content(html, {})
        >>> print(len(warnings), len(content))
        0 27
    """
    warnings: List[str] = []

    # Try Readability first (preserves heading structure for chapter detection)
    try:
        extracted_html = extract_with_readability(html)
    except ParsingError:
        # Readability failed completely, try Trafilatura
        extracted_html = None

    # Fallback to Trafilatura if needed
    if (
        not extracted_html
        or len(extracted_html.strip()) < MIN_CONTENT_LENGTH_READABILITY
    ):
        if extracted_html and len(extracted_html.strip()) > 0:
            warnings.append(
                "Readability extraction returned minimal content, "
                "using Trafilatura fallback"
            )
        else:
            warnings.append("Readability extraction failed, using Trafilatura fallback")

        extracted_html = extract_with_trafilatura(html)

        # If both fail, raise error
        if not extracted_html or len(extracted_html.strip()) < MIN_CONTENT_LENGTH_TOTAL:
            raise ParsingError(
                "Both Readability and Trafilatura failed to extract content",
                parser="HTMLParser",
            )

    return extracted_html, warnings


def extract_with_trafilatura(html: str) -> Optional[str]:
    """
    Extract main content using Trafilatura.

    Trafilatura is optimized for web articles and blogs, removing navigation,
    ads, scripts, and other boilerplate while preserving article structure.

    Args:
        html: HTML string to extract content from.

    Returns:
        Extracted HTML content or None if extraction fails.

    Example:
        >>> html = '<html><body><article>Content</article></body></html>'
        >>> result = extract_with_trafilatura(html)
        >>> result is not None
        True
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


def extract_with_readability(html: str) -> str:
    """
    Extract main content using Readability as fallback.

    Readability-lxml is more robust for complex/malformed HTML but may
    include more non-article content than Trafilatura.

    Args:
        html: HTML string to extract content from.

    Returns:
        Extracted HTML content.

    Raises:
        ParsingError: If Readability extraction fails.

    Example:
        >>> html = '<html><body><p>Text content</p></body></html>'
        >>> result = extract_with_readability(html)
        >>> 'Text content' in result
        True
    """
    try:
        doc = ReadabilityDocument(html)
        return cast(str, doc.summary())
    except Exception as e:
        raise ParsingError(
            f"Readability extraction failed: {str(e)}", parser="HTMLParser"
        ) from e
