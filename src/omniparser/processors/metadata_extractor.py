"""
HTML metadata extraction with priority-based fallback.

This module extracts metadata from HTML documents using multiple sources
with a priority-based fallback system: OpenGraph > Dublin Core > Standard > Title.

Functions:
    extract_html_metadata: Main entry point for metadata extraction.
    _extract_opengraph: Extract OpenGraph (og:*) metadata.
    _extract_dublin_core: Extract Dublin Core (DC.*) metadata.
    _extract_standard_meta: Extract standard meta tags.
    _merge_metadata: Merge metadata with priority resolution.
    _parse_date: Parse ISO date strings safely.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from ..models import Metadata


def _get_tag_content(tag: Any, attr: str = "content") -> str:
    """
    Safely extract content from a BeautifulSoup tag.

    Args:
        tag: BeautifulSoup tag object.
        attr: Attribute name to extract.

    Returns:
        Stripped string content or empty string.
    """
    value = tag.get(attr)
    return str(value).strip() if value else ""


def extract_html_metadata(html: str, url: Optional[str] = None) -> Metadata:
    """
    Extract metadata from HTML document with priority-based fallback.

    Extraction priority (highest to lowest):
    1. OpenGraph tags (og:title, og:description, og:image, og:article:author)
    2. Dublin Core meta tags (DC.title, DC.creator, DC.description, DC.date)
    3. Standard meta tags (name="description", name="author", name="keywords")
    4. HTML title element (<title>)
    5. Fallback values (None or empty)

    Features:
    - Title: og:title > DC.title > title tag > None
    - Author: og:article:author > DC.creator > meta author > None
    - Description: og:description > DC.description > meta description > None
    - Language: html lang attribute > meta language
    - Tags: og:article:tag > meta keywords (comma-separated)
    - Publication date: og:article:published_time > DC.date
    - URL stored in custom_fields if provided
    - Original format set to "html"

    Args:
        html: HTML string to extract metadata from.
        url: Optional URL where HTML was fetched from.

    Returns:
        Metadata object with extracted fields.

    Example:
        >>> html = '''
        ... <html lang="en">
        ... <head>
        ...     <meta property="og:title" content="Article Title" />
        ...     <meta property="og:description" content="Article description" />
        ...     <meta property="og:article:author" content="John Doe" />
        ...     <meta name="keywords" content="python, parsing, metadata" />
        ...     <title>Fallback Title</title>
        ... </head>
        ... </html>
        ... '''
        >>> metadata = extract_html_metadata(html, "https://example.com")
        >>> metadata.title
        'Article Title'
        >>> metadata.author
        'John Doe'
        >>> "python" in metadata.tags
        True
    """
    soup = BeautifulSoup(html, "html.parser")

    og = _extract_opengraph(soup)
    dc = _extract_dublin_core(soup)
    standard = _extract_standard_meta(soup)

    merged = _merge_metadata(og, dc, standard, soup)

    custom_fields = merged.get("custom_fields", {})
    if url:
        custom_fields["url"] = url

    return Metadata(
        title=merged.get("title"),
        author=merged.get("author"),
        authors=merged.get("authors"),
        publisher=merged.get("publisher"),
        publication_date=merged.get("publication_date"),
        language=merged.get("language"),
        description=merged.get("description"),
        tags=merged.get("tags"),
        original_format="html",
        custom_fields=custom_fields if custom_fields else None,
    )


def _extract_opengraph(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract OpenGraph metadata from HTML.

    Extracts metadata from meta tags with property attributes starting with "og:".
    Handles multiple og:article:tag entries by collecting them into a list.

    Args:
        soup: BeautifulSoup object of HTML document.

    Returns:
        Dictionary with extracted OpenGraph metadata.
    """
    og_data: Dict[str, Any] = {}
    og_tags = soup.find_all("meta", property=True)

    for tag in og_tags:
        prop = _get_tag_content(tag, "property")
        if not prop.startswith("og:"):
            continue

        content = _get_tag_content(tag, "content")
        if not content:
            continue

        if prop == "og:title":
            og_data["title"] = content
        elif prop == "og:description":
            og_data["description"] = content
        elif prop == "og:article:author":
            og_data["author"] = content
        elif prop == "og:article:published_time":
            og_data["publication_date"] = _parse_date(content)
        elif prop == "og:article:tag":
            og_data.setdefault("tags", []).append(content)
        elif prop == "og:image":
            og_data.setdefault("custom_fields", {})["og_image"] = content

    return og_data


