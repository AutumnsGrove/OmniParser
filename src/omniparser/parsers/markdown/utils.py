"""
Markdown parser utility functions.

This module provides shared utility functions for Markdown parsing, including:
- Word counting for text analysis (markdown-aware)
- Reading time estimation

These utilities are used across the Markdown parser and its components.
"""

import math
import re


def count_words(text: str) -> int:
    """
    Count words in text, excluding markdown syntax.

    Removes markdown formatting before counting to provide accurate word count
    of actual content. Handles:
    - Code blocks (fenced with ```)
    - Inline code (backticks)
    - URLs (http://, https://)
    - Image syntax (![alt](url))
    - Link syntax ([text](url))
    - Heading markers (# ## ###)
    - Emphasis markers (** __ * _)

    Args:
        text: Text to count words in (may contain markdown).

    Returns:
        Word count (excluding markdown syntax).

    Example:
        >>> count_words("# Heading\\n\\nHello **world**")
        3
        >>> count_words("![image](url.png) Check this [link](url)")
        3
        >>> count_words("```python\\ncode\\n```\\n\\nSome text")
        2
    """
    # Pre-compiled patterns for performance (matching markdown_parser patterns)
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
    INLINE_CODE_PATTERN = re.compile(r"`[^`]+`")
    URL_PATTERN = re.compile(r"https?://\S+")
    IMAGE_SYNTAX_PATTERN = re.compile(r"!\[([^\]]*)\]\([^\)]+\)")
    LINK_SYNTAX_PATTERN = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
    HEADING_PATTERN = re.compile(r"^#{1,6}\s+", re.MULTILINE)
    EMPHASIS_DOUBLE_PATTERN = re.compile(r"(\*\*|__)(.*?)\1")
    EMPHASIS_SINGLE_PATTERN = re.compile(r"(\*|_)(.*?)\1")

    # Remove code blocks
    text = CODE_BLOCK_PATTERN.sub("", text)
    # Remove inline code
    text = INLINE_CODE_PATTERN.sub("", text)
    # Remove URLs
    text = URL_PATTERN.sub("", text)
    # Remove markdown image syntax (keep alt text)
    text = IMAGE_SYNTAX_PATTERN.sub(r"\1", text)
    # Remove markdown link syntax (keep link text)
    text = LINK_SYNTAX_PATTERN.sub(r"\1", text)
    # Remove markdown heading markers
    text = HEADING_PATTERN.sub("", text)
    # Remove emphasis markers (** __ for bold, * _ for italic)
    text = EMPHASIS_DOUBLE_PATTERN.sub(r"\2", text)
    text = EMPHASIS_SINGLE_PATTERN.sub(r"\2", text)

    # Count remaining words (filter out empty strings)
    words = [word for word in text.split() if word.strip()]
    return len(words)


def estimate_reading_time(word_count: int, words_per_minute: int = 200) -> int:
    """
    Estimate reading time in minutes.

    Uses 200 words per minute as default reading speed (average adult reading
    speed for English text). Always rounds up to ensure minimum 1 minute.

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
    """
    if word_count <= 0:
        return 1

    # Calculate reading time and round up to nearest minute
    reading_time = word_count / words_per_minute
    return max(1, math.ceil(reading_time))
