"""
Unit tests for QR URL fetcher utility.

Tests URL fetching, redirect handling, content extraction, and Wayback fallback.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import requests

from omniparser.utils.qr_url_fetcher import (
    FetchResult,
    fetch_url_content,
    fetch_from_wayback,
    normalize_url,
    _extract_text_from_html,
    _generate_url_variations,
    _fetch_single_url,
    _is_safe_url,
)


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_default_values(self):
        """Test FetchResult default values."""
        result = FetchResult(success=False)
        assert result.success is False
        assert result.content is None
        assert result.status == "failed"
        assert result.notes == []
        assert result.final_url is None
        assert result.source == "original"

    def test_success_result(self):
        """Test creating a successful FetchResult."""
        result = FetchResult(
            success=True,
            content="Test content",
            status="success",
            notes=["Followed 2 redirects"],
            final_url="https://example.com/final",
            source="original",
        )
        assert result.success is True
        assert result.content == "Test content"
        assert len(result.notes) == 1


class TestNormalizeUrl:
    """Tests for URL normalization."""

    def test_add_https_scheme(self):
        """Test adding HTTPS scheme to bare URLs."""
        assert normalize_url("example.com") == "https://example.com"
        assert normalize_url("www.example.com") == "https://www.example.com"

    def test_preserve_existing_scheme(self):
        """Test preserving existing URL schemes."""
        assert normalize_url("https://example.com") == "https://example.com"
        assert normalize_url("http://example.com") == "http://example.com"

    def test_strip_whitespace(self):
        """Test stripping whitespace from URLs."""
        assert normalize_url("  https://example.com  ") == "https://example.com"


class TestGenerateUrlVariations:
    """Tests for URL variation generation."""

    def test_generates_print_version(self):
        """Test generating print version URL."""
        variations = _generate_url_variations("https://example.com/article")
        assert any("/print" in v for v in variations)

    def test_generates_clean_url(self):
        """Test generating URL without query parameters."""
        variations = _generate_url_variations("https://example.com/page?utm=123")
        assert "https://example.com/page" in variations

    def test_generates_mobile_version(self):
        """Test generating mobile version URL."""
        variations = _generate_url_variations("https://example.com/page")
        assert any("m.example.com" in v for v in variations)

    def test_generates_amp_version(self):
        """Test generating AMP version URL."""
        variations = _generate_url_variations("https://example.com/page")
        assert any("/amp" in v for v in variations)

    def test_no_duplicate_print(self):
        """Test not adding /print if already present."""
        variations = _generate_url_variations("https://example.com/print/article")
        # Should not double up print
        print_count = sum(1 for v in variations if "/print/print" in v)
        assert print_count == 0


class TestExtractTextFromHtml:
    """Tests for HTML text extraction."""

    def test_extract_simple_html(self):
        """Test extracting text from simple HTML."""
        html = "<html><body><p>Hello World</p></body></html>"
        text = _extract_text_from_html(html)
        assert "Hello World" in text

    def test_remove_scripts(self):
        """Test removing script tags."""
        html = "<html><body><script>alert('bad')</script><p>Content</p></body></html>"
        text = _extract_text_from_html(html)
        assert "alert" not in text
        assert "Content" in text

    def test_remove_styles(self):
        """Test removing style tags."""
        html = "<html><body><style>.foo{}</style><p>Content</p></body></html>"
        text = _extract_text_from_html(html)
        assert ".foo" not in text
        assert "Content" in text

    def test_extract_from_main(self):
        """Test preferring main content element."""
        html = """
        <html>
        <body>
            <nav>Navigation</nav>
            <main><p>Main Content</p></main>
            <footer>Footer</footer>
        </body>
        </html>
        """
        text = _extract_text_from_html(html)
        assert "Main Content" in text
        # Navigation and footer should be removed
        assert "Navigation" not in text
        assert "Footer" not in text

    def test_extract_from_article(self):
        """Test preferring article element."""
        html = """
        <html>
        <body>
            <header>Header</header>
            <article><p>Article Content</p></article>
        </body>
        </html>
        """
        text = _extract_text_from_html(html)
        assert "Article Content" in text

    def test_handle_empty_html(self):
        """Test handling empty HTML."""
        text = _extract_text_from_html("")
        assert text == ""

    def test_handle_malformed_html(self):
        """Test handling malformed HTML gracefully."""
        html = "<html><body><p>Unclosed"
        text = _extract_text_from_html(html)
        # Should not raise an exception
        assert isinstance(text, str)


class TestFetchSingleUrl:
    """Tests for single URL fetching."""

    @patch('omniparser.utils.qr_url_fetcher.requests.Session')
    def test_successful_fetch(self, mock_session_class):
        """Test successful URL fetch."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.history = []
        mock_response.headers = {"Content-Type": "text/html"}
        # Need >50 chars of content to be considered successful
        mock_response.iter_content.return_value = [
            b"<html><body><p>This is a test content paragraph that contains more than fifty characters to be considered valid content.</p></body></html>"
        ]

        mock_session.get.return_value = mock_response

        result = _fetch_single_url("https://example.com")
        assert result.success is True
        assert "test content" in result.content.lower()

    @patch('omniparser.utils.qr_url_fetcher.requests.Session')
    def test_redirect_tracking(self, mock_session_class):
        """Test that redirects are tracked in notes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/final"
        mock_response.history = [MagicMock(), MagicMock()]  # 2 redirects
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.iter_content.return_value = [b"<p>Content</p>"]

        mock_session.get.return_value = mock_response

        result = _fetch_single_url("https://example.com")
        assert any("redirect" in note.lower() for note in result.notes)

    @patch('omniparser.utils.qr_url_fetcher.requests.Session')
    def test_http_error(self, mock_session_class):
        """Test handling HTTP errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.url = "https://example.com"
        mock_response.history = []

        mock_session.get.return_value = mock_response

        result = _fetch_single_url("https://example.com")
        assert result.success is False
        assert any("404" in note for note in result.notes)

    @patch('omniparser.utils.qr_url_fetcher.requests.Session')
    def test_timeout_handling(self, mock_session_class):
        """Test handling request timeouts."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests.exceptions.Timeout()

        result = _fetch_single_url("https://example.com")
        assert result.success is False
        assert any("timed out" in note.lower() for note in result.notes)

    @patch('omniparser.utils.qr_url_fetcher.requests.Session')
    def test_connection_error_handling(self, mock_session_class):
        """Test handling connection errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Failed")

        result = _fetch_single_url("https://example.com")
        assert result.success is False
        assert any("connection" in note.lower() for note in result.notes)


