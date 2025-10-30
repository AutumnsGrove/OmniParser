"""
DOCX parser orchestrator - Main entry point for DOCX parsing.

This module coordinates all DOCX parsing operations by wiring together
specialized modules for validation, metadata extraction, content extraction,
and image processing. It follows the functional pattern (not class-based)
to align with the PDF parser architecture.

Functions:
    parse_docx: Main orchestrator function that coordinates all parsing steps

Architecture:
    1. Validation: Verify file exists and is valid DOCX
    2. Loading: Load python-docx Document object
    3. Metadata: Extract core properties and build Metadata object
    4. Images: Extract and save images (optional)
    5. Content: Extract full text with formatting, lists, hyperlinks, tables
    6. Analysis: Count words and estimate reading time
    7. Document: Build and return Document object

Status: Production-Ready 
Features:
    - Text extraction with formatting (bold, italic)
    - Metadata from core properties
    - Heading detection (# ## ###)
    - Table extraction (markdown tables)
    - List extraction (ordered and unordered)  NEW
    - Hyperlink extraction ([text](url))  NEW
    - Image extraction with dimension detection
"""

import logging
from pathlib import Path
from typing import List, Optional

from ...models import Document
from .content_extraction import extract_content_with_features
from .images import extract_images
from .metadata import extract_metadata
from .utils import count_words, estimate_reading_time
from .validation import load_document, validate_docx_file

logger = logging.getLogger(__name__)


def parse_docx(
    file_path: Path,
    extract_images_flag: bool = True,
    image_output_dir: Optional[Path] = None,
    preserve_formatting: bool = True,
    extract_hyperlinks: bool = True,
    extract_lists: bool = True,
) -> Document:
    """Parse DOCX file and return structured Document object.

    Main orchestrator function that coordinates all DOCX parsing operations.
    Follows a sequential pipeline:
    1. Validate file and check format
    2. Load python-docx Document
    3. Extract metadata from core properties
    4. Extract images (if requested and output_dir specified)
    5. Extract content with features (formatting, lists, hyperlinks, tables)
    6. Count words and estimate reading time
    7. Build and return Document object

    Args:
        file_path: Path to DOCX file to parse.
        extract_images_flag: Whether to extract and save images.
            Default: True
        image_output_dir: Directory to save extracted images.
            Required if extract_images_flag=True.
            Images are only saved if this is a persistent directory
            (not temporary). Default: None
        preserve_formatting: Preserve bold/italic formatting in markdown.
            Default: True
        extract_hyperlinks: Extract and format hyperlinks as markdown [text](url).
            Default: True (NEW feature)
        extract_lists: Extract and format lists as markdown (ordered/unordered).
            Default: True (NEW feature)

    Returns:
        Document object with:
        - metadata: Metadata object with title, author, tags, etc.
        - full_text: Complete document content as markdown string
        - chapters: Empty list (DOCX doesn't have chapters)
        - images: List of ImageReference objects (if extracted)
        - word_count: Total word count (excluding markdown syntax)
        - reading_time_minutes: Estimated reading time
        - warnings: List of warning messages encountered during parsing

    Raises:
        FileReadError: If file doesn't exist or isn't readable
        ValidationError: If file validation fails
        ParsingError: If DOCX parsing fails

    Example:
        >>> from pathlib import Path
        >>> from omniparser.parsers.docx import parse_docx
        >>>
        >>> # Basic usage (no images)
        >>> doc = parse_docx(Path("report.docx"))
        >>> print(doc.metadata.title)
        >>> print(doc.word_count)
        >>>
        >>> # With image extraction
        >>> doc = parse_docx(
        ...     Path("report.docx"),
        ...     extract_images_flag=True,
        ...     image_output_dir=Path("/output/images")
        ... )
        >>> print(f"Extracted {len(doc.images)} images")
        >>>
        >>> # With all features enabled
        >>> doc = parse_docx(
        ...     Path("report.docx"),
        ...     extract_images_flag=True,
        ...     image_output_dir=Path("/output/images"),
        ...     preserve_formatting=True,
        ...     extract_hyperlinks=True,
        ...     extract_lists=True
        ... )
        >>> print(doc.full_text)  # Markdown with links, lists, formatting
    """
    # Initialize warnings list
    warnings_list: List[str] = []
    logger.info(f"Starting DOCX parsing: {file_path}")

    # Step 1: Validate file
    validate_docx_file(file_path, warnings_list)
    logger.debug("File validation passed")

    # Step 2: Load document
    docx = load_document(file_path)
    logger.debug("Document loaded successfully")

    # Step 3: Extract metadata
    metadata = extract_metadata(docx, file_path)
    logger.debug(f"Metadata extracted: {metadata.title}")

    # Step 4: Extract images (optional)
    images: List = []
    if extract_images_flag:
        images, _ = extract_images(
            docx,
            extract_images_flag=extract_images_flag,
            image_output_dir=image_output_dir,
            file_path=file_path,
            warnings_list=warnings_list,
        )
        logger.debug(f"Extracted {len(images)} images")

    # Step 5: Extract content with all features
    content = extract_content_with_features(
        docx,
        preserve_formatting=preserve_formatting,
        extract_hyperlinks=extract_hyperlinks,
        extract_lists=extract_lists,
    )
    logger.debug(f"Content extracted: {len(content)} characters")

    # Step 6: Count words and estimate reading time
    word_count = count_words(content)
    reading_time = estimate_reading_time(word_count)
    logger.debug(f"Word count: {word_count}, Reading time: {reading_time} min")

    # Step 7: Build and return Document
    from datetime import datetime
    from omniparser.models import ProcessingInfo
    from omniparser import __version__

    processing_info = ProcessingInfo(
        parser_used="parse_docx",
        parser_version=__version__,
        processing_time=0.0,  # TODO: Track actual processing time
        timestamp=datetime.now(),
        warnings=warnings_list,
        options_used={
            "extract_images": extract_images_flag,
            "preserve_formatting": preserve_formatting,
            "extract_hyperlinks": extract_hyperlinks,
            "extract_lists": extract_lists,
        },
    )

    document = Document(
        document_id=f"docx_{file_path.stem}",
        content=content,
        chapters=[],  # DOCX doesn't have chapter structure
        images=images,
        metadata=metadata,
        processing_info=processing_info,
        word_count=word_count,
        estimated_reading_time=reading_time,
    )

    logger.info(
        f"DOCX parsing complete: {word_count} words, "
        f"{len(images)} images, {len(warnings_list)} warnings"
    )

    return document
