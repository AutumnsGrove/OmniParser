"""
Markdown parser module for OmniParser.

This module provides functionality for parsing Markdown (.md, .markdown) files
into structured Document objects with metadata, chapters, and image references.

Main entry point:
    parse_markdown() - Parse a Markdown file and return a Document object

Example:
    >>> from omniparser.parsers.markdown import parse_markdown
    >>> from pathlib import Path
    >>>
    >>> doc = parse_markdown(Path("example.md"))
    >>> print(doc.metadata.title)
    >>> print(f"{len(doc.chapters)} chapters")
    >>> print(f"{doc.metadata.word_count} words")
"""

from .parser import parse_markdown

__all__ = ["parse_markdown"]