class TestFetchUrlContent:
    """Tests for main fetch_url_content function."""

    @patch('omniparser.utils.qr_url_fetcher._is_safe_url')
    @patch('omniparser.utils.qr_url_fetcher._fetch_single_url')
    def test_successful_first_attempt(self, mock_fetch, mock_is_safe):
        """Test successful fetch on first attempt."""
        mock_is_safe.return_value = (True, "URL is safe")
        mock_fetch.return_value = FetchResult(
            success=True,
            content="Test content",
            status="success",
        )

        result = fetch_url_content("https://example.com")
        assert result.success is True
        assert result.content == "Test content"

    @patch('omniparser.utils.qr_url_fetcher._is_safe_url')
    @patch('omniparser.utils.qr_url_fetcher._fetch_single_url')
    @patch('omniparser.utils.qr_url_fetcher.fetch_from_wayback')
    def test_wayback_fallback(self, mock_wayback, mock_fetch, mock_is_safe):
        """Test falling back to Wayback Machine."""
        mock_is_safe.return_value = (True, "URL is safe")
        mock_fetch.return_value = FetchResult(success=False, notes=["Failed"])
        mock_wayback.return_value = FetchResult(
            success=True,
            content="Archived content",
            status="success",
            source="wayback",
        )

        result = fetch_url_content(
            "https://example.com",
            try_variations=False,
            try_wayback=True,
        )
        assert result.success is True
        assert result.source == "wayback"

    @patch('omniparser.utils.qr_url_fetcher._is_safe_url')
    @patch('omniparser.utils.qr_url_fetcher._fetch_single_url')
    def test_url_normalization(self, mock_fetch, mock_is_safe):
        """Test that URLs are normalized before fetching."""
        mock_is_safe.return_value = (True, "URL is safe")
        mock_fetch.return_value = FetchResult(success=False, notes=["Failed"])

        fetch_url_content("example.com", try_variations=False, try_wayback=False)

        # Verify the call was made with normalized URL
        call_args = mock_fetch.call_args[0]
        assert call_args[0].startswith("https://")

    @patch('omniparser.utils.qr_url_fetcher._is_safe_url')
    def test_all_attempts_fail(self, mock_is_safe):
        """Test when all fetch attempts fail."""
        mock_is_safe.return_value = (True, "URL is safe")
        with patch('omniparser.utils.qr_url_fetcher._fetch_single_url') as mock_fetch:
            mock_fetch.return_value = FetchResult(success=False, notes=["Failed"])

            result = fetch_url_content(
                "https://example.com",
                try_variations=False,
                try_wayback=False,
            )
            assert result.success is False
            assert result.status == "failed"


