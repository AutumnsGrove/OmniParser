"""
HTML to Markdown converter for OmniParser.

This module provides utilities to convert HTML content to clean Markdown format,
preserving document structure while removing unnecessary markup.
"""

from typing import Any, Optional, Union
from bs4 import BeautifulSoup, NavigableString, Tag, PageElement


def html_to_markdown(
    html: str, preserve_links: bool = True, preserve_images: bool = True
) -> str:
    """
    Convert HTML to clean Markdown format.

    Features:
    - Convert heading tags (h1-h6) to markdown headings (# - ######)
    - Convert <p> to paragraphs with proper spacing
    - Convert <strong>/<b> to **bold**
    - Convert <em>/<i> to *italic*
    - Convert <a href=""> to [text](url) if preserve_links=True
    - Convert <img src="" alt=""> to ![alt](src) if preserve_images=True
    - Convert <ul>/<ol> to markdown lists
    - Convert <code>/<pre> to code blocks
    - Convert <blockquote> to > quotes
    - Convert <table> to markdown tables
    - Strip script, style, nav, footer, aside tags completely
    - Preserve newlines and paragraph structure
    - Clean extra whitespace

    Args:
        html: HTML string to convert
        preserve_links: Whether to preserve hyperlinks
        preserve_images: Whether to preserve image references

    Returns:
        Clean markdown string

    Example:
        >>> html = '<h1>Title</h1><p>Hello <strong>world</strong>!</p>'
        >>> print(html_to_markdown(html))
        # Title

        Hello **world**!
    """
    if not html or not html.strip():
        return ""

    soup = BeautifulSoup(html, "html.parser")
    _remove_unwanted_tags(soup)
    markdown = _process_element(soup, preserve_links, preserve_images)
    return _clean_whitespace(markdown)


def _remove_unwanted_tags(soup: BeautifulSoup) -> None:
    """Remove script, style, nav, footer, aside, and header tags."""
    unwanted_tags = ["script", "style", "nav", "footer", "aside", "header"]
    for tag_name in unwanted_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()


def _process_element(
    element: Union[BeautifulSoup, Tag, NavigableString, PageElement],
    preserve_links: bool,
    preserve_images: bool,
) -> str:
    """
    Process HTML element and convert to markdown.

    Args:
        element: BeautifulSoup element to process
        preserve_links: Whether to preserve hyperlinks
        preserve_images: Whether to preserve image references

    Returns:
        Markdown string representation
    """
    if isinstance(element, NavigableString):
        return str(element)

    if not isinstance(element, Tag):
        return ""

    tag_name = element.name.lower()

    # Headings
    if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        level = int(tag_name[1])
        return (
            f"\n{'#' * level} {_get_text(element, preserve_links, preserve_images)}\n"
        )

    # Paragraph
    if tag_name == "p":
        return f"\n{_get_text(element, preserve_links, preserve_images)}\n"

    # Bold
    if tag_name in ["strong", "b"]:
        return f"**{_get_text(element, preserve_links, preserve_images)}**"

    # Italic
    if tag_name in ["em", "i"]:
        return f"*{_get_text(element, preserve_links, preserve_images)}*"

    # Links
    if tag_name == "a":
        return _convert_link(element, preserve_links, preserve_images)

    # Images
    if tag_name == "img":
        return _convert_image(element, preserve_images)

    # Lists
    if tag_name in ["ul", "ol"]:
        return _convert_list(element, tag_name, preserve_links, preserve_images)

    # List items (shouldn't appear standalone, but handle anyway)
    if tag_name == "li":
        return f"- {_get_text(element, preserve_links, preserve_images)}\n"

    # Code blocks
    if tag_name == "pre":
        code_content = element.get_text()
        return f"\n```\n{code_content}\n```\n"

    # Inline code
    if tag_name == "code":
        return f"`{element.get_text()}`"

    # Blockquote
    if tag_name == "blockquote":
        return _convert_blockquote(element, preserve_links, preserve_images)

    # Table
    if tag_name == "table":
        return _convert_table(element, preserve_links, preserve_images)

    # Line break
    if tag_name == "br":
        return "\n"

    # Horizontal rule
    if tag_name == "hr":
        return "\n---\n"

    # Default: process children
    return _get_text(element, preserve_links, preserve_images)


def _get_text(
    element: Union[Tag, BeautifulSoup], preserve_links: bool, preserve_images: bool
) -> str:
    """Extract text from element, processing child elements."""
    result = []
    for child in element.children:
        result.append(_process_element(child, preserve_links, preserve_images))
    return "".join(result)


def _convert_link(element: Tag, preserve_links: bool, preserve_images: bool) -> str:
    """Convert <a> tag to markdown link."""
    if not preserve_links:
        return _get_text(element, preserve_links, preserve_images)

    href = element.get("href", "")
    text = _get_text(element, preserve_links, preserve_images)
    return f"[{text}]({href})" if href else text


def _convert_image(element: Tag, preserve_images: bool) -> str:
    """Convert <img> tag to markdown image."""
    if not preserve_images:
        return ""

    src = element.get("src", "")
    alt = element.get("alt", "")
    return f"\n![{alt}]({src})\n" if src else ""


def _convert_list(
    element: Tag, list_type: str, preserve_links: bool, preserve_images: bool
) -> str:
    """Convert <ul> or <ol> to markdown list."""
    items = element.find_all("li", recursive=False)
    result = ["\n"]

    for idx, item in enumerate(items, start=1):
        prefix = f"{idx}." if list_type == "ol" else "-"
        content = _get_text(item, preserve_links, preserve_images).strip()
        result.append(f"{prefix} {content}\n")

    result.append("\n")
    return "".join(result)


