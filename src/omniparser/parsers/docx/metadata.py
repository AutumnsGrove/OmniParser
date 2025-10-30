"""
DOCX metadata extraction module.

This module provides functions for extracting metadata from DOCX documents
using python-docx's core properties API. It extracts standard document properties
such as title, author, keywords, and timestamps.

Functions:
    extract_metadata: Main function to extract all metadata from DOCX document
    extract_core_properties: Extract core properties as dictionary
"""

# Standard library
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local
from ...models import Metadata
from ...processors.metadata_builder import MetadataBuilder


def extract_metadata(docx: Any, file_path: Path) -> Metadata:
    """Extract metadata from DOCX core properties.

    Available properties from python-docx:
    - title, author, subject, keywords, comments
    - created, modified, last_modified_by

    Args:
        docx: python-docx Document object
        file_path: Path to source DOCX file

    Returns:
        Metadata object with extracted fields

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> metadata = extract_metadata(doc, Path("report.docx"))
        >>> print(metadata.title)
    """
    core_props = extract_core_properties(docx)
    file_size = file_path.stat().st_size

    return MetadataBuilder.build(
        title=core_props.get("title"),
        author=core_props.get("author"),
        authors=[core_props["author"]] if core_props.get("author") else None,
        publisher=None,  # DOCX doesn't have publisher field
        publication_date=core_props.get("publication_date"),
        language=None,  # DOCX doesn't expose language in core properties
        isbn=None,
        description=core_props.get("description"),
        tags=core_props.get("tags"),
        original_format="docx",
        file_size=file_size,
        custom_fields={
            "last_modified_by": core_props.get("last_modified_by"),
            "modified": core_props.get("modified"),
        },
    )


def extract_core_properties(docx: Any) -> Dict[str, Any]:
    """Extract core properties from DOCX document.

    Extracts standard document properties and converts them to a
    normalized dictionary format.

    Args:
        docx: python-docx Document object

    Returns:
        Dictionary with keys: title, author, tags, description,
        publication_date, last_modified_by, modified

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> props = extract_core_properties(doc)
        >>> print(props['title'])
    """
    props = docx.core_properties

    # Extract title
    title = props.title or None

    # Extract author
    author = props.author or None

    # Extract keywords as tags (semicolon or comma separated)
    tags: Optional[List[str]] = None
    if props.keywords:
        tags = [tag.strip() for tag in re.split(r"[;,]", props.keywords) if tag.strip()]

    # Extract description (subject or comments)
    description = props.subject or props.comments or None

    # Extract publication date (created or modified)
    publication_date: Optional[datetime] = None
    if props.created:
        publication_date = props.created
    elif props.modified:
        publication_date = props.modified

    # Convert modified datetime to ISO format string
    modified = props.modified.isoformat() if props.modified else None

    return {
        "title": title,
        "author": author,
        "tags": tags,
        "description": description,
        "publication_date": publication_date,
        "last_modified_by": props.last_modified_by,
        "modified": modified,
    }
