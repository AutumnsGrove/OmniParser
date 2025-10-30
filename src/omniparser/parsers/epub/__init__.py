"""
EPUB parser module.

This module provides both functional and object-oriented interfaces to EPUB parsing:
- parse_epub(): Functional interface (recommended for new code)
- EPUBParser: Class-based interface (for backward compatibility)

The EPUBParser class is a thin wrapper around parse_epub() that maintains the
same API as the legacy implementation while delegating to the modular functional code.
"""

# Standard library
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Local imports
from ...models import Document, ImageReference
from .images import extract_epub_images
from .loading import load_epub
from .parser import parse_epub
from .validator import supports_epub_format


class EPUBParser:
    """Parser for EPUB files using EbookLib library.

    This is a thin wrapper around the functional parse_epub() implementation
    that maintains backward compatibility with the original class-based API.

    Features:
    - TOC-based chapter detection (primary method)
    - Spine-based chapter detection (fallback when no TOC)
    - Comprehensive metadata extraction from OPF
    - Image extraction with safe temp directory cleanup
    - HTML to plain text conversion
    - Text cleaning integration

    Options:
        extract_images (bool): Extract images from EPUB. Default: True
        image_output_dir (str|Path): Directory to save extracted images.
            If None (default), images are saved to temp directory and deleted after parsing.
            If set, images are saved persistently to the specified directory.
        detect_chapters (bool): Enable chapter detection. Default: True
        clean_text (bool): Apply text cleaning. Default: True
        min_chapter_length (int): Minimum words per chapter. Default: 100
        use_toc (bool): Use TOC for chapter detection. Default: True
        use_spine_fallback (bool): Use spine if TOC missing. Default: True

    Example:
        >>> parser = EPUBParser({'extract_images': True, 'clean_text': True})
        >>> doc = parser.parse(Path('book.epub'))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")

    Note:
        For new code, consider using the functional parse_epub() interface directly:
        >>> from omniparser.parsers.epub import parse_epub
        >>> doc = parse_epub('book.epub', extract_images=True)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize EPUB parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        self.options = options or {}

        # Set default options (mirroring original implementation)
        self.options.setdefault("extract_images", True)
        self.options.setdefault("image_output_dir", None)
        self.options.setdefault("detect_chapters", True)
        self.options.setdefault("clean_text", True)
        self.options.setdefault("min_chapter_length", 100)
        self.options.setdefault("use_toc", True)
        self.options.setdefault("use_spine_fallback", True)

        # Initialize tracking (for backward compatibility)
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None

    @classmethod
    def supports_format(cls, file_path: Union[Path, str]) -> bool:
        """Check if file is an EPUB.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .epub extension, False otherwise.
        """
        return supports_epub_format(file_path)

    def parse(self, file_path: Union[Path, str]) -> Document:
        """Parse EPUB file and return Document object.

        This method delegates to the functional parse_epub() implementation,
        passing along the configured options.

        Args:
            file_path: Path to EPUB file.

        Returns:
            Document object with parsed content, chapters, images, and metadata.

        Raises:
            FileReadError: If file cannot be read or is not a valid EPUB.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.
        """
        # Delegate to functional implementation
        return parse_epub(file_path, **self.options)

    def extract_images(self, file_path: Union[Path, str]) -> List[ImageReference]:
        """Extract images from EPUB file.

        Images are saved to either a temporary directory (default) or a persistent
        directory if image_output_dir option is set.

        Args:
            file_path: Path to EPUB file.

        Returns:
            List of ImageReference objects.

        Raises:
            ParsingError: If EPUB loading fails.

        Note:
            - If image_output_dir is None: uses temp directory (auto-cleanup)
            - If image_output_dir is set: saves to persistent directory
            - Sequential image IDs: img_001, img_002, etc.
            - Position set to 0 (exact position tracking not implemented)
            - Alt text set to None (HTML parsing not implemented)
            - Preserves EPUB internal directory structure (e.g., images/cover.jpg)
        """
        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            # Load EPUB file using internal method (for test mocking compatibility)
            book = self._load_epub(file_path)

            # Get output directory from options
            image_output_dir = self.options.get("image_output_dir")
            output_path = (
                Path(image_output_dir) if image_output_dir is not None else None
            )

            # Delegate to modular image extraction function
            return extract_epub_images(book, output_path, self._warnings)

        except Exception as e:
            # Wrap any errors in ParsingError for consistency
            from ...exceptions import ParsingError

            if isinstance(e, ParsingError):
                raise
            raise ParsingError(
                f"Failed to extract images from EPUB: {e}",
                parser="EPUBParser",
                original_error=e,
            )

    # ============================================================================
    # Private methods for backward compatibility with tests
    # ============================================================================

    def _validate_epub(self, file_path: Path) -> None:
        """Validate EPUB file before parsing.

        This is a private method maintained for backward compatibility with tests.

        Args:
            file_path: Path to EPUB file.

        Raises:
            FileReadError: If file doesn't exist or isn't readable.
            ValidationError: If file validation fails.
        """
        from .validator import validate_epub_file

        validate_epub_file(file_path, self._warnings)

    def _load_epub(self, file_path: Path):
        """Load EPUB file using ebooklib.

        This is a private method maintained for backward compatibility with tests.

        Args:
            file_path: Path to EPUB file.

        Returns:
            EpubBook object.

        Raises:
            ParsingError: If EPUB cannot be loaded.
        """
        return load_epub(file_path, self._warnings)

    def _extract_metadata(self, book, file_path: Path):
        """Extract metadata from EPUB OPF file.

        This is a private method maintained for backward compatibility with tests.

        Args:
            book: EpubBook object.
            file_path: Path to EPUB file (for file_size).

        Returns:
            Metadata object with extracted fields.
        """
        from .metadata import extract_epub_metadata

        return extract_epub_metadata(book, file_path, self._warnings)

    def _extract_toc(self, book):
        """Extract table of contents from EPUB.

        This is a private method maintained for backward compatibility with tests.

        Args:
            book: EpubBook object.

        Returns:
            Flat list of TocEntry objects or None if TOC is missing/empty.
        """
        from .toc import extract_toc

        return extract_toc(book, self._warnings)

    def _parse_toc_item(self, items, flat_toc: List, level: int = 1) -> None:
        """Recursively parse TOC items into flat list.

        This is a private method maintained for backward compatibility with tests.

        Args:
            items: TOC item(s) to parse.
            flat_toc: Accumulator list for flattened TocEntry objects.
            level: Current hierarchy level.
        """
        from .toc import parse_toc_item

        parse_toc_item(items, flat_toc, level, self._warnings)

    def _extract_content_and_chapters(self, book, toc_entries):
        """Extract full content and detect chapters.

        This is a private method maintained for backward compatibility with tests.
        It orchestrates the chapter extraction logic, delegating to either TOC-based
        or spine-based extraction methods.

        Args:
            book: EpubBook object.
            toc_entries: TOC entries if available, None otherwise.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        # Determine extraction method based on TOC availability
        if toc_entries and self.options.get("use_toc", True):
            # Use TOC-based extraction
            content, chapters = self._extract_chapters_toc(book, toc_entries)
        elif self.options.get("use_spine_fallback", True):
            # Fall back to spine-based extraction
            content, chapters = self._extract_chapters_spine(book)
        else:
            # No extraction method available
            content = ""
            chapters = []

        # Post-process chapters
        if self.options.get("detect_chapters", True):
            chapters = self._postprocess_chapters(chapters)

        return content, chapters

    def _extract_chapters_toc(self, book, toc_entries: List):
        """Extract chapters using TOC-based detection.

        This is a private method maintained for backward compatibility with tests.

        Args:
            book: EpubBook object.
            toc_entries: List of TOC entries.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        from .chapters import extract_chapters_from_toc

        return extract_chapters_from_toc(book, toc_entries, self._warnings)

    def _extract_chapters_spine(self, book):
        """Extract chapters using spine-based detection.

        This is a private method maintained for backward compatibility with tests.

        Args:
            book: EpubBook object.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        from .chapters import extract_chapters_from_spine

        return extract_chapters_from_spine(book, self._warnings)

    def _postprocess_chapters(self, chapters: List):
        """Post-process chapters: filter empty ones and handle duplicates.

        This is a private method maintained for backward compatibility with tests.

        Args:
            chapters: List of chapters to process.

        Returns:
            Filtered and cleaned chapter list.
        """
        from .chapters import postprocess_chapters

        return postprocess_chapters(chapters, self.options, self._warnings)


__all__ = ["EPUBParser", "parse_epub"]
