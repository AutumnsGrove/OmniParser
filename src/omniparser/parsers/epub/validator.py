"""Validation functions for EPUB files.

This module provides format validation and file integrity checking for EPUB files.
Extracted from epub_parser.py for modularity and reusability.
"""

# Standard library
import logging
from pathlib import Path
from typing import Union

# Local
from ...exceptions import FileReadError, ValidationError

logger = logging.getLogger(__name__)


def supports_epub_format(file_path: Union[Path, str]) -> bool:
    """Check if file is an EPUB format.

    Determines EPUB format support based on file extension.

    Args:
        file_path: Path to check.

    Returns:
        True if file has .epub extension, False otherwise.

    Example:
        >>> from pathlib import Path
        >>> supports_epub_format(Path("book.epub"))
        True
        >>> supports_epub_format("document.pdf")
        False
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.suffix.lower() in [".epub"]


def validate_epub_file(file_path: Union[Path, str], warnings: list = None) -> None:
    """Validate EPUB file before parsing.

    Performs comprehensive validation including:
    - File existence and readability
    - File extension (.epub)
    - File size (not empty, reasonable size)

    Args:
        file_path: Path to EPUB file.
        warnings: Optional list to accumulate warning messages.

    Raises:
        FileReadError: If file doesn't exist or isn't readable.
        ValidationError: If file validation fails (invalid format or size).

    Example:
        >>> from pathlib import Path
        >>> validate_epub_file(Path("book.epub"))  # Passes if valid
        >>> validate_epub_file(Path("not_a_book.pdf"))  # Raises ValidationError
    """
    # Convert string to Path if needed
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Initialize warnings list if not provided
    if warnings is None:
        warnings = []

    # Check file exists
    if not file_path.exists():
        raise FileReadError(f"File not found: {file_path}")

    # Check file is readable
    if not file_path.is_file():
        raise FileReadError(f"Not a file: {file_path}")

    # Check extension
    if not supports_epub_format(file_path):
        raise ValidationError(f"Not an EPUB file: {file_path}")

    # Check file size
    file_size = file_path.stat().st_size
    if file_size == 0:
        raise ValidationError(f"Empty file: {file_path}")

    # Warn if file is very large (>500MB)
    if file_size > 500 * 1024 * 1024:
        warning_msg = f"Large EPUB file ({file_size / 1024 / 1024:.1f} MB)"
        logger.warning(warning_msg)
        warnings.append(warning_msg)
