"""
Unit tests for DOCX hyperlink extraction and formatting.

Tests cover:
- Hyperlink extraction from paragraphs
- Markdown formatting of hyperlinks
- URL resolution from relationship IDs
- Edge cases (empty text, mailto links, special characters)
"""

import pytest
from unittest.mock import Mock, MagicMock
from docx.oxml.ns import qn

from omniparser.parsers.docx.hyperlinks import (
    get_hyperlink_url,
    is_run_hyperlink,
    extract_hyperlinks_from_paragraph,
    format_hyperlink_markdown,
    apply_hyperlinks_to_paragraph,
)


class TestGetHyperlinkUrl:
    """Tests for get_hyperlink_url function."""

    def test_get_url_success(self):
        """Test successful URL retrieval from relationship."""
        # Mock document with relationship
        docx = Mock()
        rel = Mock()
        rel.target_ref = "https://example.com"
        docx.part.rels = {"rId5": rel}

        url = get_hyperlink_url(docx, "rId5")
        assert url == "https://example.com"

    def test_get_url_missing_relationship(self):
        """Test with missing relationship ID."""
        docx = Mock()
        docx.part.rels = {}

        url = get_hyperlink_url(docx, "rId99")
        assert url is None

    def test_get_url_no_part_attribute(self):
        """Test with document missing part attribute."""
        docx = Mock(spec=[])  # Mock with no attributes

        url = get_hyperlink_url(docx, "rId5")
        assert url is None

    def test_get_url_mailto(self):
        """Test mailto: URL extraction."""
        docx = Mock()
        rel = Mock()
        rel.target_ref = "mailto:test@example.com"
        docx.part.rels = {"rId1": rel}

        url = get_hyperlink_url(docx, "rId1")
        assert url == "mailto:test@example.com"


class TestIsRunHyperlink:
    """Tests for is_run_hyperlink function."""

    def test_run_with_hlinkclick(self):
        """Test run with hlinkClick property."""
        run = Mock()
        element = Mock()
        rPr = Mock()
        hlinkClick = Mock()
        hlinkClick.get = Mock(return_value="rId5")
        rPr.find = Mock(return_value=hlinkClick)
        element.rPr = rPr
        element.getparent = Mock(return_value=None)
        run._element = element

        rId = is_run_hyperlink(run)
        assert rId == "rId5"

    def test_run_with_hyperlink_parent(self):
        """Test run with hyperlink wrapper parent."""
        run = Mock()
        element = Mock()
        element.rPr = None

        parent = Mock()
        parent.tag = qn("w:hyperlink")
        parent.get = Mock(return_value="rId3")
        element.getparent = Mock(return_value=parent)
        run._element = element

        rId = is_run_hyperlink(run)
        assert rId == "rId3"

    def test_run_without_hyperlink(self):
        """Test regular run without hyperlink."""
        run = Mock()
        element = Mock()
        element.rPr = None
        element.getparent = Mock(return_value=None)
        run._element = element

        rId = is_run_hyperlink(run)
        assert rId is None

    def test_run_without_element(self):
        """Test run missing _element attribute."""
        run = Mock(spec=[])  # Mock with no attributes

        rId = is_run_hyperlink(run)
        assert rId is None


class TestExtractHyperlinksFromParagraph:
    """Tests for extract_hyperlinks_from_paragraph function."""

    def test_extract_single_hyperlink(self):
        """Test extracting single hyperlink from paragraph."""
        # Mock paragraph with one hyperlinked run
        para = Mock()
        run = Mock()
        run.text = "Example Site"

        element = Mock()
        rPr = Mock()
        hlinkClick = Mock()
        hlinkClick.get = Mock(return_value="rId1")
        rPr.find = Mock(return_value=hlinkClick)
        element.rPr = rPr
        element.getparent = Mock(return_value=None)
        run._element = element

        para.runs = [run]

        # Mock document
        docx = Mock()
        rel = Mock()
        rel.target_ref = "https://example.com"
        docx.part.rels = {"rId1": rel}

        links = extract_hyperlinks_from_paragraph(para, docx)
        assert len(links) == 1
        assert links[0] == ("Example Site", "https://example.com")

    def test_extract_multiple_hyperlinks(self):
        """Test extracting multiple hyperlinks from paragraph."""
        # Mock paragraph with two hyperlinked runs
        para = Mock()

        run1 = Mock()
        run1.text = "Site 1"
        element1 = Mock()
        rPr1 = Mock()
        hlinkClick1 = Mock()
        hlinkClick1.get = Mock(return_value="rId1")
        rPr1.find = Mock(return_value=hlinkClick1)
        element1.rPr = rPr1
        element1.getparent = Mock(return_value=None)
        run1._element = element1

        run2 = Mock()
        run2.text = "Site 2"
        element2 = Mock()
        rPr2 = Mock()
        hlinkClick2 = Mock()
        hlinkClick2.get = Mock(return_value="rId2")
        rPr2.find = Mock(return_value=hlinkClick2)
        element2.rPr = rPr2
        element2.getparent = Mock(return_value=None)
        run2._element = element2

        para.runs = [run1, run2]

        # Mock document
        docx = Mock()
        rel1 = Mock()
        rel1.target_ref = "https://example.com"
        rel2 = Mock()
        rel2.target_ref = "https://test.com"
        docx.part.rels = {"rId1": rel1, "rId2": rel2}

        links = extract_hyperlinks_from_paragraph(para, docx)
        assert len(links) == 2
        assert links[0] == ("Site 1", "https://example.com")
        assert links[1] == ("Site 2", "https://test.com")

    def test_extract_no_hyperlinks(self):
        """Test paragraph without hyperlinks."""
        para = Mock()
        run = Mock()
        run.text = "Plain text"
        element = Mock()
        element.rPr = None
        element.getparent = Mock(return_value=None)
        run._element = element
        para.runs = [run]

        docx = Mock()
        docx.part.rels = {}

        links = extract_hyperlinks_from_paragraph(para, docx)
        assert len(links) == 0

    def test_extract_hyperlink_empty_text(self):
        """Test hyperlink with empty text uses URL as fallback."""
        para = Mock()
        run = Mock()
        run.text = ""

        element = Mock()
        rPr = Mock()
        hlinkClick = Mock()
        hlinkClick.get = Mock(return_value="rId1")
        rPr.find = Mock(return_value=hlinkClick)
        element.rPr = rPr
        element.getparent = Mock(return_value=None)
        run._element = element

        para.runs = [run]

        docx = Mock()
        rel = Mock()
        rel.target_ref = "https://example.com"
        docx.part.rels = {"rId1": rel}

        links = extract_hyperlinks_from_paragraph(para, docx)
        assert len(links) == 1
        assert links[0] == ("https://example.com", "https://example.com")


