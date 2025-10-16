"""
Exception classes for the Omniparser package.

This module defines the complete exception hierarchy for Omniparser,
providing specific exception types for different error scenarios.

Example:
    >>> from omniparser.exceptions import UnsupportedFormatError
    >>> try:
    ...     parse_document("file.xyz")
    ... except UnsupportedFormatError as e:
    ...     print(f"Format not supported: {e}")
"""

from typing import Optional


class OmniparserError(Exception):
    """
    Base exception for all Omniparser errors.

    This is the parent class for all exceptions raised by the Omniparser
    package. Catching this exception will handle all Omniparser-specific
    errors.

    Example:
        >>> try:
        ...     parse_document(path)
        ... except OmniparserError as e:
        ...     print(f"Omniparser error: {e}")
    """

    pass


class UnsupportedFormatError(OmniparserError):
    """
    Raised when a file format is not supported by Omniparser.

    This exception is raised when attempting to parse a file with an
    extension or format that Omniparser does not support.

    Example:
        >>> try:
        ...     parse_document("document.xyz")
        ... except UnsupportedFormatError as e:
        ...     print(f"Format not supported: {e}")
    """

    pass


class ParsingError(OmniparserError):
    """
    Raised when document parsing fails.

    This exception is raised when a parser encounters an error during
    the parsing process. It captures details about which parser failed
    and the original error that caused the failure.

    Attributes:
        message: Description of the parsing error.
        parser: Name of the parser that failed (optional).
        original_error: The underlying exception that caused the failure (optional).

    Example:
        >>> try:
        ...     parse_document(path)
        ... except ParsingError as e:
        ...     print(f"Parser: {e.parser}, Error: {e}")
        ...     if e.original_error:
        ...         print(f"Original error: {e.original_error}")
    """

    def __init__(
        self,
        message: str,
        parser: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """
        Initialize a ParsingError.

        Args:
            message: Description of the parsing error.
            parser: Name of the parser that failed. Defaults to None.
            original_error: The underlying exception that caused the failure.
                Defaults to None.
        """
        super().__init__(message)
        self.parser = parser
        self.original_error = original_error


class FileReadError(OmniparserError):
    """
    Raised when a file cannot be read.

    This exception is raised when file I/O operations fail, such as
    when a file is not found, is not readable, or encounters permission
    errors.

    Example:
        >>> try:
        ...     parse_document(path)
        ... except FileReadError as e:
        ...     print(f"Could not read file: {e}")
    """

    pass


class NetworkError(OmniparserError):
    """
    Raised when a URL fetch fails.

    This exception is raised when attempting to fetch content from a URL
    and the network request fails (connection errors, timeouts, HTTP errors, etc.).

    Example:
        >>> try:
        ...     parse_document_from_url("https://example.com/document.pdf")
        ... except NetworkError as e:
        ...     print(f"Network error: {e}")
    """

    pass


class ValidationError(OmniparserError):
    """
    Raised when input validation fails.

    This exception is raised when provided input does not meet the required
    validation criteria, such as invalid file paths, missing required
    parameters, or malformed input.

    Example:
        >>> try:
        ...     parse_document(invalid_input)
        ... except ValidationError as e:
        ...     print(f"Validation error: {e}")
    """

    pass