def _convert_blockquote(
    element: Tag, preserve_links: bool, preserve_images: bool
) -> str:
    """Convert <blockquote> to markdown quote."""
    text = _get_text(element, preserve_links, preserve_images).strip()
    lines = text.split("\n")
    quoted_lines = [f"> {line}" for line in lines if line.strip()]
    return "\n" + "\n".join(quoted_lines) + "\n"


def _convert_table(element: Tag, preserve_links: bool, preserve_images: bool) -> str:
    """Convert <table> to markdown table."""
    rows = element.find_all("tr")
    if not rows:
        return ""

    result = ["\n"]

    # Process header row
    header_row = rows[0]
    headers = [
        _get_text(cell, preserve_links, preserve_images).strip()
        for cell in header_row.find_all(["th", "td"])
    ]

    if headers:
        result.append("| " + " | ".join(headers) + " |\n")
        result.append("| " + " | ".join(["---"] * len(headers)) + " |\n")

    # Process data rows
    for row in rows[1:]:
        cells = [
            _get_text(cell, preserve_links, preserve_images).strip()
            for cell in row.find_all(["td", "th"])
        ]
        if cells:
            result.append("| " + " | ".join(cells) + " |\n")

    result.append("\n")
    return "".join(result)


def _clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from markdown text.

    - Remove trailing whitespace from lines
    - Limit consecutive newlines to maximum 2
    - Strip leading/trailing whitespace from final result

    Args:
        text: Markdown text to clean

    Returns:
        Cleaned markdown text
    """
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Join and limit consecutive newlines
    cleaned = "\n".join(lines)

    # Replace 3+ newlines with exactly 2 newlines
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")

    return cleaned.strip()


# Basic tests
if __name__ == "__main__":
    print("Testing markdown_converter.py")
    print("=" * 60)

    # Test 1: Headings
    html = "<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>"
    result = html_to_markdown(html)
    print("Test 1 - Headings:")
    print(result)
    assert "# Title" in result
    assert "## Subtitle" in result
    assert "### Section" in result
    print("✓ Passed\n")

    # Test 2: Bold and Italic
    html = "<p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
    result = html_to_markdown(html)
    print("Test 2 - Bold/Italic:")
    print(result)
    assert "**bold**" in result
    assert "*italic*" in result
    print("✓ Passed\n")

    # Test 3: Links
    html = '<p>Visit <a href="https://example.com">this site</a>.</p>'
    result = html_to_markdown(html)
    print("Test 3 - Links:")
    print(result)
    assert "[this site](https://example.com)" in result
    print("✓ Passed\n")

    # Test 4: Lists
    html = "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
    result = html_to_markdown(html)
    print("Test 4 - Unordered List:")
    print(result)
    assert "- Item 1" in result
    assert "- Item 2" in result
    print("✓ Passed\n")

    # Test 5: Ordered List
    html = "<ol><li>First</li><li>Second</li><li>Third</li></ol>"
    result = html_to_markdown(html)
    print("Test 5 - Ordered List:")
    print(result)
    assert "1. First" in result
    assert "2. Second" in result
    assert "3. Third" in result
    print("✓ Passed\n")

    # Test 6: Code blocks
    html = "<pre>def hello():\n    print('world')</pre>"
    result = html_to_markdown(html)
    print("Test 6 - Code Block:")
    print(result)
    assert "```" in result
    assert "def hello()" in result
    print("✓ Passed\n")

    # Test 7: Inline code
    html = "<p>Use the <code>print()</code> function.</p>"
    result = html_to_markdown(html)
    print("Test 7 - Inline Code:")
    print(result)
    assert "`print()`" in result
    print("✓ Passed\n")

    # Test 8: Script removal
    html = "<p>Content</p><script>alert('bad')</script><p>More</p>"
    result = html_to_markdown(html)
    print("Test 8 - Script Removal:")
    print(result)
    assert "alert" not in result
    assert "Content" in result
    assert "More" in result
    print("✓ Passed\n")

    # Test 9: Images
    html = '<img src="image.png" alt="Description">'
    result = html_to_markdown(html)
    print("Test 9 - Images:")
    print(result)
    assert "![Description](image.png)" in result
    print("✓ Passed\n")

    # Test 10: Blockquote
    html = "<blockquote>This is a quote</blockquote>"
    result = html_to_markdown(html)
    print("Test 10 - Blockquote:")
    print(result)
    assert "> This is a quote" in result
    print("✓ Passed\n")

    # Test 11: Table
    html = """
    <table>
        <tr><th>Name</th><th>Age</th></tr>
        <tr><td>Alice</td><td>30</td></tr>
        <tr><td>Bob</td><td>25</td></tr>
    </table>
    """
    result = html_to_markdown(html)
    print("Test 11 - Table:")
    print(result)
    assert "| Name | Age |" in result
    assert "| --- | --- |" in result
    assert "| Alice | 30 |" in result
    print("✓ Passed\n")

    # Test 12: Empty HTML
    html = ""
    result = html_to_markdown(html)
    print("Test 12 - Empty HTML:")
    print(f"Result: '{result}'")
    assert result == ""
    print("✓ Passed\n")

    # Test 13: Complex nested structure
    html = """
    <div>
        <h1>Main Title</h1>
        <p>Introduction with <strong>bold</strong> and <em>italic</em>.</p>
        <ul>
            <li>First item</li>
            <li>Second item with <a href="/link">a link</a></li>
        </ul>
    </div>
    """
    result = html_to_markdown(html)
    print("Test 13 - Complex Nested:")
    print(result)
    assert "# Main Title" in result
    assert "**bold**" in result
    assert "*italic*" in result
    assert "- First item" in result
    assert "[a link](/link)" in result
    print("✓ Passed\n")

    print("=" * 60)
    print("All tests passed! ✓")
