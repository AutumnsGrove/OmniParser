"""
Text parser orchestrator - Main entry point for plain text parsing.

This module coordinates all text parsing operations by wiring together
specialized modules for validation, encoding detection, chapter detection,
and utilities. It follows the functional pattern (not class-based) to align
with the Markdown and DOCX parser architecture.

Functions:
    parse_text: Main orchestrator function that coordinates all parsing steps

Architecture:
    1. Validation: Verify file exists and is valid text file
    2. Reading: Load file content with automatic encoding detection
    3. Chapters: Detect chapters from text patterns (optional)
    4. Analysis: Count words and estimate reading time
    5. Metadata: Build Metadata object from file info
    6. Document: Build and return Document object

Status: Production-Ready
Features:
    - Automatic encoding detection (chardet)
    - Pattern-based chapter detection (Chapter 1, CHAPTER I, Part 1, etc.)
    - Single chapter fallback if no structure detected
    - Word counting and reading time estimation
    - Comprehensive error handling with warnings
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Union

from ...models import Chapter, Document, Metadata, ProcessingInfo
from .chapter_detection import detect_text_chapters
from .encoding import read_text_with_encoding
from .utils import count_words, estimate_reading_time
from .validation import validate_text_file

logger = logging.getLogger(__name__)


def parse_text(
    file_path: Union[Path, str],
    detect_chapters: bool = True,
) -> Document:
    """Parse plain text file and return structured Document object.

    Main orchestrator function that coordinates all text parsing operations.
    Follows a sequential pipeline:
    1. Validate file and check format
    2. Read file content with automatic encoding detection
    3. Detect chapters from text patterns (optional)
    4. Count words and estimate reading time
    5. Create metadata from file info
    6. Build and return Document object

    Args:
        file_path: Path to text file to parse.
        detect_chapters: Whether to attempt chapter detection from patterns.
            Default: True. If False or no patterns found, creates single chapter.

    Returns:
        Document object with:
        - metadata: Metadata object with title, format, file info
        - content: Full text content
        - chapters: List of Chapter objects (from patterns or single chapter)
        - images: Empty list (text files don't have images)
        - word_count: Total word count
        - estimated_reading_time: Reading time in minutes
        - processing_info: ProcessingInfo with warnings and options
        - warnings: List of warning messages (encoding issues, etc.)

    Raises:
        FileReadError: If file doesn't exist or isn't readable
        ValidationError: If file validation fails
        ParsingError: If text parsing fails

    Example:
        >>> from pathlib import Path
        >>> from omniparser.parsers.text import parse_text
        >>>
        >>> # Basic usage
        >>> doc = parse_text(Path("notes.txt"))
        >>> print(doc.metadata.title)
        >>> print(doc.word_count)
        >>>
        >>> # Without chapter detection
        >>> doc = parse_text(Path("notes.txt"), detect_chapters=False)
        >>> print(f"Single chapter: {doc.chapters[0].title}")
        >>>
        >>> # Check for encoding warnings
        >>> if doc.processing_info.warnings:
        ...     print("Warnings:", doc.processing_info.warnings)
    """
    # Convert string to Path if needed
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Track parsing time and warnings
    start_time = time.time()
    warnings: List[str] = []

    logger.info(f"Starting text parsing: {file_path}")

    # Step 1: Validate file
    logger.debug("Validating text file")
    validate_text_file(file_path, warnings)
    logger.debug("File validation passed")

    # Step 2: Read file content with encoding detection
    logger.debug("Reading file with encoding detection")
    content = read_text_with_encoding(file_path, warnings)
    logger.debug(f"Read {len(content)} characters")

    # Step 3: Detect chapters (optional)
    if detect_chapters:
        logger.debug("Detecting chapters from text patterns")
        chapters = detect_text_chapters(content, file_path)

        if not chapters:
            # No chapters detected: create single chapter with all content
            logger.debug("No chapters detected, creating single chapter")
            title = _extract_title_from_content(content, file_path)
            chapters = [
                Chapter(
                    chapter_id=1,
                    title=title,
                    content=content,
                    start_position=0,
                    end_position=len(content),
                    word_count=count_words(content),
                    level=1,
                    metadata={"detection_method": "single_chapter"},
                )
            ]
    else:
        logger.debug("Chapter detection disabled, creating single chapter")
        title = _extract_title_from_content(content, file_path)
        chapters = [
            Chapter(
                chapter_id=1,
                title=title,
                content=content,
                start_position=0,
                end_position=len(content),
                word_count=count_words(content),
                level=1,
                metadata={"detection_method": "single_chapter"},
            )
        ]

    logger.info(f"Created {len(chapters)} chapters")

    # Step 4: Count words and estimate reading time
    word_count = count_words(content)
    reading_time = estimate_reading_time(word_count)
    logger.debug(f"Word count: {word_count}, Reading time: {reading_time} min")

    # Step 5: Create metadata
    logger.debug("Creating metadata")
    metadata = _create_metadata(file_path, content, warnings)
    logger.debug(f"Metadata: {metadata.title}")

    # Step 6: Build ProcessingInfo
    processing_time = time.time() - start_time
    from omniparser import __version__

    processing_info = ProcessingInfo(
        parser_used="parse_text",
        parser_version=__version__,
        processing_time=processing_time,
        timestamp=datetime.now(),
        warnings=warnings,
        options_used={
            "detect_chapters": detect_chapters,
        },
    )

    # Step 7: Build and return Document
    document = Document(
        document_id=f"text_{file_path.stem}",
        content=content,
        chapters=chapters,
        images=[],  # Text files don't have images
        metadata=metadata,
        processing_info=processing_info,
        word_count=word_count,
        estimated_reading_time=reading_time,
    )

    logger.info(
        f"Text parsing complete: {word_count} words, "
        f"{len(chapters)} chapters, {len(warnings)} warnings, "
        f"{processing_time:.3f}s"
    )

    return document


def _extract_title_from_content(content: str, file_path: Path) -> str:
    """Extract title from content or use filename as fallback.

    Attempts to use the first non-empty line as title if it's short enough
    (<100 characters). Otherwise uses filename without extension.

    Args:
        content: Text content to extract title from.
        file_path: Path to source file (used as fallback).

    Returns:
        Extracted title string.

    Example:
        >>> _extract_title_from_content("My Notes\\n\\nContent here", Path("notes.txt"))
        'My Notes'
        >>> _extract_title_from_content("", Path("notes.txt"))
        'notes'
    """
    lines = content.split("\n")
    first_line = lines[0].strip() if lines else ""

    # Use first line as title if it's short and not empty
    if first_line and len(first_line) < 100:
        return first_line
    else:
        # Use filename without extension as fallback
        return file_path.stem


def _create_metadata(file_path: Path, content: str, warnings: List[str]) -> Metadata:
    """Create metadata for text file.

    Builds Metadata object with:
    - Title from first line or filename
    - File size
    - Format: "text"
    - Custom fields: line count, encoding warnings

    Args:
        file_path: Path to source file.
        content: Text content.
        warnings: List of warnings (may contain encoding info).

    Returns:
        Metadata object.

    Example:
        >>> warnings = ["Used UTF-8 encoding"]
        >>> metadata = _create_metadata(Path("notes.txt"), "Content", warnings)
        >>> metadata.title
        'notes'
        >>> metadata.original_format
        'text'
    """
    from ...processors.metadata_builder import MetadataBuilder

    # Extract title from content or filename
    title = _extract_title_from_content(content, file_path)

    # Calculate file size and line count
    file_size = file_path.stat().st_size
    line_count = len(content.split("\n"))

    # Extract encoding info from warnings if present
    encoding_info = None
    for warning in warnings:
        if "encoding" in warning.lower():
            encoding_info = warning
            break

    # Build custom fields
    custom_fields = {"line_count": line_count}
    if encoding_info:
        custom_fields["encoding_info"] = encoding_info

    return MetadataBuilder.build(
        title=title,
        author=None,
        authors=None,
        publisher=None,
        publication_date=None,
        language=None,
        isbn=None,
        description=None,
        tags=None,
        original_format="text",
        file_size=file_size,
        custom_fields=custom_fields,
    )
