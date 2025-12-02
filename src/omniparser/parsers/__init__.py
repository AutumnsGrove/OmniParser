"""
OmniParser parsers module.

Exports all available document parsers.
"""

from .epub_parser import EPUBParser
from .html import HTMLParser
from .markdown_parser import MarkdownParser
from .photo import parse_photo, supports_photo_format
from .text_parser import TextParser

__all__ = [
    "EPUBParser",
    "HTMLParser",
    "MarkdownParser",
    "TextParser",
    # Photo parser
    "parse_photo",
    "supports_photo_format",
]
