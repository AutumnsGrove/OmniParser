"""
Legacy EPUB parser module.

This module provides backward compatibility for code that imports from
src.omniparser.parsers.epub_parser. The actual implementation has been
moved to src.omniparser.parsers.epub.

New code should import from src.omniparser.parsers.epub instead.
"""

from .epub import EPUBParser, parse_epub

__all__ = ["EPUBParser", "parse_epub"]
