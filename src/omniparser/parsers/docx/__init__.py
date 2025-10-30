"""
DOCX parser module for OmniParser.

Status: Production-Ready 

This module provides comprehensive DOCX parsing capabilities using python-docx.
It follows a modular architecture with specialized sub-modules for different
aspects of DOCX parsing.

Features:
     Text extraction with formatting (bold, italic)
     Metadata extraction from core properties
     Heading detection and markdown formatting (# ## ###)
     Table extraction and markdown formatting
     List extraction (ordered and unordered) - NEW
     Hyperlink extraction and markdown formatting ([text](url)) - NEW
     Image extraction and saving with dimension detection

Architecture:
    - parser.py: Main orchestrator (parse_docx function)
    - validation.py: File validation and loading
    - metadata.py: Metadata extraction from core properties
    - content_extraction.py: Content orchestration
    - paragraphs.py: Paragraph and run conversion
    - headings.py: Heading detection and formatting
    - tables.py: Table extraction and markdown conversion
    - lists.py: List detection and formatting (NEW)
    - hyperlinks.py: Hyperlink extraction and formatting (NEW)
    - images.py: Image extraction and saving
    - utils.py: Shared utilities (word count, reading time, etc.)

Usage:
    >>> from pathlib import Path
    >>> from omniparser.parsers.docx import parse_docx
    >>>
    >>> # Basic parsing
    >>> doc = parse_docx(Path("report.docx"))
    >>> print(doc.metadata.title)
    >>> print(doc.full_text)
    >>>
    >>> # With image extraction
    >>> doc = parse_docx(
    ...     Path("report.docx"),
    ...     extract_images_flag=True,
    ...     image_output_dir=Path("/output/images")
    ... )
    >>>
    >>> # With all features
    >>> doc = parse_docx(
    ...     Path("report.docx"),
    ...     preserve_formatting=True,
    ...     extract_hyperlinks=True,
    ...     extract_lists=True
    ... )

Version: 0.3.0
Phase: 2.8 (6 parsers + AI features)
Last Updated: 2025-10-29
"""

from .parser import parse_docx

__all__ = ["parse_docx"]
