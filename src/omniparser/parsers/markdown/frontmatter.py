"""
Frontmatter extraction and parsing for Markdown files.

This module provides functions for extracting and parsing frontmatter from
Markdown documents. Supports YAML, TOML, and JSON frontmatter formats.

Functions:
    extract_frontmatter: Extract frontmatter from markdown content
    parse_frontmatter_to_metadata: Convert frontmatter dict to Metadata object
"""

# Standard library
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Third-party
import yaml  # type: ignore[import-untyped]

# Local
from ...models import Metadata
from ...processors.metadata_builder import MetadataBuilder

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for frontmatter detection
_YAML_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_TOML_PATTERN = re.compile(r"^\+\+\+\s*\n(.*?)\n\+\+\+\s*(?:\n|$)", re.DOTALL)


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract frontmatter from markdown content.

    Supports three formats:
    - YAML: Delimited by --- (most common)
    - TOML: Delimited by +++
    - JSON: Starts with { and valid JSON object

    Frontmatter must be at the very beginning of the file.

    Args:
        content: Full markdown text.

    Returns:
        Tuple of (frontmatter_dict, remaining_content).
        Returns ({}, content) if no frontmatter found.

    Example:
        >>> content = "---\\ntitle: Test\\n---\\nContent here"
        >>> fm, text = extract_frontmatter(content)
        >>> print(fm['title'])
        Test
        >>> print(text)
        Content here
    """
    if not content or not content.strip():
        return {}, content

    # Try YAML format first (most common)
    yaml_match = _YAML_PATTERN.match(content)
    if yaml_match:
        return _parse_yaml_frontmatter(yaml_match, content)

    # Try TOML format
    toml_match = _TOML_PATTERN.match(content)
    if toml_match:
        return _parse_toml_frontmatter(toml_match, content)

    # Try JSON format
    if content.lstrip().startswith("{"):
        return _parse_json_frontmatter(content)

    # No frontmatter found
    return {}, content


def _parse_yaml_frontmatter(
    match: re.Match[str], content: str
) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from regex match.

    Args:
        match: Regex match object for YAML frontmatter.
        content: Original content.

    Returns:
        Tuple of (frontmatter_dict, remaining_content).
    """
    try:
        yaml_content = match.group(1)
        frontmatter = yaml.safe_load(yaml_content)

        # Get content after frontmatter
        remaining_content = content[match.end() :]

        # Validate frontmatter is a dict
        if not isinstance(frontmatter, dict):
            logger.warning("YAML frontmatter is not a dictionary, ignoring")
            return {}, content

        logger.debug(f"Parsed YAML frontmatter with {len(frontmatter)} fields")
        return frontmatter, remaining_content

    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse YAML frontmatter: {e}")
        return {}, content


def _parse_toml_frontmatter(
    match: re.Match[str], content: str
) -> Tuple[Dict[str, Any], str]:
    """
    Parse TOML frontmatter from regex match.

    Args:
        match: Regex match object for TOML frontmatter.
        content: Original content.

    Returns:
        Tuple of (frontmatter_dict, remaining_content).
    """
    try:
        # Try to import tomli/tomllib for TOML parsing
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import-untyped]
            except ImportError:
                logger.warning("TOML frontmatter found but tomli/tomllib not available")
                return {}, content

        toml_content = match.group(1)
        frontmatter = tomllib.loads(toml_content)

        # Get content after frontmatter
        remaining_content = content[match.end() :]

        logger.debug(f"Parsed TOML frontmatter with {len(frontmatter)} fields")
        return frontmatter, remaining_content

    except Exception as e:
        logger.warning(f"Failed to parse TOML frontmatter: {e}")
        return {}, content


