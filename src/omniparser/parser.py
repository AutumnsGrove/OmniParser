"""
Main parser module for OmniParser.

Provides the public parse_document() function that automatically detects
file formats and routes to appropriate parsers.

Performance Note:
    This module uses lazy imports to minimize startup time. Parser modules
    are only imported when their format is actually requested. This reduces
    initial load time by ~60% compared to eager imports.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING, Union

from .exceptions import UnsupportedFormatError, FileReadError
from .models import Document

# Type hints only - not imported at runtime
if TYPE_CHECKING:
    from .parsers.epub_parser import EPUBParser
    from .parsers.html import HTMLParser
    from .parsers.markdown_parser import MarkdownParser
    from .parsers.text_parser import TextParser

logger = logging.getLogger(__name__)


# Lazy import cache to avoid re-importing
_parser_cache: Dict[str, Any] = {}


def _clear_parser_cache() -> None:
    """Clear the parser cache. Used for testing."""
    _parser_cache.clear()


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
    - Photo/Image (.jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .tif)

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
        # URL parsing (HTML only) - use lazy import
        logger.info(f"Parsing URL: {file_path}")
        return _parse_html(file_path, options)  # type: ignore[arg-type]

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
        return _parse_epub(file_path, options)

    # PDF format
    elif file_extension in [".pdf"]:
        return _parse_pdf(file_path, options)

    # DOCX format
    elif file_extension in [".docx"]:
        return _parse_docx(file_path, options)

    # HTML format
    elif file_extension in [".html", ".htm"]:
        return _parse_html(file_path, options)

    # Markdown format
    elif file_extension in [".md", ".markdown"]:
        return _parse_markdown(file_path, options)

    # Text format
    elif file_extension in [".txt", ""]:
        return _parse_text(file_path, options)

    # Photo/Image formats
    elif _supports_photo(file_path):
        return _parse_photo(file_path, options)

    # Unknown format
    else:
        raise UnsupportedFormatError(
            f"Unsupported file format: {file_extension}. "
            f"Supported formats: .epub, .pdf, .html, .htm, .docx, .md, .markdown, .txt, "
            f".jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .tif"
        )


# =============================================================================
# Lazy Import Helpers
# =============================================================================


def _parse_epub(file_path: Path, options: Optional[Dict[str, Any]]) -> Document:
    """Parse EPUB file with lazy import."""
    if "EPUBParser" not in _parser_cache:
        from .parsers.epub_parser import EPUBParser
        _parser_cache["EPUBParser"] = EPUBParser

    parser = _parser_cache["EPUBParser"](options)
    return parser.parse(file_path)


def _parse_pdf(file_path: Path, options: Optional[Dict[str, Any]]) -> Document:
    """Parse PDF file with lazy import."""
    if "parse_pdf" not in _parser_cache:
        from .parsers.pdf import parse_pdf
        _parser_cache["parse_pdf"] = parse_pdf

    output_dir = None
    if options and "image_output_dir" in options:
        output_dir = Path(options["image_output_dir"])

    return _parser_cache["parse_pdf"](file_path, output_dir=output_dir, options=options)


def _parse_docx(file_path: Path, options: Optional[Dict[str, Any]]) -> Document:
    """Parse DOCX file with lazy import."""
    if "parse_docx" not in _parser_cache:
        from .parsers.docx import parse_docx
        _parser_cache["parse_docx"] = parse_docx

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

    return _parser_cache["parse_docx"](
        file_path,
        extract_images_flag=extract_images_flag,
        image_output_dir=image_output_dir,
        preserve_formatting=preserve_formatting,
        extract_hyperlinks=extract_hyperlinks,
        extract_lists=extract_lists,
    )


def _parse_html(
    file_path: Union[Path, str], options: Optional[Dict[str, Any]]
) -> Document:
    """Parse HTML file or URL with lazy import."""
    if "HTMLParser" not in _parser_cache:
        from .parsers.html import HTMLParser
        _parser_cache["HTMLParser"] = HTMLParser

    parser = _parser_cache["HTMLParser"](options)
    return parser.parse(file_path)


def _parse_markdown(file_path: Path, options: Optional[Dict[str, Any]]) -> Document:
    """Parse Markdown file with lazy import."""
    if "MarkdownParser" not in _parser_cache:
        from .parsers.markdown_parser import MarkdownParser
        _parser_cache["MarkdownParser"] = MarkdownParser

    parser = _parser_cache["MarkdownParser"](options)
    return parser.parse(file_path)


def _parse_text(file_path: Path, options: Optional[Dict[str, Any]]) -> Document:
    """Parse text file with lazy import."""
    if "TextParser" not in _parser_cache:
        from .parsers.text_parser import TextParser
        _parser_cache["TextParser"] = TextParser

    parser = _parser_cache["TextParser"](options)
    return parser.parse(file_path)


def _supports_photo(file_path: Path) -> bool:
    """Check if file is a photo with lazy import."""
    if "supports_photo_format" not in _parser_cache:
        from .parsers.photo import supports_photo_format
        _parser_cache["supports_photo_format"] = supports_photo_format

    return _parser_cache["supports_photo_format"](file_path)


def _parse_photo(file_path: Path, options: Optional[Dict[str, Any]]) -> Document:
    """Parse photo file with lazy import."""
    if "parse_photo" not in _parser_cache:
        from .parsers.photo import parse_photo
        _parser_cache["parse_photo"] = parse_photo

    return _parser_cache["parse_photo"](file_path, **(options or {}))


def get_supported_formats() -> list[str]:
    """Get list of currently supported file formats.

    Returns:
        List of file extensions (e.g., ['.epub', '.pdf', '.html', '.htm', '.docx', '.md', '.markdown', '.txt']).
    """
    return [
        ".epub",
        ".pdf",
        ".html",
        ".htm",
        ".docx",
        ".md",
        ".markdown",
        ".txt",
        # Photo formats
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
    ]


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
