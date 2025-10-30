"""
PDF parser module for OmniParser.

This module provides PDF parsing functionality with support for:
- Text extraction (with OCR for scanned documents)
- Metadata extraction
- Heading detection and chapter structure
- Image extraction
- Table extraction

Main entry point:
    parse_pdf: Parse PDF file and return Document object

Example:
    >>> from pathlib import Path
    >>> from omniparser.parsers.pdf import parse_pdf
    >>> doc = parse_pdf(Path("document.pdf"))
    >>> print(doc.metadata.title)
"""

from .parser import parse_pdf

__all__ = ["parse_pdf"]
