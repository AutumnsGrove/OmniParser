"""
OmniParser - Universal Document Parser

A Python library for parsing various document formats (EPUB, PDF, DOCX, HTML,
Markdown, Text) into a unified Document structure.

Example:
    >>> from omniparser import parse_document
    >>> doc = parse_document("book.epub")
    >>> print(doc.metadata.title)
    >>> for chapter in doc.chapters:
    ...     print(chapter.title)
"""

# Main API
from .parser import parse_document, get_supported_formats, is_format_supported

# Data models (for type hints and advanced usage)
from .models import Document, Chapter, Metadata, ImageReference, ProcessingInfo

# Exceptions (for error handling)
from .exceptions import (
    OmniparserError,
    UnsupportedFormatError,
    ParsingError,
    FileReadError,
    NetworkError,
    ValidationError,
)

# Parsers (for advanced usage - users can instantiate directly if needed)
from .parsers.epub_parser import EPUBParser
from .parsers.html import HTMLParser
from .parsers.markdown_parser import MarkdownParser
# Note: DOCX parser now uses functional pattern (parse_docx) - no class
from .parsers.text_parser import TextParser

# Version
__version__ = "0.3.0"

# Public API
__all__ = [
    # Main functions
    "parse_document",
    "get_supported_formats",
    "is_format_supported",
    # Models
    "Document",
    "Chapter",
    "Metadata",
    "ImageReference",
    "ProcessingInfo",
    # Exceptions
    "OmniparserError",
    "UnsupportedFormatError",
    "ParsingError",
    "FileReadError",
    "NetworkError",
    "ValidationError",
    # Parsers
    "EPUBParser",
    "HTMLParser",
    "MarkdownParser",
    # DOCXParser removed - DOCX now uses functional pattern
    "TextParser",
    # Version
    "__version__",
]
