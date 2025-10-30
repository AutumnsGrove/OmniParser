"""
PDF parser utility functions.

This module provides shared utility functions for PDF parsing, including:
- Timeout enforcement for long-running operations
- Word counting for text analysis
- Reading time estimation

These utilities are used across the PDF parser and its components.
"""

import logging
import signal
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger(__name__)

# Constants for PDF processing
SCANNED_PDF_THRESHOLD = 100  # Character count below which to trigger OCR
OCR_DPI = 300  # DPI for OCR processing
HEADING_SEARCH_WINDOW = 100  # Character window for heading text search
READING_SPEED_WPM = 250  # Words per minute for reading time estimation
DEFAULT_OCR_TIMEOUT = 300  # Default OCR timeout in seconds (5 minutes)
DEFAULT_MAX_HEADING_WORDS = 25  # Default maximum words in heading
MIN_TABLE_ROWS = 2  # Minimum table rows for extraction
MIN_IMAGE_SIZE = 100  # Minimum image dimension in pixels


@contextmanager
def timeout_context(seconds: int) -> Iterator[None]:
    """
    Context manager for enforcing timeouts using signals.

    Args:
        seconds: Maximum execution time in seconds.

    Yields:
        None

    Raises:
        TimeoutError: If execution exceeds timeout.

    Note:
        Only works on Unix-like systems. On Windows, timeout is not enforced.

    Example:
        >>> with timeout_context(5):
        ...     long_running_operation()
    """

    def timeout_handler(signum: int, frame) -> None:
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Signal-based timeout only works on Unix-like systems
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # On Windows, no timeout enforcement (log warning)
        logger.warning(
            "Timeout not enforced on this platform (signal.SIGALRM not available)"
        )
        yield


def count_words(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Text to count words in.

    Returns:
        Word count.

    Example:
        >>> count_words("Hello world")
        2
        >>> count_words("   ")
        0
    """
    words = [word for word in text.split() if word.strip()]
    return len(words)


def estimate_reading_time(
    word_count: int, words_per_minute: int = READING_SPEED_WPM
) -> int:
    """
    Estimate reading time in minutes.

    Args:
        word_count: Number of words.
        words_per_minute: Reading speed (default: 250 wpm).

    Returns:
        Estimated reading time in minutes (minimum 1).

    Example:
        >>> estimate_reading_time(500)
        2
        >>> estimate_reading_time(100)
        1
        >>> estimate_reading_time(1000, words_per_minute=200)
        5
    """
    return max(1, word_count // words_per_minute)
