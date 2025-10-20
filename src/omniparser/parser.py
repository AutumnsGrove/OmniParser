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

logger = logging.getLogger(__name__)


def parse_document(
    file_path: str | Path, options: Optional[Dict[str, Any]] = None
) -> Document:
    """Parse a document file and return a universal Document object.

    Automatically detects the file format and routes to the appropriate parser.
    Currently supported formats:
    - EPUB (.epub)

    Future support planned for:
    - PDF (.pdf)
    - DOCX (.docx)
    - HTML (.html, .htm)
    - Markdown (.md)
    - Text (.txt)

    Args:
        file_path: Path to file to parse (string or Path object).
        options: Optional parser configuration dict. Options vary by format.
            Common options:
            - extract_images (bool): Extract images. Default: True
            - image_output_dir (str|Path): Directory to save extracted images.
              If None, images are saved to temp directory. Default: None
            - clean_text (bool): Apply text cleaning. Default: True
            - detect_chapters (bool): Detect chapter structure. Default: True

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
        parser = EPUBParser(options)
        return parser.parse(file_path)

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

    # HTML format (not yet implemented)
    elif file_extension in [".html", ".htm"]:
        raise UnsupportedFormatError(
            f"HTML format not yet implemented. Coming in future version."
        )

    # Markdown format (not yet implemented)
    elif file_extension in [".md", ".markdown"]:
        raise UnsupportedFormatError(
            f"Markdown format not yet implemented. Coming in future version."
        )

    # Text format (not yet implemented)
    elif file_extension in [".txt"]:
        raise UnsupportedFormatError(
            f"Text format not yet implemented. Coming in future version."
        )

    # Unknown format
    else:
        raise UnsupportedFormatError(
            f"Unsupported file format: {file_extension}. "
            f"Supported formats: .epub (more coming soon)"
        )


def get_supported_formats() -> list[str]:
    """Get list of currently supported file formats.

    Returns:
        List of file extensions (e.g., ['.epub', '.pdf']).
    """
    return [".epub"]


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
