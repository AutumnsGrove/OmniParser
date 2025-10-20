"""
Tests for HTML text extraction utilities.

This module provides comprehensive tests for the HTMLTextExtractor class,
which converts HTML content to clean plain text while preserving document
structure.
"""

import pytest

from src.omniparser.utils.html_extractor import HTMLTextExtractor


class TestHTMLTextExtractor:
    """Tests for HTMLTextExtractor class."""

    def test_basic_text_extraction(self):
        """Test extracting plain text from simple HTML."""
        extractor = HTMLTextExtractor()
        html = "<p>Hello world!</p>"
        result = extractor.extract_text(html)
        assert result == "Hello world!"

    def test_inline_tags_preserved(self):
        """Test that inline formatting tags don't affect text."""
        extractor = HTMLTextExtractor()
        html = "<p>Hello <b>bold</b> and <em>italic</em> text!</p>"
        result = extractor.extract_text(html)
        assert result == "Hello bold and italic text!"

    def test_paragraph_structure_preserved(self):
        """Test that paragraph breaks are preserved with double newlines."""
        extractor = HTMLTextExtractor()
        html = "<p>First paragraph.</p><p>Second paragraph.</p>"
        result = extractor.extract_text(html)
        assert result == "First paragraph.\n\nSecond paragraph."

    def test_heading_handling(self):
        """Test that headings are followed by double newlines."""
        extractor = HTMLTextExtractor()
        html = "<h1>Title</h1><p>Content</p>"
        result = extractor.extract_text(html)
        assert result == "Title\n\nContent"

    def test_multiple_heading_levels(self):
        """Test all heading levels (h1-h6)."""
        extractor = HTMLTextExtractor()
        html = "<h1>H1</h1><h2>H2</h2><h3>H3</h3><h4>H4</h4><h5>H5</h5><h6>H6</h6>"
        result = extractor.extract_text(html)
        expected = "H1\n\nH2\n\nH3\n\nH4\n\nH5\n\nH6"
        assert result == expected

    def test_line_break_handling(self):
        """Test that <br> tags create single newlines."""
        extractor = HTMLTextExtractor()
        html = "<p>Line 1<br>Line 2<br>Line 3</p>"
        result = extractor.extract_text(html)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_horizontal_rule_handling(self):
        """Test that <hr> tags are converted to separator."""
        extractor = HTMLTextExtractor()
        html = "<p>Before</p><hr><p>After</p>"
        result = extractor.extract_text(html)
        assert result == "Before\n\n---\n\nAfter"

    def test_list_formatting(self):
        """Test that list items get bullet points."""
        extractor = HTMLTextExtractor()
        html = "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
        result = extractor.extract_text(html)
        assert result == "• Item 1\n• Item 2\n• Item 3"

    def test_ordered_list_formatting(self):
        """Test ordered lists (also use bullet points)."""
        extractor = HTMLTextExtractor()
        html = "<ol><li>First</li><li>Second</li></ol>"
        result = extractor.extract_text(html)
        assert result == "• First\n• Second"

    def test_script_tag_ignored(self):
        """Test that script tag content is completely ignored."""
        extractor = HTMLTextExtractor()
        html = "<p>Visible</p><script>alert('invisible');</script><p>Also visible</p>"
        result = extractor.extract_text(html)
        assert result == "Visible\n\nAlso visible"
        assert "invisible" not in result

    def test_style_tag_ignored(self):
        """Test that style tag content is completely ignored."""
        extractor = HTMLTextExtractor()
        html = "<p>Text</p><style>body { color: red; }</style><p>More text</p>"
        result = extractor.extract_text(html)
        assert result == "Text\n\nMore text"
        assert "color" not in result

    def test_div_handling(self):
        """Test that divs add single newlines."""
        extractor = HTMLTextExtractor()
        html = "<div>First div</div><div>Second div</div>"
        result = extractor.extract_text(html)
        assert result == "First div\nSecond div"

    def test_nested_tags(self):
        """Test deeply nested HTML structure."""
        extractor = HTMLTextExtractor()
        html = """
        <div>
            <h1>Title</h1>
            <p>Paragraph with <b>bold</b> and <em>italic</em>.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        """
        result = extractor.extract_text(html)
        assert "Title" in result
        assert "Paragraph with bold and italic." in result
        assert "• Item 1" in result
        assert "• Item 2" in result

    def test_whitespace_normalization(self):
        """Test that excessive whitespace is normalized."""
        extractor = HTMLTextExtractor()
        html = "<p>Too    many     spaces</p>"
        result = extractor.extract_text(html)
        assert result == "Too many spaces"

    def test_excessive_newlines_collapsed(self):
        """Test that 3+ newlines are collapsed to 2."""
        extractor = HTMLTextExtractor()
        html = "<p>Para 1</p><br><br><br><br><p>Para 2</p>"
        result = extractor.extract_text(html)
        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in result

    def test_empty_html(self):
        """Test handling of empty HTML."""
        extractor = HTMLTextExtractor()
        result = extractor.extract_text("")
        assert result == ""

    def test_html_with_only_tags(self):
        """Test HTML with tags but no text content."""
        extractor = HTMLTextExtractor()
        html = "<div><p></p><br><hr></div>"
        result = extractor.extract_text(html)
        # Should only have the horizontal rule separator
        assert result.strip() == "---"

    def test_malformed_html_graceful(self):
        """Test that malformed HTML doesn't crash the parser."""
        extractor = HTMLTextExtractor()
        # Missing closing tags
        html = "<p>Text without closing tag<div>More text"
        result = extractor.extract_text(html)
        assert "Text without closing tag" in result
        assert "More text" in result

    def test_html_entities(self):
        """Test handling of HTML entities."""
        extractor = HTMLTextExtractor()
        html = "<p>AT&amp;T &lt;company&gt;</p>"
        result = extractor.extract_text(html)
        # HTMLParser automatically decodes entities
        assert "AT&T" in result or "AT&amp;T" in result

    def test_table_handling(self):
        """Test basic table structure preservation."""
        extractor = HTMLTextExtractor()
        html = """
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        """
        result = extractor.extract_text(html)
        assert "Header 1" in result
        assert "Header 2" in result
        assert "Cell 1" in result
        assert "Cell 2" in result

    def test_reusability(self):
        """Test that the extractor can be reused for multiple extractions."""
        extractor = HTMLTextExtractor()

        result1 = extractor.extract_text("<p>First text</p>")
        assert result1 == "First text"

        result2 = extractor.extract_text("<p>Second text</p>")
        assert result2 == "Second text"

        # Results should be independent
        assert result1 != result2

    def test_complex_nested_lists(self):
        """Test nested list structures."""
        extractor = HTMLTextExtractor()
        html = """
        <ul>
            <li>Parent 1
                <ul>
                    <li>Child 1</li>
                    <li>Child 2</li>
                </ul>
            </li>
            <li>Parent 2</li>
        </ul>
        """
        result = extractor.extract_text(html)
        assert "• Parent 1" in result
        assert "• Child 1" in result
        assert "• Child 2" in result
        assert "• Parent 2" in result

    def test_mixed_content(self):
        """Test realistic EPUB-style HTML with mixed content."""
        extractor = HTMLTextExtractor()
        html = """
        <div class="chapter">
            <h1>Chapter 1: The Beginning</h1>
            <p>It was a dark and stormy night. The rain poured down in torrents.</p>
            <p>Inside the old mansion, a figure moved silently through the shadows.</p>
            <hr>
            <h2>Section 1.1</h2>
            <p>The story continues with <em>dramatic</em> tension building.</p>
            <ul>
                <li>First clue</li>
                <li>Second clue</li>
            </ul>
        </div>
        """
        result = extractor.extract_text(html)

        # Check that all content is present
        assert "Chapter 1: The Beginning" in result
        assert "It was a dark and stormy night" in result
        assert "Inside the old mansion" in result
        assert "Section 1.1" in result
        assert "dramatic" in result
        assert "• First clue" in result
        assert "• Second clue" in result
        assert "---" in result

    def test_leading_trailing_whitespace_stripped(self):
        """Test that leading and trailing whitespace is removed."""
        extractor = HTMLTextExtractor()
        html = "   <p>Text</p>   "
        result = extractor.extract_text(html)
        assert result == "Text"
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_span_and_inline_elements(self):
        """Test that span and other inline elements don't add spacing."""
        extractor = HTMLTextExtractor()
        html = "<p>Text with <span class='highlight'>highlighted</span> word.</p>"
        result = extractor.extract_text(html)
        assert result == "Text with highlighted word."

    def test_link_text_preserved(self):
        """Test that link text is preserved (href ignored)."""
        extractor = HTMLTextExtractor()
        html = "<p>Visit <a href='http://example.com'>our website</a> for info.</p>"
        result = extractor.extract_text(html)
        assert result == "Visit our website for info."
        assert "http://example.com" not in result


class TestHTMLTextExtractorEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_unicode_content(self):
        """Test handling of Unicode characters."""
        extractor = HTMLTextExtractor()
        html = "<p>Café résumé naïve 中文 日本語 한국어</p>"
        result = extractor.extract_text(html)
        assert "Café" in result
        assert "中文" in result

    def test_very_long_text(self):
        """Test handling of large HTML documents."""
        extractor = HTMLTextExtractor()
        # Create a large HTML document
        paragraphs = "".join([f"<p>Paragraph {i}</p>" for i in range(1000)])
        result = extractor.extract_text(paragraphs)
        assert "Paragraph 0" in result
        assert "Paragraph 999" in result

    def test_deeply_nested_structure(self):
        """Test handling of deeply nested HTML."""
        extractor = HTMLTextExtractor()
        # Create deeply nested divs
        html = "<div>" * 50 + "Deep content" + "</div>" * 50
        result = extractor.extract_text(html)
        assert "Deep content" in result

    def test_empty_tags(self):
        """Test handling of empty tags."""
        extractor = HTMLTextExtractor()
        html = "<p></p><div></div><h1></h1><ul><li></li></ul>"
        result = extractor.extract_text(html)
        # Should return empty or minimal whitespace
        assert len(result.strip()) == 0

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        extractor = HTMLTextExtractor()
        html = "<p>Special: &lt; &gt; &amp; &quot; &copy; &reg;</p>"
        result = extractor.extract_text(html)
        assert "Special:" in result
