"""Integration tests for HTML parsing with real fixtures and mocked URLs."""

import time
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from omniparser import parse_document
from omniparser.parsers.html import HTMLParser
from omniparser.models import Document
from omniparser.exceptions import NetworkError, ParsingError, FileReadError


@pytest.fixture
def fixtures_dir() -> Path:
    """Get path to HTML test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "html"


class TestHTMLParsingIntegration:
    """Integration tests for complete HTML parsing pipeline."""

    # File Parsing Integration Tests

    def test_parse_simple_article_fixture(self, fixtures_dir: Path) -> None:
        """Test parsing simple_article.html with full pipeline."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        # Verify it returns Document
        assert isinstance(doc, Document)

        # Verify metadata extraction
        assert doc.metadata.title == "Simple Article Example"
        assert doc.metadata.author == "Jane Doe"
        assert doc.metadata.description == "A simple article for testing HTML parsing"
        assert doc.metadata.language == "en"
        assert doc.metadata.original_format == "html"

        # Verify tags/keywords extracted
        assert doc.metadata.tags is not None
        assert "testing" in doc.metadata.tags
        assert "html" in doc.metadata.tags
        assert "parser" in doc.metadata.tags

        # Verify chapter detection (h1 + 3 h2 sections)
        assert len(doc.chapters) >= 4
        assert doc.chapters[0].title == "Simple Article Example"
        chapter_titles = [ch.title for ch in doc.chapters]
        assert "First Section" in chapter_titles
        assert "Second Section" in chapter_titles
        assert "Conclusion" in chapter_titles

        # Verify markdown conversion
        content_lower = doc.content.lower()
        assert "bold" in content_lower  # Should have bold text
        assert "italic" in content_lower  # Should have italic text
        assert "example.com" in doc.content  # Should have link
        assert (
            "first item" in content_lower or "First item" in doc.content
        )  # Should have list

        # Verify word count and reading time
        assert doc.word_count > 50
        assert doc.estimated_reading_time > 0

        # Verify processing info
        assert doc.processing_info.parser_used == "html"
        assert doc.processing_info.processing_time > 0
        assert doc.processing_info.timestamp is not None

    def test_parse_opengraph_fixture(self, fixtures_dir: Path) -> None:
        """Test OpenGraph metadata priority with opengraph_article.html."""
        html_path = fixtures_dir / "opengraph_article.html"
        doc = parse_document(html_path)

        # OpenGraph should take priority over Dublin Core and title tag
        assert doc.metadata.title == "Advanced HTML Article"
        assert doc.metadata.author == "John Smith"  # from og:article:author
        assert (
            doc.metadata.description
            == "An article with OpenGraph and Dublin Core metadata"
        )

        # Verify tags from og:article:tag (multiple)
        assert doc.metadata.tags is not None
        assert "html" in doc.metadata.tags
        assert "metadata" in doc.metadata.tags
        assert "testing" in doc.metadata.tags

        # Verify publication date parsed
        assert doc.metadata.publication_date is not None

        # Verify publisher from Dublin Core (not in OpenGraph)
        assert doc.metadata.publisher == "Test Publisher"

        # Verify og:image in custom fields
        assert doc.metadata.custom_fields is not None
        assert "og_image" in doc.metadata.custom_fields
        assert doc.metadata.custom_fields["og_image"] == "https://example.com/image.jpg"

        # Verify chapters (h1 + 4 h2)
        assert len(doc.chapters) >= 5

        # Verify code block in content (may be in code fence or inline)
        assert "hello" in doc.content.lower() or "print" in doc.content.lower()

    def test_parse_complex_structure_fixture(self, fixtures_dir: Path) -> None:
        """Test complex HTML elements with complex_structure.html."""
        html_path = fixtures_dir / "complex_structure.html"
        doc = parse_document(html_path)

        assert doc.metadata.title == "Complex Document Structure"
        assert doc.metadata.author == "Alice Johnson"
        assert doc.metadata.language == "fr"

        # Verify table content present (markdown tables or plain text)
        content_lower = doc.content.lower()
        assert "name" in content_lower
        assert "value" in content_lower
        assert "alpha" in content_lower
        assert "beta" in content_lower

        # Verify blockquote content present
        assert "blockquote" in content_lower or ">" in doc.content

        # Verify code content
        assert "code" in content_lower or "function" in content_lower

        # Verify image alt text present
        assert "test image" in content_lower or "image" in content_lower

        # Verify horizontal rule or section breaks
        # (may be converted to various formats)

        # Verify chapters with nested headings
        assert len(doc.chapters) >= 5  # At least h1 + h2 sections

    def test_parse_no_headings_fixture(self, fixtures_dir: Path) -> None:
        """Test document without headings creates single chapter."""
        html_path = fixtures_dir / "no_headings.html"
        doc = parse_document(html_path)

        assert doc.metadata.title == "Document Without Headings"

        # Should create single "Full Document" chapter
        assert len(doc.chapters) == 1
        assert doc.chapters[0].title == "Full Document"
        assert doc.chapters[0].level == 1

        # Content should still be extracted
        assert "headings" in doc.content.lower()
        assert doc.word_count > 20

    def test_parse_minimal_fixture(self, fixtures_dir: Path) -> None:
        """Test minimal HTML parsing."""
        html_path = fixtures_dir / "minimal.html"
        doc = parse_document(html_path)

        assert doc.metadata.title == "Minimal HTML"
        assert "paragraph" in doc.content.lower()
        assert doc.word_count > 0

    # URL Parsing Integration Tests (Mocked)

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
    def test_parse_url_with_metadata(
        self, mock_fetch: Mock, fixtures_dir: Path
    ) -> None:
        """Test URL parsing with full metadata extraction."""
        # Use opengraph fixture as mock response
        with open(fixtures_dir / "opengraph_article.html", "r", encoding="utf-8") as f:
            mock_html = f.read()
        mock_fetch.return_value = mock_html

        doc = parse_document("https://example.com/article")

        assert isinstance(doc, Document)
        assert doc.metadata.title == "Advanced HTML Article"
        assert doc.metadata.author == "John Smith"

        # URL should be stored in custom_fields
        assert doc.metadata.custom_fields is not None
        assert doc.metadata.custom_fields.get("url") == "https://example.com/article"

        mock_fetch.assert_called_once()

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
    def test_parse_url_with_chapters(
        self, mock_fetch: Mock, fixtures_dir: Path
    ) -> None:
        """Test URL parsing with chapter detection."""
        with open(fixtures_dir / "simple_article.html", "r", encoding="utf-8") as f:
            mock_html = f.read()
        mock_fetch.return_value = mock_html

        doc = parse_document("https://blog.example.com/post")

        assert len(doc.chapters) >= 4
        assert any("First Section" in ch.title for ch in doc.chapters)

    # Custom Options Integration Tests

    def test_parse_with_custom_chapter_levels(self, fixtures_dir: Path) -> None:
        """Test parsing with custom chapter heading levels."""
        html_path = fixtures_dir / "complex_structure.html"

        # Parse with only H1-H2 as chapters
        parser = HTMLParser(options={"min_chapter_level": 1, "max_chapter_level": 2})
        doc = parser.parse(html_path)
        h2_chapters = len(doc.chapters)

        # Parse with H1-H3 as chapters
        parser = HTMLParser(options={"min_chapter_level": 1, "max_chapter_level": 3})
        doc = parser.parse(html_path)
        h3_chapters = len(doc.chapters)

        # H1-H3 should have more chapters than H1-H2
        assert h3_chapters >= h2_chapters

    def test_parse_without_chapter_detection(self, fixtures_dir: Path) -> None:
        """Test parsing with chapter detection disabled."""
        html_path = fixtures_dir / "simple_article.html"

        parser = HTMLParser(options={"detect_chapters": False})
        doc = parser.parse(html_path)

        # No chapters should be detected
        assert len(doc.chapters) == 0

        # But content should still be present
        assert len(doc.content) > 100
        assert doc.word_count > 50

    # Performance Integration Tests

    def test_parse_large_document_performance(self, fixtures_dir: Path) -> None:
        """Test parsing performance on larger documents."""
        html_path = fixtures_dir / "complex_structure.html"

        start = time.time()
        doc = parse_document(html_path)
        elapsed = time.time() - start

        # Should parse in under 2 seconds
        assert elapsed < 2.0
        assert doc.processing_info.processing_time < 2.0

    # Error Handling Integration Tests

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
    def test_url_timeout_error(self, mock_fetch: Mock) -> None:
        """Test NetworkError on URL timeout."""
        mock_fetch.side_effect = NetworkError("Connection timeout")

        with pytest.raises(NetworkError):
            parse_document("https://example.com/timeout")

    def test_file_not_found_error(self) -> None:
        """Test FileReadError for missing HTML file."""
        with pytest.raises(FileReadError):
            parse_document(Path("nonexistent.html"))

    # Content Extraction Integration Tests

    def test_script_style_removal(self, fixtures_dir: Path) -> None:
        """Test that script and style tags are removed."""
        html_path = fixtures_dir / "complex_structure.html"
        doc = parse_document(html_path)

        # Should not contain script or style content
        assert "console.log" not in doc.content
        assert "color: red" not in doc.content
        assert "color:red" not in doc.content
        content_lower = doc.content.lower()
        assert "<script>" not in content_lower
        assert "<style>" not in content_lower

    def test_navigation_footer_removal(self, fixtures_dir: Path) -> None:
        """Test that navigation and footer are removed."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        # Main content should be preserved
        assert (
            "simple article" in doc.content.lower() or "article" in doc.content.lower()
        )

        # Navigation and footer should be removed
        # (depends on Trafilatura/Readability effectiveness)
        # We can check word count is reasonable
        assert doc.word_count > 30  # Has main content
        assert doc.word_count < 500  # Not including everything


class TestHTMLURLParsing:
    """Additional tests for URL-specific features."""

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
    def test_parse_http_url(self, mock_fetch: Mock, fixtures_dir: Path) -> None:
        """Test parsing HTTP URL (should upgrade to HTTPS)."""
        with open(fixtures_dir / "minimal.html", "r", encoding="utf-8") as f:
            mock_html = f.read()
        mock_fetch.return_value = mock_html

        # Note: The actual upgrade happens in requests, we just test parsing works
        doc = parse_document("http://example.com/page")

        assert isinstance(doc, Document)
        assert doc.metadata.title == "Minimal HTML"

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
    def test_parse_url_with_custom_timeout(
        self, mock_fetch: Mock, fixtures_dir: Path
    ) -> None:
        """Test URL parsing with custom timeout option."""
        with open(fixtures_dir / "minimal.html", "r", encoding="utf-8") as f:
            mock_html = f.read()
        mock_fetch.return_value = mock_html

        parser = HTMLParser(options={"timeout": 5})
        doc = parser.parse("https://example.com/page")

        assert isinstance(doc, Document)
        mock_fetch.assert_called_once()


class TestHTMLMarkdownConversion:
    """Tests for HTML to Markdown conversion quality."""

    def test_bold_italic_conversion(self, fixtures_dir: Path) -> None:
        """Test bold and italic text conversion."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        # Should have formatting indicators (markdown or plain text)
        content = doc.content
        content_lower = content.lower()

        # Check that bold/italic content is present
        assert "bold" in content_lower
        assert "italic" in content_lower

    def test_link_conversion(self, fixtures_dir: Path) -> None:
        """Test hyperlink conversion to markdown."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        # Should contain the link URL
        assert "example.com" in doc.content

    def test_list_conversion(self, fixtures_dir: Path) -> None:
        """Test list conversion to markdown."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        content_lower = doc.content.lower()
        # Should have list items
        assert "first item" in content_lower
        assert "second item" in content_lower
        assert "third item" in content_lower

    def test_table_conversion(self, fixtures_dir: Path) -> None:
        """Test table conversion to markdown or plain text."""
        html_path = fixtures_dir / "complex_structure.html"
        doc = parse_document(html_path)

        content_lower = doc.content.lower()
        # Table data should be present
        assert "name" in content_lower
        assert "value" in content_lower
        assert "alpha" in content_lower
        assert "100" in doc.content

    def test_blockquote_conversion(self, fixtures_dir: Path) -> None:
        """Test blockquote conversion."""
        html_path = fixtures_dir / "complex_structure.html"
        doc = parse_document(html_path)

        # Blockquote content should be present
        content_lower = doc.content.lower()
        assert "blockquote" in content_lower

    def test_code_block_conversion(self, fixtures_dir: Path) -> None:
        """Test code block and inline code conversion."""
        html_path = fixtures_dir / "complex_structure.html"
        doc = parse_document(html_path)

        content_lower = doc.content.lower()
        # Code content should be present
        assert "function" in content_lower or "code" in content_lower


