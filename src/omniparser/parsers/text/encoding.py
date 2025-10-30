"""
Text file encoding detection and reading utilities.

This module provides functions for detecting and reading text files with
proper encoding handling. It uses chardet for encoding detection and provides
robust fallback mechanisms for reading files with unknown or problematic encodings.

Functions:
    read_text_with_encoding: Read text file with automatic encoding detection
"""

# Standard library
import logging
from pathlib import Path
from typing import List

# Third-party
import chardet

# Local
from ...exceptions import FileReadError

logger = logging.getLogger(__name__)


def read_text_with_encoding(file_path: Path, warnings: List[str]) -> str:
    """
    Read text file with automatic encoding detection and fallback mechanisms.

    Uses a three-stage approach to maximize success:
    1. Try UTF-8 first (most common for modern text files)
    2. If UTF-8 fails, use chardet to detect encoding
    3. If detection fails or detected encoding fails, fall back to latin-1

    The latin-1 fallback ensures we can always read the file, since latin-1
    can decode any byte sequence (though may produce incorrect characters).

    Args:
        file_path: Path to text file to read.
        warnings: List to append warnings to (for encoding issues).

    Returns:
        File content as string.

    Raises:
        FileReadError: If file cannot be read with any encoding method.

    Example:
        >>> from pathlib import Path
        >>> warnings = []
        >>> content = read_text_with_encoding(Path("notes.txt"), warnings)
        >>> print(f"Read {len(content)} characters")
        >>> if warnings:
        ...     print("Encoding warnings:", warnings)
    """
    # Stage 1: Try UTF-8 first (most common encoding)
    try:
        logger.debug(f"Attempting UTF-8 encoding for {file_path.name}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"Successfully read file with UTF-8 encoding")
        return content
    except UnicodeDecodeError:
        logger.debug("UTF-8 decode failed, attempting encoding detection")
        warnings.append("UTF-8 decode failed, detecting encoding")

    # Stage 2: Detect encoding using chardet
    try:
        logger.debug("Detecting file encoding with chardet")
        with open(file_path, "rb") as f:
            raw_data = f.read()
            detection_result = chardet.detect(raw_data)
            detected_encoding = detection_result.get("encoding")
            confidence = detection_result.get("confidence", 0)

        if detected_encoding:
            logger.info(
                f"Detected encoding: {detected_encoding} "
                f"(confidence: {confidence:.2f})"
            )

            # Try reading with detected encoding
            try:
                with open(file_path, "r", encoding=detected_encoding) as f:
                    content = f.read()
                logger.info(
                    f"Successfully read file with detected encoding: {detected_encoding}"
                )
                warnings.append(
                    f"Used detected encoding: {detected_encoding} "
                    f"(confidence: {confidence:.2f})"
                )
                return content
            except (UnicodeDecodeError, LookupError) as e:
                logger.warning(
                    f"Failed to read with detected encoding "
                    f"{detected_encoding}: {e}"
                )
                warnings.append(
                    f"Detected encoding {detected_encoding} failed, "
                    f"falling back to latin-1"
                )
        else:
            logger.warning("Encoding detection returned no result")
            warnings.append("Encoding detection failed, falling back to latin-1")

    except Exception as e:
        logger.warning(f"Encoding detection error: {e}")
        warnings.append(f"Encoding detection error: {e}, falling back to latin-1")

    # Stage 3: Fall back to latin-1 (can decode any byte sequence)
    try:
        logger.info("Attempting latin-1 encoding as fallback")
        with open(file_path, "r", encoding="latin-1", errors="replace") as f:
            content = f.read()
        logger.warning("File read with latin-1 fallback - characters may be incorrect")
        warnings.append(
            "Used latin-1 fallback encoding - some characters may be incorrect"
        )
        return content
    except Exception as e:
        logger.error(f"Failed to read file with any encoding: {e}")
        raise FileReadError(
            f"Failed to read file {file_path} with any encoding method: {e}"
        )
