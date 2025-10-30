"""
DOCX parser utility functions.

This module provides shared utility functions for DOCX parsing, including:
- Filename sanitization for safe filesystem usage
- Word counting for text analysis (markdown-aware)
- Reading time estimation

These utilities are used across the DOCX parser and its components.
"""

import re
import unicodedata


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem use.

    Removes or replaces characters that are invalid in filenames across
    different operating systems (Windows, macOS, Linux).

    Args:
        filename: Original filename to sanitize.

    Returns:
        Sanitized filename safe for filesystem use.

    Example:
        >>> sanitize_filename("file:name?.txt")
        'filename.txt'
        >>> sanitize_filename("my/file\\name.docx")
        'myfilename.docx'
    """
    # Normalize unicode characters
    filename = unicodedata.normalize("NFKD", filename)

    # Remove path separators and invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)

    # Replace spaces with underscores
    filename = filename.replace(" ", "_")

    # Remove control characters
    filename = "".join(char for char in filename if ord(char) >= 32)

    # Ensure not empty
    return filename if filename else "unnamed"


def count_words(text: str) -> int:
    """
    Count words in text, excluding markdown syntax.

    Strips markdown formatting characters before counting to provide
    accurate word count of actual content. Handles:
    - Markdown headings (# ## ###)
    - Bold/italic formatting (** * ***)
    - Table pipes and separators
    - Escaped characters

    Args:
        text: Text to count words in (may contain markdown).

    Returns:
        Word count (excluding markdown syntax).

    Example:
        >>> count_words("# Heading\\n\\nHello **world**")
        3
        >>> count_words("| Col1 | Col2 |\\n|---|---|")
        2
    """
    # Remove markdown headings
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove markdown bold/italic/bold-italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)  # ***text***
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **text**
    text = re.sub(r"\*(.+?)\*", r"\1", text)  # *text*

    # Remove markdown table pipes and separators
    text = re.sub(r"\|", " ", text)  # Remove table pipes
    text = re.sub(r"^[\s\-]+$", "", text, flags=re.MULTILINE)  # Remove separator rows

    # Remove escaped characters
    text = re.sub(r"\\(.)", r"\1", text)  # \| -> |

    return len(text.split())


def estimate_reading_time(word_count: int, wpm: int = 225) -> int:
    """
    Estimate reading time in minutes.

    Assumes average reading speed of 200-250 words per minute.
    Uses 225 WPM as middle ground between slow (200) and fast (250) readers.

    Args:
        word_count: Total word count.
        wpm: Words per minute reading speed (default: 225).

    Returns:
        Estimated reading time in minutes (minimum 1).

    Example:
        >>> estimate_reading_time(500)
        2
        >>> estimate_reading_time(100)
        1
        >>> estimate_reading_time(1000, wpm=200)
        5
    """
    return max(1, round(word_count / wpm))
