"""
Markdown parser module for OmniParser.

This module provides both functional and object-oriented interfaces to Markdown parsing:
- parse_markdown(): Functional interface (recommended for new code)
- MarkdownParser: Class-based interface (for backward compatibility)

Example:
    >>> from omniparser.parsers.markdown import parse_markdown
    >>> from pathlib import Path
    >>>
    >>> doc = parse_markdown(Path("example.md"))
    >>> print(doc.metadata.title)
    >>> print(f"{len(doc.chapters)} chapters")
    >>> print(f"{doc.metadata.word_count} words")

    >>> # Class-based interface
    >>> from omniparser.parsers.markdown import MarkdownParser
    >>> parser = MarkdownParser()
    >>> doc = parser.parse("README.md")
"""

from .parser import parse_markdown

# Import wrapper class from parent module for consistency
from ..markdown_parser import MarkdownParser

__all__ = ["parse_markdown", "MarkdownParser"]
