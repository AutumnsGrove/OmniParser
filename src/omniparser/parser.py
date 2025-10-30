"""
Main parser module for OmniParser.

Provides the public parse_document() function that automatically detects
file formats and routes to appropriate parsers.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import UnsupportedFormatError, FileReadError
from .models import Document
from .parsers.epub_parser import EPUBParser
from .parsers.html_parser import HTMLParser
from .parsers.pdf import parse_pdf
from .parsers.markdown_parser import MarkdownParser
from .parsers.docx import parse_docx
from .parsers.text_parser import TextParser

logger = logging.getLogger(__name__)


def parse_document(
    file_path: str | Path, options: Optional[Dict[str, Any]] = None
) -> Document:
    """Parse a document file or URL and return a universal Document object.

    Automatically detects the file format and routes to the appropriate parser.
    Currently supported formats:
    - EPUB (.epub)
    - HTML (.html, .htm) - local files and URLs
    - PDF (.pdf)
    - DOCX (.docx)
    - Markdown (.md, .markdown)
    - Text (.txt, or no extension)

    Args:
        file_path: Path to file to parse, or URL string (string or Path object).
        options: Optional parser configuration dict. Options vary by format.
            Common options:
            - extract_images (bool): Extract images. Default: True
            - image_output_dir (str|Path): Directory to save extracted images.
              If None, images are saved to temp directory. Default: None
            - clean_text (bool): Apply text cleaning. Default: True
            - detect_chapters (bool): Detect chapter structure. Default: True

            HTML-specific options:
            - timeout (int): URL fetch timeout in seconds. Default: 10
            - min_chapter_level (int): Minimum heading level for chapters. Default: 1
            - max_chapter_level (int): Maximum heading level for chapters. Default: 2

            PDF-specific options:
            - ocr_enabled (bool): Enable OCR for scanned PDFs. Default: True
            - ocr_language (str): Tesseract language code. Default: 'eng'
            - min_heading_size (float): Minimum font size for headings. Default: auto
            - extract_tables (bool): Extract and convert tables. Default: True

    Returns:
        Document object with parsed content, chapters, images, and metadata.

    Raises:
        FileReadError: If file cannot be read.
        UnsupportedFormatError: If file format is not supported.
        ParsingError: If parsing fails.

    Example:
        >>> from omniparser import parse_document
        >>> doc = parse_document("book.epub")
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")
        >>> print(f"Word count: {doc.word_count}")
    """
    # Check if it's a URL (for HTML parser)
    is_url = isinstance(file_path, str) and (
        file_path.startswith("http://") or file_path.startswith("https://")
    )

    if is_url:
        # URL parsing (HTML only)
        logger.info(f"Parsing URL: {file_path}")
        parser = HTMLParser(options)
        return parser.parse(file_path)

    # Convert to Path object if string
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Validate file exists
    if not file_path.exists():
        raise FileReadError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileReadError(f"Not a file: {file_path}")

    # Detect format and route to appropriate parser
    file_extension = file_path.suffix.lower()

    logger.info(f"Parsing file: {file_path} (format: {file_extension})")

    # EPUB format
    if file_extension in [".epub"]:
        epub_parser = EPUBParser(options)
        return epub_parser.parse(file_path)

    # PDF format
    elif file_extension in [".pdf"]:
        # Extract image output directory from options if provided
        output_dir = None
        if options and "image_output_dir" in options:
            output_dir = Path(options["image_output_dir"])
        return parse_pdf(file_path, output_dir=output_dir, options=options)

    # DOCX format
    elif file_extension in [".docx"]:
        # Extract options for parse_docx function
        extract_images_flag = True
        image_output_dir = None
        preserve_formatting = True
        extract_hyperlinks = True
        extract_lists = True

        if options:
            extract_images_flag = options.get("extract_images", True)
            if "image_output_dir" in options:
                image_output_dir = Path(options["image_output_dir"])
            preserve_formatting = options.get("preserve_formatting", True)
            extract_hyperlinks = options.get("extract_hyperlinks", True)
            extract_lists = options.get("extract_lists", True)

        return parse_docx(
            file_path,
            extract_images_flag=extract_images_flag,
            image_output_dir=image_output_dir,
            preserve_formatting=preserve_formatting,
            extract_hyperlinks=extract_hyperlinks,
            extract_lists=extract_lists,
        )

    # HTML format
    elif file_extension in [".html", ".htm"]:
        html_parser = HTMLParser(options)
        return html_parser.parse(file_path)

    # Markdown format
    elif file_extension in [".md", ".markdown"]:
        markdown_parser = MarkdownParser(options)
        return markdown_parser.parse(file_path)

    # Text format
    elif file_extension in [".txt", ""]:
        text_parser = TextParser(options)
        return text_parser.parse(file_path)

    # Unknown format
    else:
        raise UnsupportedFormatError(
            f"Unsupported file format: {file_extension}. "
            f"Supported formats: .epub, .pdf, .html, .htm, .docx, .md, .markdown, .txt"
        )


def get_supported_formats() -> list[str]:
    """Get list of currently supported file formats.

    Returns:
        List of file extensions (e.g., ['.epub', '.pdf', '.html', '.htm', '.docx', '.md', '.markdown', '.txt']).
    """
    return [".epub", ".pdf", ".html", ".htm", ".docx", ".md", ".markdown", ".txt"]


def is_format_supported(file_path: str | Path) -> bool:
    """Check if a file format is supported.

    Args:
        file_path: Path to check (string or Path object).

    Returns:
        True if format is supported, False otherwise.
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    extension = file_path.suffix.lower()
    return extension in get_supported_formats()
