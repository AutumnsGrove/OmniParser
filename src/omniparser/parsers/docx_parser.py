"""
DOCX parser implementation using python-docx.

This module provides the DOCXParser class for parsing Microsoft Word DOCX files
and converting them to OmniParser's universal Document format. It includes
style-based heading detection, formatting preservation, image extraction,
table conversion, and text cleaning.

Features:
- Style-based heading detection (Heading 1 through Heading 6)
- Formatting preservation (bold, italic)
- Image extraction with metadata
- Table extraction and markdown conversion
- Metadata from document properties

Not Yet Implemented:
- List conversion (bullets and numbered lists) - TODO
- Hyperlink extraction and conversion - TODO
"""

import io
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from docx import Document as DocxDocument  # type: ignore[import]
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image

from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from ..processors.chapter_detector import detect_chapters
from ..processors.text_cleaner import clean_text

logger = logging.getLogger(__name__)

# Security: Maximum size for individual images (50MB)
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB


class DOCXParser(BaseParser):
    """Parser for Microsoft Word DOCX files using python-docx.

    Features:
    - Style-based heading detection (Heading 1 through Heading 6)
    - Formatting preservation (bold, italic)
    - Image extraction with metadata
    - Table extraction and markdown conversion
    - Metadata from document properties

    Not Yet Implemented (TODO for future versions):
    - List conversion (bullets and numbered lists)
    - Hyperlink extraction and conversion

    Options:
        extract_images (bool): Extract embedded images. Default: True
        image_output_dir (str|Path): Directory for images. REQUIRED for image
            extraction - if None (default), images will NOT be extracted.
        preserve_formatting (bool): Preserve bold/italic formatting. Default: True
        extract_tables (bool): Extract and convert tables. Default: True
        clean_text (bool): Apply text cleaning. Default: True
        heading_styles (List[str]): Style names to treat as headings.
        min_chapter_level (int): Minimum heading level for chapters. Default: 1
        max_chapter_level (int): Maximum heading level for chapters. Default: 2

    Example:
        >>> parser = DOCXParser({
        ...     'extract_images': True,
        ...     'image_output_dir': '/path/to/images'
        ... })
        >>> doc = parser.parse(Path("report.docx"))
        >>> print(f"Chapters: {len(doc.chapters)}")
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize DOCX parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
        self.options.setdefault("extract_images", True)
        self.options.setdefault("image_output_dir", None)
        self.options.setdefault("preserve_formatting", True)
        self.options.setdefault("extract_tables", True)
        self.options.setdefault("clean_text", True)
        self.options.setdefault("min_chapter_level", 1)
        self.options.setdefault("max_chapter_level", 2)
        self.options.setdefault(
            "heading_styles",
            [
                "Heading 1",
                "Heading 2",
                "Heading 3",
                "Heading 4",
                "Heading 5",
                "Heading 6",
            ],
        )

        # Default heading styles
        self.heading_styles = self.options["heading_styles"]

        # Initialize tracking
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None
        self._image_counter = 0

    def supports_format(self, file_path: Union[Path, str]) -> bool:
        """Check if file is DOCX format.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .docx extension, False otherwise.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() in [".docx"]

    def parse(self, file_path: Union[Path, str]) -> Document:
        """Parse DOCX file and return Document object.

        This is the main entry point for DOCX parsing. It orchestrates:
        1. File validation
        2. DOCX loading
        3. Metadata extraction
        4. Content extraction (paragraphs, tables, images)
        5. Heading detection and markdown conversion
        6. Chapter detection using chapter_detector
        7. Text cleaning (if enabled)
        8. Document object creation

        Args:
            file_path: Path to DOCX file.

        Returns:
            Document object with parsed content, chapters, images, and metadata.

        Raises:
            FileReadError: If file cannot be read or is not a valid DOCX.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.
        """
        import time

        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)

        self._start_time = time.time()
        self._warnings = []
        self._image_counter = 0

        try:
            # Step 1: Validate DOCX file
            self._validate_docx(file_path)

            # Step 2: Load DOCX with python-docx
            logger.info(f"Loading DOCX: {file_path}")
            docx = self._load_docx(file_path)

            # Step 3: Extract metadata
            logger.info("Extracting metadata")
            metadata = self._extract_metadata(docx, file_path)

            # Step 4: Extract content (paragraphs and tables)
            logger.info("Extracting content")
            markdown_content = self._extract_content(docx)

            # Step 5: Extract images (if enabled)
            images: List[ImageReference] = []
            if self.options.get("extract_images"):
                logger.info("Extracting images")
                try:
                    images = self._extract_images(docx)
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    self._warnings.append(f"Image extraction failed: {e}")

            # Step 6: Detect chapters using chapter_detector
            logger.info("Detecting chapters")
            min_level = self.options.get("min_chapter_level", 1)
            max_level = self.options.get("max_chapter_level", 2)
            chapters = detect_chapters(markdown_content, min_level, max_level)

            # Step 7: Clean text (if enabled)
            if self.options.get("clean_text"):
                logger.info("Cleaning text")
                markdown_content = self.clean_text(markdown_content)
                for chapter in chapters:
                    chapter.content = self.clean_text(chapter.content)

            # Step 8: Calculate statistics
            word_count = self._count_words(markdown_content)
            reading_time = self._estimate_reading_time(word_count)

            # Step 9: Create processing info
            processing_time = time.time() - self._start_time
            processing_info = ProcessingInfo(
                parser_used="DOCXParser",
                parser_version="1.0.0",
                processing_time=processing_time,
                timestamp=datetime.now(),
                warnings=self._warnings,
                options_used=self.options.copy(),
            )

            # Step 10: Create and return Document
            document = Document(
                document_id=str(uuid.uuid4()),
                content=markdown_content,
                chapters=chapters,
                images=images,
                metadata=metadata,
                processing_info=processing_info,
                word_count=word_count,
                estimated_reading_time=reading_time,
            )

            logger.info(
                f"DOCX parsing complete: {word_count} words, {len(chapters)} chapters, {len(images)} images"
            )
            return document

        except (FileReadError, ValidationError):
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"DOCX parsing failed: {e}")
            raise ParsingError(
                f"Failed to parse DOCX file: {e}",
                parser="DOCXParser",
                original_error=e,
            )

    def _validate_docx(self, file_path: Path) -> None:
        """Validate DOCX file before parsing.

        Checks:
        - File exists
        - File is readable
        - File has .docx extension
        - File size is reasonable (not empty, not too large)

        Args:
            file_path: Path to DOCX file.

        Raises:
            FileReadError: If file doesn't exist or isn't readable.
            ValidationError: If file validation fails.
        """
        # Check file exists
        if not file_path.exists():
            raise FileReadError(f"File not found: {file_path}")

        # Check file is readable
        if not file_path.is_file():
            raise FileReadError(f"Not a file: {file_path}")

        # Check extension
        if not self.supports_format(file_path):
            raise ValidationError(f"Not a DOCX file: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"Empty file: {file_path}")

        # Warn if file is very large (>500MB)
        if file_size > 500 * 1024 * 1024:
            logger.warning(f"Large DOCX file ({file_size / 1024 / 1024:.1f} MB)")
            self._warnings.append(f"Large file size: {file_size / 1024 / 1024:.1f} MB")

    def _load_docx(self, file_path: Path) -> Any:
        """Load DOCX file using python-docx.

        Args:
            file_path: Path to DOCX file.

        Returns:
            DocxDocument object.

        Raises:
            ParsingError: If DOCX cannot be loaded.
        """
        try:
            docx = DocxDocument(str(file_path))  # type: ignore[misc]
            return docx
        except Exception as e:
            logger.error(f"Failed to load DOCX: {e}")
            raise ParsingError(
                f"Failed to load DOCX file: {e}",
                parser="DOCXParser",
                original_error=e,
            )

    def _extract_metadata(self, docx: Any, file_path: Path) -> Metadata:
        """Extract metadata from DOCX core properties.

        Available properties:
        - docx.core_properties.title
        - docx.core_properties.author
        - docx.core_properties.subject
        - docx.core_properties.keywords
        - docx.core_properties.comments
        - docx.core_properties.created
        - docx.core_properties.modified
        - docx.core_properties.last_modified_by

        Args:
            docx: DocxDocument object.
            file_path: Path to DOCX file (for file_size).

        Returns:
            Metadata object with extracted fields.
        """
        props = docx.core_properties

        # Extract title
        title = props.title or None

        # Extract author
        author = props.author or None

        # Extract keywords as tags
        tags: Optional[List[str]] = None
        if props.keywords:
            # Keywords are typically semicolon or comma separated
            tags = [
                tag.strip() for tag in re.split(r"[;,]", props.keywords) if tag.strip()
            ]

        # Extract description (subject or comments)
        description = props.subject or props.comments or None

        # Extract publication date (created or modified)
        publication_date: Optional[datetime] = None
        if props.created:
            publication_date = props.created
        elif props.modified:
            publication_date = props.modified

        # Calculate file size
        file_size = file_path.stat().st_size

        return Metadata(
            title=title,
            author=author,
            authors=[author] if author else None,
            publisher=None,  # DOCX doesn't have publisher field
            publication_date=publication_date,
            language=None,  # DOCX doesn't expose language in core properties
            isbn=None,
            description=description,
            tags=tags,
            original_format="docx",
            file_size=file_size,
            custom_fields={
                "last_modified_by": props.last_modified_by,
                "modified": props.modified.isoformat() if props.modified else None,
            },
        )

    def _extract_content(self, docx: Any) -> str:
        """Extract all content from DOCX and convert to markdown.

        Processes document elements in order (paragraphs, tables) and converts
        them to markdown format. Preserves formatting if enabled.

        Args:
            docx: DocxDocument object.

        Returns:
            Full document content in markdown format.
        """
        markdown_parts: List[str] = []

        # Iterate through all document elements (paragraphs and tables)
        for element in docx.element.body:
            # Check if it's a paragraph
            if isinstance(element, CT_P):
                para = Paragraph(element, docx)
                markdown_text = self._paragraph_to_markdown(para)
                if markdown_text.strip():  # Skip empty paragraphs
                    markdown_parts.append(markdown_text)

            # Check if it's a table
            elif isinstance(element, CT_Tbl):
                if self.options.get("extract_tables"):
                    table = Table(element, docx)
                    markdown_table = self._table_to_markdown(table)
                    if markdown_table.strip():
                        markdown_parts.append(markdown_table)
                        markdown_parts.append("")  # Add blank line after table

        # Join all parts with newlines
        return "\n\n".join(markdown_parts)

    def _paragraph_to_markdown(self, para: Paragraph) -> str:
        """Convert DOCX paragraph to markdown.

        Currently Handles:
        - Heading styles → markdown headings (# ## ###)
        - Bold text → **text**
        - Italic text → *text*

        Not Yet Implemented (TODO):
        - Hyperlinks → [text](url)
        - Lists → - item or 1. item

        Args:
            para: python-docx Paragraph object.

        Returns:
            Markdown-formatted text.
        """
        # Check if it's a heading
        if self._is_heading(para):
            level = self._get_heading_level(para)
            heading_prefix = "#" * level
            text = para.text.strip()
            return f"{heading_prefix} {text}"

        # Process runs with formatting
        if self.options.get("preserve_formatting"):
            formatted_text = ""
            for run in para.runs:
                formatted_text += self._run_to_markdown(run)
            return formatted_text.strip()
        else:
            # Just return plain text
            return para.text.strip()

    def _run_to_markdown(self, run: Any) -> str:
        """Convert text run with formatting to markdown.

        Args:
            run: python-docx Run object.

        Returns:
            Formatted text (e.g., **bold**, *italic*).
        """
        text = str(run.text) if run.text else ""

        # TODO: Handle hyperlinks - they're complex in DOCX XML structure
        # Hyperlinks are stored in the document's relationships, not directly
        # in runs. Future implementation needed to extract and convert them.

        # Apply formatting
        if run.bold and run.italic:
            return f"***{text}***"
        elif run.bold:
            return f"**{text}**"
        elif run.italic:
            return f"*{text}*"
        else:
            return text

    def _is_heading(self, para: Paragraph) -> bool:
        """Check if paragraph is a heading style.

        Args:
            para: Paragraph to check.

        Returns:
            True if paragraph uses a heading style.
        """
        style_name = para.style.name if para.style else ""
        return style_name in self.heading_styles

    def _get_heading_level(self, para: Paragraph) -> int:
        """Get heading level (1-6) from style name.

        Args:
            para: Paragraph with heading style.

        Returns:
            Heading level (1-6).
        """
        style_name = para.style.name if para.style else ""
        if "Heading" in style_name:
            # Extract number from "Heading 1", "Heading 2", etc.
            try:
                match = re.search(r"Heading (\d+)", style_name)
                if match:
                    level = int(match.group(1))
                    return min(level, 6)  # Cap at 6
            except (ValueError, AttributeError):
                pass
        return 1

    def _table_to_markdown(self, table: Table) -> str:
        """Convert DOCX table to markdown table.

        Markdown table format:
        | Header 1 | Header 2 |
        |----------|----------|
        | Cell 1   | Cell 2   |

        Note: Pipe characters (|) in cell content are escaped as \\| to prevent
        breaking the table formatting.

        Args:
            table: python-docx Table object.

        Returns:
            Markdown-formatted table.
        """
        if not table.rows:
            return ""

        markdown_rows: List[str] = []

        # Process each row
        for row_idx, row in enumerate(table.rows):
            cells = []
            for cell in row.cells:
                # Get cell text (handle None case for empty cells)
                cell_text = (cell.text or "").strip().replace("\n", " ")
                # Escape pipe characters to prevent breaking table formatting
                cell_text = cell_text.replace("|", "\\|")
                cells.append(cell_text)

            # Create markdown row
            markdown_row = "| " + " | ".join(cells) + " |"
            markdown_rows.append(markdown_row)

            # Add separator after first row (header)
            if row_idx == 0:
                separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                markdown_rows.append(separator)

        return "\n".join(markdown_rows)

    def _extract_images(self, docx: Any) -> List[ImageReference]:
        """Extract embedded images from DOCX.

        IMPORTANT: Images are only extracted when image_output_dir is specified.
        If image_output_dir is None, images are not extracted and an empty list
        is returned. This prevents creating ImageReference objects with invalid
        file paths to deleted temporary directories.

        Process:
        1. Check if image_output_dir is specified
        2. If not, return empty list
        3. Access document relationships (docx.part.rels)
        4. Find image relationships (rId)
        5. Extract image data
        6. Save to output directory
        7. Create ImageReference objects

        Args:
            docx: DocxDocument object.

        Returns:
            List of ImageReference objects. Empty list if image_output_dir is None.
        """
        # Determine output directory
        image_output_dir = self.options.get("image_output_dir")

        # Only extract images if a persistent output directory is specified
        if image_output_dir is None:
            logger.info(
                "Skipping image extraction: no image_output_dir specified. "
                "Set image_output_dir option to extract images."
            )
            return []

        try:
            # Use persistent directory
            output_path = Path(image_output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving images to persistent directory: {output_path}")
            images = self._extract_images_to_directory(docx, output_path)
            logger.info(f"Successfully extracted {len(images)} images")
            return images

        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            raise ParsingError(
                f"Failed to extract images from DOCX: {e}",
                parser="DOCXParser",
                original_error=e,
            )

    def _extract_images_to_directory(
        self, docx: Any, output_path: Path
    ) -> List[ImageReference]:
        """Extract images to specified directory.

        Helper method that performs the actual image extraction and saves to
        the provided directory path. Includes security validation:
        - Skips images larger than 50MB (MAX_IMAGE_SIZE)
        - Validates image data with PIL before saving
        - Logs warnings and continues on invalid images

        Args:
            docx: DocxDocument object.
            output_path: Directory path to save images to.

        Returns:
            List of ImageReference objects with file paths pointing to saved images.
            Invalid or oversized images are skipped with warnings logged.
        """
        images: List[ImageReference] = []

        # Access document relationships to find images
        try:
            # Get all image parts from document relationships
            for rel in docx.part.rels.values():
                if "image" in rel.target_ref:
                    try:
                        self._image_counter += 1
                        image_part = rel.target_part
                        image_bytes = image_part.blob

                        # Security: Validate image size to prevent disk exhaustion
                        if len(image_bytes) > MAX_IMAGE_SIZE:
                            logger.warning(
                                f"Skipping image {self._image_counter}: too large "
                                f"({len(image_bytes) / 1024 / 1024:.1f} MB, max {MAX_IMAGE_SIZE / 1024 / 1024:.0f} MB)"
                            )
                            self._warnings.append(
                                f"Skipped oversized image: {len(image_bytes) / 1024 / 1024:.1f} MB"
                            )
                            continue

                        # Determine image format from content type
                        content_type = image_part.content_type
                        format_ext = "png"  # Default
                        if "jpeg" in content_type or "jpg" in content_type:
                            format_ext = "jpg"
                        elif "png" in content_type:
                            format_ext = "png"
                        elif "gif" in content_type:
                            format_ext = "gif"
                        elif "bmp" in content_type:
                            format_ext = "bmp"

                        # Create filename
                        image_filename = f"image_{self._image_counter:03d}.{format_ext}"
                        image_path = output_path / image_filename

                        # Validate image data with PIL before saving
                        try:
                            with Image.open(io.BytesIO(image_bytes)) as img:
                                # Just opening validates it's a valid image
                                img.verify()
                        except Exception as e:
                            logger.warning(
                                f"Skipping image {self._image_counter}: invalid image data ({e})"
                            )
                            self._warnings.append(f"Skipped invalid image: {e}")
                            continue

                        # Save image
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)

                        # Get image dimensions using PIL
                        width: Optional[int] = None
                        height: Optional[int] = None
                        format_name: str = "unknown"

                        try:
                            with Image.open(io.BytesIO(image_bytes)) as img:
                                width, height = img.size
                                format_name = (
                                    img.format.lower() if img.format else format_ext
                                )
                        except Exception as e:
                            logger.warning(f"Could not read image dimensions: {e}")
                            format_name = format_ext

                        # Create ImageReference
                        image_ref = ImageReference(
                            image_id=f"img_{self._image_counter:03d}",
                            position=0,  # We don't track exact position in DOCX
                            file_path=str(image_path),
                            alt_text=None,  # DOCX doesn't easily expose alt text
                            size=(width, height) if width and height else None,
                            format=format_name,
                        )

                        images.append(image_ref)
                        logger.debug(
                            f"Extracted image {self._image_counter}: {image_filename} ({format_name}, {width}x{height})"
                        )

                    except Exception as e:
                        logger.warning(
                            f"Failed to extract image {self._image_counter}: {e}"
                        )
                        self._warnings.append(f"Failed to extract image: {e}")
                        # Continue with next image

        except Exception as e:
            logger.warning(f"Error accessing document relationships: {e}")
            self._warnings.append(f"Error accessing document relationships: {e}")

        return images

    def _count_words(self, text: str) -> int:
        """Count words in text, excluding markdown syntax.

        Strips markdown formatting characters before counting to provide
        accurate word count of actual content.

        Args:
            text: Text to count words in (may contain markdown).

        Returns:
            Word count (excluding markdown syntax).
        """
        # Remove markdown headings
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove markdown bold/italic/bold-italic
        text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)  # ***text***
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **text**
        text = re.sub(r"\*(.+?)\*", r"\1", text)  # *text*

        # Remove markdown table pipes and separators
        text = re.sub(r"\|", " ", text)  # Remove table pipes
        text = re.sub(
            r"^[\s\-]+$", "", text, flags=re.MULTILINE
        )  # Remove separator rows

        # Remove escaped characters
        text = re.sub(r"\\(.)", r"\1", text)  # \| → |

        return len(text.split())

    def _estimate_reading_time(self, word_count: int) -> int:
        """Estimate reading time in minutes.

        Assumes average reading speed of 200-250 words per minute.
        Uses 225 WPM as middle ground.

        Args:
            word_count: Total word count.

        Returns:
            Estimated reading time in minutes.
        """
        return max(1, round(word_count / 225))