class TestFetchFromWayback:
    """Tests for Wayback Machine fetching."""

    @patch('omniparser.utils.qr_url_fetcher.requests.get')
    @patch('omniparser.utils.qr_url_fetcher._fetch_single_url')
    def test_successful_wayback_fetch(self, mock_fetch_single, mock_get):
        """Test successful fetch from Wayback Machine."""
        # Mock Wayback API response
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {
            "archived_snapshots": {
                "closest": {
                    "available": True,
                    "url": "https://web.archive.org/web/20200101/https://example.com",
                    "timestamp": "20200101000000",
                }
            }
        }
        mock_api_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_api_response

        # Mock fetching archived content
        mock_fetch_single.return_value = FetchResult(
            success=True,
            content="Archived content",
            status="success",
        )

        result = fetch_from_wayback("https://example.com")
        assert result.success is True
        assert "Archived content" in result.content
        assert result.source == "wayback"

    @patch('omniparser.utils.qr_url_fetcher.requests.get')
    def test_no_wayback_snapshot(self, mock_get):
        """Test when no Wayback snapshot is available."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"archived_snapshots": {}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_from_wayback("https://example.com")
        assert result.success is False
        assert any("no" in note.lower() and "snapshot" in note.lower()
                   for note in result.notes)

    @patch('omniparser.utils.qr_url_fetcher.requests.get')
    def test_wayback_api_error(self, mock_get):
        """Test handling Wayback API errors."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        result = fetch_from_wayback("https://example.com")
        assert result.success is False
        assert any("error" in note.lower() for note in result.notes)


class TestIntegration:
    """Integration tests for URL fetching pipeline."""

    @patch('omniparser.utils.qr_url_fetcher._is_safe_url')
    def test_fetch_result_notes_accumulate(self, mock_is_safe):
        """Test that notes accumulate through the fetch process."""
        mock_is_safe.return_value = (True, "URL is safe")
        with patch('omniparser.utils.qr_url_fetcher._fetch_single_url') as mock_fetch:
            mock_fetch.return_value = FetchResult(
                success=False,
                notes=["Original failed"],
            )

            result = fetch_url_content(
                "https://example.com",
                try_variations=False,
                try_wayback=False,
            )

            # Should have accumulated notes
            assert len(result.notes) > 0
            assert any("failed" in note.lower() for note in result.notes)


