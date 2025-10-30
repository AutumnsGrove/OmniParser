"""
Markdown file validation and loading utilities.

This module provides functions for validating Markdown files and reading
their content. It ensures files exist, have correct extensions, and can be
read successfully before processing.

Functions:
    validate_markdown_file: Validate Markdown file existence and format
    read_markdown_file: Read Markdown file content with proper encoding
"""

# Standard library
import logging
from pathlib import Path
from typing import List

# Local
from ...exceptions import FileReadError, ValidationError

logger = logging.getLogger(__name__)


def validate_markdown_file(file_path: Path, warnings: List[str]) -> None:
    """
    Validate Markdown file before parsing.

    Checks:
    - File exists
    - File is readable
    - File has .md or .markdown extension
    - File size is reasonable (not empty, warning if very large)

    Args:
        file_path: Path to Markdown file.
        warnings: List to append warnings to (for large files).

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
    if file_path.suffix.lower() not in [".md", ".markdown"]:
        raise ValidationError(f"Not a Markdown file: {file_path}")

    # Check file size
    file_size = file_path.stat().st_size
    if file_size == 0:
        raise ValidationError(f"Empty file: {file_path}")

    # Warn if file is very large (>50MB)
    if file_size > 50 * 1024 * 1024:
        warning_msg = f"Large file size: {file_size / 1024 / 1024:.1f} MB"
        logger.warning(f"Large Markdown file ({file_size / 1024 / 1024:.1f} MB)")
        warnings.append(warning_msg)


def read_markdown_file(file_path: Path, warnings: List[str]) -> str:
    """
    Read Markdown file with proper encoding.

    Attempts UTF-8 encoding first, falls back to latin-1 if UTF-8 fails.

    Args:
        file_path: Path to Markdown file.
        warnings: List to append warnings to (for encoding issues).

    Returns:
        File content as string.

    Raises:
        FileReadError: If file cannot be read.

    Example:
        >>> from pathlib import Path
        >>> warnings = []
        >>> content = read_markdown_file(Path("README.md"), warnings)
        >>> print(f"Length: {len(content)}")
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with latin-1 encoding as fallback
        logger.warning("UTF-8 decode failed, trying latin-1 encoding")
        warnings.append("Used latin-1 encoding (UTF-8 decode failed)")
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            raise FileReadError(f"Failed to read file: {e}")
    except Exception as e:
        raise FileReadError(f"Failed to read file: {e}")
