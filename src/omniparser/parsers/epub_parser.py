"""
EPUB parser implementation using EbookLib.

This module provides the EPUBParser class for parsing EPUB files and converting
them to OmniParser's universal Document format. It includes TOC-based and
spine-based chapter detection, metadata extraction, image handling, and text
cleaning.

Ported and adapted from epub2tts project with TTS-specific features removed.
"""

# Standard library
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party
import ebooklib
from ebooklib import epub

# Local
from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from ..processors.metadata_builder import MetadataBuilder
from .epub.chapters import (
    extract_content_and_chapters,
    extract_chapters_from_toc,
    extract_chapters_from_spine,
    postprocess_chapters,
)
from .epub.images import extract_epub_images
from .epub.loading import load_epub
from .epub.metadata import extract_epub_metadata
from .epub.toc import TocEntry, extract_toc, parse_toc_item
from .epub.utils import count_words, estimate_reading_time
from .epub.validator import supports_epub_format, validate_epub_file

logger = logging.getLogger(__name__)


class EPUBParser(BaseParser):
    """Parser for EPUB files using EbookLib library.

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
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize EPUB parser with options.

        Args:
            options: Parser configuration dictionary.
        """
        super().__init__(options)

        # Set default options
        self.options.setdefault("extract_images", True)
        self.options.setdefault("image_output_dir", None)
        self.options.setdefault("detect_chapters", True)
        self.options.setdefault("clean_text", True)
        self.options.setdefault("min_chapter_length", 100)
        self.options.setdefault("use_toc", True)
        self.options.setdefault("use_spine_fallback", True)

        # Initialize tracking
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None

    def supports_format(self, file_path: Union[Path, str]) -> bool:
        """Check if file is an EPUB.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .epub extension, False otherwise.
        """
        return supports_epub_format(file_path)

    def parse(self, file_path: Union[Path, str]) -> Document:
        """Parse EPUB file and return Document object.

        This is the main entry point for EPUB parsing. It orchestrates:
        1. File validation
        2. EPUB loading
        3. Metadata extraction
        4. TOC extraction
        5. Content and chapter extraction
        6. Image extraction (if enabled)
        7. Text cleaning (if enabled)
        8. Document object creation

        Args:
            file_path: Path to EPUB file.

        Returns:
            Document object with parsed content, chapters, images, and metadata.

        Raises:
            FileReadError: If file cannot be read or is not a valid EPUB.
            ParsingError: If parsing fails.
            ValidationError: If file validation fails.
        """
        import time

        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)

        self._start_time = time.time()
        self._warnings = []

        try:
            # Step 1: Validate EPUB file
            self._validate_epub(file_path)

            # Step 2: Load EPUB with ebooklib
            logger.info(f"Loading EPUB: {file_path}")
            book = self._load_epub(file_path)

            # Step 3: Extract metadata
            logger.info("Extracting metadata")
            metadata = self._extract_metadata(book, file_path)

            # Step 4: Extract TOC structure
            logger.info("Extracting table of contents")
            toc_entries = (
                self._extract_toc(book) if self.options.get("use_toc") else None
            )

            # Step 5: Extract content and detect chapters
            logger.info("Extracting content and detecting chapters")
            content, chapters = self._extract_content_and_chapters(book, toc_entries)

            # Step 6: Extract images (if enabled)
            images: List[ImageReference] = []
            if self.options.get("extract_images"):
                logger.info("Extracting images")
                try:
                    images = self.extract_images(file_path)
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    self._warnings.append(f"Image extraction failed: {e}")

            # Step 7: Clean text (if enabled)
            if self.options.get("clean_text"):
                logger.info("Cleaning text")
                content = self.clean_text(content)
                for chapter in chapters:
                    chapter.content = self.clean_text(chapter.content)

            # Step 8: Calculate statistics
            word_count = count_words(content)
            reading_time = estimate_reading_time(word_count)

            # Step 9: Create processing info
            processing_time = time.time() - self._start_time
            processing_info = ProcessingInfo(
                parser_used="EPUBParser",
                parser_version="1.0.0",
                processing_time=processing_time,
                timestamp=datetime.now(),
                warnings=self._warnings,
                options_used=self.options.copy(),
            )

            # Step 10: Create and return Document
            document = Document(
                document_id=str(uuid.uuid4()),
                content=content,
                chapters=chapters,
                images=images,
                metadata=metadata,
                processing_info=processing_info,
                word_count=word_count,
                estimated_reading_time=reading_time,
            )

            logger.info(
                f"EPUB parsing complete: {word_count} words, {len(chapters)} chapters, {len(images)} images"
            )
            return document

        except (FileReadError, ValidationError):
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"EPUB parsing failed: {e}")
            raise ParsingError(
                f"Failed to parse EPUB file: {e}", parser="EPUBParser", original_error=e
            )

    def _validate_epub(self, file_path: Path) -> None:
        """Validate EPUB file before parsing.

        Checks:
        - File exists
        - File is readable
        - File has .epub extension
        - File size is reasonable (not empty, not too large)

        Args:
            file_path: Path to EPUB file.

        Raises:
            FileReadError: If file doesn't exist or isn't readable.
            ValidationError: If file validation fails.
        """
        validate_epub_file(file_path, warnings=self._warnings)

    def _load_epub(self, file_path: Path) -> epub.EpubBook:
        """Load EPUB file using ebooklib.

        Args:
            file_path: Path to EPUB file.

        Returns:
            EpubBook object.

        Raises:
            ParsingError: If EPUB cannot be loaded.
        """
        return load_epub(file_path, self._warnings)

    def _extract_metadata(self, book: epub.EpubBook, file_path: Path) -> Metadata:
        """Extract metadata from EPUB OPF file.

        Delegates to the modular metadata extraction function to extract
        standard Dublin Core metadata fields from the EPUB package document (OPF file).

        Args:
            book: EpubBook object.
            file_path: Path to EPUB file (for file_size).

        Returns:
            Metadata object with extracted fields.
        """
        return extract_epub_metadata(book, file_path, self._warnings)

    def _extract_toc(self, book: epub.EpubBook) -> Optional[List[TocEntry]]:
        """Extract table of contents from EPUB.

        Delegates to the modular extract_toc function in the toc module.

        Args:
            book: EpubBook object.

        Returns:
            Flat list of TocEntry objects with level indicating hierarchy,
            or None if TOC is missing/empty.
        """
        return extract_toc(book, self._warnings)

    def _parse_toc_item(
        self, items: Any, flat_toc: List[TocEntry], level: int = 1
    ) -> None:
        """Recursively parse TOC items into flat list.

        Delegates to the modular parse_toc_item function in the toc module.

        Args:
            items: TOC item(s) to parse (Link, tuple, or list).
            flat_toc: Accumulator list for flattened TocEntry objects.
            level: Current hierarchy level (1=top-level, 2=subsection, etc.).
        """
        parse_toc_item(items, flat_toc, level, self._warnings)

    def _extract_content_and_chapters(
        self, book: epub.EpubBook, toc_entries: Optional[List[TocEntry]]
    ) -> Tuple[str, List[Chapter]]:
        """Extract full content and detect chapters.

        Delegates to the modular chapter extraction module which handles:
        - TOC-based detection if available
        - Spine-based detection as fallback
        - Post-processing (filtering and deduplication)

        Args:
            book: EpubBook object.
            toc_entries: TOC entries if available, None otherwise.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        return extract_content_and_chapters(
            book, toc_entries, self.options, self._warnings
        )

    def _extract_chapters_toc(
        self, book: epub.EpubBook, toc_entries: List[TocEntry]
    ) -> Tuple[str, List[Chapter]]:
        """Extract chapters using TOC-based detection.

        Delegates to the modular chapter extraction function which maps TOC entries
        to spine items and creates chapter boundaries based on TOC structure.
        This respects the author's intended chapter divisions.

        Args:
            book: EpubBook object.
            toc_entries: List of TOC entries.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        return extract_chapters_from_toc(book, toc_entries, self._warnings)

    def _extract_chapters_spine(self, book: epub.EpubBook) -> Tuple[str, List[Chapter]]:
        """Extract chapters using spine-based detection (fallback method).

        Delegates to the modular chapter extraction function which creates one
        chapter per spine item when TOC is not available. This is a simple fallback
        that may not match the author's intended chapter structure.

        Args:
            book: EpubBook object.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        return extract_chapters_from_spine(book, self._warnings)

    def _postprocess_chapters(self, chapters: List[Chapter]) -> List[Chapter]:
        """Post-process chapters: filter empty ones and handle duplicates.

        Delegates to the modular chapter processing function which applies:
        - Remove chapters below min_chapter_length threshold
        - Disambiguate duplicate chapter titles
        - Re-number chapter IDs sequentially

        Args:
            chapters: List of chapters to process.

        Returns:
            Filtered and cleaned chapter list.
        """
        return postprocess_chapters(chapters, self.options, self._warnings)

    def extract_images(self, file_path: Union[Path, str]) -> List[ImageReference]:
        """Extract images from EPUB file.

        Delegates to the modular image extraction function in the images module.
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
            # Load EPUB file
            logger.info(f"Loading EPUB for image extraction: {file_path}")
            book = self._load_epub(file_path)

            # Get output directory from options
            image_output_dir = self.options.get("image_output_dir")
            output_path = (
                Path(image_output_dir) if image_output_dir is not None else None
            )

            # Delegate to modular image extraction function
            return extract_epub_images(book, output_path, self._warnings)

        except ParsingError:
            # Re-raise ParsingError
            raise
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            raise ParsingError(
                f"Failed to extract images from EPUB: {e}",
                parser="EPUBParser",
                original_error=e,
            )
