"""
Parser registry for dynamic format registration.

This module provides a centralized registry for parser registration and discovery,
enabling a plugin-like architecture where parsers can be registered dynamically
rather than through static imports.

Example:
    >>> from omniparser.base.registry import ParserRegistry, registry
    >>>
    >>> # Register a custom parser
    >>> registry.register(
    ...     extensions=[".custom"],
    ...     parser_class=CustomParser,
    ...     parse_func=parse_custom,
    ...     name="custom"
    ... )
    >>>
    >>> # Get parser for a file
    >>> parser_info = registry.get_parser(".custom")
    >>> doc = parser_info.parse_func("file.custom")
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

logger = logging.getLogger(__name__)


@dataclass
class ParserInfo:
    """Information about a registered parser.

    Attributes:
        name: Short identifier for the parser (e.g., "epub", "pdf").
        extensions: List of file extensions this parser handles.
        parser_class: Optional class-based parser (for backward compatibility).
        parse_func: Optional functional parser (recommended).
        supports_func: Function to check if a file is supported.
        description: Human-readable description.
        version: Parser version string.
        priority: Priority for format detection (higher = preferred).
    """

    name: str
    extensions: List[str]
    parser_class: Optional[Type] = None
    parse_func: Optional[Callable[..., Any]] = None
    supports_func: Optional[Callable[[Union[Path, str]], bool]] = None
    description: str = ""
    version: str = "1.0.0"
    priority: int = 0

    def __post_init__(self) -> None:
        """Validate parser info after initialization."""
        if not self.parser_class and not self.parse_func:
            raise ValueError(
                f"Parser '{self.name}' must have either parser_class or parse_func"
            )
        # Normalize extensions to lowercase with leading dot
        self.extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in self.extensions
        ]


class ParserRegistry:
    """Central registry for document parsers.

    Provides dynamic registration and lookup of parsers by file extension
    or format name. Supports both class-based and functional parsers.

    Attributes:
        _parsers: Dictionary mapping parser names to ParserInfo.
        _extension_map: Dictionary mapping extensions to parser names.

    Example:
        >>> registry = ParserRegistry()
        >>> registry.register(
        ...     extensions=[".epub"],
        ...     parser_class=EPUBParser,
        ...     parse_func=parse_epub,
        ...     name="epub",
        ...     description="EPUB ebook parser"
        ... )
        >>> info = registry.get_parser(".epub")
        >>> doc = info.parse_func("book.epub")
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._parsers: Dict[str, ParserInfo] = {}
        self._extension_map: Dict[str, str] = {}  # ext -> parser name

    def register(
        self,
        extensions: List[str],
        name: str,
        parser_class: Optional[Type] = None,
        parse_func: Optional[Callable[..., Any]] = None,
        supports_func: Optional[Callable[[Union[Path, str]], bool]] = None,
        description: str = "",
        version: str = "1.0.0",
        priority: int = 0,
    ) -> None:
        """Register a parser for the given extensions.

        Args:
            extensions: List of file extensions (e.g., [".epub", ".pdf"]).
            name: Short identifier for the parser.
            parser_class: Optional class-based parser.
            parse_func: Optional functional parser.
            supports_func: Function to check if a file is supported.
            description: Human-readable description.
            version: Parser version string.
            priority: Priority for format detection (higher = preferred).

        Raises:
            ValueError: If parser is invalid or name already registered.
        """
        if name in self._parsers:
            logger.warning(f"Parser '{name}' already registered, overwriting")

        info = ParserInfo(
            name=name,
            extensions=extensions,
            parser_class=parser_class,
            parse_func=parse_func,
            supports_func=supports_func,
            description=description,
            version=version,
            priority=priority,
        )

        self._parsers[name] = info

        # Map extensions to parser name
        for ext in info.extensions:
            if ext in self._extension_map:
                existing = self._extension_map[ext]
                existing_priority = self._parsers[existing].priority
                if priority > existing_priority:
                    logger.info(
                        f"Extension '{ext}' reassigned from '{existing}' to '{name}' "
                        f"(priority {priority} > {existing_priority})"
                    )
                    self._extension_map[ext] = name
                else:
                    logger.debug(
                        f"Extension '{ext}' kept with '{existing}' "
                        f"(priority {existing_priority} >= {priority})"
                    )
            else:
                self._extension_map[ext] = name

        logger.debug(f"Registered parser '{name}' for extensions: {info.extensions}")

    def unregister(self, name: str) -> bool:
        """Unregister a parser by name.

        Args:
            name: Parser name to unregister.

        Returns:
            True if parser was unregistered, False if not found.
        """
        if name not in self._parsers:
            return False

        info = self._parsers.pop(name)

        # Remove extension mappings
        for ext in info.extensions:
            if self._extension_map.get(ext) == name:
                del self._extension_map[ext]

        logger.debug(f"Unregistered parser '{name}'")
        return True

    def get_parser(self, extension_or_path: Union[str, Path]) -> Optional[ParserInfo]:
        """Get parser info for a file extension or path.

        Args:
            extension_or_path: File extension (e.g., ".epub") or file path.

        Returns:
            ParserInfo if found, None otherwise.
        """
        # Extract extension if path provided
        if isinstance(extension_or_path, Path):
            ext = extension_or_path.suffix.lower()
        elif extension_or_path.startswith("."):
            ext = extension_or_path.lower()
        else:
            # Might be a path string
            ext = Path(extension_or_path).suffix.lower()

        parser_name = self._extension_map.get(ext)
        if parser_name:
            return self._parsers.get(parser_name)
        return None

    def get_parser_by_name(self, name: str) -> Optional[ParserInfo]:
        """Get parser info by name.

        Args:
            name: Parser name (e.g., "epub", "pdf").

        Returns:
            ParserInfo if found, None otherwise.
        """
        return self._parsers.get(name)

    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """Check if a file format is supported.

        Args:
            file_path: Path to check.

        Returns:
            True if format is supported.
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        ext = path.suffix.lower()

        # Check extension map first
        if ext in self._extension_map:
            return True

        # Check supports_func for each parser (for complex format detection)
        for info in self._parsers.values():
            if info.supports_func and info.supports_func(file_path):
                return True

        return False

    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions.

        Returns:
            Sorted list of extensions (e.g., [".docx", ".epub", ".pdf"]).
        """
        return sorted(self._extension_map.keys())

    def get_all_parsers(self) -> Dict[str, ParserInfo]:
        """Get all registered parsers.

        Returns:
            Dictionary of parser name to ParserInfo.
        """
        return self._parsers.copy()

    def list_parsers(self) -> List[str]:
        """Get list of all registered parser names.

        Returns:
            Sorted list of parser names.
        """
        return sorted(self._parsers.keys())

    def clear(self) -> None:
        """Clear all registered parsers."""
        self._parsers.clear()
        self._extension_map.clear()
        logger.debug("Registry cleared")


