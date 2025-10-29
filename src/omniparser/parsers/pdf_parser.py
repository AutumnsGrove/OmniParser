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

import io
import logging
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import fitz  # PyMuPDF
from PIL import Image

from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo

logger = logging.getLogger(__name__)


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
        ocr_language (str): Tesseract language code (default: 'eng')
        min_heading_size (float): Minimum font size for headings (default: auto-detect)
        extract_tables (bool): Extract and convert tables (default: True)
        clean_text (bool): Apply text cleaning (default: True)
        detect_chapters (bool): Enable chapter detection (default: True)
        min_chapter_level (int): Minimum heading level for chapters (default: 1)
        max_chapter_level (int): Maximum heading level for chapters (default: 2)

    Example:
        >>> parser = PDFParser({'extract_images': True, 'ocr_enabled': True})
        >>> doc = parser.parse(Path("document.pdf"))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize PDF parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
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

        try:
            # Step 1: Validate PDF file
            self._validate_pdf(file_path)

            # Step 2: Load PDF with PyMuPDF
            logger.info(f"Loading PDF: {file_path}")
            doc = self._load_pdf(file_path)

            # Step 3: Extract metadata
            logger.info("Extracting metadata")
            metadata = self._extract_metadata(doc, file_path)

            # Step 4: Detect if scanned PDF
            logger.info("Detecting PDF type (text-based vs scanned)")
            is_scanned = self._is_scanned_pdf(doc)

            # Step 5: Extract text
            logger.info("Extracting text content")
            if is_scanned and self.options.get("ocr_enabled"):
                logger.info("Using OCR for scanned PDF")
                content = self._extract_text_with_ocr(doc)
                text_blocks = []  # OCR doesn't provide font info
            else:
                content, text_blocks = self._extract_text_with_formatting(doc)

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
                    images = self._extract_images(doc)
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    self._warnings.append(f"Image extraction failed: {e}")

            # Step 9: Extract tables (if enabled)
            if self.options.get("extract_tables"):
                logger.info("Extracting tables")
                try:
                    tables = self._extract_tables(doc)
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

            # Close PDF document
            doc.close()

            # Cleanup temp directory if used
            if self._temp_dir:
                self._temp_dir.cleanup()

            logger.info(
                f"PDF parsing complete: {word_count} words, "
                f"{len(chapters)} chapters, {len(images)} images"
            )

            return document

        except fitz.FileDataError as e:
            raise FileReadError(f"Failed to read PDF file: {e}")
        except Exception as e:
            raise ParsingError(f"PDF parsing failed: {e}", parser="PDFParser")

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
        - If < 100 chars per page on average, consider scanned

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

        # Threshold: < 100 chars per page suggests scanned PDF
        is_scanned = avg_chars_per_page < 100

        if is_scanned:
            logger.info(
                f"PDF appears to be scanned "
                f"(avg {avg_chars_per_page:.0f} chars/page)"
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

        for page_num in range(len(doc)):
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

                        # Store text block info
                        text_blocks.append(
                            {
                                "text": text,
                                "font_size": font_size,
                                "is_bold": is_bold,
                                "page_num": page_num + 1,
                                "position": len(" ".join(full_text)),
                            }
                        )

                        full_text.append(text)

            # Add page break marker
            full_text.append(f"\n\n--- Page {page_num + 1} ---\n\n")

        return " ".join(full_text), text_blocks

    def _extract_text_with_ocr(self, doc: fitz.Document) -> str:
        """
        Extract text using OCR (Tesseract) for scanned PDFs.

        Process:
        1. Convert each page to PIL Image
        2. Run Tesseract OCR
        3. Combine results
        4. Add page markers

        Args:
            doc: PyMuPDF document object

        Returns:
            OCR-extracted text
        """
        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract not available, falling back to text extraction")
            self._warnings.append("OCR not available, using basic text extraction")
            return self._extract_text_with_formatting(doc)[0]

        full_text = []
        language = self.options.get("ocr_language", "eng")

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Convert page to image
            pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Run OCR
            try:
                text = pytesseract.image_to_string(img, lang=language)
                full_text.append(text.strip())
                full_text.append(f"\n\n--- Page {page_num + 1} ---\n\n")
            except Exception as e:
                logger.warning(f"OCR failed on page {page_num + 1}: {e}")
                self._warnings.append(f"OCR failed on page {page_num + 1}")

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

        # Calculate font size statistics
        font_sizes = [block["font_size"] for block in text_blocks]
        avg_size = sum(font_sizes) / len(font_sizes)
        variance = sum((s - avg_size) ** 2 for s in font_sizes) / len(font_sizes)
        std_dev = variance**0.5

        # Determine heading threshold
        min_heading_size = self.options.get("min_heading_size")
        if min_heading_size is None:
            min_heading_size = avg_size + (1.5 * std_dev)

        # Find headings
        headings = []
        unique_sizes = sorted(set(font_sizes), reverse=True)

        for block in text_blocks:
            if block["font_size"] >= min_heading_size or block["is_bold"]:
                # Only consider lines with reasonable length for headings
                text = block["text"].strip()
                word_count = len(text.split())
                # Headings are typically 1-20 words (adjust min to 1 to catch short headings)
                if 1 <= word_count <= 20:
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

        Args:
            text: Original text
            headings: Detected headings with levels

        Returns:
            Text with markdown headings
        """
        if not headings:
            return text

        # Sort headings by position (descending) to avoid offset issues
        sorted_headings = sorted(headings, key=lambda x: x[2], reverse=True)

        result = text
        for heading_text, level, position in sorted_headings:
            # Create markdown heading
            markdown_heading = f"\n{'#' * level} {heading_text}\n"

            # Find and replace the heading text
            # Use simple string replacement since positions might be approximate
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

        return Metadata(
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
        4. Save to output directory
        5. Create ImageReference objects

        Args:
            doc: PyMuPDF document object

        Returns:
            List of ImageReference objects
        """
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

        for page_num in range(len(doc)):
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

                    # Generate unique image ID
                    image_id = f"img_{image_counter:04d}"
                    image_counter += 1

                    # Save image file
                    image_filename = f"{image_id}.{image_ext}"
                    image_path = output_dir / image_filename

                    with open(image_path, "wb") as img_file:
                        img_file.write(image_data)

                    # Get image dimensions
                    try:
                        with Image.open(io.BytesIO(image_data)) as pil_img:
                            width, height = pil_img.size
                            size = (width, height)
                    except Exception:
                        size = None

                    # Create ImageReference
                    img_ref = ImageReference(
                        image_id=image_id,
                        position=page_num * 1000 + img_index,  # Approximate position
                        file_path=str(image_path),
                        alt_text=f"Image on page {page_num + 1}",
                        size=size,
                        format=image_ext,
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

        Args:
            doc: PyMuPDF document object

        Returns:
            List of markdown-formatted tables
        """
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

            except Exception as e:
                logger.warning(f"Table extraction failed on page {page_num + 1}: {e}")

        logger.info(f"Extracted {len(tables)} tables")
        return tables

    def _table_to_markdown(self, table_data: List[List]) -> str:
        """Convert table data to markdown format.

        Args:
            table_data: 2D list of table cells.

        Returns:
            Markdown-formatted table string.
        """
        if not table_data or len(table_data) < 2:
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

        Uses average reading speed of 250 words per minute.

        Args:
            word_count: Number of words.

        Returns:
            Estimated reading time in minutes.
        """
        return max(1, word_count // 250)
