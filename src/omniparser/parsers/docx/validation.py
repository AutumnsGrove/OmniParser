"""
DOCX file validation and loading utilities.

This module provides validation functions for DOCX files, including
existence checks, format validation, and document loading using python-docx.

Functions:
    validate_docx_file: Validate DOCX file before parsing
    load_document: Load python-docx Document object
"""

# Standard library
import logging
from pathlib import Path
from typing import Any, List, Union

# Third-party
from docx import Document as DocxDocument  # type: ignore[import]

# Local
from ...exceptions import FileReadError, ParsingError, ValidationError

logger = logging.getLogger(__name__)


def supports_format(file_path: Union[Path, str]) -> bool:
    """Check if file is DOCX format.

    Args:
        file_path: Path to check.

    Returns:
        True if file has .docx extension, False otherwise.
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.suffix.lower() in [".docx"]


def validate_docx_file(file_path: Path, warnings: List[str]) -> None:
    """Validate DOCX file before parsing.

    Checks:
    - File exists
    - File is readable
    - File has .docx extension
    - File size is reasonable (not empty, not too large)

    Args:
        file_path: Path to DOCX file.
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
    if not supports_format(file_path):
        raise ValidationError(f"Not a DOCX file: {file_path}")

    # Check file size
    file_size = file_path.stat().st_size
    if file_size == 0:
        raise ValidationError(f"Empty file: {file_path}")

    # Warn if file is very large (>500MB)
    if file_size > 500 * 1024 * 1024:
        logger.warning(f"Large DOCX file ({file_size / 1024 / 1024:.1f} MB)")
        warnings.append(f"Large file size: {file_size / 1024 / 1024:.1f} MB")


def load_document(file_path: Path) -> Any:
    """Load DOCX file using python-docx.

    Args:
        file_path: Path to DOCX file.

    Returns:
        DocxDocument object.

    Raises:
        ParsingError: If DOCX cannot be loaded.
    """
    try:
        docx = DocxDocument(str(file_path))  # type: ignore[misc]
        logger.info(f"Successfully loaded DOCX: {file_path}")
        return docx
    except Exception as e:
        logger.error(f"Failed to load DOCX: {e}")
        raise ParsingError(
            f"Failed to load DOCX file: {e}",
            parser="DOCXParser",
            original_error=e,
        )