class TestFormatHyperlinkMarkdown:
    """Tests for format_hyperlink_markdown function."""

    def test_format_basic_hyperlink(self):
        """Test formatting basic HTTP hyperlink."""
        md = format_hyperlink_markdown("Example", "https://example.com")
        assert md == "[Example](https://example.com)"

    def test_format_mailto_link(self):
        """Test formatting mailto: hyperlink."""
        md = format_hyperlink_markdown("Email", "mailto:test@example.com")
        assert md == "[Email](mailto:test@example.com)"

    def test_format_with_special_chars_in_text(self):
        """Test escaping special characters in link text."""
        md = format_hyperlink_markdown("Example [Site]", "https://example.com")
        assert md == "[Example \\[Site\\]](https://example.com)"

    def test_format_with_special_chars_in_url(self):
        """Test escaping special characters in URL."""
        md = format_hyperlink_markdown(
            "Example", "https://example.com/path(with)parens"
        )
        assert md == "[Example](https://example.com/path\\(with\\)parens)"

    def test_format_with_query_params(self):
        """Test URL with query parameters."""
        md = format_hyperlink_markdown("Search", "https://example.com?q=test&limit=10")
        assert md == "[Search](https://example.com?q=test&limit=10)"

    def test_format_file_protocol(self):
        """Test file:// protocol."""
        md = format_hyperlink_markdown("Local File", "file:///path/to/file.pdf")
        assert md == "[Local File](file:///path/to/file.pdf)"


class TestApplyHyperlinksToParag:
    """Tests for apply_hyperlinks_to_paragraph function."""

    def test_apply_single_hyperlink(self):
        """Test converting paragraph with one hyperlink."""
        para = Mock()
        run = Mock()
        run.text = "Example Site"

        element = Mock()
        rPr = Mock()
        hlinkClick = Mock()
        hlinkClick.get = Mock(return_value="rId1")
        rPr.find = Mock(return_value=hlinkClick)
        element.rPr = rPr
        element.getparent = Mock(return_value=None)
        run._element = element

        para.runs = [run]

        docx = Mock()
        rel = Mock()
        rel.target_ref = "https://example.com"
        docx.part.rels = {"rId1": rel}

        result = apply_hyperlinks_to_paragraph(para, docx)
        assert result == "[Example Site](https://example.com)"

    def test_apply_mixed_content(self):
        """Test paragraph with hyperlink and plain text."""
        para = Mock()

        # Plain text run
        run1 = Mock()
        run1.text = "Visit "
        element1 = Mock()
        element1.rPr = None
        element1.getparent = Mock(return_value=None)
        run1._element = element1

        # Hyperlink run
        run2 = Mock()
        run2.text = "our site"
        element2 = Mock()
        rPr2 = Mock()
        hlinkClick2 = Mock()
        hlinkClick2.get = Mock(return_value="rId1")
        rPr2.find = Mock(return_value=hlinkClick2)
        element2.rPr = rPr2
        element2.getparent = Mock(return_value=None)
        run2._element = element2

        # Plain text run
        run3 = Mock()
        run3.text = " for info"
        element3 = Mock()
        element3.rPr = None
        element3.getparent = Mock(return_value=None)
        run3._element = element3

        para.runs = [run1, run2, run3]

        docx = Mock()
        rel = Mock()
        rel.target_ref = "https://example.com"
        docx.part.rels = {"rId1": rel}

        result = apply_hyperlinks_to_paragraph(para, docx)
        assert result == "Visit [our site](https://example.com) for info"

    def test_apply_no_hyperlinks(self):
        """Test paragraph without hyperlinks."""
        para = Mock()
        run = Mock()
        run.text = "Plain text only"
        element = Mock()
        element.rPr = None
        element.getparent = Mock(return_value=None)
        run._element = element
        para.runs = [run]

        docx = Mock()
        docx.part.rels = {}

        result = apply_hyperlinks_to_paragraph(para, docx)
        assert result == "Plain text only"

    def test_apply_empty_paragraph(self):
        """Test empty paragraph."""
        para = Mock()
        para.runs = []

        docx = Mock()

        result = apply_hyperlinks_to_paragraph(para, docx)
        assert result == ""
