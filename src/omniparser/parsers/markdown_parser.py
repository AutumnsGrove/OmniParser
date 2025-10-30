"""
Markdown parser implementation - Backward compatibility wrapper.

This module provides the MarkdownParser class as a thin wrapper around the new
modular Markdown parser implementation. It maintains backward compatibility with
existing code while delegating all functionality to the new functional parser.

Classes:
    MarkdownParser: Backward compatibility wrapper for parse_markdown()

Note:
    The actual parsing logic lives in the modular implementation at
    src/omniparser/parsers/markdown/. This class exists solely to maintain
    the MarkdownParser API for existing code and tests.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..base.base_parser import BaseParser
from ..models import Document

logger = logging.getLogger(__name__)


class MarkdownParser(BaseParser):
    """Parser for Markdown files with optional YAML frontmatter.

    This is a backward compatibility wrapper around the new modular
    Markdown parser implementation. It delegates all parsing to the
    parse_markdown() function while maintaining the class-based API.

    Features:
    - YAML/TOML/JSON frontmatter extraction
    - Heading-based chapter detection (configurable levels)
    - Image reference extraction (inline and reference-style)
    - Markdown normalization (heading styles, list markers)
    - Word counting (markdown-aware)
    - Reading time estimation

    Options:
        extract_images (bool): Extract image references (default: True)
        normalize_headings (bool): Normalize markdown format (default: True)
        min_chapter_level (int): Minimum heading level for chapters (default: 1)
        max_chapter_level (int): Maximum heading level for chapters (default: 2)

    Example:
        >>> parser = MarkdownParser({'extract_images': True})
        >>> doc = parser.parse(Path("README.md"))
        >>> print(doc.metadata.title)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize Markdown parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
        self.options.setdefault("extract_images", True)
        self.options.setdefault("normalize_headings", True)
        self.options.setdefault("min_chapter_level", 1)
        self.options.setdefault("max_chapter_level", 2)

    def supports_format(self, file_path: Union[Path, str]) -> bool:
        """Check if file is Markdown.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .md or .markdown extension, False otherwise.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() in [".md", ".markdown"]

    def parse(
        self, file_path: Union[Path, str], options: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Parse Markdown file and return Document object.

        This method delegates to the new modular parse_markdown() function
        while maintaining backward compatibility with the class-based API.

        Process:
        1. Read file with UTF-8 encoding
        2. Extract frontmatter if present
        3. Parse frontmatter to Metadata
        4. Normalize markdown if enabled
        5. Detect chapters from headings
        6. Extract image references
        7. Build and return Document

        Args:
            file_path: Path to Markdown file.
            options: Override parser options for this parse operation.

        Returns:
            Document object with parsed content, chapters, images, and metadata.

        Raises:
            FileReadError: If file cannot be read.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.
        """
        # Delegate to new modular implementation
        from .markdown import parse_markdown

        # Merge options: instance options + method options
        merged_options = self.options.copy()
        if options:
            merged_options.update(options)

        # Extract options for parse_markdown()
        extract_images = merged_options.get("extract_images", True)
        min_level = merged_options.get("min_chapter_level", 1)
        max_level = merged_options.get("max_chapter_level", 2)
        normalize = merged_options.get("normalize_headings", True)

        logger.info(f"Parsing Markdown file via modular implementation: {file_path}")

        # Delegate to functional parser
        return parse_markdown(
            file_path=file_path,
            extract_images=extract_images,
            min_chapter_level=min_level,
            max_chapter_level=max_level,
            normalize_content=normalize,
        )