def _extract_dublin_core(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract Dublin Core metadata from HTML.

    Extracts metadata from meta tags with name attributes starting with "DC.".
    Dublin Core provides standardized metadata fields for digital resources.

    Args:
        soup: BeautifulSoup object of HTML document.

    Returns:
        Dictionary with extracted Dublin Core metadata.
    """
    dc_data: Dict[str, Any] = {}
    all_meta_tags = soup.find_all("meta", attrs={"name": True})

    for tag in all_meta_tags:
        name = _get_tag_content(tag, "name")
        if not name.startswith("DC."):
            continue

        content = _get_tag_content(tag, "content")
        if not content:
            continue

        if name == "DC.title":
            dc_data["title"] = content
        elif name == "DC.creator":
            dc_data["author"] = content
        elif name == "DC.description":
            dc_data["description"] = content
        elif name == "DC.date":
            dc_data["publication_date"] = _parse_date(content)
        elif name == "DC.subject":
            dc_data["tags"] = [t.strip() for t in content.split(",") if t.strip()]
        elif name == "DC.publisher":
            dc_data["publisher"] = content

    return dc_data


def _extract_standard_meta(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract standard HTML meta tags.

    Extracts metadata from common meta tags (description, author, keywords)
    and the html lang attribute.

    Args:
        soup: BeautifulSoup object of HTML document.

    Returns:
        Dictionary with extracted standard metadata.
    """
    standard_data: Dict[str, Any] = {}

    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        desc = _get_tag_content(desc_tag, "content")
        if desc:
            standard_data["description"] = desc

    author_tag = soup.find("meta", attrs={"name": "author"})
    if author_tag:
        author = _get_tag_content(author_tag, "content")
        if author:
            standard_data["author"] = author

    keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    if keywords_tag:
        keywords = _get_tag_content(keywords_tag, "content")
        if keywords:
            standard_data["tags"] = [
                k.strip() for k in keywords.split(",") if k.strip()
            ]

    html_tag = soup.find("html")
    if html_tag:
        lang = _get_tag_content(html_tag, "lang")
        if lang:
            standard_data["language"] = lang

    return standard_data


def _merge_metadata(
    og: Dict[str, Any],
    dc: Dict[str, Any],
    standard: Dict[str, Any],
    soup: BeautifulSoup,
) -> Dict[str, Any]:
    """
    Merge metadata with priority: og > dc > standard > title tag.

    Combines metadata from multiple sources, preferring higher-priority sources
    when the same field is available in multiple places.

    Args:
        og: OpenGraph metadata dictionary.
        dc: Dublin Core metadata dictionary.
        standard: Standard meta tag dictionary.
        soup: BeautifulSoup object for title tag fallback.

    Returns:
        Merged metadata dictionary with priority resolution.
    """
    merged: Dict[str, Any] = {}

    merged["title"] = og.get("title") or dc.get("title")
    if not merged["title"]:
        title_tag = soup.find("title")
        merged["title"] = title_tag.get_text(strip=True) if title_tag else None

    merged["author"] = og.get("author") or dc.get("author") or standard.get("author")

    merged["description"] = (
        og.get("description") or dc.get("description") or standard.get("description")
    )

    merged["publication_date"] = og.get("publication_date") or dc.get(
        "publication_date"
    )

    merged["publisher"] = dc.get("publisher")

    merged["language"] = standard.get("language")

    og_tags = og.get("tags", [])
    dc_tags = dc.get("tags", [])
    standard_tags = standard.get("tags", [])
    all_tags = og_tags or dc_tags or standard_tags
    merged["tags"] = all_tags if all_tags else None

    if "custom_fields" in og:
        merged["custom_fields"] = og["custom_fields"]

    return merged


def _parse_date(date_string: str) -> Optional[datetime]:
    """
    Parse ISO date string to datetime object.

    Handles ISO 8601 date formats commonly used in metadata.
    Returns None if parsing fails.

    Args:
        date_string: ISO format date string.

    Returns:
        Datetime object if parsing succeeds, None otherwise.
    """
    try:
        return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
