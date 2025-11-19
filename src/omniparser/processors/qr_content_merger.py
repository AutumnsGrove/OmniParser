"""
QR code content merger for OmniParser.

This module provides functionality to merge QR code detected content
into the document structure, including fetching URL content and
adding it as document sections.

Functions:
    process_qr_codes: Process all QR codes and fetch their content.
    merge_qr_content_to_document: Add QR content to document structure.
    format_qr_section: Format fetched content as a document section.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from omniparser.models import Chapter, Document, QRCodeReference
from omniparser.utils.qr_url_fetcher import fetch_url_content, FetchResult

logger = logging.getLogger(__name__)


def process_qr_codes(
    qr_codes: List[QRCodeReference],
    fetch_urls: bool = True,
    timeout: int = 15,
    parallel: bool = False,
    max_workers: int = 4,
    rate_limit: float = 0.5,
) -> List[QRCodeReference]:
    """Process QR codes and fetch content for URL types.

    Args:
        qr_codes: List of detected QR code references.
        fetch_urls: Whether to fetch content from URL QR codes.
        timeout: Request timeout in seconds.
        parallel: Whether to fetch URLs in parallel (default: False).
        max_workers: Maximum number of parallel workers (default: 4).
        rate_limit: Delay between requests in seconds for rate limiting (default: 0.5).

    Returns:
        Updated list of QRCodeReference objects with fetched content.

    Example:
        >>> qr_codes, warnings = detect_qr_codes(image_data)
        >>> processed_qr = process_qr_codes(qr_codes)
        >>> for qr in processed_qr:
        ...     if qr.fetched_content:
        ...         print(f"Got content from {qr.raw_data}")

        # With parallel fetching
        >>> processed_qr = process_qr_codes(qr_codes, parallel=True, max_workers=4)
    """
    # Separate URL and non-URL QR codes
    url_qr_codes = []
    for qr in qr_codes:
        if qr.data_type == "URL" and fetch_urls:
            url_qr_codes.append(qr)
        elif qr.data_type != "URL":
            qr.fetch_status = "skipped"
            qr.fetch_notes.append(f"Non-URL QR code ({qr.data_type}), fetch skipped")

    if not url_qr_codes:
        return qr_codes

    if parallel and len(url_qr_codes) > 1:
        # Parallel fetching
        _fetch_urls_parallel(url_qr_codes, timeout, max_workers, rate_limit)
    else:
        # Sequential fetching
        _fetch_urls_sequential(url_qr_codes, timeout)

    return qr_codes


def _fetch_urls_sequential(qr_codes: List[QRCodeReference], timeout: int) -> None:
    """Fetch URLs sequentially.

    Args:
        qr_codes: List of URL QR codes to fetch.
        timeout: Request timeout in seconds.
    """
    for qr in qr_codes:
        logger.info(f"Fetching content from QR URL: {qr.raw_data}")
        result = fetch_url_content(qr.raw_data, timeout=timeout)
        _apply_fetch_result(qr, result)


def _fetch_urls_parallel(
    qr_codes: List[QRCodeReference],
    timeout: int,
    max_workers: int,
    rate_limit: float,
) -> None:
    """Fetch URLs in parallel with rate limiting.

    Args:
        qr_codes: List of URL QR codes to fetch.
        timeout: Request timeout in seconds.
        max_workers: Maximum number of parallel workers.
        rate_limit: Delay between requests in seconds.
    """
    logger.info(f"Fetching {len(qr_codes)} URLs in parallel (max_workers={max_workers})")

    def fetch_with_delay(qr: QRCodeReference, index: int) -> tuple:
        """Fetch URL with rate limiting delay."""
        if index > 0 and rate_limit > 0:
            time.sleep(rate_limit * index)
        logger.info(f"Fetching content from QR URL: {qr.raw_data}")
        result = fetch_url_content(qr.raw_data, timeout=timeout)
        return qr, result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_with_delay, qr, idx): qr
            for idx, qr in enumerate(qr_codes)
        }

        for future in as_completed(futures):
            try:
                qr, result = future.result()
                _apply_fetch_result(qr, result)
            except Exception as e:
                qr = futures[future]
                qr.fetch_status = "failed"
                qr.fetch_notes.append(f"Parallel fetch error: {str(e)}")
                logger.error(f"Parallel fetch failed for {qr.raw_data}: {e}")


def _apply_fetch_result(qr: QRCodeReference, result: FetchResult) -> None:
    """Apply fetch result to a QR code reference.

    Args:
        qr: QR code reference to update.
        result: Fetch result to apply.
    """
    qr.fetch_status = result.status
    qr.fetch_notes = result.notes.copy()

    if result.success and result.content:
        qr.fetched_content = result.content
        qr.fetch_notes.append(f"Retrieved {len(result.content)} characters")

        if result.source != "original":
            qr.fetch_notes.append(f"Content source: {result.source}")
    else:
        qr.fetched_content = None


def merge_qr_content_to_document(
    document: Document,
    qr_codes: List[QRCodeReference],
    add_sections: bool = True,
) -> Document:
    """Merge QR code content into a document.

    Adds QR code references to metadata and optionally adds
    fetched content as new document sections.

    Args:
        document: Document to merge QR content into.
        qr_codes: List of processed QRCodeReference objects.
        add_sections: Whether to add fetched content as document sections.

    Returns:
        Updated Document with QR content merged.

    Example:
        >>> doc = parse_document("document.pdf")
        >>> qr_codes = detect_and_process_qr_codes(doc)
        >>> doc = merge_qr_content_to_document(doc, qr_codes)
    """
    if not qr_codes:
        return document

    # Set QR codes on the document directly
    document.qr_codes = qr_codes

    # Add QR codes to metadata custom_fields
    if document.metadata.custom_fields is None:
        document.metadata.custom_fields = {}

    # Store QR code references (without full content to avoid bloat)
    qr_summaries = []
    for qr in qr_codes:
        summary = {
            "qr_id": qr.qr_id,
            "raw_data": qr.raw_data,
            "data_type": qr.data_type,
            "page_number": qr.page_number,
            "fetch_status": qr.fetch_status,
            "fetch_notes": qr.fetch_notes,
            "has_content": qr.fetched_content is not None,
            "content_length": len(qr.fetched_content) if qr.fetched_content else 0,
        }
        qr_summaries.append(summary)

    document.metadata.custom_fields["qr_codes"] = qr_summaries
    document.metadata.custom_fields["qr_code_count"] = len(qr_codes)

    # Add fetched content as document sections
    if add_sections:
        for qr in qr_codes:
            if qr.fetched_content:
                section_content = format_qr_section(qr)
                document.content += f"\n\n{section_content}"

                # Update word count
                word_count = len(qr.fetched_content.split())
                document.word_count += word_count

        # Recalculate reading time (200 words per minute)
        document.estimated_reading_time = max(1, document.word_count // 200)

    return document


def format_qr_section(qr: QRCodeReference) -> str:
    """Format a QR code's fetched content as a document section.

    Creates a formatted section with header, content, and metadata notes.

    Args:
        qr: QRCodeReference with fetched content.

    Returns:
        Formatted markdown string for the section.

    Example:
        >>> section = format_qr_section(qr)
        >>> print(section)
        ## Content from QR Code qr_001

        [content here]

        ---
        > Source: https://example.com/recipe
        > Status: success
        > Notes: Followed 2 redirects
    """
    if not qr.fetched_content:
        return ""

    lines = []

    # Header
    page_info = f" (Page {qr.page_number})" if qr.page_number else ""
    lines.append(f"## Content from QR Code {qr.qr_id}{page_info}")
    lines.append("")

    # Content
    lines.append(qr.fetched_content)
    lines.append("")

    # Metadata footer
    lines.append("---")
    lines.append(f"> **Source:** {qr.raw_data}")
    lines.append(f"> **Status:** {qr.fetch_status}")

    if qr.fetch_notes:
        notes_str = "; ".join(qr.fetch_notes)
        lines.append(f"> **Notes:** {notes_str}")

    return "\n".join(lines)


def create_qr_chapter(
    qr: QRCodeReference,
    chapter_id: int,
    start_position: int,
) -> Optional[Chapter]:
    """Create a Chapter object from QR code fetched content.

    Args:
        qr: QRCodeReference with fetched content.
        chapter_id: ID for the new chapter.
        start_position: Character position in document.

    Returns:
        Chapter object, or None if no content.
    """
    if not qr.fetched_content:
        return None

    content = format_qr_section(qr)
    word_count = len(qr.fetched_content.split())

    page_info = f" (Page {qr.page_number})" if qr.page_number else ""
    title = f"Content from QR Code {qr.qr_id}{page_info}"

    chapter = Chapter(
        chapter_id=chapter_id,
        title=title,
        content=content,
        start_position=start_position,
        end_position=start_position + len(content),
        word_count=word_count,
        level=2,  # Subsection level
        metadata={
            "source_type": "qr_code",
            "qr_id": qr.qr_id,
            "original_url": qr.raw_data,
            "fetch_status": qr.fetch_status,
        },
    )

    return chapter


def generate_qr_summary(qr_codes: List[QRCodeReference]) -> str:
    """Generate a summary of all QR codes found.

    Args:
        qr_codes: List of QRCodeReference objects.

    Returns:
        Formatted summary string.

    Example:
        >>> summary = generate_qr_summary(qr_codes)
        >>> print(summary)
        QR Code Summary:
        - 3 QR codes detected
        - 2 URLs fetched successfully
        - 1 text QR code (no fetch needed)
    """
    if not qr_codes:
        return "No QR codes detected."

    total = len(qr_codes)
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}

    for qr in qr_codes:
        by_type[qr.data_type] = by_type.get(qr.data_type, 0) + 1
        by_status[qr.fetch_status] = by_status.get(qr.fetch_status, 0) + 1

    lines = ["## QR Code Summary", ""]
    lines.append(f"**Total QR codes detected:** {total}")
    lines.append("")

    lines.append("**By type:**")
    for dtype, count in sorted(by_type.items()):
        lines.append(f"- {dtype}: {count}")
    lines.append("")

    lines.append("**By fetch status:**")
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}: {count}")

    return "\n".join(lines)
