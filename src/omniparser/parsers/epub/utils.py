"""Utility functions for EPUB parsing.

This module provides helper functions for text processing during EPUB parsing,
including word counting and reading time estimation.
"""


def count_words(text: str) -> int:
    """Count words in text.

    Splits text by whitespace to count word tokens. This is a simple
    implementation that works well for most languages.

    Args:
        text: Text to count words in.

    Returns:
        Number of words in the text.

    Example:
        >>> count_words("Hello world")
        2
        >>> count_words("")
        0
    """
    return len(text.split())


def estimate_reading_time(word_count: int) -> int:
    """Estimate reading time in minutes.

    Assumes average reading speed of 225 words per minute (WPM).
    This is a middle ground between typical silent reading speeds
    of 200-250 WPM.

    Args:
        word_count: Total word count.

    Returns:
        Estimated reading time in minutes (minimum 1 minute).

    Example:
        >>> estimate_reading_time(225)
        1
        >>> estimate_reading_time(450)
        2
    """
    return max(1, round(word_count / 225))
