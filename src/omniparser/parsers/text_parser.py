"""
Text parser implementation for plain text files.

This module provides the TextParser class as a backward-compatible wrapper
around the new modular text parsing implementation. It maintains the class-based
API for existing code while delegating all functionality to the new functional
parser in the `text/` submodule.

Backward Compatibility:
- Maintains TextParser class interface for existing tests and code
- All parsing logic now handled by modular implementation in text/ submodule
- See text/parser.py for actual implementation details

Migration Note:
- New code should use `from omniparser.parsers.text import parse_text` directly
- This wrapper exists for backward compatibility with existing code/tests
- The class-based API will be maintained but new features will be added to
  the functional parser only

Features:
- Automatic encoding detection using chardet
- Pattern-based chapter detection
- Fallback to single chapter if no structure detected
- See text/parser.py for complete feature documentation
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..base.base_parser import BaseParser
from ..models import Document


class TextParser(BaseParser):
    """
    Parser for plain text files with encoding detection.

    This is a backward-compatible wrapper around the new modular text parser
    implementation. All parsing logic is now handled by the functional
    parse_text() function in the text/ submodule.

    Features:
    - Automatic encoding detection (chardet)
    - Pattern-based chapter detection from text structure
    - Fallback to single chapter if no structure detected
    - Word counting and reading time estimation

    Options:
        detect_chapters (bool): Try to detect chapters from patterns (default: True)
        All other legacy options are ignored - the new implementation uses
        sensible defaults and doesn't require configuration

    Chapter Detection Patterns:
        - "Chapter 1", "Chapter One", "CHAPTER I"
        - "Part 1", "Section A"
        - "I. Introduction", "II. Methods"
        - Numbered patterns at line start

    Example:
        >>> parser = TextParser()
        >>> doc = parser.parse(Path("notes.txt"))
        >>> print(doc.chapters[0].title)
        >>> print(f"{doc.word_count} words")

    Note:
        For new code, prefer using the functional API directly:
        >>> from omniparser.parsers.text import parse_text
        >>> doc = parse_text(Path("notes.txt"))
    """

    @classmethod
    def supports_format(cls, file_path: Union[Path, str]) -> bool:
        """Check if file is plain text.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .txt extension or no extension, False otherwise.

        Example:
            >>> TextParser.supports_format(Path("notes.txt"))
            True
            >>> TextParser.supports_format(Path("document.pdf"))
            False
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() in [".txt", ""]

    def parse(
        self, file_path: Union[Path, str], options: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Parse plain text file using new modular implementation.

        This method delegates to the functional parse_text() implementation
        while maintaining backward compatibility with the class-based API.

        Process (handled by text/parser.py):
        1. Validate file exists and is readable
        2. Read file with automatic encoding detection
        3. Detect chapters from text patterns (optional)
        4. Count words and estimate reading time
        5. Create metadata
        6. Build and return Document

        Args:
            file_path: Path to text file to parse.
            options: Optional configuration dictionary.
                Supported keys:
                - detect_chapters (bool): Enable chapter detection (default: True)
                Legacy options are ignored for simplicity.

        Returns:
            Document object with parsed content, chapters, and metadata.

        Raises:
            FileReadError: If file cannot be read.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.

        Example:
            >>> parser = TextParser()
            >>> doc = parser.parse(Path("notes.txt"))
            >>> print(f"{len(doc.chapters)} chapters")
            >>> print(f"{doc.word_count} words")
        """
        # Import the new functional parser
        from .text import parse_text

        # Extract options (use instance options if not provided)
        if options is None:
            options = self.options

        # Extract detect_chapters option (default: True)
        # Old option name: "attempt_chapter_detection"
        # New option name: "detect_chapters"
        detect_chapters = options.get(
            "detect_chapters", options.get("attempt_chapter_detection", True)
        )

        # Delegate to new functional implementation
        return parse_text(
            file_path=file_path,
            detect_chapters=detect_chapters,
        )
