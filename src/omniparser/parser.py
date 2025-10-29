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
from .parsers.markdown_parser import MarkdownParser
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
    - Text (.txt, or no extension)

    Future support planned for:
    - PDF (.pdf)
    - DOCX (.docx)
    - Markdown (.md)

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

    # PDF format (not yet implemented)
    elif file_extension in [".pdf"]:
        raise UnsupportedFormatError(
            f"PDF format not yet implemented. Coming in future version."
        )

    # DOCX format (not yet implemented)
    elif file_extension in [".docx", ".doc"]:
        raise UnsupportedFormatError(
            f"DOCX format not yet implemented. Coming in future version."
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
            f"Supported formats: .epub, .html, .htm, .txt (more coming soon)"
        )


def get_supported_formats() -> list[str]:
    """Get list of currently supported file formats.

    Returns:
        List of file extensions (e.g., ['.epub', '.html', '.htm', '.md', '.markdown']).
    """
    return [".epub", ".html", ".htm", ".md", ".markdown"]
        List of file extensions (e.g., ['.epub', '.html', '.htm', '.txt']).
    """
    return [".epub", ".html", ".htm", ".txt", ""]


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
