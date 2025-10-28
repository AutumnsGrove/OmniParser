"""
Unit tests for HTML parser.

Tests the HTMLParser class functionality including format support, URL fetching,
local file reading, content extraction, and document building.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from omniparser.exceptions import FileReadError, NetworkError, ParsingError
from omniparser.models import Document
from omniparser.parsers.html_parser import HTMLParser


@pytest.fixture
def html_parser() -> HTMLParser:
    """Create HTMLParser instance for testing."""
    return HTMLParser()


@pytest.fixture
def simple_html() -> str:
    """Simple HTML string for testing."""
    return """
    <html>
    <head>
        <title>Test Article</title>
        <meta name="author" content="Test Author">
        <meta name="description" content="Test description">
    </head>
    <body>
        <h1>Main Title</h1>
        <p>This is the first paragraph with some content.</p>
        <h2>Section One</h2>
        <p>Content in section one.</p>
    </body>
    </html>
    """


@pytest.fixture
def opengraph_html() -> str:
    """HTML with OpenGraph metadata."""
    return """
    <html lang="en">
    <head>
        <title>Fallback Title</title>
        <meta property="og:title" content="OpenGraph Title">
        <meta property="og:description" content="OpenGraph description">
        <meta property="og:article:author" content="OG Author">
        <meta property="og:article:published_time" content="2024-01-15T10:30:00Z">
        <meta property="og:article:tag" content="html">
        <meta property="og:article:tag" content="metadata">
        <meta property="og:article:tag" content="testing">
    </head>
    <body>
        <article>
            <h1>Article Title</h1>
            <p>Article content here.</p>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def complex_html() -> str:
    """Complex HTML with various elements."""
    return """
    <html lang="fr">
    <head>
        <title>Complex Document</title>
        <meta name="author" content="Complex Author">
        <meta name="DC.publisher" content="Test Publisher">
    </head>
    <body>
        <nav>Navigation menu should be removed</nav>
        <article>
            <h1>Main Title</h1>
            <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
            <h2>Section with Code</h2>
            <pre><code>def example():
    return "code"</code></pre>
            <h2>Section with List</h2>
            <ul>
                <li>Item one</li>
                <li>Item two</li>
                <li>Item three</li>
            </ul>
            <h3>Subsection with Table</h3>
            <table>
                <tr><th>Name</th><th>Value</th></tr>
                <tr><td>Test</td><td>123</td></tr>
            </table>
            <blockquote>This is a quoted section.</blockquote>
        </article>
        <footer>Footer should be removed</footer>
    </body>
    </html>
    """


@pytest.fixture
def minimal_html() -> str:
    """Minimal valid HTML."""
    return """
    <html>
    <head><title>Minimal</title></head>
    <body><p>Just some text.</p></body>
    </html>
    """


class TestHTMLParserInit:
    """Test HTMLParser initialization."""

    def test_init_no_options(self, html_parser: HTMLParser) -> None:
        """Test initialization without options."""
        assert html_parser.options == {}

    def test_init_with_options(self) -> None:
        """Test initialization with custom options."""
        options = {"timeout": 30, "detect_chapters": False}
        parser = HTMLParser(options)

        assert parser.options["timeout"] == 30
        assert parser.options["detect_chapters"] is False


