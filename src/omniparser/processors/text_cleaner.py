"""
Text cleaning processor for OmniParser.

Provides text cleaning functionality for parsed documents, including pattern
removal, text normalization, and encoding fixes. Adapted from epub2tts with
TTS-specific features removed.

This module offers a simple functional interface for cleaning text extracted
from various document formats, removing common artifacts like footnotes and
page numbers, normalizing punctuation, and fixing encoding issues.

Example:
    >>> from omniparser.processors.text_cleaner import clean_text
    >>> text = "Hello   world!  [1]  This is a test…"
    >>> clean_text(text)
    'Hello world! This is a test...'
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import ftfy
import yaml

logger = logging.getLogger(__name__)

# Module-level pattern cache
_compiled_patterns: Optional[Dict[str, Any]] = None


def load_patterns() -> Dict[str, Any]:
    """
    Load cleaning patterns from YAML config file.

    Patterns are loaded once and cached at module level for efficiency.
    The configuration file defines regex patterns for text removal and
    transformation operations.

    Returns:
        Dictionary with 'removal_patterns' and 'transformation_patterns' keys.
        Each pattern entry contains:
        - pattern: Compiled regex pattern
        - description: Human-readable description
        - replacement: (transformation patterns only) Replacement string

    Raises:
        No exceptions raised - returns empty patterns on error.

    Example:
        >>> patterns = load_patterns()
        >>> len(patterns['removal_patterns']) > 0
        True
    """
    global _compiled_patterns

    if _compiled_patterns is not None:
        return _compiled_patterns

    # Load patterns from config file
    config_path = Path(__file__).parent.parent / "config" / "cleaning_patterns.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            patterns = yaml.safe_load(f)

        # Compile regex patterns
        compiled: Dict[str, List[Dict[str, Any]]] = {
            "removal_patterns": [],
            "transformation_patterns": [],
        }

        # Compile removal patterns
        for pattern_dict in patterns.get("removal_patterns", []):
            flags = 0
            if "flags" in pattern_dict:
                flag_names = pattern_dict["flags"]
                if isinstance(flag_names, str):
                    for flag_name in flag_names.split("|"):
                        flag_name = flag_name.strip()
                        if hasattr(re, flag_name):
                            flags |= getattr(re, flag_name)

            compiled["removal_patterns"].append(
                {
                    "pattern": re.compile(pattern_dict["pattern"], flags),
                    "description": pattern_dict.get("description", ""),
                }
            )

        # Compile transformation patterns
        for pattern_dict in patterns.get("transformation_patterns", []):
            compiled["transformation_patterns"].append(
                {
                    "pattern": re.compile(pattern_dict["pattern"]),
                    "replacement": pattern_dict["replacement"],
                    "description": pattern_dict.get("description", ""),
                }
            )

        _compiled_patterns = compiled
        logger.info(
            f"Loaded {len(compiled['removal_patterns'])} removal patterns, "
            f"{len(compiled['transformation_patterns'])} transformation patterns"
        )

        return compiled

    except Exception as e:
        logger.warning(f"Failed to load cleaning patterns: {e}. Using empty patterns.")
        _compiled_patterns = {"removal_patterns": [], "transformation_patterns": []}
        return _compiled_patterns


def clean_text(text: str, apply_patterns: bool = True) -> str:
    """
    Clean text by applying removal patterns, transformations, and normalization.

    This is the main entry point for text cleaning operations. It performs
    the following steps in order:
    1. Fix encoding issues (Mojibake, etc.)
    2. Apply removal patterns (footnotes, page numbers, etc.)
    3. Apply transformation patterns (punctuation normalization)
    4. Normalize whitespace

    Args:
        text: Raw text to clean.
        apply_patterns: Whether to apply regex patterns from config. Default True.
            Set to False to only fix encoding and normalize whitespace.

    Returns:
        Cleaned text with artifacts removed and punctuation normalized.

    Example:
        >>> text = "Hello   world!  [1]  This is a test…"
        >>> clean_text(text)
        'Hello world! This is a test...'

        >>> text = "Keep this simple"
        >>> clean_text(text, apply_patterns=False)
        'Keep this simple'
    """
    if not text:
        return text

    # Step 1: Fix encoding issues
    text = _fix_encoding(text)

    # Step 2: Apply removal patterns
    if apply_patterns:
        text = _apply_removal_patterns(text)

    # Step 3: Apply transformation patterns
    if apply_patterns:
        text = _apply_transformation_patterns(text)

    # Step 4: Normalize whitespace
    text = _normalize_whitespace(text)

    return text


def _fix_encoding(text: str) -> str:
    """
    Fix encoding issues using ftfy (fixes text for you).

    This handles common encoding issues like:
    - Mojibake (incorrectly decoded text)
    - Mixed encodings
    - HTML entities
    - Unicode normalization

    Args:
        text: Text that may have encoding issues.

    Returns:
        Text with encoding issues fixed.

    Example:
        >>> _fix_encoding("caf\\u00e9")
        'café'
    """
    try:
        return ftfy.fix_text(text)
    except Exception as e:
        logger.warning(f"ftfy encoding fix failed: {e}")
        return text


def _apply_removal_patterns(text: str) -> str:
    """
    Apply removal patterns to text.

    Removes common artifacts like:
    - Footnote markers ([1], [2], etc.)
    - Page numbers
    - Chapter number lines
    - HTML tags
    - Section breaks (asterisks, underscores)

    Args:
        text: Text to process.

    Returns:
        Text with patterns removed.

    Example:
        >>> _apply_removal_patterns("Hello [1] world")
        'Hello  world'
    """
    patterns = load_patterns()

    for pattern_dict in patterns["removal_patterns"]:
        pattern = pattern_dict["pattern"]
        text = pattern.sub("", text)

    return text


def _apply_transformation_patterns(text: str) -> str:
    """
    Apply transformation patterns to text.

    Normalizes punctuation and special characters:
    - Em dash (—) to double hyphen (--)
    - En dash (–) to hyphen (-)
    - Ellipsis (…) to three periods (...)
    - Smart quotes to regular quotes
    - Non-breaking spaces to regular spaces
    - Multiple spaces to single space

    Args:
        text: Text to process.

    Returns:
        Text with patterns transformed.

    Example:
        >>> _apply_transformation_patterns("Hello—world")
        'Hello -- world'
    """
    patterns = load_patterns()

    for pattern_dict in patterns["transformation_patterns"]:
        pattern = pattern_dict["pattern"]
        replacement = pattern_dict["replacement"]
        text = pattern.sub(replacement, text)

    return text


def _normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    Performs the following operations:
    - Strips leading/trailing whitespace from each line
    - Collapses multiple spaces to single space
    - Collapses 3+ newlines to 2 newlines (preserves paragraph breaks)
    - Strips leading/trailing whitespace from entire text

    Args:
        text: Text to normalize.

    Returns:
        Text with normalized whitespace.

    Example:
        >>> _normalize_whitespace("Hello   world\\n\\n\\n\\nNext paragraph")
        'Hello world\\n\\nNext paragraph'
    """
    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse multiple spaces to single space
    text = re.sub(r" +", " ", text)

    # Collapse 3+ newlines to 2 newlines (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    return text.strip()


def reset_pattern_cache() -> None:
    """
    Reset the compiled pattern cache.

    This is primarily useful for testing to force reloading patterns
    or to clear memory if needed.

    Example:
        >>> reset_pattern_cache()
        >>> _compiled_patterns is None
        True
    """
    global _compiled_patterns
    _compiled_patterns = None
