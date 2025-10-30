"""
EPUB loading functionality.

This module provides the core function for loading EPUB files using the ebooklib
library. It handles file I/O and error handling for EPUB document loading.
"""

import logging
from pathlib import Path
from typing import List

from ebooklib import epub

from ...exceptions import ParsingError

logger = logging.getLogger(__name__)


def load_epub(file_path: Path, warnings: List[str]) -> epub.EpubBook:
    """Load EPUB file using ebooklib.

    Opens and reads an EPUB file from disk, converting it into an EpubBook
    object for further processing. Handles file I/O errors gracefully.

    Args:
        file_path: Path to EPUB file to load.
        warnings: List to accumulate warning messages during loading.

    Returns:
        EpubBook object loaded from the file.

    Raises:
        ParsingError: If the EPUB file cannot be read or parsed by ebooklib.

    Example:
        >>> from pathlib import Path
        >>> file_path = Path("book.epub")
        >>> warnings = []
        >>> book = load_epub(file_path, warnings)
        >>> print(f"Loaded: {book.title}")
    """
    try:
        book = epub.read_epub(str(file_path))
        return book
    except Exception as e:
        logger.error(f"Failed to load EPUB: {e}")
        raise ParsingError(
            f"Failed to load EPUB file: {e}", parser="EPUBParser", original_error=e
        )
