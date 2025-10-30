"""
Text parser utility functions.

This module provides shared utility functions for text parsing, including:
- Word counting for text analysis
- Reading time estimation

These utilities are used across the Text parser and its components.
"""

# Standard library
import math


def count_words(text: str) -> int:
    """
    Count words in text using simple whitespace splitting.

    This is a straightforward word counting implementation that splits
    on whitespace and counts non-empty tokens. Unlike the Markdown
    parser's count_words, this doesn't need to filter syntax since
    plain text has no special formatting.

    Args:
        text: Text to count words in.

    Returns:
        Word count (number of whitespace-separated tokens).

    Example:
        >>> count_words("Hello world")
        2
        >>> count_words("  Multiple   spaces   here  ")
        3
        >>> count_words("")
        0
        >>> count_words("One-hyphenated-word is counted as one")
        5
    """
    # Split on whitespace and filter empty strings
    words = [word for word in text.split() if word.strip()]
    return len(words)


def estimate_reading_time(word_count: int, words_per_minute: int = 200) -> int:
    """
    Estimate reading time in minutes.

    Uses 200 words per minute as default reading speed (average adult reading
    speed for English text). Always rounds up to ensure minimum 1 minute.

    This is consistent with the Markdown parser's reading time estimation
    and provides realistic reading time estimates for plain text documents.

    Args:
        word_count: Total word count.
        words_per_minute: Reading speed in WPM (default: 200).

    Returns:
        Estimated reading time in minutes (minimum 1, rounded up).

    Example:
        >>> estimate_reading_time(500)
        3
        >>> estimate_reading_time(100)
        1
        >>> estimate_reading_time(1000, words_per_minute=250)
        4
        >>> estimate_reading_time(0)
        1
        >>> estimate_reading_time(199)
        1
        >>> estimate_reading_time(201)
        2
    """
    if word_count <= 0:
        return 1

    # Calculate reading time and round up to nearest minute
    reading_time = word_count / words_per_minute
    return max(1, math.ceil(reading_time))
