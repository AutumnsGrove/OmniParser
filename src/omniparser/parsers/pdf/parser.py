"""
Main PDF parser orchestrator - coordinates all PDF parsing operations.

This module provides the main entry point for parsing PDF files. It orchestrates
the complete PDF parsing pipeline by coordinating all specialized modules:
- File validation and loading
- Metadata extraction
- Text extraction (with OCR support)
- Heading detection and chapter extraction
- Image extraction
- Table extraction

The orchestrator follows a functional approach, delegating to specialized modules
while maintaining a clean, linear flow.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...models import Chapter, Document, ImageReference, Metadata, ProcessingInfo, QRCodeReference
from ...processors.text_cleaner import clean_text
from ...processors.qr_content_merger import process_qr_codes, merge_qr_content_to_document
from .heading_detection import process_pdf_headings
from .images import extract_pdf_images, scan_pdf_for_qr_codes
from .metadata import extract_pdf_metadata
from .tables import extract_pdf_tables
from .text_extraction import extract_text_content
from .utils import count_words, estimate_reading_time
from .validation import validate_and_load_pdf

logger = logging.getLogger(__name__)


def parse_pdf(
    file_path: Path,
    output_dir: Optional[Path] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Document:
    """
    Parse PDF file and extract structured content.

    This is the main entry point for PDF parsing. It orchestrates the complete
    parsing pipeline:
    1. Validate and load PDF file
    2. Extract metadata
    3. Extract text (with OCR for scanned PDFs)
    4. Detect headings and chapters
    5. Extract images (if output_dir provided)
    6. Extract tables
    7. Build Document with all extracted data

    Args:
        file_path: Path to PDF file to parse.
        output_dir: Optional directory for extracted images. If None, images
            are not extracted.
        options: Optional parsing options dictionary. Supported options:
            - use_ocr: Enable OCR for scanned PDFs (default: True)
            - ocr_language: OCR language code (default: 'eng')
            - ocr_timeout: OCR timeout in seconds (default: 300)
            - max_pages: Maximum pages to process (default: None = all)
            - extract_images: Extract images (default: True if output_dir provided)
            - extract_tables: Extract tables (default: True)
            - clean_text: Apply text cleaning (default: True)
            - detect_qr_codes: Scan for QR codes in PDF (default: False)
            - qr_fetch_urls: Fetch content from QR code URLs (default: True)
            - qr_timeout: Timeout for QR URL fetching in seconds (default: 15)
            - qr_dpi: DPI for rendering pages for QR detection (default: 150)
            - max_qr_scan_pages: Max pages to scan for QR codes (default: None = all)

    Returns:
        Document object with parsed content, metadata, and processing info.

    Raises:
        ValidationError: If file validation fails.
        FileReadError: If PDF cannot be opened.
        ParsingError: If parsing fails.

    Example:
        >>> from pathlib import Path
        >>> doc = parse_pdf(Path("document.pdf"))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Pages: {doc.metadata.custom_fields['page_count']}")
        >>> print(f"Chapters: {len(doc.chapters)}")
    """
    start_time = time.time()
    options = options or {}

    # Parse options
    use_ocr = options.get("use_ocr", True)
    ocr_language = options.get("ocr_language", "eng")
    ocr_timeout = options.get("ocr_timeout", 300)
    max_pages = options.get("max_pages")
    extract_images_flag = options.get("extract_images", output_dir is not None)
    extract_tables_flag = options.get("extract_tables", True)
    clean_text_flag = options.get("clean_text", True)
    detect_qr_codes_flag = options.get("detect_qr_codes", False)
    qr_fetch_urls = options.get("qr_fetch_urls", True)
    qr_timeout = options.get("qr_timeout", 15)
    qr_dpi = options.get("qr_dpi", 150)
    max_qr_scan_pages = options.get("max_qr_scan_pages")

    # Step 1: Validate and load PDF
    logger.info(f"Loading PDF: {file_path}")
    doc = validate_and_load_pdf(file_path)

    try:
        # Step 2: Extract metadata
        metadata = extract_pdf_metadata(doc, file_path)
        logger.info(f"Extracted metadata: {metadata.title}")

        # Step 3: Extract text content
        logger.info("Extracting text content")
        content, text_blocks = extract_text_content(
            doc,
            use_ocr=use_ocr,
            ocr_language=ocr_language,
            ocr_timeout=ocr_timeout,
            max_pages=max_pages,
        )

        # Step 4: Process headings and detect chapters
        logger.info("Processing headings and detecting chapters")
        markdown_content, chapters = process_pdf_headings(text_blocks, content)

        # Step 5: Clean text (if enabled)
        if clean_text_flag:
            logger.info("Cleaning text")
            markdown_content = clean_text(markdown_content)

        # Step 6: Extract images (if output_dir provided)
        images: List[ImageReference] = []
        if extract_images_flag and output_dir:
            logger.info(f"Extracting images to: {output_dir}")
            images = extract_pdf_images(doc, output_dir=output_dir)

        # Step 7: Extract tables (if enabled)
        tables: List[str] = []
        if extract_tables_flag:
            logger.info("Extracting tables")
            tables = extract_pdf_tables(doc)
            # Append tables to content
            if tables:
                markdown_content += "\n\n## Extracted Tables\n\n"
                markdown_content += "\n\n".join(tables)

        # Step 8: Detect QR codes (if enabled)
        qr_codes: List[QRCodeReference] = []
        qr_warnings: List[str] = []
        if detect_qr_codes_flag:
            logger.info("Scanning for QR codes")
            qr_codes, qr_warnings = scan_pdf_for_qr_codes(
                doc, dpi=qr_dpi, max_pages=max_qr_scan_pages
            )

            if qr_codes:
                logger.info(f"Found {len(qr_codes)} QR code(s), processing...")
                # Fetch content from QR code URLs
                qr_codes = process_qr_codes(
                    qr_codes,
                    fetch_urls=qr_fetch_urls,
                    timeout=qr_timeout,
                )

        # Step 9: Calculate word count and reading time
        word_count = count_words(markdown_content)
        reading_time = estimate_reading_time(word_count)

        # Step 10: Build ProcessingInfo
        processing_time = time.time() - start_time
        all_warnings = qr_warnings.copy()  # Include QR warnings
        processing_info = ProcessingInfo(
            parser_used="PDFParser",
            parser_version="1.0.0",
            processing_time=processing_time,
            timestamp=datetime.now(),
            warnings=all_warnings,
            options_used=options,
        )

        # Step 11: Build Document
        document = Document(
            document_id=file_path.stem,
            content=markdown_content,
            chapters=chapters,
            images=images,
            metadata=metadata,
            processing_info=processing_info,
            word_count=word_count,
            estimated_reading_time=reading_time,
        )

        # Step 12: Merge QR code content into document
        if qr_codes:
            document = merge_qr_content_to_document(
                document,
                qr_codes,
                add_sections=True,
            )
            logger.info(f"Merged content from {len(qr_codes)} QR code(s)")

        logger.info(
            f"PDF parsing complete: {document.word_count} words, "
            f"{len(chapters)} chapters, {len(images)} images, "
            f"{len(tables)} tables, {len(qr_codes)} QR codes, {processing_time:.2f}s"
        )

        return document

    finally:
        # Always close the PDF document
        doc.close()
