"""
OmniParser parsers module.

Exports all available document parsers.
"""

from .epub_parser import EPUBParser
from .html import HTMLParser
from .markdown_parser import MarkdownParser
from .text_parser import TextParser

__all__ = [
    "EPUBParser",
    "HTMLParser",
    "MarkdownParser",
    "TextParser",
]