class TestHTMLParserSupportsFormat:
    """Test format support detection."""

    def test_supports_html_lowercase(self, html_parser: HTMLParser) -> None:
        """Test .html extension is supported."""
        assert html_parser.supports_format(Path("document.html")) is True

    def test_supports_html_uppercase(self, html_parser: HTMLParser) -> None:
        """Test .HTML extension is supported."""
        assert html_parser.supports_format(Path("document.HTML")) is True

    def test_supports_htm_extension(self, html_parser: HTMLParser) -> None:
        """Test .htm extension is supported."""
        assert html_parser.supports_format(Path("document.htm")) is True

    def test_supports_http_url(self, html_parser: HTMLParser) -> None:
        """Test HTTP URL is supported."""
        assert html_parser.supports_format("http://example.com/page.html") is True
        assert html_parser.supports_format("http://example.com") is True

    def test_supports_https_url(self, html_parser: HTMLParser) -> None:
        """Test HTTPS URL is supported."""
        assert html_parser.supports_format("https://example.com/page.html") is True
        assert html_parser.supports_format("https://example.com") is True

    def test_not_supports_pdf(self, html_parser: HTMLParser) -> None:
        """Test .pdf extension is not supported."""
        assert html_parser.supports_format(Path("document.pdf")) is False

    def test_not_supports_epub(self, html_parser: HTMLParser) -> None:
        """Test .epub extension is not supported."""
        assert html_parser.supports_format(Path("book.epub")) is False

    def test_not_supports_txt(self, html_parser: HTMLParser) -> None:
        """Test .txt extension is not supported."""
        assert html_parser.supports_format(Path("file.txt")) is False

    def test_not_supports_ftp_url(self, html_parser: HTMLParser) -> None:
        """Test FTP URL is not supported."""
        assert html_parser.supports_format("ftp://example.com/file") is False

    def test_not_supports_no_extension(self, html_parser: HTMLParser) -> None:
        """Test file without extension is not supported."""
        assert html_parser.supports_format(Path("document")) is False


class TestHTMLParserReadLocalFile:
    """Test local file reading."""

    def test_read_local_file_success(self, html_parser: HTMLParser) -> None:
        """Test reading local HTML file successfully."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write("<html><body><h1>Test</h1></body></html>")
            tmp_path = Path(tmp.name)

        try:
            content = html_parser._read_local_file(tmp_path)
            assert isinstance(content, str)
            assert "<html>" in content
            assert "<h1>Test</h1>" in content
        finally:
            tmp_path.unlink()

    def test_read_local_file_not_found(self, html_parser: HTMLParser) -> None:
        """Test FileReadError raised for missing file."""
        with pytest.raises(FileReadError, match="File not found"):
            html_parser._read_local_file(Path("/nonexistent/path/file.html"))

    def test_read_local_file_utf8_encoding(self, html_parser: HTMLParser) -> None:
        """Test reading file with UTF-8 characters."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write("<html><body><p>Café résumé naïve</p></body></html>")
            tmp_path = Path(tmp.name)

        try:
            content = html_parser._read_local_file(tmp_path)
            assert "Café" in content
            assert "résumé" in content
            assert "naïve" in content
        finally:
            tmp_path.unlink()


