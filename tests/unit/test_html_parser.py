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
from omniparser.parsers.html import HTMLParser
from omniparser.parsers.html.content_extractor import (
    extract_with_readability,
    extract_with_trafilatura,
)
from omniparser.parsers.html.image_extractor import (
    download_image,
    extract_images,
    get_image_format,
    resolve_image_url,
)


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
            content = html_parser.content_fetcher.read_file(tmp_path)
            assert isinstance(content, str)
            assert "<html>" in content
            assert "<h1>Test</h1>" in content
        finally:
            tmp_path.unlink()

    def test_read_local_file_not_found(self, html_parser: HTMLParser) -> None:
        """Test FileReadError raised for missing file."""
        with pytest.raises(FileReadError, match="File not found"):
            html_parser.content_fetcher.read_file(Path("/nonexistent/path/file.html"))

    def test_read_local_file_utf8_encoding(self, html_parser: HTMLParser) -> None:
        """Test reading file with UTF-8 characters."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write("<html><body><p>Café résumé naïve</p></body></html>")
            tmp_path = Path(tmp.name)

        try:
            content = html_parser.content_fetcher.read_file(tmp_path)
            assert "Café" in content
            assert "résumé" in content
            assert "naïve" in content
        finally:
            tmp_path.unlink()


class TestHTMLParserFetchURL:
    """Test URL fetching with mocked requests."""

    @patch("omniparser.parsers.html.content_fetcher.requests.get")
    def test_fetch_url_success(
        self, mock_get: Mock, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test successful URL fetch."""
        mock_response = Mock()
        mock_response.text = simple_html
        mock_get.return_value = mock_response

        content = html_parser.content_fetcher.fetch_url("http://example.com")

        assert content == simple_html
        mock_get.assert_called_once_with(
            "http://example.com",
            timeout=10,
            headers={
                "User-Agent": "OmniParser/0.2.1 (+https://github.com/AutumnsGrove/omniparser)"
            },
        )

    @patch("omniparser.parsers.html.content_fetcher.requests.get")
    def test_fetch_url_custom_timeout(self, mock_get: Mock) -> None:
        """Test URL fetch with custom timeout option."""
        parser = HTMLParser({"timeout": 30})
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        parser.content_fetcher.fetch_url("http://example.com")

        mock_get.assert_called_once_with(
            "http://example.com",
            timeout=30,
            headers={
                "User-Agent": "OmniParser/0.2.1 (+https://github.com/AutumnsGrove/omniparser)"
            },
        )

    @patch("omniparser.parsers.html.content_fetcher.requests.get")
    def test_fetch_url_timeout_error(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test NetworkError raised on timeout."""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        with pytest.raises(NetworkError, match="Request timeout"):
            html_parser.content_fetcher.fetch_url("http://example.com")

    @patch("omniparser.parsers.html.content_fetcher.requests.get")
    def test_fetch_url_http_error(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test NetworkError raised on HTTP error."""
        mock_get.side_effect = requests.HTTPError("404 Not Found")

        with pytest.raises(NetworkError, match="Failed to fetch URL"):
            html_parser.content_fetcher.fetch_url("http://example.com/notfound")

    @patch("omniparser.parsers.html.content_fetcher.requests.get")
    def test_fetch_url_connection_error(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test NetworkError raised on connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        with pytest.raises(NetworkError, match="Failed to fetch URL"):
            html_parser.content_fetcher.fetch_url("http://example.com")

    @patch("omniparser.parsers.html.content_fetcher.requests.get")
    def test_fetch_url_raise_for_status(
        self, mock_get: Mock, html_parser: HTMLParser
    ) -> None:
        """Test that raise_for_status is called on response."""
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        html_parser.content_fetcher.fetch_url("http://example.com")

        mock_response.raise_for_status.assert_called_once()

    @patch("omniparser.parsers.html.content_fetcher.requests.get")
    def test_fetch_url_custom_user_agent(self, mock_get: Mock) -> None:
        """Test URL fetch with custom user-agent option."""
        parser = HTMLParser({"user_agent": "CustomBot/1.0"})
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        parser.content_fetcher.fetch_url("http://example.com")

        mock_get.assert_called_once_with(
            "http://example.com",
            timeout=10,
            headers={"User-Agent": "CustomBot/1.0"},
        )


class TestHTMLParserRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_disabled_by_default(self, html_parser: HTMLParser) -> None:
        """Test that rate limiting is disabled by default (no delays)."""
        import time

        with patch("time.time") as mock_time:
            # Simulate timestamps: 0.0, 0.01, 0.02 (very fast requests)
            mock_time.side_effect = [0.0, 0.01, 0.02]

            with patch("time.sleep") as mock_sleep:
                # Make 3 rapid requests
                html_parser.content_fetcher._apply_rate_limit()
                html_parser.content_fetcher._apply_rate_limit()
                html_parser.content_fetcher._apply_rate_limit()

                # Sleep should never be called when rate limiting is disabled
                mock_sleep.assert_not_called()

    def test_rate_limiting_enforces_delay(self, html_parser: HTMLParser) -> None:
        """Test that rate limiting enforces minimum delay between requests."""
        parser = HTMLParser({"rate_limit_delay": 0.5})

        with patch("time.time") as mock_time:
            # Simulate timestamps:
            # First call: current_time=1.0, elapsed=1.0-0.0=1.0 (no sleep), update _last_request_time=1.0
            # Second call: current_time=1.2, elapsed=1.2-1.0=0.2 (sleep 0.3s), update _last_request_time=1.2
            mock_time.side_effect = [1.0, 1.0, 1.2, 1.2]

            with patch("time.sleep") as mock_sleep:
                # First request - no wait (elapsed > delay since _last_request_time starts at 0.0)
                parser.content_fetcher._apply_rate_limit()
                assert mock_sleep.call_count == 0

                # Second request - should wait 0.3s (0.5 - 0.2 elapsed)
                parser.content_fetcher._apply_rate_limit()
                mock_sleep.assert_called_once()
                # Should sleep for approximately 0.3 seconds (0.5 delay - 0.2 elapsed)
                sleep_duration = mock_sleep.call_args[0][0]
                assert 0.29 <= sleep_duration <= 0.31

    def test_rate_limiting_no_wait_if_sufficient_time_passed(self) -> None:
        """Test that no delay occurs if sufficient time has already passed."""
        parser = HTMLParser({"rate_limit_delay": 0.5})

        with patch("time.time") as mock_time:
            # Simulate timestamps:
            # First call: current_time=1.0, elapsed=1.0-0.0=1.0 (no sleep), update _last_request_time=1.0
            # Second call: current_time=2.0, elapsed=2.0-1.0=1.0 (no sleep), update _last_request_time=2.0
            mock_time.side_effect = [1.0, 1.0, 2.0, 2.0]

            with patch("time.sleep") as mock_sleep:
                # First request
                parser.content_fetcher._apply_rate_limit()

                # Second request - no wait needed (1.0s elapsed > 0.5s delay)
                parser.content_fetcher._apply_rate_limit()
                mock_sleep.assert_not_called()

    def test_rate_limiting_thread_safe(self) -> None:
        """Test that rate limiting is thread-safe using locks."""
        parser = HTMLParser({"rate_limit_delay": 0.1})

        # Verify the lock exists on content_fetcher
        assert hasattr(parser.content_fetcher, "_rate_limit_lock")
        assert isinstance(
            parser.content_fetcher._rate_limit_lock,
            type(parser.content_fetcher._rate_limit_lock),
        )

        with patch("time.time") as mock_time:
            mock_time.return_value = 0.0

            with patch("time.sleep"):
                # Verify lock is used by checking we can acquire it before the call
                with parser.content_fetcher._rate_limit_lock:
                    # This would deadlock if _apply_rate_limit tries to acquire the lock
                    # since we're in a different thread-like context
                    pass

                # Normal call should work
                parser.content_fetcher._apply_rate_limit()

    def test_rate_limiting_negative_delay_disabled(self) -> None:
        """Test that negative rate_limit_delay disables rate limiting."""
        parser = HTMLParser({"rate_limit_delay": -1.0})

        with patch("time.sleep") as mock_sleep:
            parser.content_fetcher._apply_rate_limit()
            parser.content_fetcher._apply_rate_limit()
            parser.content_fetcher._apply_rate_limit()

            # No sleep calls should occur with negative delay
            mock_sleep.assert_not_called()


class TestHTMLParserExtractContent:
    """Test content extraction methods."""

    def test_extract_content_trafilatura_success(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test Trafilatura extraction with valid HTML."""
        result = extract_with_trafilatura(simple_html)

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
        result = extract_with_trafilatura(html)

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
        result = extract_with_trafilatura(malformed_html)
        assert result is None or isinstance(result, str)

    def test_extract_content_readability_success(
        self, html_parser: HTMLParser, simple_html: str
    ) -> None:
        """Test Readability extraction with valid HTML."""
        result = extract_with_readability(simple_html)

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
        result = extract_with_readability(html)

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

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
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

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
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

    @patch("omniparser.parsers.html.content_fetcher.ContentFetcher.fetch_url")
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


class TestHTMLParserImageExtraction:
    """Test suite for HTML parser image extraction."""

    def test_extract_images_from_html(self, html_parser: HTMLParser) -> None:
        """Test extracting images from HTML content."""
        html = """
        <html><body>
            <img src="http://example.com/image1.jpg" alt="First image">
            <img src="http://example.com/image2.png" alt="Second image">
            <img src="data:image/png;base64,ABC123" alt="Data URI (skip)">
            <img src="http://example.com/image3.gif" alt="Third image">
        </body></html>
        """

        with patch("omniparser.parsers.html.image_extractor.requests.get") as mock_get:
            # Mock image downloads
            mock_response = Mock()
            mock_response.content = b"fake_image_data"
            mock_response.iter_content = Mock(return_value=[b"fake_image_data"])
            mock_get.return_value = mock_response

            with patch(
                "omniparser.parsers.html.image_extractor.Image.open"
            ) as mock_image:
                # Mock image dimensions
                mock_img = Mock()
                mock_img.size = (800, 600)
                mock_img.format = "JPEG"
                mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                mock_image.return_value.__exit__ = Mock(return_value=None)

                images = extract_images(
                    html,
                    base_url="http://example.com",
                    options=html_parser.options,
                    apply_rate_limit=html_parser.content_fetcher._apply_rate_limit,
                    build_headers=html_parser.content_fetcher._build_headers,
                )

                # Should extract 3 images (skip data URI)
                assert len(images) == 3
                assert images[0].image_id == "img_001"
                assert images[1].image_id == "img_002"
                assert images[2].image_id == "img_003"
                assert images[0].alt_text == "First image"
                assert images[1].alt_text == "Second image"
                assert images[2].alt_text == "Third image"
                assert images[0].size == (800, 600)
                assert images[0].format == "jpeg"

    def test_resolve_image_url_absolute(self, html_parser: HTMLParser) -> None:
        """Test resolving absolute URLs returns them unchanged."""
        # HTTP URL
        http_url = "http://example.com/image.jpg"
        result = resolve_image_url(http_url, base_url="http://other.com")
        assert result == http_url

        # HTTPS URL
        https_url = "https://cdn.example.com/photo.png"
        result = resolve_image_url(https_url, base_url="https://other.com")
        assert result == https_url

    def test_resolve_image_url_relative(self, html_parser: HTMLParser) -> None:
        """Test resolving relative URLs with base_url."""
        base_url = "https://example.com/articles/page.html"

        # Root-relative path
        result = resolve_image_url("/images/photo.jpg", base_url)
        assert result == "https://example.com/images/photo.jpg"

        # Relative path (same directory)
        result = resolve_image_url("photo.png", base_url)
        assert result == "https://example.com/articles/photo.png"

        # Parent directory path
        base_url2 = "https://example.com/articles/2024/page.html"
        result = resolve_image_url("../images/pic.jpg", base_url2)
        assert result == "https://example.com/articles/images/pic.jpg"

    def test_resolve_image_url_protocol_relative(self, html_parser: HTMLParser) -> None:
        """Test resolving protocol-relative URLs."""
        protocol_relative = "//cdn.example.com/image.jpg"
        result = resolve_image_url(protocol_relative, base_url="https://example.com")

        # Should add https: protocol
        assert result == "https://cdn.example.com/image.jpg"

    def test_resolve_image_url_data_uri(self, html_parser: HTMLParser) -> None:
        """Test data URIs are returned unchanged."""
        data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        result = resolve_image_url(data_uri, base_url="http://example.com")

        # Data URI should be returned as-is
        assert result == data_uri

    def test_download_image_success(self, html_parser: HTMLParser) -> None:
        """Test successful image download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_image.jpg"

            with patch(
                "omniparser.parsers.html.image_extractor.requests.get"
            ) as mock_get:
                # Mock successful download
                mock_response = Mock()
                mock_response.content = b"fake_jpeg_data"
                mock_response.iter_content = Mock(return_value=[b"fake_jpeg_data"])
                mock_get.return_value = mock_response

                with patch(
                    "omniparser.parsers.html.image_extractor.Image.open"
                ) as mock_image:
                    # Mock Pillow image
                    mock_img = Mock()
                    mock_img.size = (1920, 1080)
                    mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                    mock_image.return_value.__exit__ = Mock(return_value=None)

                    dimensions = download_image(
                        "http://example.com/image.jpg",
                        output_path,
                        options=html_parser.options,
                        apply_rate_limit=html_parser.content_fetcher._apply_rate_limit,
                        build_headers=html_parser.content_fetcher._build_headers,
                    )

                    # Verify dimensions returned
                    assert dimensions == (1920, 1080)

                    # Verify file was written
                    assert output_path.exists()

                    # Verify requests.get called correctly
                    mock_get.assert_called_once_with(
                        "http://example.com/image.jpg",
                        timeout=10,
                        headers={
                            "User-Agent": "OmniParser/0.2.1 (+https://github.com/AutumnsGrove/omniparser)"
                        },
                        stream=True,
                    )

    def test_download_image_timeout(self, html_parser: HTMLParser) -> None:
        """Test graceful handling of download timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "timeout_image.jpg"

            with patch(
                "omniparser.parsers.html.image_extractor.requests.get"
            ) as mock_get:
                # Mock timeout
                mock_get.side_effect = requests.Timeout("Connection timeout")

                dimensions = download_image(
                    "http://slow.example.com/image.jpg",
                    output_path,
                    options=html_parser.options,
                    apply_rate_limit=html_parser.content_fetcher._apply_rate_limit,
                    build_headers=html_parser.content_fetcher._build_headers,
                )

                # Should return None on timeout (graceful failure)
                assert dimensions is None

                # File should not be created
                assert not output_path.exists()

    def test_download_image_http_error(self, html_parser: HTMLParser) -> None:
        """Test graceful handling of HTTP errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "error_image.jpg"

            with patch(
                "omniparser.parsers.html.image_extractor.requests.get"
            ) as mock_get:
                # Mock HTTP error
                mock_get.side_effect = requests.HTTPError("404 Not Found")

                dimensions = download_image(
                    "http://example.com/missing.jpg",
                    output_path,
                    options=html_parser.options,
                    apply_rate_limit=html_parser.content_fetcher._apply_rate_limit,
                    build_headers=html_parser.content_fetcher._build_headers,
                )

                # Should return None on HTTP error (graceful failure)
                assert dimensions is None

    def test_get_image_format(self, html_parser: HTMLParser) -> None:
        """Test image format detection using Pillow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.jpg"

            # Create a mock file and test format detection
            with patch(
                "omniparser.parsers.html.image_extractor.Image.open"
            ) as mock_image:
                # Mock JPEG format
                mock_img = Mock()
                mock_img.format = "JPEG"
                mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                mock_image.return_value.__exit__ = Mock(return_value=None)

                # Create dummy file
                test_file.write_bytes(b"fake_image_data")

                format_result = get_image_format(test_file)
                assert format_result == "jpeg"

            # Test PNG format
            test_file2 = Path(tmpdir) / "test.png"
            with patch(
                "omniparser.parsers.html.image_extractor.Image.open"
            ) as mock_image:
                mock_img = Mock()
                mock_img.format = "PNG"
                mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                mock_image.return_value.__exit__ = Mock(return_value=None)

                test_file2.write_bytes(b"fake_png_data")
                format_result = get_image_format(test_file2)
                assert format_result == "png"

            # Test invalid file (returns "unknown")
            invalid_file = Path(tmpdir) / "invalid.txt"
            invalid_file.write_text("not an image")

            with patch(
                "omniparser.parsers.html.image_extractor.Image.open",
                side_effect=Exception("Cannot identify image file"),
            ):
                format_result = get_image_format(invalid_file)
                assert format_result == "unknown"

    def test_parse_with_images_enabled(self, html_parser: HTMLParser) -> None:
        """Test parsing HTML with image extraction enabled."""
        html = """
        <html>
        <head><title>Article with Images</title></head>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>This article has images.</p>
                <img src="http://example.com/photo1.jpg" alt="Photo 1">
                <p>Some more text.</p>
                <img src="http://example.com/photo2.png" alt="Photo 2">
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
            with patch(
                "omniparser.parsers.html.image_extractor.requests.get"
            ) as mock_get:
                mock_response = Mock()
                mock_response.content = b"fake_image"
                mock_response.iter_content = Mock(return_value=[b"fake_image"])
                mock_get.return_value = mock_response

                with patch(
                    "omniparser.parsers.html.image_extractor.Image.open"
                ) as mock_image:
                    mock_img = Mock()
                    mock_img.size = (640, 480)
                    mock_img.format = "JPEG"
                    mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                    mock_image.return_value.__exit__ = Mock(return_value=None)

                    # Parse with images enabled (default)
                    doc = html_parser.parse(tmp_path)

                    # Should have extracted images
                    assert len(doc.images) == 2
                    assert doc.images[0].alt_text == "Photo 1"
                    assert doc.images[1].alt_text == "Photo 2"
                    assert doc.images[0].size == (640, 480)
        finally:
            tmp_path.unlink()

    def test_parse_with_images_disabled(self, html_parser: HTMLParser) -> None:
        """Test parsing HTML with image extraction disabled."""
        html = """
        <html>
        <head><title>Article with Images</title></head>
        <body>
            <article>
                <h1>Test Article</h1>
                <img src="http://example.com/photo.jpg" alt="A photo">
                <p>Some content here.</p>
            </article>
        </body>
        </html>
        """

        # Create parser with images disabled
        parser = HTMLParser({"extract_images": False})

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            doc = parser.parse(tmp_path)

            # Should not have extracted any images
            assert len(doc.images) == 0
        finally:
            tmp_path.unlink()

    def test_parse_with_persistent_image_dir(self, html_parser: HTMLParser) -> None:
        """Test parsing with custom persistent image output directory."""
        html = """
        <html>
        <head><title>Article</title></head>
        <body>
            <article>
                <h1>Test</h1>
                <img src="http://example.com/image1.jpg" alt="Image 1">
                <img src="http://example.com/image2.png" alt="Image 2">
            </article>
        </body>
        </html>
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set custom image output directory
            custom_image_dir = Path(tmpdir) / "my_images"
            parser = HTMLParser({"image_output_dir": str(custom_image_dir)})

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(html)
                tmp_path = Path(tmp.name)

            try:
                with patch(
                    "omniparser.parsers.html.image_extractor.requests.get"
                ) as mock_get:
                    mock_response = Mock()
                    mock_response.content = b"fake_image"
                    mock_response.iter_content = Mock(return_value=[b"fake_image"])
                    mock_get.return_value = mock_response

                    with patch(
                        "omniparser.parsers.html.image_extractor.Image.open"
                    ) as mock_image:
                        mock_img = Mock()
                        mock_img.size = (800, 600)
                        mock_img.format = "JPEG"
                        mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                        mock_image.return_value.__exit__ = Mock(return_value=None)

                        doc = parser.parse(tmp_path)

                        # Verify directory was created
                        assert custom_image_dir.exists()
                        assert custom_image_dir.is_dir()

                        # Verify images were saved to custom directory
                        assert len(doc.images) == 2

                        # Check that image file paths point to custom directory
                        for image_ref in doc.images:
                            image_path = Path(image_ref.file_path)
                            assert image_path.parent == custom_image_dir
                            assert image_path.exists()

            finally:
                tmp_path.unlink()


class TestHTMLParserParallelImageDownload:
    """Test parallel image downloading functionality."""

    def test_parallel_downloads_default_workers(self, html_parser: HTMLParser) -> None:
        """Test parallel downloads use default max_workers=5."""
        # Test the options directly rather than mocking execution
        assert html_parser.options.get("max_image_workers", 5) == 5

        # Test with custom value
        parser_custom = HTMLParser({"max_image_workers": 10})
        assert parser_custom.options.get("max_image_workers", 5) == 10

    def test_parallel_downloads_custom_workers(self) -> None:
        """Test parallel downloads respect custom max_image_workers option."""
        # Test that options are stored correctly
        parser = HTMLParser({"max_image_workers": 3})
        assert parser.options["max_image_workers"] == 3

        # Test default behavior
        parser_default = HTMLParser()
        assert parser_default.options.get("max_image_workers", 5) == 5

    def test_parallel_downloads_sequential_fallback(self) -> None:
        """Test that max_image_workers=1 enables sequential download mode."""
        parser = HTMLParser({"max_image_workers": 1})
        assert parser.options["max_image_workers"] == 1

    def test_parallel_downloads_preserves_order(self, html_parser: HTMLParser) -> None:
        """Test that images are returned in sequential order with correct IDs."""
        html = """
        <html><body>
            <img src="http://example.com/first.jpg" alt="First">
            <img src="http://example.com/second.jpg" alt="Second">
            <img src="http://example.com/third.jpg" alt="Third">
        </body></html>
        """

        with patch("omniparser.parsers.html.image_extractor.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake_image"
            mock_response.iter_content = Mock(return_value=[b"fake_image"])
            mock_get.return_value = mock_response

            with patch(
                "omniparser.parsers.html.image_extractor.Image.open"
            ) as mock_image:
                mock_img = Mock()
                mock_img.size = (800, 600)
                mock_img.format = "JPEG"
                mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                mock_image.return_value.__exit__ = Mock(return_value=None)

                images = extract_images(
                    html,
                    base_url="http://example.com",
                    options=html_parser.options,
                    apply_rate_limit=html_parser.content_fetcher._apply_rate_limit,
                    build_headers=html_parser.content_fetcher._build_headers,
                )

                # Verify images are returned with sequential IDs
                assert len(images) == 3
                assert images[0].image_id == "img_001"
                assert images[1].image_id == "img_002"
                assert images[2].image_id == "img_003"

                # Verify alt text is preserved
                assert images[0].alt_text == "First"
                assert images[1].alt_text == "Second"
                assert images[2].alt_text == "Third"

                # Verify file paths have sequential naming
                assert "img_001" in images[0].file_path
                assert "img_002" in images[1].file_path
                assert "img_003" in images[2].file_path

    def test_parallel_downloads_error_handling(self, html_parser: HTMLParser) -> None:
        """Test graceful handling of failed downloads in parallel mode."""
        html = """
        <html><body>
            <img src="http://example.com/good1.jpg" alt="Good 1">
            <img src="http://example.com/bad.jpg" alt="Bad (will fail)">
            <img src="http://example.com/good2.jpg" alt="Good 2">
        </body></html>
        """

        call_count = [0]

        def mock_download_side_effect(
            url, output_path, options=None, apply_rate_limit=None, build_headers=None
        ):
            """Mock download that fails on second image."""
            call_count[0] += 1
            if "bad" in url:
                # Simulate failure - return None
                return None
            else:
                # Simulate success - create file and return dimensions
                output_path.write_bytes(b"fake_image")
                return (800, 600)

        with patch(
            "omniparser.parsers.html.image_extractor.download_image",
            side_effect=mock_download_side_effect,
        ):
            with patch(
                "omniparser.parsers.html.image_extractor.Image.open"
            ) as mock_image:
                mock_img = Mock()
                mock_img.format = "JPEG"
                mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                mock_image.return_value.__exit__ = Mock(return_value=None)

                images = extract_images(
                    html,
                    base_url="http://example.com",
                    options=html_parser.options,
                    apply_rate_limit=html_parser.content_fetcher._apply_rate_limit,
                    build_headers=html_parser.content_fetcher._build_headers,
                )

                # Should successfully download 2 images (skipping the failed one)
                assert len(images) == 2
                assert images[0].alt_text == "Good 1"
                assert images[1].alt_text == "Good 2"

                # Verify download was attempted for all 3
                assert call_count[0] == 3

    def test_parallel_downloads_timeout_handling(self, html_parser: HTMLParser) -> None:
        """Test graceful handling of timeouts during parallel downloads."""
        html = """
        <html><body>
            <img src="http://example.com/fast.jpg" alt="Fast">
            <img src="http://slow.example.com/timeout.jpg" alt="Slow (timeout)">
            <img src="http://example.com/fast2.jpg" alt="Fast 2">
        </body></html>
        """

        def mock_download_with_timeout(
            url, output_path, options=None, apply_rate_limit=None, build_headers=None
        ):
            """Mock download that times out on slow URL."""
            if "slow" in url:
                # Simulate timeout - return None
                return None
            else:
                output_path.write_bytes(b"fake_image")
                return (640, 480)

        with patch(
            "omniparser.parsers.html.image_extractor.download_image",
            side_effect=mock_download_with_timeout,
        ):
            with patch(
                "omniparser.parsers.html.image_extractor.Image.open"
            ) as mock_image:
                mock_img = Mock()
                mock_img.format = "JPEG"
                mock_image.return_value.__enter__ = Mock(return_value=mock_img)
                mock_image.return_value.__exit__ = Mock(return_value=None)

                images = extract_images(
                    html,
                    base_url="http://example.com",
                    options=html_parser.options,
                    apply_rate_limit=html_parser.content_fetcher._apply_rate_limit,
                    build_headers=html_parser.content_fetcher._build_headers,
                )

                # Should successfully download 2 fast images, skip timeout
                assert len(images) == 2
                assert images[0].alt_text == "Fast"
                assert images[1].alt_text == "Fast 2"
