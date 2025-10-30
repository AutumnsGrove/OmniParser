"""Table of Contents (TOC) structures and parsing for EPUB files.

This module provides:
- TocEntry class: Internal representation of TOC entries
- extract_toc(): Main function to extract TOC structure from EPUB
- parse_toc_item(): Recursive helper for parsing TOC items

Handles various TOC structures from ebooklib:
- Individual epub.Link objects
- Tuples of (Section, [children])
- Lists of Links or nested tuples
- Nested hierarchies with level tracking
"""

import logging
from typing import Any, List, Optional

from ebooklib import epub

logger = logging.getLogger(__name__)


class TocEntry:
    """Internal representation of a table of contents entry.

    This is used during TOC parsing to build the chapter structure before
    converting to OmniParser's Chapter model.

    Attributes:
        title: Chapter title from TOC.
        href: EPUB internal reference (e.g., "chapter1.xhtml#section").
        level: Heading level (1=main chapter, 2=subsection, etc.).
        children: List of nested TocEntry objects.
    """

    def __init__(
        self,
        title: str,
        href: str,
        level: int = 1,
        children: Optional[List["TocEntry"]] = None,
    ):
        """Initialize TocEntry.

        Args:
            title: Chapter title from TOC.
            href: EPUB internal reference (e.g., "chapter1.xhtml#section").
            level: Heading level (1=main chapter, 2=subsection, etc.). Defaults to 1.
            children: List of nested TocEntry objects. Defaults to empty list.
        """
        self.title = title
        self.href = href
        self.level = level
        self.children = children or []


def extract_toc(book: epub.EpubBook, warnings: List[str]) -> Optional[List[TocEntry]]:
    """Extract table of contents from EPUB.

    Parses the EPUB's table of contents structure and converts it to a flat
    list of TocEntry objects. Handles nested TOC structures by preserving
    hierarchy information via the level attribute.

    Args:
        book: EpubBook object from ebooklib.
        warnings: List to accumulate warning messages during processing.

    Returns:
        Flat list of TocEntry objects with level indicating hierarchy
        (1=main chapter, 2=subsection, etc.), or None if TOC is missing/empty.

    Note:
        The returned list is flattened - all TocEntry objects have empty
        children lists, but the level attribute indicates nesting depth.
        Handles various TOC structures from ebooklib including Links, Sections,
        tuples, and nested lists.
    """
    try:
        toc = book.toc

        # Check if TOC is empty or None
        if not toc:
            logger.info("EPUB has no table of contents")
            return None

        # Parse TOC structure recursively
        flat_toc: List[TocEntry] = []
        parse_toc_item(toc, flat_toc, level=1, warnings=warnings)

        # Return None if parsing produced no entries
        if not flat_toc:
            logger.info("EPUB TOC parsing produced no entries")
            return None

        logger.info(f"Extracted {len(flat_toc)} TOC entries")
        return flat_toc

    except Exception as e:
        logger.warning(f"Failed to extract TOC: {e}")
        warnings.append(f"TOC extraction failed: {e}")
        return None


def parse_toc_item(
    items: Any,
    flat_toc: List[TocEntry],
    level: int = 1,
    warnings: Optional[List[str]] = None,
) -> None:
    """Recursively parse TOC items into flat list.

    Handles various TOC structures from ebooklib:
    - Individual epub.Link objects
    - Tuples of (Section, [children])
    - Lists of Links or nested tuples

    This recursive function flattens the hierarchical TOC structure while
    preserving level information for chapters at different nesting depths.

    Args:
        items: TOC item(s) to parse (Link, tuple, or list).
        flat_toc: Accumulator list for flattened TocEntry objects.
        level: Current hierarchy level (1=top-level, 2=subsection, etc.).
        warnings: List to accumulate warning messages during processing.
    """
    if warnings is None:
        warnings = []

    # Handle list of items
    if isinstance(items, list):
        for item in items:
            parse_toc_item(item, flat_toc, level, warnings)
        return

    # Handle tuple (Section, children)
    if isinstance(items, tuple):
        if len(items) >= 2:
            section, children = items[0], items[1]

            # Process section (could be Link or Section)
            if hasattr(section, "title") and hasattr(section, "href"):
                # It's a Link
                try:
                    title = section.title or "Untitled"
                    href = section.href or ""
                    flat_toc.append(TocEntry(title=title, href=href, level=level))
                except Exception as e:
                    logger.warning(f"Failed to parse TOC Link: {e}")
                    warnings.append(f"Malformed TOC Link: {e}")
            elif hasattr(section, "title"):
                # It's a Section (has title but maybe no href)
                try:
                    title = section.title or "Untitled"
                    # Sections might not have href - use empty string
                    href = getattr(section, "href", "")
                    flat_toc.append(TocEntry(title=title, href=href, level=level))
                except Exception as e:
                    logger.warning(f"Failed to parse TOC Section: {e}")
                    warnings.append(f"Malformed TOC Section: {e}")

            # Recursively process children at deeper level
            if children:
                parse_toc_item(children, flat_toc, level + 1, warnings)
        return

    # Handle individual epub.Link
    if hasattr(items, "title") and hasattr(items, "href"):
        try:
            title = items.title or "Untitled"
            href = items.href or ""
            flat_toc.append(TocEntry(title=title, href=href, level=level))
        except Exception as e:
            logger.warning(f"Failed to parse TOC item: {e}")
            warnings.append(f"Malformed TOC item: {e}")
        return

    # Unknown structure - log warning
    logger.warning(f"Unknown TOC item structure: {type(items)}")
    warnings.append(f"Unknown TOC item type: {type(items).__name__}")
