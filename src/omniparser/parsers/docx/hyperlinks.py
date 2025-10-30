"""
Hyperlink extraction and formatting for DOCX documents.

This module provides utilities for extracting hyperlinks from DOCX documents
and formatting them as markdown. Hyperlinks in DOCX are stored in the document's
relationship structure and linked to runs via relationship IDs.

Functions:
    extract_hyperlinks_from_paragraph: Extract all hyperlinks from a paragraph
    format_hyperlink_markdown: Format hyperlink as markdown [text](url)
    apply_hyperlinks_to_paragraph: Convert paragraph text with markdown hyperlinks
    get_hyperlink_url: Get URL from relationship ID
    is_run_hyperlink: Check if run is part of a hyperlink
"""

from typing import Any, List, Tuple, Optional
from docx.oxml.ns import qn


def get_hyperlink_url(docx: Any, relationship_id: str) -> Optional[str]:
    """Get URL from document relationship ID.

    Args:
        docx: python-docx Document object
        relationship_id: Relationship ID (e.g., 'rId5')

    Returns:
        URL string if found, None otherwise

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> url = get_hyperlink_url(doc, 'rId5')
        >>> print(url)
        'https://example.com'
    """
    try:
        rel = docx.part.rels[relationship_id]
        return rel.target_ref
    except (KeyError, AttributeError):
        return None


def is_run_hyperlink(run: Any) -> Optional[str]:
    """Check if run is part of a hyperlink and return relationship ID.

    Hyperlinks can be identified in two ways:
    1. Run has hlinkClick property (most common)
    2. Run's parent is a hyperlink element

    Args:
        run: python-docx Run object

    Returns:
        Relationship ID if run is a hyperlink, None otherwise

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> for run in para.runs:
        ...     rId = is_run_hyperlink(run)
        ...     if rId:
        ...         print(f"Found hyperlink: {rId}")
    """
    if not hasattr(run, "_element"):
        return None

    # Check for hlinkClick in run properties (inline hyperlink)
    rPr = run._element.rPr
    if rPr is not None:
        hlinkClick = rPr.find(qn("w:hlinkClick"))
        if hlinkClick is not None:
            rId = hlinkClick.get(qn("r:id"))
            if rId:
                return rId

    # Check if parent is hyperlink element (hyperlink wrapper)
    parent = run._element.getparent()
    if parent is not None and parent.tag == qn("w:hyperlink"):
        rId = parent.get(qn("r:id"))
        if rId:
            return rId

    return None


def extract_hyperlinks_from_paragraph(
    paragraph: Any, docx: Any
) -> List[Tuple[str, str]]:
    """Extract all hyperlinks from paragraph.

    Processes all runs in the paragraph and extracts hyperlink text and URLs.
    Handles both inline hyperlinks and hyperlink wrapper elements.

    Args:
        paragraph: python-docx Paragraph object
        docx: python-docx Document object (for relationship lookup)

    Returns:
        List of (text, url) tuples. Empty list if no hyperlinks found.

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> links = extract_hyperlinks_from_paragraph(para, doc)
        >>> for text, url in links:
        ...     print(f"{text} -> {url}")
    """
    hyperlinks = []

    for run in paragraph.runs:
        rId = is_run_hyperlink(run)
        if rId:
            url = get_hyperlink_url(docx, rId)
            if url:
                text = run.text if run.text else url
                hyperlinks.append((text, url))

    return hyperlinks


def format_hyperlink_markdown(text: str, url: str) -> str:
    """Format hyperlink as markdown [text](url).

    Escapes special characters in both text and URL to ensure valid markdown.
    Handles edge cases like empty text, mailto: links, and special characters.

    Args:
        text: Link text to display
        url: Link URL

    Returns:
        Markdown formatted hyperlink string

    Example:
        >>> md = format_hyperlink_markdown("Example Site", "https://example.com")
        >>> print(md)
        [Example Site](https://example.com)

        >>> md = format_hyperlink_markdown("Email", "mailto:test@example.com")
        >>> print(md)
        [Email](mailto:test@example.com)
    """
    # Escape special characters in text
    text_escaped = text.replace("[", "\\[").replace("]", "\\]")

    # Escape special characters in URL (parentheses)
    url_escaped = url.replace("(", "\\(").replace(")", "\\)")

    return f"[{text_escaped}]({url_escaped})"


def apply_hyperlinks_to_paragraph(paragraph: Any, docx: Any) -> str:
    """Extract paragraph text with hyperlinks formatted as markdown.

    Processes all runs in the paragraph and converts hyperlinks to markdown
    format while preserving other text. Handles both hyperlinked and regular
    text runs.

    Args:
        paragraph: python-docx Paragraph object
        docx: python-docx Document object

    Returns:
        Paragraph text with hyperlinks as markdown, other text preserved

    Example:
        >>> from docx import Document
        >>> doc = Document("report.docx")
        >>> para = doc.paragraphs[0]
        >>> markdown = apply_hyperlinks_to_paragraph(para, doc)
        >>> print(markdown)
        Visit [our website](https://example.com) for more info.
    """
    result = ""
    processed_runs = set()

    for run in paragraph.runs:
        if id(run) in processed_runs:
            continue

        rId = is_run_hyperlink(run)
        if rId:
            url = get_hyperlink_url(docx, rId)
            if url:
                text = run.text if run.text else url
                result += format_hyperlink_markdown(text, url)
                processed_runs.add(id(run))
                continue

        # Not a hyperlink, add text as-is
        result += run.text if run.text else ""
        processed_runs.add(id(run))

    return result.strip()
