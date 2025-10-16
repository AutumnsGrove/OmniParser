"""
Abstract base parser for all document format parsers.

This module defines the BaseParser abstract class that all format-specific
parsers must inherit from. It provides a consistent interface for parsing
different document types (EPUB, PDF, DOCX, HTML, etc.) and returning
standardized Document objects.

Classes:
    BaseParser: Abstract base class defining the parser interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from ..models import Document, ImageReference


class BaseParser(ABC):
    """Abstract base class for all document parsers.

    All format-specific parsers must inherit from this class and implement
    the required abstract methods.

    Attributes:
        options: Configuration dict for parser behavior.

    Example:
        >>> class EPUBParser(BaseParser):
        ...     def parse(self, file_path: Path) -> Document:
        ...         # Implementation
        ...         pass
        ...     def supports_format(self, file_path: Path) -> bool:
        ...         return file_path.suffix.lower() == '.epub'
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize parser with options.

        Args:
            options: Parser configuration dict. Defaults to empty dict.
        """
        self.options = options or {}

    @abstractmethod
    def parse(self, file_path: Path) -> Document:
        """Parse document and return Document object.

        Args:
            file_path: Path to file to parse.

        Returns:
            Document object with parsed content.

        Raises:
            ParsingError: If parsing fails.
            FileReadError: If file cannot be read.
        """
        pass

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if this parser supports the file format.

        Args:
            file_path: Path to check.

        Returns:
            True if format is supported, False otherwise.
        """
        pass

    def extract_images(self, file_path: Path) -> List[ImageReference]:
        """Extract images from document (optional override).

        Args:
            file_path: Path to document.

        Returns:
            List of ImageReference objects. Empty list by default.
        """
        return []

    def clean_text(self, text: str) -> str:
        """Apply text cleaning (optional override).

        Args:
            text: Raw text to clean.

        Returns:
            Cleaned text.
        """
        if self.options.get("clean_text", True):
            # Import here to avoid circular dependency
            from ..processors.text_cleaner import clean_text  # type: ignore[import-not-found]

            return cast(str, clean_text(text))
        return text