class TestUrlSecurity:
    """Tests for SSRF protection in URL fetching."""

    def test_blocks_localhost(self):
        """Test blocking localhost addresses."""
        is_safe, reason = _is_safe_url("http://127.0.0.1/admin")
        assert is_safe is False
        assert "blocked range" in reason.lower()

    def test_blocks_localhost_hostname(self):
        """Test blocking localhost hostname."""
        is_safe, reason = _is_safe_url("http://localhost/admin")
        assert is_safe is False
        assert "blocked range" in reason.lower()

    def test_blocks_private_class_a(self):
        """Test blocking private Class A addresses (10.x.x.x)."""
        is_safe, reason = _is_safe_url("http://10.0.0.1/internal")
        assert is_safe is False
        assert "blocked range" in reason.lower()

    def test_blocks_private_class_b(self):
        """Test blocking private Class B addresses (172.16-31.x.x)."""
        is_safe, reason = _is_safe_url("http://172.16.0.1/internal")
        assert is_safe is False
        assert "blocked range" in reason.lower()

    def test_blocks_private_class_c(self):
        """Test blocking private Class C addresses (192.168.x.x)."""
        is_safe, reason = _is_safe_url("http://192.168.1.1/router")
        assert is_safe is False
        assert "blocked range" in reason.lower()

    def test_blocks_cloud_metadata(self):
        """Test blocking cloud metadata endpoint."""
        is_safe, reason = _is_safe_url("http://169.254.169.254/latest/meta-data")
        assert is_safe is False
        assert "blocked range" in reason.lower()

    def test_blocks_link_local(self):
        """Test blocking link-local addresses."""
        is_safe, reason = _is_safe_url("http://169.254.1.1/")
        assert is_safe is False
        assert "blocked range" in reason.lower()

    def test_blocks_file_scheme(self):
        """Test blocking file:// URLs."""
        is_safe, reason = _is_safe_url("file:///etc/passwd")
        assert is_safe is False
        assert "blocked scheme" in reason.lower()

    def test_blocks_ftp_scheme(self):
        """Test blocking ftp:// URLs."""
        is_safe, reason = _is_safe_url("ftp://example.com/file")
        assert is_safe is False
        assert "blocked scheme" in reason.lower()

    @patch('omniparser.utils.qr_url_fetcher.socket.getaddrinfo')
    def test_allows_valid_https(self, mock_getaddrinfo):
        """Test allowing valid HTTPS URLs."""
        # Mock DNS to return a public IP
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('93.184.216.34', 0))]
        is_safe, reason = _is_safe_url("https://example.com/page")
        assert is_safe is True
        assert "safe" in reason.lower()

    @patch('omniparser.utils.qr_url_fetcher.socket.getaddrinfo')
    def test_allows_valid_http(self, mock_getaddrinfo):
        """Test allowing valid HTTP URLs."""
        # Mock DNS to return a public IP
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('93.184.216.34', 0))]
        is_safe, reason = _is_safe_url("http://example.com/page")
        assert is_safe is True
        assert "safe" in reason.lower()

    def test_blocklist_blocks_domain(self):
        """Test that blocklist blocks specified domains."""
        is_safe, reason = _is_safe_url(
            "https://example.com/page",
            blocked_domains=["example.com"]
        )
        assert is_safe is False
        assert "blocklist" in reason.lower()

    def test_blocklist_blocks_subdomain(self):
        """Test that blocklist blocks subdomains."""
        is_safe, reason = _is_safe_url(
            "https://api.example.com/data",
            blocked_domains=["example.com"]
        )
        assert is_safe is False
        assert "blocklist" in reason.lower()

    def test_allowlist_restricts_domains(self):
        """Test that allowlist restricts to specified domains."""
        is_safe, reason = _is_safe_url(
            "https://untrusted.com/page",
            allowed_domains=["trusted.com"]
        )
        assert is_safe is False
        assert "allowlist" in reason.lower()

    @patch('omniparser.utils.qr_url_fetcher.socket.getaddrinfo')
    def test_allowlist_allows_specified_domain(self, mock_getaddrinfo):
        """Test that allowlist allows specified domains."""
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('93.184.216.34', 0))]
        is_safe, reason = _is_safe_url(
            "https://trusted.com/page",
            allowed_domains=["trusted.com"]
        )
        assert is_safe is True

    @patch('omniparser.utils.qr_url_fetcher.socket.getaddrinfo')
    def test_allowlist_allows_subdomain(self, mock_getaddrinfo):
        """Test that allowlist allows subdomains of specified domains."""
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('93.184.216.34', 0))]
        is_safe, reason = _is_safe_url(
            "https://api.trusted.com/data",
            allowed_domains=["trusted.com"]
        )
        assert is_safe is True

    @patch('omniparser.utils.qr_url_fetcher._is_safe_url')
    @patch('omniparser.utils.qr_url_fetcher._fetch_single_url')
    def test_fetch_url_content_blocks_unsafe(self, mock_fetch, mock_is_safe):
        """Test that fetch_url_content respects SSRF protection."""
        mock_is_safe.return_value = (False, "IP address is in blocked range")

        result = fetch_url_content("http://10.0.0.1/admin")

        assert result.success is False
        assert result.status == "blocked"
        assert any("security" in note.lower() for note in result.notes)
        # Should not attempt to fetch
        mock_fetch.assert_not_called()

    def test_handles_invalid_hostname(self):
        """Test handling URLs with no hostname."""
        is_safe, reason = _is_safe_url("http:///path")
        assert is_safe is False
        assert "hostname" in reason.lower()

    def test_handles_dns_resolution_failure(self):
        """Test handling DNS resolution failures."""
        is_safe, reason = _is_safe_url("http://nonexistent.invalid/page")
        assert is_safe is False
        assert "dns" in reason.lower() or "resolution" in reason.lower()
