"""
PDF text extraction with OCR support and font-based formatting.

This module provides functions for extracting text from PDF documents using PyMuPDF,
with support for OCR (Optical Character Recognition) for scanned PDFs. It includes:
- Detection of scanned PDFs vs text-based PDFs
- Text extraction with font information for heading detection
- OCR extraction using Tesseract for scanned documents
- Main coordinator function for automatic extraction strategy selection

The module handles both text-based and image-based (scanned) PDFs intelligently,
choosing the appropriate extraction method based on text content analysis.
"""

import logging
from typing import Dict, List, Tuple

import fitz  # PyMuPDF
from PIL import Image

from ...exceptions import ParsingError
from .utils import DEFAULT_OCR_TIMEOUT, OCR_DPI, SCANNED_PDF_THRESHOLD, timeout_context

logger = logging.getLogger(__name__)


def is_scanned_pdf(doc: fitz.Document, threshold: int = SCANNED_PDF_THRESHOLD) -> bool:
    """
    Determine if PDF is scanned (image-based) or text-based.

    Strategy:
    - Sample first 3 pages (or all if < 3)
    - Count extracted text characters
    - If < threshold chars per page on average, consider scanned

    Args:
        doc: PyMuPDF document object
        threshold: Character count threshold (default: SCANNED_PDF_THRESHOLD)

    Returns:
        True if scanned (needs OCR), False if text-based

    Example:
        >>> import fitz
        >>> doc = fitz.open("document.pdf")
        >>> if is_scanned_pdf(doc):
        ...     print("PDF needs OCR")
    """
    sample_pages = min(3, len(doc))
    total_chars = 0

    for page_num in range(sample_pages):
        page = doc[page_num]
        text = page.get_text()
        total_chars += len(text.strip())

    avg_chars_per_page = total_chars / sample_pages if sample_pages > 0 else 0

    # Threshold: < threshold chars per page suggests scanned PDF
    is_scanned = avg_chars_per_page < threshold

    if is_scanned:
        logger.info(
            f"PDF appears to be scanned "
            f"(avg {avg_chars_per_page:.0f} chars/page, "
            f"threshold={threshold})"
        )
    else:
        logger.info(
            f"PDF appears to be text-based "
            f"(avg {avg_chars_per_page:.0f} chars/page)"
        )

    return is_scanned


def extract_text_with_formatting(
    doc: fitz.Document,
    max_pages: int = None,
    include_page_breaks: bool = False,
) -> Tuple[str, List[Dict]]:
    """
    Extract text with font information for heading detection.

    Returns full text content and list of text blocks with font metadata
    for analysis and heading detection.

    Args:
        doc: PyMuPDF document object
        max_pages: Maximum number of pages to process (None = all)
        include_page_breaks: Whether to include page break markers

    Returns:
        Tuple of (full_text, text_blocks) where text_blocks contains:
        - text: Text content
        - font_size: Font size in points
        - is_bold: Whether text is bold
        - page_num: Page number (1-indexed)
        - position: Character position in full text

    Example:
        >>> doc = fitz.open("document.pdf")
        >>> text, blocks = extract_text_with_formatting(doc)
        >>> for block in blocks:
        ...     if block['is_bold'] and block['font_size'] > 14:
        ...         print(f"Heading: {block['text']}")
    """
    full_text = []
    text_blocks = []
    current_position = 0  # Track position incrementally (O(1) instead of O(n�))

    # Apply page limit if specified
    num_pages = min(len(doc), max_pages) if max_pages else len(doc)

    for page_num in range(num_pages):
        page = doc[page_num]

        # Get text blocks with font information
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                if "spans" not in line:
                    continue

                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    font_size = span.get("size", 12.0)
                    font_flags = span.get("flags", 0)
                    font_name = span.get("font", "")

                    # Check if bold (flag 16 is bold in PyMuPDF)
                    is_bold = bool(font_flags & 16) or "Bold" in font_name

                    # Store text block info with incremental position
                    text_blocks.append(
                        {
                            "text": text,
                            "font_size": font_size,
                            "is_bold": is_bold,
                            "page_num": page_num + 1,
                            "position": current_position,
                        }
                    )

                    full_text.append(text)
                    # Update position: add text length + 1 for space separator
                    current_position += len(text) + 1

        # Add page break marker (if enabled)
        if include_page_breaks:
            page_marker = f"\n\n--- Page {page_num + 1} ---\n\n"
            full_text.append(page_marker)
            current_position += len(page_marker) + 1

    return " ".join(full_text), text_blocks