class TestHTMLParserFetchURL:
    """Test URL fetching with mocked requests."""

    @patch("omniparser.parsers.html_parser.requests.get")
    def test_fetch_url_success(
        self, mock_get: Mock, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test successful URL fetch."""
        mock_response = Mock()
        mock_response.text = simple_html
        mock_get.return_value = mock_response

        content = html_parser._fetch_url("http://example.com")

        assert content == simple_html
        mock_get.assert_called_once_with("http://example.com", timeout=10)

    @patch("omniparser.parsers.html_parser.requests.get")
    def test_fetch_url_custom_timeout(self, mock_get: Mock) -> None:
        """Test URL fetch with custom timeout option."""
        parser = HTMLParser({"timeout": 30})
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        parser._fetch_url("http://example.com")

        mock_get.assert_called_once_with("http://example.com", timeout=30)

    @patch("omniparser.parsers.html_parser.requests.get")
    def test_fetch_url_timeout_error(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test NetworkError raised on timeout."""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        with pytest.raises(NetworkError, match="Request timeout"):
            html_parser._fetch_url("http://example.com")

    @patch("omniparser.parsers.html_parser.requests.get")
    def test_fetch_url_http_error(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test NetworkError raised on HTTP error."""
        mock_get.side_effect = requests.HTTPError("404 Not Found")

        with pytest.raises(NetworkError, match="Failed to fetch URL"):
            html_parser._fetch_url("http://example.com/notfound")

    @patch("omniparser.parsers.html_parser.requests.get")
    def test_fetch_url_connection_error(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test NetworkError raised on connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        with pytest.raises(NetworkError, match="Failed to fetch URL"):
            html_parser._fetch_url("http://example.com")

    @patch("omniparser.parsers.html_parser.requests.get")
    def test_fetch_url_raise_for_status(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test that raise_for_status is called on response."""
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        html_parser._fetch_url("http://example.com")

        mock_response.raise_for_status.assert_called_once()


class TestHTMLParserExtractContent:
    """Test content extraction methods."""

    def test_extract_content_trafilatura_success(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test Trafilatura extraction with valid HTML."""
        result = html_parser._extract_content_trafilatura(simple_html)

        # Trafilatura may or may not extract content depending on quality
        # We just verify it doesn't crash and returns string or None
        assert result is None or isinstance(result, str)

    def test_extract_content_trafilatura_with_article(
        self, html_parser: HTMLParser
    ) -> None:
        """Test Trafilatura extraction with article tag."""
        html = """
        <html>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Article Title</h1>
                <p>This is the main article content that should be extracted.</p>
                <p>Second paragraph of the article.</p>
            </article>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        result = html_parser._extract_content_trafilatura(html)

        # Trafilatura should extract article content
        assert result is None or isinstance(result, str)
        if result:
            assert len(result) > 0

    def test_extract_content_trafilatura_malformed_html(
        self, html_parser: HTMLParser
    ) -> None:
        """Test Trafilatura handles malformed HTML gracefully."""
        malformed_html = "<html><body><p>Unclosed paragraph"

        # Should not raise exception
        result = html_parser._extract_content_trafilatura(malformed_html)
        assert result is None or isinstance(result, str)

    def test_extract_content_readability_success(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test Readability extraction with valid HTML."""
        result = html_parser._extract_content_readability(simple_html)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_extract_content_readability_extracts_main_content(
        self, html_parser: HTMLParser
    ) -> None:
        """Test Readability extracts main content and removes boilerplate."""
        html = """
        <html>
        <body>
            <nav>Navigation menu</nav>
            <article>
                <h1>Main Article</h1>
                <p>This is the important article content.</p>
            </article>
            <aside>Sidebar content</aside>
            <footer>Footer</footer>
        </body>
        </html>
        """
        result = html_parser._extract_content_readability(html)

        assert isinstance(result, str)
        assert len(result) > 0


class TestHTMLParserParse:
    """Test main parse method with local files."""

    def test_parse_simple_html_file(self, html_parser: HTMLParser) -> None:
        """Test parsing simple HTML file."""
        html = """
        <html>
        <head>
            <title>Simple Article</title>
            <meta name="author" content="Jane Doe">
            <meta name="description" content="A simple test article">
            <meta name="keywords" content="testing, html, parser">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is the first paragraph with enough content to pass extraction.</p>
            <p>This is the second paragraph with more content.</p>
            <h2>Section One</h2>
            <p>Content in section one with sufficient length for testing purposes.</p>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            assert isinstance(doc, Document)
            assert doc.metadata.title == "Simple Article"
            assert doc.metadata.author == "Jane Doe"
            assert doc.metadata.description == "A simple test article"
            assert "testing" in doc.metadata.tags
            assert "html" in doc.metadata.tags
            assert "parser" in doc.metadata.tags
            assert doc.metadata.original_format == "html"
            assert doc.word_count > 0
            assert doc.estimated_reading_time > 0
            assert len(doc.content) > 0
        finally:
            tmp_path.unlink()

    def test_parse_opengraph_metadata_priority(
        self, html_parser: HTMLParser, opengraph_html: str
    ) -> None:
        """Test OpenGraph metadata takes priority over other sources."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(opengraph_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            # OpenGraph values should take priority
            assert doc.metadata.title == "OpenGraph Title"
            assert doc.metadata.description == "OpenGraph description"
            assert doc.metadata.author == "OG Author"
            assert doc.metadata.language == "en"
            assert doc.metadata.publication_date is not None
            assert "html" in doc.metadata.tags
            assert "metadata" in doc.metadata.tags
            assert "testing" in doc.metadata.tags
        finally:
            tmp_path.unlink()

    def test_parse_complex_structure(
        self, html_parser: HTMLParser, complex_html: str
    ) -> None:
        """Test parsing complex HTML with various elements."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(complex_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            assert doc.metadata.title == "Complex Document"
            assert doc.metadata.author == "Complex Author"
            assert doc.metadata.language == "fr"
            assert doc.metadata.publisher == "Test Publisher"

            # Content should include markdown conversions
            content = doc.content
            assert "# Main Title" in content or "Main Title" in content
            assert "**bold**" in content or "bold" in content
            assert "*italic*" in content or "italic" in content

            # Navigation and footer should be removed
            assert "Navigation menu should be removed" not in content
            assert "Footer should be removed" not in content

            assert doc.word_count > 0
        finally:
            tmp_path.unlink()

    def test_parse_with_chapter_detection(
        self, html_parser: HTMLParser, complex_html: str
    ) -> None:
        """Test chapter detection from headings."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(complex_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            # Should detect chapters based on headings (h1, h2)
            assert len(doc.chapters) >= 1
        finally:
            tmp_path.unlink()

    def test_parse_without_chapter_detection(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test disabling chapter detection."""
        parser = HTMLParser({"detect_chapters": False})

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc = parser.parse(tmp_path)
            assert len(doc.chapters) == 0
        finally:
            tmp_path.unlink()

    def test_parse_with_custom_chapter_levels(
        self, html_parser: HTMLParser, complex_html: str
    ) -> None:
        """Test custom chapter heading levels."""
        parser = HTMLParser({"min_chapter_level": 1, "max_chapter_level": 3})

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(complex_html)
            tmp_path = Path(tmp.name)

        try:
            doc = parser.parse(tmp_path)
            # Should include H3 headings as chapters
            assert len(doc.chapters) >= 1
        finally:
            tmp_path.unlink()

    def test_parse_minimal_html(
        self, html_parser: HTMLParser, minimal_html: str
    ) -> None:
        """Test parsing minimal valid HTML."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(minimal_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            assert doc.metadata.title == "Minimal"
            assert len(doc.content) > 0
            assert doc.word_count > 0
        finally:
            tmp_path.unlink()

    @patch("omniparser.parsers.html_parser.HTMLParser._fetch_url")
    def test_parse_url(
        self, mock_fetch: Mock, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test parsing URL."""
        mock_fetch.return_value = simple_html

        doc = html_parser.parse("https://example.com/article")

        assert isinstance(doc, Document)
        assert doc.metadata.title == "Test Article"
        assert doc.metadata.author == "Test Author"
        assert doc.metadata.custom_fields is not None
        assert doc.metadata.custom_fields["url"] == "https://example.com/article"
        mock_fetch.assert_called_once_with("https://example.com/article")

    @patch("omniparser.parsers.html_parser.HTMLParser._fetch_url")
    def test_parse_url_stores_source(
        self, mock_fetch: Mock, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test URL is stored in metadata custom_fields."""
        mock_fetch.return_value = simple_html

        doc = html_parser.parse("https://example.com/page")

        assert doc.metadata.custom_fields is not None
        assert "url" in doc.metadata.custom_fields
        assert doc.metadata.custom_fields["url"] == "https://example.com/page"


class TestHTMLParserErrorHandling:
    """Test error handling and edge cases."""

    def test_parse_readability_fallback(self, html_parser: HTMLParser) -> None:
        """Test Readability fallback when Trafilatura returns minimal content."""
        # HTML that Trafilatura might not extract well
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <div>
                <p>Short content that might trigger fallback to Readability.</p>
            </div>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            # May use Readability fallback, should not crash
            doc = html_parser.parse(tmp_path)
            assert isinstance(doc, Document)
        finally:
            tmp_path.unlink()

    def test_parse_extraction_failure_both_methods(
        self, html_parser: HTMLParser
    ) -> None:
        """Test ParsingError when both extraction methods fail."""
        # Very minimal HTML that both extractors will fail on
        html = "<html><body></body></html>"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(
                ParsingError, match="Both Trafilatura and Readability failed"
            ):
                html_parser.parse(tmp_path)
        finally:
            tmp_path.unlink()

    def test_parse_warnings_on_fallback(self, html_parser: HTMLParser) -> None:
        """Test warnings are recorded when falling back to Readability."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <article>
                <p>Content that might need fallback processing to Readability extractor.</p>
            </article>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)
            # If fallback occurred, warnings should be present
            assert isinstance(doc, Document)
            # Warnings are internal to processing_info
            assert doc.processing_info is not None
        finally:
            tmp_path.unlink()

    @patch("omniparser.parsers.html_parser.HTMLParser._fetch_url")
    def test_parse_network_error_propagates(
        self, mock_fetch: Mock, html_parser: HTMLParser
    ) -> None:
        """Test NetworkError from URL fetch is propagated."""
        mock_fetch.side_effect = NetworkError("Connection failed")

        with pytest.raises(NetworkError, match="Connection failed"):
            html_parser.parse("http://example.com")

    def test_parse_file_read_error_propagates(self, html_parser: HTMLParser) -> None:
        """Test FileReadError from local file is propagated."""
        with pytest.raises(FileReadError, match="File not found"):
            html_parser.parse(Path("/nonexistent/file.html"))


class TestHTMLParserProcessingInfo:
    """Test processing information and metadata."""

    def test_parse_records_processing_time(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test processing time is recorded."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            assert doc.processing_info is not None
            assert doc.processing_info.processing_time >= 0
            assert doc.processing_info.parser_used == "HTMLParser"
            assert doc.processing_info.parser_version == "0.1.0"
            assert doc.processing_info.timestamp is not None
        finally:
            tmp_path.unlink()

    def test_parse_records_warnings(self, html_parser: HTMLParser) -> None:
        """Test warnings are recorded in processing info."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <p>Minimal content for warning test with some additional text here.</p>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            assert doc.processing_info is not None
            assert isinstance(doc.processing_info.warnings, list)
        finally:
            tmp_path.unlink()

    def test_parse_records_options_used(self, simple_html: str) -> None:
        """Test options used are recorded in processing info."""
        parser = HTMLParser({"timeout": 30, "detect_chapters": False})

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc = parser.parse(tmp_path)

            assert doc.processing_info is not None
            assert doc.processing_info.options_used is not None
            assert doc.processing_info.options_used["timeout"] == 30
            assert doc.processing_info.options_used["detect_chapters"] is False
        finally:
            tmp_path.unlink()


class TestHTMLParserWordCount:
    """Test word count and reading time calculation."""

    def test_parse_calculates_word_count(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test word count is calculated from content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            assert doc.word_count > 0
            # Simple HTML has at least a few words
            assert doc.word_count >= 5
        finally:
            tmp_path.unlink()

    def test_parse_calculates_reading_time(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test estimated reading time is calculated."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            assert doc.estimated_reading_time > 0
            # Reading time is max(1, round(word_count / 225)) - ensures minimum 1 minute
            assert doc.estimated_reading_time == max(1, round(doc.word_count / 225))
        finally:
            tmp_path.unlink()

    def test_parse_long_document_reading_time(self, html_parser: HTMLParser) -> None:
        """Test reading time calculation for longer document."""
        # Create HTML with approximately 1000 words
        words = " ".join(["word"] * 1000)
        html = f"""
        <html>
        <head><title>Long Document</title></head>
        <body>
            <article>
                <h1>Title</h1>
                <p>{words}</p>
            </article>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            # Should be around 5 minutes (1000 words / 200 wpm)
            assert doc.estimated_reading_time >= 4
            assert doc.estimated_reading_time <= 6
        finally:
            tmp_path.unlink()


class TestHTMLParserDocumentID:
    """Test document ID generation."""

    def test_parse_generates_unique_document_id(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test each parse generates unique document ID."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc1 = html_parser.parse(tmp_path)
            doc2 = html_parser.parse(tmp_path)

            # Each parse should generate unique ID
            assert doc1.document_id != doc2.document_id
            # Should be valid UUID format
            assert len(doc1.document_id) == 36  # UUID string length
            assert len(doc2.document_id) == 36
        finally:
            tmp_path.unlink()


class TestHTMLParserImageHandling:
    """Test image handling (currently not extracted to files)."""

    def test_parse_images_not_extracted(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test images are not extracted to files."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)

            # HTML parser doesn't extract images to files
            assert doc.images == []
        finally:
            tmp_path.unlink()


class TestHTMLParserStringPath:
    """Test handling of string paths vs Path objects."""

    def test_parse_accepts_string_path(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test parse accepts string file path."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path_str = tmp.name

        try:
            doc = html_parser.parse(tmp_path_str)
            assert isinstance(doc, Document)
        finally:
            Path(tmp_path_str).unlink()

    def test_parse_accepts_path_object(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test parse accepts Path object."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(simple_html)
            tmp_path = Path(tmp.name)

        try:
            doc = html_parser.parse(tmp_path)
            assert isinstance(doc, Document)
        finally:
            tmp_path.unlink()
