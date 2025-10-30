"""
Functional orchestrator for EPUB parsing.

This module provides the main parse_epub() function that coordinates all EPUB
parsing operations using the modular components extracted from epub_parser.py.

This is the functional interface to EPUB parsing, providing a stateless alternative
to the EPUBParser class.
"""

# Standard library
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Third-party
from ebooklib import epub

# Local
from ...exceptions import FileReadError, ParsingError, ValidationError
from ...models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from .chapters import extract_content_and_chapters
from .images import extract_epub_images
from .loading import load_epub
from .metadata import extract_epub_metadata
from .toc import TocEntry, extract_toc
from .utils import count_words, estimate_reading_time
from .validator import supports_epub_format, validate_epub_file

logger = logging.getLogger(__name__)


def parse_epub(file_path: Union[Path, str], **options) -> Document:
    """Parse EPUB file and return Document object.

    This is the main functional entry point for EPUB parsing. It orchestrates
    all parsing operations using modular components in a stateless, functional style.

    Parsing Pipeline:
    1. File validation (existence, format, size)
    2. EPUB loading (using ebooklib)
    3. Metadata extraction (from OPF file)
    4. TOC extraction (table of contents)
    5. Content and chapter extraction (TOC-based or spine-based)
    6. Image extraction (if enabled)
    7. Text cleaning (if enabled)
    8. Document object creation

    Args:
        file_path: Path to EPUB file (str or Path).
        **options: Parser configuration options:
            extract_images (bool): Extract images from EPUB. Default: True
            image_output_dir (str|Path): Directory to save extracted images.
                If None (default), images are saved to temp directory and deleted after parsing.
                If set, images are saved persistently to the specified directory.
            detect_chapters (bool): Enable chapter detection. Default: True
            clean_text (bool): Apply text cleaning. Default: True
            min_chapter_length (int): Minimum words per chapter. Default: 100
            use_toc (bool): Use TOC for chapter detection. Default: True
            use_spine_fallback (bool): Use spine if TOC missing. Default: True

    Returns:
        Document object with parsed content, chapters, images, and metadata.

    Raises:
        FileReadError: If file cannot be read or is not a valid EPUB.
        ParsingError: If parsing fails at any stage.
        ValidationError: If file validation fails.

    Example:
        >>> from pathlib import Path
        >>> doc = parse_epub(Path("book.epub"))
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Chapters: {len(doc.chapters)}")
        >>> print(f"Words: {doc.word_count}")

        >>> # With custom options
        >>> doc = parse_epub(
        ...     "book.epub",
        ...     extract_images=True,
        ...     image_output_dir="./images",
        ...     min_chapter_length=200
        ... )

    Note:
        This function is stateless and thread-safe. Each call creates a fresh
        parsing context with no shared state.
    """
    # Convert string to Path if needed
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Start timing
    start_time = time.time()

    # Initialize warnings list
    warnings: List[str] = []

    # Set default options
    config = _build_config(options)

    try:
        # Step 1: Validate EPUB file
        logger.info(f"Validating EPUB file: {file_path}")
        validate_epub_file(file_path, warnings)

        # Step 2: Load EPUB with ebooklib
        logger.info(f"Loading EPUB: {file_path}")
        book = load_epub(file_path, warnings)

        # Step 3: Extract metadata
        logger.info("Extracting metadata")
        metadata = extract_epub_metadata(book, file_path, warnings)

        # Step 4: Extract TOC structure
        toc_entries: Optional[List[TocEntry]] = None
        if config["use_toc"]:
            logger.info("Extracting table of contents")
            toc_entries = extract_toc(book, warnings)

        # Step 5: Extract content and detect chapters
        logger.info("Extracting content and detecting chapters")
        content, chapters = extract_content_and_chapters(
            book, toc_entries, config, warnings
        )

        # Step 6: Extract images (if enabled)
        images: List[ImageReference] = []
        if config["extract_images"]:
            logger.info("Extracting images")
            try:
                images = _extract_images(book, file_path, config, warnings)
            except Exception as e:
                logger.warning(f"Image extraction failed: {e}")
                warnings.append(f"Image extraction failed: {e}")

        # Step 7: Clean text (if enabled)
        if config["clean_text"]:
            logger.info("Cleaning text")
            content = _clean_text(content)
            chapters = _clean_chapters(chapters)

        # Step 8: Calculate statistics
        word_count = count_words(content)
        reading_time = estimate_reading_time(word_count)

        # Step 9: Create processing info
        processing_time = time.time() - start_time
        processing_info = ProcessingInfo(
            parser_used="EPUBParser",
            parser_version="1.0.0",
            processing_time=processing_time,
            timestamp=datetime.now(),
            warnings=warnings,
            options_used=config.copy(),
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

        # Log completion
        logger.info(
            f"EPUB parsing complete: {word_count} words, {len(chapters)} chapters, "
            f"{len(images)} images (took {processing_time:.2f}s)"
        )

        # Log warnings if any
        if warnings:
            logger.warning(f"Parsing completed with {len(warnings)} warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        return document

    except (FileReadError, ValidationError):
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"EPUB parsing failed: {e}")
        raise ParsingError(
            f"Failed to parse EPUB file: {e}", parser="EPUBParser", original_error=e
        )


# ============================================================================
# Helper Functions
# ============================================================================


def _build_config(options: Dict[str, Any]) -> Dict[str, Any]:
    """Build complete configuration with defaults.

    Merges user-provided options with default values.

    Args:
        options: User-provided options dictionary.

    Returns:
        Complete configuration dictionary with all defaults set.
    """
    config = {
        "extract_images": True,
        "image_output_dir": None,
        "detect_chapters": True,
        "clean_text": True,
        "min_chapter_length": 100,
        "use_toc": True,
        "use_spine_fallback": True,
    }
    config.update(options)
    return config


def _extract_images(
    book: epub.EpubBook,
    file_path: Path,
    config: Dict[str, Any],
    warnings: List[str],
) -> List[ImageReference]:
    """Extract images from EPUB file.

    Delegates to the modular image extraction function. Handles both temporary
    and persistent image storage based on configuration.

    Args:
        book: EpubBook object.
        file_path: Path to EPUB file (for logging).
        config: Parser configuration dictionary.
        warnings: List to accumulate warning messages.

    Returns:
        List of ImageReference objects.
    """
    # Get output directory from config
    image_output_dir = config.get("image_output_dir")
    output_path = Path(image_output_dir) if image_output_dir is not None else None

    # Delegate to modular image extraction function
    return extract_epub_images(book, output_path, warnings)


def _clean_text(text: str) -> str:
    """Clean text content.

    Applies text cleaning operations like removing extra whitespace,
    normalizing line breaks, etc.

    Args:
        text: Text content to clean.

    Returns:
        Cleaned text content.

    Note:
        Currently performs basic whitespace normalization.
        Future: integrate with TextCleaner processor for advanced cleaning.
    """
    # TODO: Integrate with processors.text_cleaner when available
    # For now, do basic cleaning
    if not text:
        return text

    # Normalize whitespace
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines]

    # Remove excessive blank lines (max 2 consecutive)
    result_lines: List[str] = []
    blank_count = 0

    for line in cleaned_lines:
        if not line:
            blank_count += 1
            if blank_count <= 2:
                result_lines.append(line)
        else:
            blank_count = 0
            result_lines.append(line)

    return "\n".join(result_lines).strip()


def _clean_chapters(chapters: List[Chapter]) -> List[Chapter]:
    """Clean text content in all chapters.

    Applies text cleaning to each chapter's content.

    Args:
        chapters: List of chapters to clean.

    Returns:
        List of chapters with cleaned content.
    """
    for chapter in chapters:
        chapter.content = _clean_text(chapter.content)
    return chapters