def extract_text_with_ocr(
    doc: fitz.Document,
    dpi: int = OCR_DPI,
    language: str = "eng",
    max_pages: int = None,
    include_page_breaks: bool = False,
    timeout: int = DEFAULT_OCR_TIMEOUT,
) -> str:
    """
    Extract text using OCR (Tesseract) for scanned PDFs.

    Process:
    1. Convert each page to PIL Image at specified DPI
    2. Run Tesseract OCR (with timeout enforcement)
    3. Combine results
    4. Add page markers if requested

    Args:
        doc: PyMuPDF document object
        dpi: DPI for rendering pages (default: OCR_DPI = 300)
        language: Tesseract language code (default: 'eng')
        max_pages: Maximum number of pages to process (None = all)
        include_page_breaks: Whether to include page break markers
        timeout: OCR timeout in seconds (default: DEFAULT_OCR_TIMEOUT)

    Returns:
        OCR-extracted text

    Raises:
        TimeoutError: If OCR processing exceeds configured timeout
        ParsingError: If OCR processing fails or times out

    Note:
        Requires pytesseract to be installed. If not available, falls back
        to basic text extraction.

    Example:
        >>> doc = fitz.open("scanned.pdf")
        >>> text = extract_text_with_ocr(doc, language='eng')
        >>> print(text)
    """
    try:
        import pytesseract
    except ImportError:
        logger.warning("pytesseract not available, falling back to text extraction")
        text, _ = extract_text_with_formatting(doc, max_pages, include_page_breaks)
        return text

    full_text = []

    # Apply page limit if specified
    num_pages = min(len(doc), max_pages) if max_pages else len(doc)

    # Wrap OCR processing in timeout context
    try:
        with timeout_context(timeout):
            for page_num in range(num_pages):
                page = doc[page_num]

                # Convert page to image
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Run OCR
                try:
                    text = pytesseract.image_to_string(img, lang=language)
                    full_text.append(text.strip())
                    # Add page break marker (if enabled)
                    if include_page_breaks:
                        full_text.append(f"\n\n--- Page {page_num + 1} ---\n\n")
                except TimeoutError:
                    # Re-raise TimeoutError to be caught by outer handler
                    raise
                except Exception as e:
                    logger.warning(f"OCR failed on page {page_num + 1}: {e}")
    except TimeoutError as e:
        logger.error(f"OCR processing timed out: {e}")
        raise ParsingError(
            f"OCR processing exceeded timeout of {timeout} seconds",
            parser="PDFParser",
            original_error=e,
        )

    return "\n".join(full_text)


def extract_text_content(
    doc: fitz.Document,
    use_ocr: bool = True,
    ocr_threshold: int = SCANNED_PDF_THRESHOLD,
    ocr_timeout: int = DEFAULT_OCR_TIMEOUT,
    ocr_language: str = "eng",
    max_pages: int = None,
    include_page_breaks: bool = False,
) -> Tuple[str, List[Dict]]:
    """
    Main coordinator for text extraction with automatic strategy selection.

    This function automatically detects whether a PDF is scanned or text-based
    and chooses the appropriate extraction method. For text-based PDFs, it
    extracts text with font information. For scanned PDFs, it uses OCR.

    Args:
        doc: PyMuPDF document object
        use_ocr: Enable OCR for scanned PDFs (default: True)
        ocr_threshold: Character threshold for scanned detection
        ocr_timeout: Timeout for OCR operations in seconds
        ocr_language: Tesseract language code
        max_pages: Maximum number of pages to process (None = all)
        include_page_breaks: Whether to include page break markers

    Returns:
        Tuple of (text, text_blocks) where:
        - text: Extracted text content
        - text_blocks: List of blocks with font info (empty for OCR)

    Example:
        >>> doc = fitz.open("document.pdf")
        >>> text, blocks = extract_text_content(doc, use_ocr=True)
        >>> print(f"Extracted {len(text)} characters")
        >>> if blocks:
        ...     print(f"Found {len(blocks)} text blocks with font info")
    """
    # Detect if scanned PDF
    scanned = is_scanned_pdf(doc, threshold=ocr_threshold)

    # Extract text based on PDF type
    if scanned and use_ocr:
        logger.info("Using OCR for scanned PDF")
        text = extract_text_with_ocr(
            doc,
            language=ocr_language,
            max_pages=max_pages,
            include_page_breaks=include_page_breaks,
            timeout=ocr_timeout,
        )
        text_blocks = []  # OCR doesn't provide font info
    else:
        if scanned and not use_ocr:
            logger.warning("Scanned PDF detected but OCR is disabled")
        text, text_blocks = extract_text_with_formatting(
            doc, max_pages=max_pages, include_page_breaks=include_page_breaks
        )

    return text, text_blocks
