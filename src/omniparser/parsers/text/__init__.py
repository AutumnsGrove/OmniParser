"""
Text parser module for OmniParser.

This module provides functionality for parsing plain text (.txt) files
into structured Document objects with metadata, chapters, and word counts.

Main entry point:
    parse_text() - Parse a text file and return a Document object

Example:
    >>> from omniparser.parsers.text import parse_text
    >>> from pathlib import Path
    >>>
    >>> doc = parse_text(Path("document.txt"))
    >>> print(doc.metadata.title)
    >>> print(f"{len(doc.chapters)} chapters")
    >>> print(f"{doc.metadata.word_count} words")
"""

from .parser import parse_text

__all__ = ["parse_text"]
