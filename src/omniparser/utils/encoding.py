"""Encoding detection and normalization utilities."""

import chardet
from pathlib import Path


def detect_encoding(file_path: Path) -> str:
    """
    Detect file encoding using chardet.

    Reads the file in binary mode and uses the chardet library to detect
    the character encoding. Returns 'utf-8' as a fallback if detection fails.

    Args:
        file_path: Path to file.

    Returns:
        Detected encoding (e.g., "utf-8", "latin-1", "iso-8859-1").

    Example:
        >>> from pathlib import Path
        >>> detect_encoding(Path("file.txt"))
        'utf-8'
        >>> detect_encoding(Path("legacy_doc.txt"))
        'iso-8859-1'
    """
    with open(file_path, "rb") as f:
        raw = f.read()
        result = chardet.detect(raw)
        return result["encoding"] or "utf-8"


def normalize_to_utf8(text: str) -> str:
    """
    Normalize text to UTF-8.

    Converts text to UTF-8 encoding, ignoring any characters that cannot
    be encoded. This ensures compatibility with systems expecting UTF-8.

    Args:
        text: Input text.

    Returns:
        UTF-8 normalized text.

    Example:
        >>> normalize_to_utf8("Hello World")
        'Hello World'
        >>> normalize_to_utf8("Café résumé")
        'Café résumé'
    """
    return text.encode("utf-8", errors="ignore").decode("utf-8")


def normalize_line_endings(text: str) -> str:
    """
    Normalize line endings to \\n.

    Converts Windows (\\r\\n) and old Mac (\\r) line endings to Unix-style
    line endings (\\n) for consistency across platforms.

    Args:
        text: Input text.

    Returns:
        Text with normalized line endings.

    Example:
        >>> normalize_line_endings("line1\\r\\nline2\\r\\nline3")
        'line1\\nline2\\nline3'
        >>> normalize_line_endings("line1\\rline2\\rline3")
        'line1\\nline2\\nline3'
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")
