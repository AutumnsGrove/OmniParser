"""
PDF parser implementation using PyMuPDF with OCR fallback.

This module provides the PDFParser class for parsing PDF files and converting
them to OmniParser's universal Document format. It includes font-based heading
detection, OCR fallback for scanned PDFs, image extraction, table extraction,
and text cleaning.

Features:
- Text extraction from text-based PDFs using PyMuPDF
- Font-based heading detection for chapter structure
- OCR fallback for scanned/image-based PDFs using Tesseract
- Image extraction with metadata
- Table extraction and markdown conversion
- Integration with shared processors (chapter_detector, text_cleaner)
"""

# Standard library
import io
import logging
import signal
import statistics
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party
import fitz  # PyMuPDF
from PIL import Image

# Local
from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from ..processors.metadata_builder import MetadataBuilder

logger = logging.getLogger(__name__)

# Constants
SCANNED_PDF_THRESHOLD = 100  # Character count below which to trigger OCR
OCR_DPI = 300  # DPI for OCR processing
HEADING_SEARCH_WINDOW = 100  # Character window for heading text search
READING_SPEED_WPM = 250  # Words per minute for reading time estimation
DEFAULT_OCR_TIMEOUT = 300  # Default OCR timeout in seconds (5 minutes)
DEFAULT_MAX_HEADING_WORDS = 25  # Default maximum words in heading
MIN_TABLE_ROWS = 2  # Minimum table rows for extraction
MIN_IMAGE_SIZE = 100  # Minimum image dimension in pixels


