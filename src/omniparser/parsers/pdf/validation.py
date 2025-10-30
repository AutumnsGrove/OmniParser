"""
PDF file validation and loading utilities.

This module provides functions for validating PDF files and loading them
with PyMuPDF. It ensures files exist, have correct extensions, and can be
opened successfully before processing.

Functions:
    validate_pdf_file: Validate PDF file existence and format
    load_pdf_document: Load PDF file with PyMuPDF
    validate_and_load_pdf: Combined validation and loading operation
"""

from pathlib import Path

import fitz  # PyMuPDF

from ...exceptions import FileReadError, ValidationError


def validate_pdf_file(file_path: Path) -> None:
    """
    Validate PDF file exists and has correct extension.

    Args:
        file_path: Path to PDF file.

    Raises:
        ValidationError: If file validation fails (not found, not a file,
            or wrong extension).
    """
    if not file_path.exists():
        raise ValidationError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValidationError(f"Not a file: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValidationError(f"Not a PDF file: {file_path}")


def load_pdf_document(file_path: Path) -> fitz.Document:
    """
    Load PDF file with PyMuPDF.

    Args:
        file_path: Path to PDF file.

    Returns:
        PyMuPDF Document object.

    Raises:
        FileReadError: If PDF cannot be opened (corrupted, encrypted,
            or invalid format).
    """
    try:
        doc = fitz.open(file_path)
        return doc
    except Exception as e:
        raise FileReadError(f"Failed to open PDF: {e}")


def validate_and_load_pdf(file_path: Path) -> fitz.Document:
    """
    Validate and load PDF file in a single operation.

    Convenience function combining validation and loading. Ensures the file
    exists, has correct extension, and can be opened successfully.

    Args:
        file_path: Path to PDF file.

    Returns:
        PyMuPDF Document object.

    Raises:
        ValidationError: If file validation fails.
        FileReadError: If PDF cannot be opened.

    Example:
        >>> from pathlib import Path
        >>> doc = validate_and_load_pdf(Path("document.pdf"))
        >>> print(f"Pages: {len(doc)}")
        >>> doc.close()
    """
    validate_pdf_file(file_path)
    return load_pdf_document(file_path)
