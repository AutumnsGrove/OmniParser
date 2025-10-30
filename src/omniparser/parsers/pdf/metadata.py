"""
PDF metadata extraction and parsing utilities.

This module provides functions for extracting and processing metadata from PDF documents,
including parsing PDF-specific date formats, keywords, and custom metadata fields.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

from ...models import Metadata
from ...processors.metadata_builder import MetadataBuilder

logger = logging.getLogger(__name__)


def extract_pdf_metadata(doc: fitz.Document, file_path: Path) -> Metadata:
    """
    Extract metadata from PDF properties.

    Extracts standard PDF metadata fields including title, author, subject,
    keywords, creator, and creation date. Uses MetadataBuilder to create
    a standardized Metadata object.

    Args:
        doc: PyMuPDF document object.
        file_path: Path to PDF file.

    Returns:
        Metadata object with extracted PDF metadata.

    Example:
        >>> doc = fitz.open("document.pdf")
        >>> metadata = extract_pdf_metadata(doc, Path("document.pdf"))
        >>> print(metadata.title)
    """
    meta = doc.metadata or {}

    # Extract basic metadata
    title = meta.get("title") or file_path.stem
    author = meta.get("author")
    subject = meta.get("subject")
    keywords = meta.get("keywords")

    # Parse creation date
    creation_date = parse_pdf_date(meta.get("creationDate"))

    # Parse keywords into tags
    tags = parse_keywords_to_tags(keywords)

    # Get file size
    file_size = file_path.stat().st_size if file_path.exists() else 0

    # Build custom fields
    custom_fields = build_custom_fields(doc, meta)

    return MetadataBuilder.build(
        title=title,
        author=author,
        description=subject,
        publication_date=creation_date,
        tags=tags,
        original_format="pdf",
        file_size=file_size,
        custom_fields=custom_fields,
    )


def parse_pdf_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse PDF date string to datetime object.

    PDF dates are in the format: D:YYYYMMDDHHmmSSOHH'mm'
    where:
    - D: is a literal prefix
    - YYYY: year
    - MM: month
    - DD: day
    - HH: hour
    - mm: minute
    - SS: second
    - O: timezone offset direction (+ or -)
    - HH'mm': timezone offset

    Args:
        date_str: PDF date string.

    Returns:
        datetime object, or None if parsing fails.

    Example:
        >>> parse_pdf_date("D:20240101120000")
        datetime.datetime(2024, 1, 1, 12, 0, 0)
    """
    if not date_str:
        return None

    try:
        # PDF dates start with "D:" prefix
        if date_str.startswith("D:"):
            # Extract YYYYMMDDHHmmSS (14 characters after "D:")
            date_str = date_str[2:16]
            return datetime.strptime(date_str, "%Y%m%d%H%M%S")
    except Exception as e:
        logger.warning(f"Failed to parse PDF date '{date_str}': {e}")

    return None


def parse_keywords_to_tags(keywords: Optional[str]) -> List[str]:
    """
    Parse comma-separated keywords string into list of tags.

    Splits the keywords string by commas and strips whitespace from
    each tag. Empty tags are filtered out.

    Args:
        keywords: Comma-separated keywords string.

    Returns:
        List of tag strings.

    Example:
        >>> parse_keywords_to_tags("pdf, document, test")
        ['pdf', 'document', 'test']
    """
    if not keywords:
        return []

    tags = [k.strip() for k in keywords.split(",") if k.strip()]
    return tags


def build_custom_fields(doc: fitz.Document, meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build custom metadata fields dictionary for PDF-specific information.

    Extracts PDF-specific metadata that doesn't fit into the standard
    Metadata fields, including page count, creator, producer, and PDF version.

    Args:
        doc: PyMuPDF document object.
        meta: PDF metadata dictionary from doc.metadata.

    Returns:
        Dictionary of custom metadata fields.

    Example:
        >>> doc = fitz.open("document.pdf")
        >>> custom = build_custom_fields(doc, doc.metadata)
        >>> print(custom['page_count'])
    """
    return {
        "page_count": len(doc),
        "creator": meta.get("creator"),
        "producer": meta.get("producer"),
        "pdf_version": meta.get("format", "Unknown"),
    }
