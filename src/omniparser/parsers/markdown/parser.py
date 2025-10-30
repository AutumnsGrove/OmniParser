"""
Markdown parser orchestrator - Main entry point for Markdown parsing.

This module coordinates all Markdown parsing operations by wiring together
specialized modules for validation, frontmatter extraction, content processing,
chapter detection, and image extraction. It follows the functional pattern
(not class-based) to align with the PDF and DOCX parser architecture.

Functions:
    parse_markdown: Main orchestrator function that coordinates all parsing steps

Architecture:
    1. Validation: Verify file exists and is valid Markdown
    2. Reading: Load file content with proper encoding
    3. Frontmatter: Extract and parse YAML/TOML/JSON frontmatter (optional)
    4. Metadata: Build Metadata object from frontmatter or defaults
    5. Normalization: Standardize markdown formatting
    6. Chapters: Detect chapters from headings
    7. Images: Extract image references
    8. Analysis: Count words and estimate reading time
    9. Document: Build and return Document object

Status: Production-Ready
Features:
    - YAML/TOML/JSON frontmatter extraction
    - Heading-based chapter detection (configurable levels)
    - Image reference extraction (inline and reference-style)
    - Markdown normalization (heading styles, list markers)
    - Word counting (markdown-aware)
    - Reading time estimation
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Union

from ...models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from .content import normalize_markdown_content, process_markdown_chapters
from .frontmatter import extract_frontmatter, parse_frontmatter_to_metadata
from .images import extract_image_references
from .utils import count_words, estimate_reading_time
from .validation import read_markdown_file, validate_markdown_file

logger = logging.getLogger(__name__)


def parse_markdown(
    file_path: Union[Path, str],
    extract_images: bool = True,
    min_chapter_level: int = 1,
    max_chapter_level: int = 2,
    normalize_content: bool = True,
) -> Document:
    """Parse Markdown file and return structured Document object.

    Main orchestrator function that coordinates all Markdown parsing operations.
    Follows a sequential pipeline:
    1. Validate file and check format
    2. Read file content with proper encoding
    3. Extract frontmatter (YAML/TOML/JSON)
    4. Parse frontmatter to Metadata object
    5. Normalize markdown content (optional)
    6. Process chapters from headings
    7. Extract image references (optional)
    8. Count words and estimate reading time
    9. Build and return Document object

    Args:
        file_path: Path to Markdown file to parse.
        extract_images: Whether to extract image references.
            Default: True
        min_chapter_level: Minimum heading level for chapters (1 = #).
            Default: 1
        max_chapter_level: Maximum heading level for chapters (2 = ##).
            Default: 2
        normalize_content: Whether to normalize markdown formatting
            (heading styles, list markers, blank lines). Default: True

    Returns:
        Document object with:
        - metadata: Metadata object from frontmatter or defaults
        - content: Full markdown content (after frontmatter)
        - chapters: List of Chapter objects from headings
        - images: List of ImageReference objects (if extracted)
        - word_count: Total word count (markdown-aware)
        - estimated_reading_time: Reading time in minutes
        - processing_info: ProcessingInfo with warnings and options
        - warnings: List of warning messages

    Raises:
        FileReadError: If file doesn't exist or isn't readable
        ValidationError: If file validation fails
        ParsingError: If Markdown parsing fails

    Example:
        >>> from pathlib import Path
        >>> from omniparser.parsers.markdown import parse_markdown
        >>>
        >>> # Basic usage
        >>> doc = parse_markdown(Path("README.md"))
        >>> print(doc.metadata.title)
        >>> print(doc.word_count)
        >>>
        >>> # With custom chapter levels (only H1 as chapters)
        >>> doc = parse_markdown(
        ...     Path("README.md"),
        ...     min_chapter_level=1,
        ...     max_chapter_level=1
        ... )
        >>> print(f"Found {len(doc.chapters)} H1 chapters")
        >>>
        >>> # Without image extraction
        >>> doc = parse_markdown(
        ...     Path("README.md"),
        ...     extract_images=False
        ... )
    """
    # Convert string to Path if needed
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Track parsing time and warnings
    start_time = time.time()
    warnings: List[str] = []

    logger.info(f"Starting Markdown parsing: {file_path}")

    # Step 1: Validate file
    logger.debug("Validating Markdown file")
    validate_markdown_file(file_path, warnings)
    logger.debug("File validation passed")

    # Step 2: Read file content
    logger.debug("Reading file content")
    content = read_markdown_file(file_path, warnings)
    logger.debug(f"Read {len(content)} characters")

    # Step 3: Extract frontmatter
    logger.debug("Extracting frontmatter")
    frontmatter_dict, markdown_content = extract_frontmatter(content)

    if frontmatter_dict:
        logger.info(f"Found frontmatter with {len(frontmatter_dict)} fields")
    else:
        logger.debug("No frontmatter found")

    # Step 4: Parse frontmatter to Metadata
    if frontmatter_dict:
        logger.debug("Parsing frontmatter to Metadata")
        metadata = parse_frontmatter_to_metadata(frontmatter_dict, file_path, warnings)
    else:
        logger.debug("Creating default Metadata")
        # Create default metadata using filename as title
        from ...processors.metadata_builder import MetadataBuilder

        metadata = MetadataBuilder.build(
            title=file_path.stem,
            author=None,
            authors=None,
            publisher=None,
            publication_date=None,
            language=None,
            isbn=None,
            description=None,
            tags=None,
            original_format="markdown",
            file_size=file_path.stat().st_size,
            custom_fields=None,
        )

    logger.debug(f"Metadata: {metadata.title}")

    # Step 5: Normalize content (optional)
    if normalize_content:
        logger.debug("Normalizing markdown content")
        markdown_content = normalize_markdown_content(markdown_content)

    # Step 6: Process chapters
    logger.debug("Processing chapters from headings")
    chapters = process_markdown_chapters(
        markdown_content, file_path, min_chapter_level, max_chapter_level
    )

    if not chapters:
        # No chapters found: create single chapter with all content
        logger.debug("No chapters detected, creating single chapter")
        chapters = [
            Chapter(
                chapter_id="ch_001",
                title=metadata.title or file_path.stem,
                content=markdown_content,
                position=0,
                level=1,
                word_count=count_words(markdown_content),
            )
        ]

    logger.info(f"Detected {len(chapters)} chapters")

    # Step 7: Extract images (optional)
    images: List[ImageReference] = []
    if extract_images:
        logger.debug("Extracting image references")
        images = extract_image_references(markdown_content, file_path)
        logger.info(f"Found {len(images)} image references")

    # Step 8: Count words and estimate reading time
    word_count = count_words(markdown_content)
    reading_time = estimate_reading_time(word_count)
    logger.debug(f"Word count: {word_count}, Reading time: {reading_time} min")

    # Step 9: Build ProcessingInfo
    processing_time = time.time() - start_time
    from omniparser import __version__

    processing_info = ProcessingInfo(
        parser_used="parse_markdown",
        parser_version=__version__,
        processing_time=processing_time,
        timestamp=datetime.now(),
        warnings=warnings,
        options_used={
            "extract_images": extract_images,
            "min_chapter_level": min_chapter_level,
            "max_chapter_level": max_chapter_level,
            "normalize_content": normalize_content,
        },
    )

    # Step 10: Build and return Document
    document = Document(
        document_id=f"markdown_{file_path.stem}",
        content=markdown_content,
        chapters=chapters,
        images=images,
        metadata=metadata,
        processing_info=processing_info,
        word_count=word_count,
        estimated_reading_time=reading_time,
    )

    logger.info(
        f"Markdown parsing complete: {word_count} words, "
        f"{len(chapters)} chapters, {len(images)} images, "
        f"{len(warnings)} warnings, {processing_time:.3f}s"
    )

    return document
