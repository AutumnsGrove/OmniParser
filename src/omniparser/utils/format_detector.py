"""File format detection using magic bytes and extensions."""

import magic
from pathlib import Path
from ..exceptions import UnsupportedFormatError


def detect_format(file_path: Path) -> str:
    """
    Detect file format using magic bytes with extension fallback.

    Uses python-magic to inspect file headers (magic bytes) for accurate
    format detection. Falls back to file extension checking if magic bytes
    detection fails or returns an unknown MIME type.

    Args:
        file_path: Path to file to detect.

    Returns:
        Format identifier: "epub", "pdf", "docx", "html", "markdown", or "text".

    Raises:
        UnsupportedFormatError: If format is not supported.

    Example:
        >>> from pathlib import Path
        >>> detect_format(Path("book.epub"))
        'epub'
        >>> detect_format(Path("document.pdf"))
        'pdf'
        >>> detect_format(Path("notes.md"))
        'markdown'
    """
    # Try magic bytes detection
    try:
        mime = magic.from_file(str(file_path), mime=True)

        format_map = {
            "application/epub+zip": "epub",
            "application/pdf": "pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "text/html": "html",
            "text/plain": "text",
            "text/markdown": "markdown",
        }

        if mime in format_map:
            return format_map[mime]
    except Exception:
        # Fall through to extension detection
        pass

    # Fallback to extension detection
    ext = file_path.suffix.lower()
    if ext in [".md", ".markdown"]:
        return "markdown"
    elif ext == ".txt":
        return "text"
    elif ext == ".html":
        return "html"
    elif ext == ".epub":
        return "epub"
    elif ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"

    raise UnsupportedFormatError(f"Unsupported file format: {file_path.suffix}")
