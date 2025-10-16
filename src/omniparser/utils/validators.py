"""Input validation utilities."""

from pathlib import Path
from ..exceptions import FileReadError, ValidationError


def validate_file_exists(file_path: Path) -> None:
    """
    Validate that file exists.

    Checks if the provided path exists and is a file (not a directory).
    Raises an exception if validation fails.

    Args:
        file_path: Path to check.

    Raises:
        FileReadError: If file doesn't exist or path is not a file.

    Example:
        >>> from pathlib import Path
        >>> validate_file_exists(Path("existing_file.txt"))  # No exception
        >>> validate_file_exists(Path("missing.txt"))  # Raises FileReadError
        Traceback (most recent call last):
            ...
        FileReadError: File not found: missing.txt
    """
    if not file_path.exists():
        raise FileReadError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise FileReadError(f"Path is not a file: {file_path}")


def validate_file_size(file_path: Path, max_size_mb: int = 500) -> None:
    """
    Validate file size is within limits.

    Checks if the file size is below the specified maximum. This prevents
    processing extremely large files that might cause memory issues.

    Args:
        file_path: Path to check.
        max_size_mb: Maximum size in megabytes. Defaults to 500MB.

    Raises:
        ValidationError: If file is too large.

    Example:
        >>> from pathlib import Path
        >>> validate_file_size(Path("small.txt"), max_size_mb=10)  # No exception
        >>> validate_file_size(Path("huge.pdf"), max_size_mb=1)  # Raises ValidationError
        Traceback (most recent call last):
            ...
        ValidationError: File too large: 5.2MB (max: 1MB)
    """
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValidationError(f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)")


def validate_format_supported(format_type: str) -> None:
    """
    Validate that format is supported.

    Checks if the provided format type is one of the supported formats.
    This is used to ensure only valid format identifiers are processed.

    Args:
        format_type: Format identifier.

    Raises:
        ValidationError: If format not supported.

    Example:
        >>> validate_format_supported("epub")  # No exception
        >>> validate_format_supported("pdf")  # No exception
        >>> validate_format_supported("xyz")  # Raises ValidationError
        Traceback (most recent call last):
            ...
        ValidationError: Unsupported format: xyz. Supported formats: epub, pdf, ...
    """
    supported_formats = ["epub", "pdf", "docx", "html", "markdown", "text"]
    if format_type not in supported_formats:
        raise ValidationError(
            f"Unsupported format: {format_type}. "
            f"Supported formats: {', '.join(supported_formats)}"
        )
