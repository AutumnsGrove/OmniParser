"""
Text parser module for OmniParser.

This module provides both functional and object-oriented interfaces to text parsing:
- parse_text(): Functional interface (recommended for new code)
- TextParser: Class-based interface (for backward compatibility)

Example:
    >>> from omniparser.parsers.text import parse_text
    >>> from pathlib import Path
    >>>
    >>> doc = parse_text(Path("document.txt"))
    >>> print(doc.metadata.title)
    >>> print(f"{len(doc.chapters)} chapters")
    >>> print(f"{doc.metadata.word_count} words")

    >>> # Class-based interface
    >>> from omniparser.parsers.text import TextParser
    >>> parser = TextParser()
    >>> doc = parser.parse("notes.txt")
"""

from .parser import parse_text

# Import wrapper class from parent module for consistency
from ..text_parser import TextParser

__all__ = ["parse_text", "TextParser"]
