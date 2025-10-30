"""
PDF parser module for OmniParser.

This module provides both functional and object-oriented interfaces to PDF parsing:
- parse_pdf(): Functional interface (recommended for new code)
- PDFParser: Class-based interface (for backward compatibility)

The PDFParser class is a thin wrapper around parse_pdf() that maintains the
same API as the legacy implementation while delegating to the modular functional code.

This module provides PDF parsing functionality with support for:
- Text extraction (with OCR for scanned documents)
- Metadata extraction
- Heading detection and chapter structure
- Image extraction
- Table extraction

Example:
    >>> from pathlib import Path
    >>> from omniparser.parsers.pdf import parse_pdf
    >>> doc = parse_pdf(Path("document.pdf"))
    >>> print(doc.metadata.title)
"""

# Standard library
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Local imports
from ...base.base_parser import BaseParser
from ...models import Document
from .parser import parse_pdf


class PDFParser(BaseParser):
    """Parser for PDF files using PyMuPDF (fitz) library.

    This is a thin wrapper around the functional parse_pdf() implementation
    that maintains backward compatibility with the original class-based API.

    Features:
    - Text extraction (with OCR for scanned documents)
    - Metadata extraction (title, author, dates, etc.)
    - Heading detection and chapter structure
    - Image extraction with configurable output directory
    - Table extraction
    - Processing statistics and timing

    Options:
        use_ocr (bool): Enable OCR for scanned PDFs. Default: True
        ocr_language (str): OCR language code. Default: 'eng'
        ocr_timeout (int): OCR timeout in seconds. Default: 300
        max_pages (int): Maximum pages to process. Default: None (all pages)
        extract_images (bool): Extract images. Default: True if output_dir provided
        extract_tables (bool): Extract tables. Default: True
        clean_text (bool): Apply text cleaning. Default: True
        output_dir (str|Path): Directory to save extracted images. Default: None

    Example:
        >>> parser = PDFParser({'use_ocr': True, 'clean_text': True})
        >>> doc = parser.parse(Path('document.pdf'))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Pages: {doc.metadata.custom_fields['page_count']}")
        >>> print(f"Chapters: {len(doc.chapters)}")

    Note:
        For new code, consider using the functional parse_pdf() interface directly:
        >>> from omniparser.parsers.pdf import parse_pdf
        >>> doc = parse_pdf('document.pdf', use_ocr=True)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize PDF parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
        self.options.setdefault("use_ocr", True)
        self.options.setdefault("ocr_language", "eng")
        self.options.setdefault("ocr_timeout", 300)
        self.options.setdefault("max_pages", None)
        self.options.setdefault("extract_images", True)
        self.options.setdefault("extract_tables", True)
        self.options.setdefault("clean_text", True)
        self.options.setdefault("output_dir", None)

    @classmethod
    def supports_format(cls, file_path: Union[Path, str]) -> bool:
        """Check if file is a PDF.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .pdf extension, False otherwise.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() == ".pdf"

    def parse(self, file_path: Union[Path, str]) -> Document:
        """Parse PDF file and return Document object.

        This method delegates to the functional parse_pdf() implementation,
        passing along the configured options.

        Args:
            file_path: Path to PDF file.

        Returns:
            Document object with parsed content, chapters, images, metadata,
            and processing info.

        Raises:
            FileReadError: If file cannot be read or is not a valid PDF.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.
        """
        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Extract output_dir from options if present
        output_dir = self.options.get("output_dir")
        if output_dir is not None and not isinstance(output_dir, Path):
            output_dir = Path(output_dir)

        # Create options dict without output_dir (it's a separate parameter)
        parse_options = {
            k: v for k, v in self.options.items() if k != "output_dir"
        }

        # Delegate to functional implementation
        return parse_pdf(file_path, output_dir=output_dir, options=parse_options)


__all__ = ["PDFParser", "parse_pdf"]
