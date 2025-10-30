"""Table of Contents (TOC) structures for EPUB parsing.

This module provides the TocEntry class used during EPUB table of contents
parsing to represent the hierarchical structure before converting to the
OmniParser Chapter model.
"""

from typing import List, Optional


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
