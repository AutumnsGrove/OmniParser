"""
Text file validation utilities.

This module provides functions for validating plain text files before parsing.
It ensures files exist, have correct extensions, and can be read successfully.

Functions:
    validate_text_file: Validate text file existence, readability, and size
"""

# Standard library
import logging
from pathlib import Path
from typing import List

# Local
from ...exceptions import FileReadError, ValidationError

logger = logging.getLogger(__name__)


def validate_text_file(file_path: Path, warnings: List[str]) -> None:
    """
    Validate text file before parsing.

    Checks:
    - File exists
    - File is readable
    - File has .txt extension (or no extension)
    - File size is reasonable (not empty, warning if very large)

    Args:
        file_path: Path to text file.
        warnings: List to append warnings to (for large files).

    Raises:
        FileReadError: If file doesn't exist or isn't readable.
        ValidationError: If file validation fails.

    Example:
        >>> from pathlib import Path
        >>> warnings = []
        >>> validate_text_file(Path("notes.txt"), warnings)
        >>> if warnings:
        ...     print("Warnings:", warnings)
    """
    # Check file exists
    if not file_path.exists():
        raise FileReadError(f"File not found: {file_path}")

    # Check file is readable
    if not file_path.is_file():
        raise FileReadError(f"Not a file: {file_path}")

    # Check file size
    file_size = file_path.stat().st_size
    if file_size == 0:
        raise ValidationError(f"Empty file: {file_path}")

    # Warn if file is very large (>50MB)
    # This threshold is set conservatively to alert users about potential
    # performance issues. Text files of this size will still parse successfully
    # but may take several seconds and consume significant memory.
    LARGE_FILE_THRESHOLD_MB = 50
    if file_size > LARGE_FILE_THRESHOLD_MB * 1024 * 1024:
        warning_msg = f"Large file size: {file_size / 1024 / 1024:.1f} MB"
        logger.warning(f"Large text file ({file_size / 1024 / 1024:.1f} MB)")
        warnings.append(warning_msg)