@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for enforcing timeouts using signals.

    Args:
        seconds: Maximum execution time in seconds.

    Raises:
        TimeoutError: If execution exceeds timeout.

    Note:
        Only works on Unix-like systems. On Windows, timeout is not enforced.
    """

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Signal-based timeout only works on Unix-like systems
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # On Windows, no timeout enforcement (log warning)
        logger.warning(
            "Timeout not enforced on this platform (signal.SIGALRM not available)"
        )
        yield


class PDFParser(BaseParser):
    """
    Parser for PDF files using PyMuPDF with OCR fallback.

    Features:
    - Text extraction from text-based PDFs
    - Font-based heading detection for chapter structure
    - OCR fallback for scanned/image-based PDFs using Tesseract
    - Image extraction with metadata
    - Table extraction and markdown conversion
    - Metadata extraction from PDF properties

    Options:
        extract_images (bool): Extract embedded images (default: True)
        image_output_dir (Path): Directory for extracted images (default: temp)
        ocr_enabled (bool): Enable OCR for scanned PDFs (default: True)
        ocr_language (str): Tesseract language code (default: 'eng').
            For non-English PDFs, specify the appropriate language code
            (e.g., 'fra' for French, 'deu' for German).
        min_heading_size (float): Minimum font size for headings (default: auto-detect)
        extract_tables (bool): Extract and convert tables (default: True)
        clean_text (bool): Apply text cleaning (default: True)
        detect_chapters (bool): Enable chapter detection (default: True)
        min_chapter_level (int): Minimum heading level for chapters (default: 1)
        max_chapter_level (int): Maximum heading level for chapters (default: 2)
        include_page_breaks (bool): Include page break markers in content (default: False)
        max_pages (int): Maximum number of pages to process (default: None = all pages)
        max_images (int): Maximum number of images to extract (default: None = all images)
        ocr_timeout (int): Timeout for OCR operations in seconds (default: 300)
        max_heading_words (int): Maximum words in a heading (default: 25).
            Increase for academic papers with long section titles.
            Decrease for documents with short, concise headings.

    Security Notes:
        - Use max_pages and max_images when processing untrusted PDFs to prevent DoS
        - OCR operations are resource-intensive; ocr_timeout prevents runaway processes
        - Temp directory is automatically cleaned up on completion/error
        - All file paths are validated before processing

    Performance Notes:
        - For PDFs with 100+ pages, consider using max_pages option to limit memory usage
        - Processing is done in-memory without streaming
        - OCR is significantly slower than text extraction (factor of 10-100x)
        - Font analysis scales linearly with number of text blocks

    Example:
        >>> # Basic usage
        >>> parser = PDFParser({'extract_images': True, 'ocr_enabled': True})
        >>> doc = parser.parse(Path("document.pdf"))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")
        >>>
        >>> # Processing untrusted PDFs
        >>> parser = PDFParser({
        ...     'max_pages': 100,
        ...     'max_images': 50,
        ...     'ocr_enabled': False  # Disable expensive OCR
        ... })
        >>> doc = parser.parse(Path("untrusted.pdf"))
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize PDF parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Check PyMuPDF version for table extraction support
        fitz_version = tuple(map(int, fitz.version[0].split(".")))
        self._table_extraction_supported = fitz_version >= (1, 18, 0)
        if not self._table_extraction_supported:
            logger.warning(
                f"PyMuPDF version {fitz.version[0]} does not support table extraction. "
                "Tables will not be extracted. Please upgrade to 1.18.0 or later."
            )

        # Set default options (using module constants)
        self.options.setdefault("extract_images", True)
        self.options.setdefault("image_output_dir", None)
        self.options.setdefault("ocr_enabled", True)
        self.options.setdefault("ocr_language", "eng")
        self.options.setdefault("min_heading_size", None)
        self.options.setdefault("extract_tables", True)
        self.options.setdefault("clean_text", True)
        self.options.setdefault("detect_chapters", True)
        self.options.setdefault("min_chapter_level", 1)
        self.options.setdefault("max_chapter_level", 2)
        self.options.setdefault("include_page_breaks", False)
        self.options.setdefault("max_pages", None)
        self.options.setdefault("max_images", None)
        self.options.setdefault("ocr_timeout", DEFAULT_OCR_TIMEOUT)
        self.options.setdefault("max_heading_words", DEFAULT_MAX_HEADING_WORDS)

        # Initialize tracking
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None

    def supports_format(self, file_path: Union[Path, str]) -> bool:
        """Check if file is PDF format.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .pdf extension, False otherwise.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() == ".pdf"

    def parse(self, file_path: Union[Path, str]) -> Document:
        """
        Parse PDF file and return Document object.

        Process:
        1. Open PDF with PyMuPDF
        2. Extract metadata from PDF properties
        3. Detect if text-based or scanned (check text content ratio)
        4. Extract text (native or OCR)
        5. Analyze font sizes to detect headings
        6. Convert detected headings to markdown
        7. Use chapter_detector to create chapters
        8. Extract images if enabled
        9. Extract tables if enabled
        10. Apply text cleaning
        11. Build and return Document

        Args:
            file_path: Path to PDF file

        Returns:
            Document object with parsed content

        Raises:
            FileReadError: If PDF cannot be opened
            ParsingError: If parsing fails
        """
        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)

        self._start_time = time.time()
        self._warnings = []

        pdf_doc = None
        try:
            # Step 1: Validate PDF file
            self._validate_pdf(file_path)

            # Step 2: Load PDF with PyMuPDF
            logger.info(f"Loading PDF: {file_path}")
            pdf_doc = self._load_pdf(file_path)

            # Check page limit
            max_pages = self.options.get("max_pages")
            if max_pages and len(pdf_doc) > max_pages:
                logger.warning(f"PDF has {len(pdf_doc)} pages, limiting to {max_pages}")
                self._warnings.append(
                    f"PDF truncated: {len(pdf_doc)} pages > max_pages ({max_pages})"
                )

            # Step 3: Extract metadata
            logger.info("Extracting metadata")
            metadata = self._extract_metadata(pdf_doc, file_path)

            # Step 4: Detect if scanned PDF
            logger.info("Detecting PDF type (text-based vs scanned)")
            is_scanned = self._is_scanned_pdf(pdf_doc)

            # Step 5: Extract text
            logger.info("Extracting text content")
            if is_scanned and self.options.get("ocr_enabled"):
                logger.info("Using OCR for scanned PDF")
                content = self._extract_text_with_ocr(pdf_doc)
                text_blocks = []  # OCR doesn't provide font info
            else:
                content, text_blocks = self._extract_text_with_formatting(pdf_doc)

            # Step 6: Detect headings and convert to markdown
            chapters: List[Chapter] = []
            if self.options.get("detect_chapters") and text_blocks:
                logger.info("Detecting headings from font analysis")
                headings = self._detect_headings_from_fonts(text_blocks)

                if headings:
                    logger.info(f"Found {len(headings)} headings")
                    content = self._convert_headings_to_markdown(content, headings)

            # Step 7: Detect chapters from markdown
            if self.options.get("detect_chapters"):
                logger.info("Detecting chapters")
                chapters = self._detect_chapters_from_markdown(content)

            # Step 8: Extract images (if enabled)
            images: List[ImageReference] = []
            if self.options.get("extract_images"):
                logger.info("Extracting images")
                try:
                    images = self._extract_images(pdf_doc)
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    self._warnings.append(f"Image extraction failed: {e}")

            # Step 9: Extract tables (if enabled)
            if self.options.get("extract_tables"):
                logger.info("Extracting tables")
                try:
                    tables = self._extract_tables(pdf_doc)
                    if tables:
                        # Append tables to content
                        content += "\n\n" + "\n\n".join(tables)
                except Exception as e:
                    logger.warning(f"Table extraction failed: {e}")
                    self._warnings.append(f"Table extraction failed: {e}")

            # Step 10: Clean text (if enabled)
            if self.options.get("clean_text"):
                logger.info("Cleaning text")
                content = self.clean_text(content)
                for chapter in chapters:
                    chapter.content = self.clean_text(chapter.content)

            # Step 11: Calculate statistics
            word_count = self._count_words(content)
            reading_time = self._estimate_reading_time(word_count)

            # Step 12: Create processing info
            processing_time = time.time() - self._start_time
            processing_info = ProcessingInfo(
                parser_used="PDFParser",
                parser_version="1.0.0",
                processing_time=processing_time,
                timestamp=datetime.now(),
                warnings=self._warnings,
                options_used=self.options,
            )

            # Step 13: Create Document object
            document = Document(
                document_id=str(uuid.uuid4()),
                content=content,
                chapters=chapters,
                images=images,
                metadata=metadata,
                processing_info=processing_info,
                word_count=word_count,
                estimated_reading_time=reading_time,
            )

            logger.info(
                f"PDF parsing complete: {word_count} words, "
                f"{len(chapters)} chapters, {len(images)} images"
            )

            return document

        except fitz.FileDataError as e:
            raise FileReadError(f"Failed to read PDF file: {e}")
        except Exception as e:
            raise ParsingError(f"PDF parsing failed: {e}", parser="PDFParser")
        finally:
            # Always cleanup resources, even if an exception occurred
            if pdf_doc is not None:
                try:
                    pdf_doc.close()
                except Exception as e:
                    logger.warning(f"Error closing PDF document: {e}")

            if self._temp_dir is not None:
                try:
                    self._temp_dir.cleanup()
                    self._temp_dir = None
                except Exception as e:
                    logger.warning(f"Error cleaning up temp directory: {e}")

    def _validate_pdf(self, file_path: Path) -> None:
        """Validate PDF file exists and is readable.

        Args:
            file_path: Path to PDF file.

        Raises:
            ValidationError: If file validation fails.
        """
        if not file_path.exists():
            raise ValidationError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValidationError(f"Not a file: {file_path}")

        if not self.supports_format(file_path):
            raise ValidationError(f"Not a PDF file: {file_path}")

    def _load_pdf(self, file_path: Path) -> fitz.Document:
        """Load PDF file with PyMuPDF.

        Args:
            file_path: Path to PDF file.

        Returns:
            PyMuPDF Document object.

        Raises:
            FileReadError: If PDF cannot be opened.
        """
        try:
            doc = fitz.open(file_path)
            return doc
        except Exception as e:
            raise FileReadError(f"Failed to open PDF: {e}")

    def _is_scanned_pdf(self, doc: fitz.Document) -> bool:
        """
        Determine if PDF is scanned (image-based) or text-based.

        Strategy:
        - Sample first 3 pages (or all if < 3)
        - Count extracted text characters
        - If < SCANNED_PDF_THRESHOLD chars per page on average, consider scanned

        Args:
            doc: PyMuPDF document object

        Returns:
            True if scanned (needs OCR), False if text-based
        """
        sample_pages = min(3, len(doc))
        total_chars = 0

        for page_num in range(sample_pages):
            page = doc[page_num]
            text = page.get_text()
            total_chars += len(text.strip())

        avg_chars_per_page = total_chars / sample_pages if sample_pages > 0 else 0

        # Threshold: < SCANNED_PDF_THRESHOLD chars per page suggests scanned PDF
        is_scanned = avg_chars_per_page < SCANNED_PDF_THRESHOLD

        if is_scanned:
            logger.info(
                f"PDF appears to be scanned "
                f"(avg {avg_chars_per_page:.0f} chars/page, "
                f"threshold={SCANNED_PDF_THRESHOLD})"
            )
        else:
            logger.info(
                f"PDF appears to be text-based "
                f"(avg {avg_chars_per_page:.0f} chars/page)"
            )

        return is_scanned

    def _extract_text_with_formatting(
        self, doc: fitz.Document
    ) -> Tuple[str, List[Dict]]:
        """
        Extract text with font information for heading detection.

        Returns:
        - full_text: Complete text content
        - text_blocks: List of dicts with {text, font_size, font_weight, is_bold, page_num}

        Args:
            doc: PyMuPDF document object

        Returns:
            Tuple of (full_text, text_blocks)
        """
        full_text = []
        text_blocks = []
        current_position = 0  # Track position incrementally (O(1) instead of O(n²))

        # Apply page limit if specified
        max_pages = self.options.get("max_pages")
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
            if self.options.get("include_page_breaks", False):
                page_marker = f"\n\n--- Page {page_num + 1} ---\n\n"
                full_text.append(page_marker)
                current_position += len(page_marker) + 1

        return " ".join(full_text), text_blocks

    def _extract_text_with_ocr(self, doc: fitz.Document) -> str:
        """
        Extract text using OCR (Tesseract) for scanned PDFs.

        Process:
        1. Convert each page to PIL Image
        2. Run Tesseract OCR (with timeout enforcement)
        3. Combine results
        4. Add page markers

        Args:
            doc: PyMuPDF document object

        Returns:
            OCR-extracted text

        Raises:
            TimeoutError: If OCR processing exceeds configured timeout
        """
        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract not available, falling back to text extraction")
            self._warnings.append("OCR not available, using basic text extraction")
            return self._extract_text_with_formatting(doc)[0]

        full_text = []
        language = self.options.get("ocr_language", "eng")
        ocr_timeout = self.options.get("ocr_timeout", DEFAULT_OCR_TIMEOUT)

        # Apply page limit if specified
        max_pages = self.options.get("max_pages")
        num_pages = min(len(doc), max_pages) if max_pages else len(doc)

        # Wrap OCR processing in timeout context
        try:
            with timeout_context(ocr_timeout):
                for page_num in range(num_pages):
                    page = doc[page_num]

                    # Convert page to image
                    pix = page.get_pixmap(dpi=OCR_DPI)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # Run OCR
                    try:
                        text = pytesseract.image_to_string(img, lang=language)
                        full_text.append(text.strip())
                        # Add page break marker (if enabled)
                        if self.options.get("include_page_breaks", False):
                            full_text.append(f"\n\n--- Page {page_num + 1} ---\n\n")
                    except Exception as e:
                        logger.warning(f"OCR failed on page {page_num + 1}: {e}")
                        self._warnings.append(f"OCR failed on page {page_num + 1}")
        except TimeoutError as e:
            logger.error(f"OCR processing timed out: {e}")
            raise ParsingError(
                f"OCR processing exceeded timeout of {ocr_timeout} seconds",
                parser="PDFParser",
                original_error=e,
            )

        return "\n".join(full_text)

    def _detect_headings_from_fonts(
        self, text_blocks: List[Dict]
    ) -> List[Tuple[str, int, int]]:
        """
        Detect headings based on font size analysis.

        Algorithm:
        1. Calculate average font size across document
        2. Calculate standard deviation
        3. Threshold = average + (1.5 * std_dev)
        4. Blocks above threshold = headings
        5. Map font sizes to heading levels (1-6)

        Args:
            text_blocks: List of text blocks with font info

        Returns:
            List of (heading_text, level, position) tuples
        """
        if not text_blocks:
            return []

        # Calculate font size statistics using statistics module
        font_sizes = [block["font_size"] for block in text_blocks]
        avg_size = statistics.mean(font_sizes)
        std_dev = statistics.stdev(font_sizes) if len(font_sizes) > 1 else 0.0

        # Determine heading threshold
        min_heading_size = self.options.get("min_heading_size")
        if min_heading_size is None:
            min_heading_size = avg_size + (1.5 * std_dev)

        # Find headings
        headings = []
        unique_sizes = sorted(set(font_sizes), reverse=True)
        max_heading_words = self.options.get("max_heading_words", 25)

        for block in text_blocks:
            # Refined heuristic: heading must meet one of these criteria:
            # 1. Font size above threshold
            # 2. Bold AND font size above average (not just any bold text)
            is_heading_candidate = block["font_size"] >= min_heading_size or (
                block["is_bold"] and block["font_size"] > avg_size
            )

            if is_heading_candidate:
                # Only consider lines with reasonable length for headings
                text = block["text"].strip()
                word_count = len(text.split())
                # Headings are typically 1-25 words (configurable via options)
                if 1 <= word_count <= max_heading_words:
                    # Map font size to heading level
                    level = self._map_font_size_to_level(
                        block["font_size"], unique_sizes
                    )
                    headings.append((text, level, block["position"]))

        logger.info(
            f"Font analysis: avg={avg_size:.1f}, std={std_dev:.1f}, "
            f"threshold={min_heading_size:.1f}, found {len(headings)} headings"
        )

        return headings

    def _map_font_size_to_level(
        self, font_size: float, unique_sizes: List[float]
    ) -> int:
        """Map font size to heading level (1-6).

        Larger fonts get lower level numbers (1 is biggest).

        Args:
            font_size: Font size to map.
            unique_sizes: Sorted list of unique font sizes (descending).

        Returns:
            Heading level (1-6).
        """
        # Find position in sorted sizes
        try:
            position = unique_sizes.index(font_size)
            # Map to level 1-6
            level = min(position + 1, 6)
            return level
        except ValueError:
            return 3  # Default to level 3 if not found

    def _convert_headings_to_markdown(
        self, text: str, headings: List[Tuple[str, int, int]]
    ) -> str:
        """
        Convert detected headings to markdown format.

        Replace heading text in content with markdown headings:
        - Level 1: # Heading
        - Level 2: ## Heading
        - etc.

        Uses position-based replacement to avoid replacing wrong occurrences.

        Args:
            text: Original text
            headings: Detected headings with levels (text, level, position)

        Returns:
            Text with markdown headings
        """
        if not headings:
            return text

        # Sort headings by position (descending) to process from end to start
        # This avoids position offset issues when modifying the string
        sorted_headings = sorted(headings, key=lambda x: x[2], reverse=True)

        result = text
        for heading_text, level, approx_position in sorted_headings:
            # Create markdown heading
            markdown_heading = f"\n{'#' * level} {heading_text}\n"

            # Search for the heading text near the approximate position
            # Use a window around the position to account for minor discrepancies
            search_start = max(0, approx_position - HEADING_SEARCH_WINDOW)
            search_end = min(
                len(result), approx_position + len(heading_text) + HEADING_SEARCH_WINDOW
            )
            search_region = result[search_start:search_end]

            # Find the heading text in the search region
            heading_index = search_region.find(heading_text)

            if heading_index != -1:
                # Calculate actual position in the full text
                actual_position = search_start + heading_index

                # Replace at the specific position
                result = (
                    result[:actual_position]
                    + markdown_heading
                    + result[actual_position + len(heading_text) :]
                )
            else:
                # Fallback: use simple replacement if position-based fails
                # This handles cases where spacing might have changed
                logger.debug(
                    f"Position-based replacement failed for '{heading_text}', "
                    f"using fallback"
                )
                result = result.replace(heading_text, markdown_heading, 1)

        return result

    def _detect_chapters_from_markdown(self, text: str) -> List[Chapter]:
        """
        Detect chapters from markdown headings.

        Uses the shared chapter_detector processor.

        Args:
            text: Markdown text with headings.

        Returns:
            List of Chapter objects.
        """
        from ..processors.chapter_detector import detect_chapters

        min_level = self.options.get("min_chapter_level", 1)
        max_level = self.options.get("max_chapter_level", 2)

        chapters = detect_chapters(text, min_level=min_level, max_level=max_level)

        logger.info(f"Detected {len(chapters)} chapters")

        return chapters

    def _extract_metadata(self, doc: fitz.Document, file_path: Path) -> Metadata:
        """
        Extract metadata from PDF properties.

        PDF Properties:
        - Title: doc.metadata['title']
        - Author: doc.metadata['author']
        - Subject: doc.metadata['subject']
        - Keywords: doc.metadata['keywords']
        - Creator: doc.metadata['creator']
        - Producer: doc.metadata['producer']
        - CreationDate: doc.metadata['creationDate']

        Args:
            doc: PyMuPDF document object
            file_path: Path to PDF file

        Returns:
            Metadata object
        """
        meta = doc.metadata or {}

        # Extract basic metadata
        title = meta.get("title") or file_path.stem
        author = meta.get("author")
        subject = meta.get("subject")
        keywords = meta.get("keywords")
        creator = meta.get("creator")
        producer = meta.get("producer")

        # Parse creation date
        creation_date = None
        if meta.get("creationDate"):
            try:
                # PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
                date_str = meta["creationDate"]
                if date_str.startswith("D:"):
                    date_str = date_str[2:16]  # Extract YYYYMMDDHHmmSS
                    creation_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            except Exception as e:
                logger.warning(f"Failed to parse creation date: {e}")

        # Parse keywords into tags
        tags = []
        if keywords:
            tags = [k.strip() for k in keywords.split(",") if k.strip()]

        # Get file size
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Custom fields for PDF-specific metadata
        custom_fields = {
            "page_count": len(doc),
            "creator": creator,
            "producer": producer,
            "pdf_version": doc.metadata.get("format", "Unknown"),
        }

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

    def _extract_images(self, doc: fitz.Document) -> List[ImageReference]:
        """
        Extract embedded images from PDF.

        Process:
        1. Iterate through pages
        2. Get image list: page.get_images()
        3. Extract image data: doc.extract_image(xref)
        4. Validate and save using shared image_extractor
        5. Create ImageReference objects

        Args:
            doc: PyMuPDF document object

        Returns:
            List of ImageReference objects
        """
        from ..processors.image_extractor import (
            get_image_dimensions,
            save_image,
            validate_image_data,
        )

        images = []

        # Set up output directory
        if self.options.get("image_output_dir"):
            output_dir = Path(self.options["image_output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Use temp directory
            if not self._temp_dir:
                self._temp_dir = tempfile.TemporaryDirectory()
            output_dir = Path(self._temp_dir.name)

        image_counter = 0
        max_images = self.options.get("max_images")

        for page_num in range(len(doc)):
            # Check if we've reached the image limit
            if max_images and image_counter >= max_images:
                logger.info(
                    f"Reached max_images limit ({max_images}), stopping extraction"
                )
                self._warnings.append(
                    f"Image extraction limited to {max_images} images"
                )
                break
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    if not base_image:
                        continue

                    image_data = base_image["image"]
                    image_ext = base_image["ext"]

                    # Validate image data using shared utility
                    is_valid, error = validate_image_data(
                        image_data, min_size=MIN_IMAGE_SIZE
                    )
                    if not is_valid:
                        logger.debug(
                            f"Skipping invalid image on page {page_num + 1}: {error}"
                        )
                        continue

                    # Increment counter
                    image_counter += 1

                    # Save image using shared utility
                    image_path, format_name = save_image(
                        image_data,
                        output_dir,
                        base_name="img",
                        extension=image_ext,
                        counter=image_counter,
                    )

                    # Get image dimensions using shared utility
                    width, height, detected_format = get_image_dimensions(image_data)
                    if detected_format != "unknown":
                        format_name = detected_format

                    # Create ImageReference
                    img_ref = ImageReference(
                        image_id=f"img_{image_counter:04d}",
                        position=page_num * 1000 + img_index,  # Approximate position
                        file_path=str(image_path),
                        alt_text=f"Image on page {page_num + 1}",
                        size=(width, height) if width and height else None,
                        format=format_name,
                    )

                    images.append(img_ref)

                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index} "
                        f"on page {page_num + 1}: {e}"
                    )

        logger.info(f"Extracted {len(images)} images")
        return images

    def _extract_tables(self, doc: fitz.Document) -> List[str]:
        """
        Extract tables and convert to markdown format.

        Note: PyMuPDF has basic table detection via page.find_tables()
        Requires PyMuPDF version 1.18.0 or later.

        Args:
            doc: PyMuPDF document object

        Returns:
            List of markdown-formatted tables
        """
        # Check if table extraction is supported in this PyMuPDF version
        if not self._table_extraction_supported:
            logger.debug("Table extraction not supported in this PyMuPDF version")
            return []

        tables = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            try:
                # Find tables on page
                table_finder = page.find_tables()

                if not table_finder or not table_finder.tables:
                    continue

                for table in table_finder.tables:
                    # Extract table data
                    table_data = table.extract()

                    if not table_data:
                        continue

                    # Convert to markdown
                    markdown_table = self._table_to_markdown(table_data)
                    if markdown_table:
                        tables.append(
                            f"**Table from page {page_num + 1}**\n\n{markdown_table}"
                        )

            except AttributeError as e:
                # find_tables() might not be available in all PyMuPDF versions
                logger.debug(
                    f"Table extraction not supported or failed on page {page_num + 1}: {e}"
                )
            except Exception as e:
                # Log exception type for debugging
                logger.warning(
                    f"Table extraction failed on page {page_num + 1} "
                    f"({type(e).__name__}): {e}"
                )

        logger.info(f"Extracted {len(tables)} tables")
        return tables

    def _table_to_markdown(self, table_data: List[List]) -> str:
        """Convert table data to markdown format.

        Single-row tables (header only) are discarded as they likely
        represent formatting artifacts rather than actual data tables.

        Args:
            table_data: 2D list of table cells.

        Returns:
            Markdown-formatted table string, or empty string if invalid.
        """
        if not table_data:
            return ""

        if len(table_data) < MIN_TABLE_ROWS:
            # Single-row table (just headers) - likely not a real table
            logger.debug(f"Discarding single-row table: {table_data[0]}")
            return ""

        lines = []

        # Header row
        header = table_data[0]
        lines.append("| " + " | ".join(str(cell or "") for cell in header) + " |")

        # Separator
        lines.append("| " + " | ".join("---" for _ in header) + " |")

        # Data rows
        for row in table_data[1:]:
            lines.append("| " + " | ".join(str(cell or "") for cell in row) + " |")

        return "\n".join(lines)

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Text to count words in.

        Returns:
            Word count.
        """
        words = [word for word in text.split() if word.strip()]
        return len(words)

    def _estimate_reading_time(self, word_count: int) -> int:
        """Estimate reading time in minutes.

        Uses average reading speed of READING_SPEED_WPM words per minute.

        Args:
            word_count: Number of words.

        Returns:
            Estimated reading time in minutes.
        """
        return max(1, word_count // READING_SPEED_WPM)