class TestHTMLChapterDetection:
    """Tests for chapter detection from HTML headings."""

    def test_chapter_hierarchy(self, fixtures_dir: Path) -> None:
        """Test chapter hierarchy levels are correct."""
        html_path = fixtures_dir / "complex_structure.html"
        doc = parse_document(html_path)

        # H1 should be level 1
        assert any(ch.level == 1 for ch in doc.chapters)

        # H2 should be level 2
        assert any(ch.level == 2 for ch in doc.chapters)

    def test_chapter_content_positions(self, fixtures_dir: Path) -> None:
        """Test chapter start/end positions are valid."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        for chapter in doc.chapters:
            assert chapter.start_position >= 0
            assert chapter.end_position > chapter.start_position
            assert chapter.word_count > 0

    def test_chapter_word_counts(self, fixtures_dir: Path) -> None:
        """Test chapter word counts sum approximately to total."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        chapter_words = sum(ch.word_count for ch in doc.chapters)
        # Allow some difference due to chapter boundaries
        difference = abs(doc.word_count - chapter_words)
        # Allow up to 20% difference (chapter detection may skip some content)
        assert difference < doc.word_count * 0.2


class TestHTMLMetadataExtraction:
    """Tests for metadata extraction from HTML."""

    def test_standard_meta_tags(self, fixtures_dir: Path) -> None:
        """Test extraction from standard meta tags."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        assert doc.metadata.title == "Simple Article Example"
        assert doc.metadata.author == "Jane Doe"
        assert doc.metadata.description is not None

    def test_opengraph_priority(self, fixtures_dir: Path) -> None:
        """Test OpenGraph takes priority over other metadata."""
        html_path = fixtures_dir / "opengraph_article.html"
        doc = parse_document(html_path)

        # Should use OpenGraph title, not fallback
        assert doc.metadata.title == "Advanced HTML Article"
        assert doc.metadata.title != "Fallback Title"

    def test_dublin_core_fallback(self, fixtures_dir: Path) -> None:
        """Test Dublin Core metadata extraction."""
        html_path = fixtures_dir / "opengraph_article.html"
        doc = parse_document(html_path)

        # Publisher from Dublin Core (not in OpenGraph)
        assert doc.metadata.publisher == "Test Publisher"

    def test_keywords_to_tags(self, fixtures_dir: Path) -> None:
        """Test keywords converted to tags."""
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)

        assert doc.metadata.tags is not None
        assert len(doc.metadata.tags) >= 3
        assert "testing" in doc.metadata.tags
        assert "html" in doc.metadata.tags
        assert "parser" in doc.metadata.tags

    def test_multiple_article_tags(self, fixtures_dir: Path) -> None:
        """Test multiple og:article:tag values."""
        html_path = fixtures_dir / "opengraph_article.html"
        doc = parse_document(html_path)

        assert doc.metadata.tags is not None
        assert "html" in doc.metadata.tags
        assert "metadata" in doc.metadata.tags
        assert "testing" in doc.metadata.tags

    def test_publication_date_parsing(self, fixtures_dir: Path) -> None:
        """Test publication date parsing from OpenGraph."""
        html_path = fixtures_dir / "opengraph_article.html"
        doc = parse_document(html_path)

        assert doc.metadata.publication_date is not None
        # Should be datetime object
        from datetime import datetime

        assert isinstance(doc.metadata.publication_date, datetime)

    def test_language_detection(self, fixtures_dir: Path) -> None:
        """Test language detection from html lang attribute."""
        # English document
        html_path = fixtures_dir / "simple_article.html"
        doc = parse_document(html_path)
        assert doc.metadata.language == "en"

        # French document
        html_path = fixtures_dir / "complex_structure.html"
        doc = parse_document(html_path)
        assert doc.metadata.language == "fr"
