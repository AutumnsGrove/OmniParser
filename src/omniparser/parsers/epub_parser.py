"""
EPUB parser implementation using EbookLib.

This module provides the EPUBParser class for parsing EPUB files and converting
them to OmniParser's universal Document format. It includes TOC-based and
spine-based chapter detection, metadata extraction, image handling, and text
cleaning.

Ported and adapted from epub2tts project with TTS-specific features removed.
"""

import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ebooklib
from ebooklib import epub

from ..base.base_parser import BaseParser
from ..exceptions import FileReadError, ParsingError, ValidationError
from ..models import Chapter, Document, ImageReference, Metadata, ProcessingInfo

logger = logging.getLogger(__name__)


class TocEntry:
    """Internal representation of a table of contents entry.

    This is used during TOC parsing to build the chapter structure before
    converting to OmniParser's Chapter model.

    Attributes:
        title: Chapter title from TOC.
        href: EPUB internal reference (e.g., "chapter1.xhtml#section").
        level: Heading level (1=main chapter, 2=subsection, etc.).
        children: List of nested TocEntry objects.
    """

    def __init__(
        self,
        title: str,
        href: str,
        level: int = 1,
        children: Optional[List["TocEntry"]] = None
    ):
        self.title = title
        self.href = href
        self.level = level
        self.children = children or []


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
        self.options.setdefault('extract_images', True)
        self.options.setdefault('detect_chapters', True)
        self.options.setdefault('clean_text', True)
        self.options.setdefault('min_chapter_length', 100)
        self.options.setdefault('use_toc', True)
        self.options.setdefault('use_spine_fallback', True)

        # Initialize tracking
        self._warnings: List[str] = []
        self._start_time: Optional[float] = None

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is an EPUB.

        Args:
            file_path: Path to check.

        Returns:
            True if file has .epub extension, False otherwise.
        """
        return file_path.suffix.lower() in ['.epub']

    def parse(self, file_path: Path) -> Document:
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
            toc_entries = self._extract_toc(book) if self.options.get('use_toc') else None

            # Step 5: Extract content and detect chapters
            logger.info("Extracting content and detecting chapters")
            content, chapters = self._extract_content_and_chapters(book, toc_entries)

            # Step 6: Extract images (if enabled)
            images: List[ImageReference] = []
            if self.options.get('extract_images'):
                logger.info("Extracting images")
                try:
                    images = self.extract_images(file_path)
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    self._warnings.append(f"Image extraction failed: {e}")

            # Step 7: Clean text (if enabled)
            if self.options.get('clean_text'):
                logger.info("Cleaning text")
                content = self.clean_text(content)
                for chapter in chapters:
                    chapter.content = self.clean_text(chapter.content)

            # Step 8: Calculate statistics
            word_count = self._count_words(content)
            reading_time = self._estimate_reading_time(word_count)

            # Step 9: Create processing info
            processing_time = time.time() - self._start_time
            processing_info = ProcessingInfo(
                parser_used="EPUBParser",
                parser_version="1.0.0",
                processing_time=processing_time,
                timestamp=datetime.now(),
                warnings=self._warnings,
                options_used=self.options.copy()
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
                estimated_reading_time=reading_time
            )

            logger.info(f"EPUB parsing complete: {word_count} words, {len(chapters)} chapters, {len(images)} images")
            return document

        except (FileReadError, ValidationError):
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"EPUB parsing failed: {e}")
            raise ParsingError(
                f"Failed to parse EPUB file: {e}",
                parser="EPUBParser",
                original_error=e
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
        # Check file exists
        if not file_path.exists():
            raise FileReadError(f"File not found: {file_path}")

        # Check file is readable
        if not file_path.is_file():
            raise FileReadError(f"Not a file: {file_path}")

        # Check extension
        if not self.supports_format(file_path):
            raise ValidationError(f"Not an EPUB file: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValidationError(f"Empty file: {file_path}")

        # Warn if file is very large (>500MB)
        if file_size > 500 * 1024 * 1024:
            logger.warning(f"Large EPUB file ({file_size / 1024 / 1024:.1f} MB)")
            self._warnings.append(f"Large file size: {file_size / 1024 / 1024:.1f} MB")

    def _load_epub(self, file_path: Path) -> epub.EpubBook:
        """Load EPUB file using ebooklib.

        Args:
            file_path: Path to EPUB file.

        Returns:
            EpubBook object.

        Raises:
            ParsingError: If EPUB cannot be loaded.
        """
        try:
            book = epub.read_epub(str(file_path))
            return book
        except Exception as e:
            logger.error(f"Failed to load EPUB: {e}")
            raise ParsingError(
                f"Failed to load EPUB file: {e}",
                parser="EPUBParser",
                original_error=e
            )

    def _extract_metadata(self, book: epub.EpubBook, file_path: Path) -> Metadata:
        """Extract metadata from EPUB OPF file.

        Extracts standard Dublin Core metadata fields from the EPUB package
        document (OPF file).

        Args:
            book: EpubBook object.
            file_path: Path to EPUB file (for file_size).

        Returns:
            Metadata object with extracted fields.
        """
        # Helper function to safely extract first metadata value
        def get_first_metadata(namespace: str, name: str) -> Optional[str]:
            """Get first metadata value from book."""
            try:
                metadata_list = book.get_metadata(namespace, name)
                if metadata_list and len(metadata_list) > 0:
                    # Metadata returns list of tuples: [(value, attributes_dict)]
                    return metadata_list[0][0]
            except Exception as e:
                logger.debug(f"Failed to get metadata {namespace}:{name}: {e}")
            return None

        # Helper function to get all metadata values
        def get_all_metadata(namespace: str, name: str) -> List[str]:
            """Get all metadata values from book."""
            try:
                metadata_list = book.get_metadata(namespace, name)
                if metadata_list:
                    return [item[0] for item in metadata_list if item[0]]
            except Exception as e:
                logger.debug(f"Failed to get metadata list {namespace}:{name}: {e}")
            return []

        # Extract title
        title = get_first_metadata('DC', 'title')

        # Extract authors (all contributors)
        authors = get_all_metadata('DC', 'creator')
        # Primary author is first in list
        author = authors[0] if authors else None

        # Extract publisher
        publisher = get_first_metadata('DC', 'publisher')

        # Extract and parse publication date
        publication_date: Optional[datetime] = None
        date_str = get_first_metadata('DC', 'date')
        if date_str:
            # Try common date formats
            date_formats = [
                '%Y-%m-%d',           # 2023-01-15
                '%Y-%m-%dT%H:%M:%S',  # 2023-01-15T10:30:00
                '%Y-%m-%dT%H:%M:%SZ', # 2023-01-15T10:30:00Z
                '%Y',                 # 2023
                '%Y-%m',              # 2023-01
            ]
            for fmt in date_formats:
                try:
                    publication_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            if publication_date is None:
                logger.warning(f"Could not parse publication date: {date_str}")
                self._warnings.append(f"Could not parse publication date: {date_str}")

        # Extract language
        language = get_first_metadata('DC', 'language')

        # Extract ISBN from identifiers
        isbn: Optional[str] = None
        identifiers = get_all_metadata('DC', 'identifier')
        for identifier in identifiers:
            # Look for ISBN in identifier string
            if identifier and 'isbn' in identifier.lower():
                # Extract just the ISBN number (remove "ISBN:" prefix if present)
                isbn = identifier.replace('urn:isbn:', '').replace('ISBN:', '').replace('isbn:', '').strip()
                break

        # Extract description
        description = get_first_metadata('DC', 'description')

        # Extract tags/subjects
        tags = get_all_metadata('DC', 'subject')

        # Calculate file size
        file_size = file_path.stat().st_size

        return Metadata(
            title=title,
            author=author,
            authors=authors,
            publisher=publisher,
            publication_date=publication_date,
            language=language,
            isbn=isbn,
            description=description,
            tags=tags,
            original_format="epub",
            file_size=file_size,
            custom_fields={}
        )

    def _extract_toc(self, book: epub.EpubBook) -> Optional[List[TocEntry]]:
        """Extract table of contents from EPUB.

        Args:
            book: EpubBook object.

        Returns:
            List of TocEntry objects, or None if TOC is missing/empty.
        """
        # TODO: Implement TOC extraction
        # This will be implemented in a later task
        return None

    def _extract_content_and_chapters(
        self,
        book: epub.EpubBook,
        toc_entries: Optional[List[TocEntry]]
    ) -> Tuple[str, List[Chapter]]:
        """Extract full content and detect chapters.

        Args:
            book: EpubBook object.
            toc_entries: TOC entries if available, None otherwise.

        Returns:
            Tuple of (full_content, chapters_list).
        """
        # TODO: Implement content and chapter extraction
        # This will be implemented in later tasks

        # Placeholder
        content = "TODO: Extract content from EPUB"
        chapters: List[Chapter] = []

        return content, chapters

    def extract_images(self, file_path: Path) -> List[ImageReference]:
        """Extract images from EPUB file.

        Args:
            file_path: Path to EPUB file.

        Returns:
            List of ImageReference objects.
        """
        # TODO: Implement image extraction
        # This will be implemented in a later task
        return []

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Text to count words in.

        Returns:
            Word count.
        """
        return len(text.split())

    def _estimate_reading_time(self, word_count: int) -> int:
        """Estimate reading time in minutes.

        Assumes average reading speed of 200-250 words per minute.
        Uses 225 WPM as middle ground.

        Args:
            word_count: Total word count.

        Returns:
            Estimated reading time in minutes.
        """
        return max(1, round(word_count / 225))