# Global registry instance
registry = ParserRegistry()


def register_builtin_parsers() -> None:
    """Register all built-in parsers with the global registry.

    This function lazily imports and registers all built-in parsers.
    Called automatically when needed, or can be called explicitly.
    """
    # EPUB parser
    from ..parsers.epub import EPUBParser, parse_epub, supports_epub_format

    registry.register(
        extensions=[".epub"],
        name="epub",
        parser_class=EPUBParser,
        parse_func=parse_epub,
        supports_func=supports_epub_format,
        description="EPUB ebook parser with TOC-based chapter detection",
        version="1.0.0",
    )

    # PDF parser
    from ..parsers.pdf import PDFParser, parse_pdf

    registry.register(
        extensions=[".pdf"],
        name="pdf",
        parser_class=PDFParser,
        parse_func=parse_pdf,
        description="PDF parser with OCR, table, and QR code support",
        version="1.0.0",
    )

    # DOCX parser
    from ..parsers.docx import parse_docx

    registry.register(
        extensions=[".docx"],
        name="docx",
        parse_func=parse_docx,
        description="Microsoft Word DOCX parser with formatting preservation",
        version="1.0.0",
    )

    # HTML parser
    from ..parsers.html import HTMLParser, supports_html_format

    registry.register(
        extensions=[".html", ".htm"],
        name="html",
        parser_class=HTMLParser,
        supports_func=supports_html_format,
        description="HTML parser with Trafilatura and Readability support",
        version="1.0.0",
    )

    # Markdown parser
    from ..parsers.markdown import MarkdownParser, parse_markdown

    registry.register(
        extensions=[".md", ".markdown"],
        name="markdown",
        parser_class=MarkdownParser,
        parse_func=parse_markdown,
        description="Markdown parser with frontmatter support",
        version="1.0.0",
    )

    # Text parser
    from ..parsers.text import TextParser, parse_text

    registry.register(
        extensions=[".txt", ""],
        name="text",
        parser_class=TextParser,
        parse_func=parse_text,
        description="Plain text parser with encoding detection",
        version="1.0.0",
    )

    # Photo parser
    from ..parsers.photo import PhotoParser, parse_photo, supports_photo_format

    registry.register(
        extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"],
        name="photo",
        parser_class=PhotoParser,
        parse_func=parse_photo,
        supports_func=supports_photo_format,
        description="Photo parser with EXIF extraction and AI analysis",
        version="1.0.0",
    )

    logger.info(f"Registered {len(registry.list_parsers())} built-in parsers")


__all__ = [
    "ParserInfo",
    "ParserRegistry",
    "registry",
    "register_builtin_parsers",
]
