"""
Shared metadata building utilities for all parsers.

This module provides the MetadataBuilder helper class that standardizes
metadata creation across all parsers, reducing code duplication.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import Metadata


class MetadataBuilder:
    """
    Helper for building Metadata objects with consistent API.

    This class centralizes metadata creation logic used across all parsers,
    ensuring consistent parameter handling and reducing code duplication.

    Values are passed through as-is without forced defaults - the Metadata
    model itself defines default values for each field.

    Example:
        >>> from omniparser.processors.metadata_builder import MetadataBuilder
        >>> metadata = MetadataBuilder.build(
        ...     title="My Document",
        ...     author="John Doe",
        ...     original_format="pdf",
        ...     file_size=1024000
        ... )
        >>> print(metadata.title)  # "My Document"
        >>> print(metadata.author)  # "John Doe"
    """

    @staticmethod
    def build(
        title: Optional[str] = None,
        author: Optional[str] = None,
        authors: Optional[List[str]] = None,
        publisher: Optional[str] = None,
        publication_date: Optional[datetime] = None,
        language: Optional[str] = None,
        isbn: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        original_format: Optional[str] = None,
        file_size: int = 0,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Metadata:
        """
        Build Metadata object with standardized API.

        This method provides a centralized way to create Metadata objects with
        consistent parameter ordering across all parsers. Values are passed
        through directly to the Metadata model without modification.

        Args:
            title: Document title
            author: Primary author name
            authors: List of all authors/contributors
            publisher: Publishing organization or imprint
            publication_date: Date document was published
            language: Primary language code (e.g., "en", "fr")
            isbn: International Standard Book Number
            description: Summary or abstract of document content
            tags: List of keywords or categorization tags
            original_format: Original file format before parsing (e.g., "epub", "pdf")
            file_size: Size of original file in bytes (default: 0)
            custom_fields: Format-specific metadata not covered by standard fields

        Returns:
            Metadata object.

        Example:
            >>> metadata = MetadataBuilder.build(
            ...     title="Example Book",
            ...     author="Jane Smith",
            ...     language="en",
            ...     original_format="epub",
            ...     file_size=1024000
            ... )
            >>> print(metadata.title)  # "Example Book"
            >>> print(metadata.language)  # "en"
        """
        return Metadata(
            title=title,
            author=author,
            authors=authors,
            publisher=publisher,
            publication_date=publication_date,
            language=language,
            isbn=isbn,
            description=description,
            tags=tags,
            original_format=original_format,
            file_size=file_size,
            custom_fields=custom_fields,
        )
