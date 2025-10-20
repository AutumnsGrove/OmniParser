"""HTML text extraction utilities for EPUB processing."""

import re
from html.parser import HTMLParser
from typing import List


class HTMLTextExtractor(HTMLParser):
    """
    Extract clean text from HTML content.

    Converts HTML to plain text while preserving document structure.
    Handles common HTML elements found in EPUB files.

    This parser processes HTML tags to maintain readability while removing
    markup. Block-level elements (paragraphs, headings, divs) preserve
    document structure through newlines. Script and style tags are ignored.

    Args:
        None

    Attributes:
        _text_parts: Internal list accumulating text fragments.
        _ignore_content: Flag to skip content (for script/style tags).
        _in_list_item: Flag to track list item processing.
        _li_has_content: Flag to track if list item has actual content.

    Example:
        >>> extractor = HTMLTextExtractor()
        >>> text = extractor.extract_text("<p>Hello <b>world</b>!</p>")
        >>> print(text)
        Hello world!

        >>> html = "<h1>Title</h1><p>Paragraph 1</p><p>Paragraph 2</p>"
        >>> text = extractor.extract_text(html)
        >>> print(text)
        Title

        Paragraph 1

        Paragraph 2
    """

    def __init__(self) -> None:
        """Initialize the HTML text extractor."""
        super().__init__()
        self._text_parts: List[str] = []
        self._ignore_content = False
        self._in_list_item = False
        self._li_has_content = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """
        Handle opening HTML tags.

        Processes start tags to determine text formatting and structure.
        Sets flags for ignoring content (script/style) and handles
        special formatting for certain elements.

        Args:
            tag: HTML tag name (lowercase).
            attrs: List of (name, value) tuples for tag attributes.
        """
        # Ignore content in script and style tags
        if tag in ("script", "style"):
            self._ignore_content = True

        # Handle line breaks
        elif tag == "br":
            self._text_parts.append("\n")

        # Handle horizontal rules (self-closing, so add both before and after spacing)
        elif tag == "hr":
            self._text_parts.append("\n---\n\n")

        # Track list items for bullet points
        elif tag == "li":
            self._in_list_item = True
            self._li_has_content = False
            self._text_parts.append("• ")

    def handle_endtag(self, tag: str) -> None:
        """
        Handle closing HTML tags.

        Processes end tags to add appropriate spacing and restore state.
        Block-level elements add newlines to preserve document structure.

        Args:
            tag: HTML tag name (lowercase).
        """
        # Re-enable content processing after script/style
        if tag in ("script", "style"):
            self._ignore_content = False

        # Add double newline after block-level elements
        elif tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._text_parts.append("\n\n")

        # Add single newline after divs and list items
        elif tag in ("div", "li"):
            if tag == "li":
                self._in_list_item = False
                # If list item had no content, remove the bullet point we added
                if (
                    not self._li_has_content
                    and self._text_parts
                    and self._text_parts[-1] == "• "
                ):
                    self._text_parts.pop()
                    return  # Don't add newline for empty list items
            self._text_parts.append("\n")

        # Add newline after table rows
        elif tag == "tr":
            self._text_parts.append("\n")

        # Add space after table cells
        elif tag in ("td", "th"):
            self._text_parts.append(" ")

    def handle_data(self, data: str) -> None:
        """
        Handle text content between tags.

        Collects text data unless currently inside an ignored tag
        (script or style). Whitespace is preserved but will be
        normalized during final extraction.

        Args:
            data: Text content from HTML.
        """
        if not self._ignore_content:
            self._text_parts.append(data)
            # Track that list item has content (not just whitespace)
            if self._in_list_item and data.strip():
                self._li_has_content = True

    def extract_text(self, html: str) -> str:
        """
        Extract text from HTML string.

        Parses the HTML and returns clean plain text with normalized
        whitespace and preserved document structure.

        Args:
            html: HTML string to parse.

        Returns:
            Cleaned plain text with normalized whitespace.

        Example:
            >>> extractor = HTMLTextExtractor()
            >>> html = "<p>Hello   <em>beautiful</em>   world!</p>"
            >>> extractor.extract_text(html)
            'Hello beautiful world!'

            >>> html = "<div><h1>Title</h1><p>Content</p></div>"
            >>> extractor.extract_text(html)
            'Title\\n\\nContent'
        """
        # Reset state for fresh parsing
        self._text_parts = []
        self._ignore_content = False
        self._in_list_item = False
        self._li_has_content = False

        # Parse the HTML
        try:
            self.feed(html)
        except Exception:
            # Handle malformed HTML gracefully - return what we have so far
            pass

        # Join all text parts
        text = "".join(self._text_parts)

        # Normalize whitespace
        return self._normalize_whitespace(text)

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.

        Performs the following normalizations:
        - Strips leading/trailing whitespace from each line
        - Collapses multiple spaces to single space
        - Collapses 3+ consecutive newlines to 2 newlines
        - Strips leading/trailing whitespace from final text

        Args:
            text: Text to normalize.

        Returns:
            Text with normalized whitespace.

        Example:
            >>> extractor = HTMLTextExtractor()
            >>> extractor._normalize_whitespace("  Hello    world  ")
            'Hello world'

            >>> extractor._normalize_whitespace("Line1\\n\\n\\n\\n\\nLine2")
            'Line1\\n\\nLine2'
        """
        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Collapse multiple spaces to single space
        text = re.sub(r" +", " ", text)

        # Collapse 3+ newlines to 2 newlines (preserve paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip leading/trailing whitespace from entire text
        return text.strip()
