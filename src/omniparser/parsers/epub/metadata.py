"""EPUB metadata extraction functionality.

This module provides functions for extracting metadata from EPUB files using
the Dublin Core metadata standard. It handles OPF (Open Packaging Format) parsing,
date parsing, ISBN extraction, and metadata building.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ebooklib import epub

from ...models import Metadata
from ...processors.metadata_builder import MetadataBuilder

logger = logging.getLogger(__name__)


def get_first_metadata(book: epub.EpubBook, namespace: str, name: str) -> Optional[str]:
    """Get first metadata value from EPUB book.

    Safely extracts the first value for a given metadata field from the EPUB's
    OPF package document. Handles missing values and parsing errors gracefully.

    Args:
        book: EpubBook object to extract metadata from.
        namespace: Metadata namespace (e.g., "DC" for Dublin Core).
        name: Metadata field name (e.g., "title", "creator").

    Returns:
        First metadata value as string, or None if not found or error occurs.

    Example:
        >>> title = get_first_metadata(book, "DC", "title")
        >>> print(title)  # "The Great Gatsby"
    """
    try:
        metadata_list = book.get_metadata(namespace, name)
        if metadata_list and len(metadata_list) > 0:
            # Metadata returns list of tuples: [(value, attributes_dict)]
            return metadata_list[0][0]
    except Exception as e:
        logger.debug(f"Failed to get metadata {namespace}:{name}: {e}")
    return None


def get_all_metadata(book: epub.EpubBook, namespace: str, name: str) -> List[str]:
    """Get all metadata values from EPUB book.

    Extracts all values for a given metadata field from the EPUB's OPF package
    document. Filters out empty values and handles errors gracefully.

    Args:
        book: EpubBook object to extract metadata from.
        namespace: Metadata namespace (e.g., "DC" for Dublin Core).
        name: Metadata field name (e.g., "creator", "subject").

    Returns:
        List of metadata values as strings, or empty list if none found or error occurs.

    Example:
        >>> authors = get_all_metadata(book, "DC", "creator")
        >>> print(authors)  # ["Author One", "Author Two"]
    """
    try:
        metadata_list = book.get_metadata(namespace, name)
        if metadata_list:
            return [item[0] for item in metadata_list if item[0]]
    except Exception as e:
        logger.debug(f"Failed to get metadata list {namespace}:{name}: {e}")
    return []


def parse_publication_date(date_str: str, warnings: List[str]) -> Optional[datetime]:
    """Parse publication date from various common formats.

    Attempts to parse the date string using multiple common date formats.
    Logs warnings if parsing fails but continues gracefully.

    Args:
        date_str: Date string to parse (e.g., "2023-01-15", "2023").
        warnings: List to accumulate warning messages.

    Returns:
        Parsed datetime object, or None if all formats fail.

    Example:
        >>> warnings = []
        >>> dt = parse_publication_date("2023-01-15", warnings)
        >>> print(dt.year)  # 2023
    """
    # Try common date formats
    date_formats = [
        "%Y-%m-%d",  # 2023-01-15
        "%Y-%m-%dT%H:%M:%S",  # 2023-01-15T10:30:00
        "%Y-%m-%dT%H:%M:%SZ",  # 2023-01-15T10:30:00Z
        "%Y-%m-%dT%H:%M:%S%z",  # 2024-07-09T05:00:00+00:00
        "%Y",  # 2023
        "%Y-%m",  # 2023-01
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # All formats failed
    logger.warning(f"Could not parse publication date: {date_str}")
    warnings.append(f"Could not parse publication date: {date_str}")
    return None


def extract_isbn(identifiers: List[str]) -> Optional[str]:
    """Extract ISBN from list of identifiers.

    Searches through a list of identifier strings and extracts the ISBN,
    removing common prefixes like "ISBN:", "urn:isbn:", etc.

    Args:
        identifiers: List of identifier strings from EPUB metadata.

    Returns:
        ISBN number as string, or None if no ISBN found.

    Example:
        >>> ids = ["urn:isbn:9781234567890", "uuid:12345"]
        >>> isbn = extract_isbn(ids)
        >>> print(isbn)  # "9781234567890"
    """
    for identifier in identifiers:
        # Look for ISBN in identifier string
        if identifier and "isbn" in identifier.lower():
            # Extract just the ISBN number (remove prefixes if present)
            isbn = (
                identifier.replace("urn:isbn:", "")
                .replace("ISBN:", "")
                .replace("isbn:", "")
                .strip()
            )
            return isbn
    return None


def extract_epub_metadata(
    book: epub.EpubBook, file_path: Path, warnings: List[str]
) -> Metadata:
    """Extract metadata from EPUB OPF file.

    Main metadata extraction function that orchestrates extraction of all
    metadata fields from the EPUB's Open Packaging Format (OPF) file.
    Uses Dublin Core metadata standard fields.

    Extracted fields:
    - Title (DC.title)
    - Authors (DC.creator)
    - Publisher (DC.publisher)
    - Publication date (DC.date, parsed to datetime)
    - Language (DC.language)
    - ISBN (DC.identifier, filtered for ISBN)
    - Description (DC.description)
    - Subject tags (DC.subject)
    - File size (from file path)

    Args:
        book: EpubBook object loaded from file.
        file_path: Path to EPUB file (used to calculate file size).
        warnings: List to accumulate warning messages during extraction.

    Returns:
        Metadata object with all extracted fields populated.

    Example:
        >>> from pathlib import Path
        >>> from ebooklib import epub
        >>> book = epub.read_epub("book.epub")
        >>> warnings = []
        >>> metadata = extract_epub_metadata(book, Path("book.epub"), warnings)
        >>> print(metadata.title)
        >>> print(metadata.author)
    """
    # Extract title
    title = get_first_metadata(book, "DC", "title")

    # Extract authors (all contributors)
    authors = get_all_metadata(book, "DC", "creator")
    # Primary author is first in list
    author = authors[0] if authors else None

    # Extract publisher
    publisher = get_first_metadata(book, "DC", "publisher")

    # Extract and parse publication date
    publication_date: Optional[datetime] = None
    date_str = get_first_metadata(book, "DC", "date")
    if date_str:
        publication_date = parse_publication_date(date_str, warnings)

    # Extract language
    language = get_first_metadata(book, "DC", "language")

    # Extract ISBN from identifiers
    isbn: Optional[str] = None
    identifiers = get_all_metadata(book, "DC", "identifier")
    if identifiers:
        isbn = extract_isbn(identifiers)

    # Extract description
    description = get_first_metadata(book, "DC", "description")

    # Extract tags/subjects
    tags = get_all_metadata(book, "DC", "subject")

    # Calculate file size
    file_size = file_path.stat().st_size

    # Build and return metadata using MetadataBuilder
    return MetadataBuilder.build(
        title=title,
        author=author,
        authors=authors,
        publisher=publisher,
        publication_date=publication_date,
        language=language,
        isbn=isbn,
        description=description,
        tags=tags,
        original_format="epub",
        file_size=file_size,
        custom_fields={},
    )