def _parse_json_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse JSON frontmatter from beginning of content.

    JSON frontmatter is a single JSON object at the start of the file,
    followed by the markdown content.

    Args:
        content: Original content.

    Returns:
        Tuple of (frontmatter_dict, remaining_content).
    """
    try:
        # Find the end of the JSON object by counting braces
        brace_count = 0
        in_string = False
        escape_next = False
        end_pos = -1

        for i, char in enumerate(content):
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break

        if end_pos == -1:
            logger.warning("Could not find end of JSON frontmatter")
            return {}, content

        json_content = content[:end_pos]
        frontmatter = json.loads(json_content)

        # Get remaining content (skip whitespace after JSON)
        remaining_content = content[end_pos:].lstrip()

        logger.debug(f"Parsed JSON frontmatter with {len(frontmatter)} fields")
        return frontmatter, remaining_content

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON frontmatter: {e}")
        return {}, content


def parse_frontmatter_to_metadata(
    frontmatter: Dict[str, Any], file_path: Path, warnings: Optional[List[str]] = None
) -> Metadata:
    """
    Convert frontmatter dictionary to Metadata object.

    Extracts common metadata fields from frontmatter:
    - title
    - author / authors
    - date / publication_date
    - tags / keywords
    - description / summary
    - language / lang
    - publisher

    All other fields are stored in custom_fields.

    Args:
        frontmatter: Parsed frontmatter dictionary.
        file_path: Source file path.
        warnings: Optional list to append warnings to.

    Returns:
        Metadata object with extracted and normalized fields.

    Example:
        >>> fm = {'title': 'Test Doc', 'author': 'John Doe', 'tags': ['python', 'code']}
        >>> metadata = parse_frontmatter_to_metadata(fm, Path('test.md'))
        >>> print(metadata.title)
        Test Doc
        >>> print(metadata.tags)
        ['python', 'code']
    """
    # Normalize field names to lowercase for case-insensitive lookup
    normalized_fm = {k.lower(): v for k, v in frontmatter.items()}

    # Extract title
    title = normalized_fm.get("title")

    # Extract author(s)
    author = None
    authors = None

    if "authors" in normalized_fm:
        authors_value = normalized_fm["authors"]
        if isinstance(authors_value, list):
            authors = [str(a) for a in authors_value]
            author = authors[0] if authors else None
        else:
            author = str(authors_value)
            authors = [author]
    elif "author" in normalized_fm:
        author = str(normalized_fm["author"])
        authors = [author]

    # Extract publication date
    publication_date = _extract_date(normalized_fm, warnings)

    # Extract tags/keywords
    tags = _extract_tags(normalized_fm)

    # Extract description
    description = normalized_fm.get("description") or normalized_fm.get("summary")

    # Extract language
    language = normalized_fm.get("language") or normalized_fm.get("lang")

    # Extract publisher
    publisher = normalized_fm.get("publisher")

    # Get file size
    file_size = file_path.stat().st_size

    # Build custom fields (exclude standard fields)
    standard_fields = {
        "title",
        "author",
        "authors",
        "date",
        "publication_date",
        "tags",
        "keywords",
        "description",
        "summary",
        "language",
        "lang",
        "publisher",
    }

    # Use original keys (not lowercased) for custom fields
    custom_fields = {
        k: v for k, v in frontmatter.items() if k.lower() not in standard_fields
    }

    # Validate custom fields for common typos
    if custom_fields and warnings is not None:
        _validate_custom_fields(custom_fields, warnings)

    return MetadataBuilder.build(
        title=title,
        author=author,
        authors=authors,
        publisher=publisher,
        publication_date=publication_date,
        language=language,
        isbn=None,  # Markdown files don't have ISBN
        description=description,
        tags=tags,
        original_format="markdown",
        file_size=file_size,
        custom_fields=custom_fields if custom_fields else None,
    )


def _extract_date(
    normalized_fm: Dict[str, Any], warnings: Optional[List[str]]
) -> Optional[datetime]:
    """
    Extract publication date from frontmatter.

    Supports multiple field names and formats:
    - Field names: 'date', 'publication_date', 'published'
    - Formats: datetime objects, ISO strings, common date formats

    Args:
        normalized_fm: Frontmatter dict with lowercase keys.
        warnings: Optional list to append warnings to.

    Returns:
        datetime object or None if not found/parseable.
    """
    # Try different field names
    date_value = (
        normalized_fm.get("date")
        or normalized_fm.get("publication_date")
        or normalized_fm.get("published")
    )

    if not date_value:
        return None

    # If already a datetime, return it
    if isinstance(date_value, datetime):
        return date_value

    # Try to parse string
    if isinstance(date_value, str):
        date_formats = [
            "%Y-%m-%d",  # 2025-01-15
            "%Y/%m/%d",  # 2025/01/15
            "%Y-%m-%dT%H:%M:%S",  # 2025-01-15T10:30:00
            "%Y-%m-%dT%H:%M:%SZ",  # 2025-01-15T10:30:00Z
            "%Y-%m-%dT%H:%M:%S.%fZ",  # 2025-01-15T10:30:00.000Z
            "%Y",  # 2025
            "%Y-%m",  # 2025-01
            "%B %d, %Y",  # January 15, 2025
            "%b %d, %Y",  # Jan 15, 2025
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_value, fmt)
            except ValueError:
                continue

        # Could not parse date
        logger.warning(f"Could not parse date: {date_value}")
        if warnings is not None:
            warnings.append(f"Could not parse date: {date_value}")

    return None


def _extract_tags(normalized_fm: Dict[str, Any]) -> Optional[List[str]]:
    """
    Extract tags/keywords from frontmatter.

    Handles multiple formats:
    - List of strings: ['tag1', 'tag2']
    - Comma-separated string: 'tag1, tag2, tag3'
    - Semicolon-separated string: 'tag1; tag2; tag3'

    Args:
        normalized_fm: Frontmatter dict with lowercase keys.

    Returns:
        List of tags or None if not found.
    """
    # Try 'tags' field first, then 'keywords'
    tags_value = normalized_fm.get("tags") or normalized_fm.get("keywords")

    if not tags_value:
        return None

    # Handle list
    if isinstance(tags_value, list):
        return [str(t).strip() for t in tags_value if str(t).strip()]

    # Handle string (comma or semicolon separated)
    if isinstance(tags_value, str):
        # Split by comma or semicolon
        tags = [t.strip() for t in re.split(r"[,;]", tags_value) if t.strip()]
        return tags if tags else None

    return None


def _validate_custom_fields(custom_fields: Dict[str, Any], warnings: List[str]) -> None:
    """
    Validate custom fields for common typos of standard metadata fields.

    Checks for keys that might be typos and adds warnings.

    Args:
        custom_fields: Dictionary of custom frontmatter fields.
        warnings: List to append warnings to.
    """
    # Common typos for standard fields
    typo_mappings = {
        "titel": "title",
        "tittle": "title",
        "autor": "author",
        "auteur": "author",
        "auther": "author",
        "publiser": "publisher",
        "languaje": "language",
        "langue": "language",
        "descripton": "description",
        "discription": "description",
        "desciption": "description",
    }

    for field_name in custom_fields.keys():
        # Check for exact typo matches (case-insensitive)
        if field_name.lower() in typo_mappings:
            correct = typo_mappings[field_name.lower()]
            warning = (
                f"Custom field '{field_name}' might be a typo of '{correct}'. "
                f"Did you mean '{correct}' instead?"
            )
            logger.warning(warning)
            warnings.append(warning)
