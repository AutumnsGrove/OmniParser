"""
Unit tests for PDF parser utility functions.

Tests the utility functions in src/omniparser/parsers/pdf/utils.py including
timeout enforcement, word counting, and reading time estimation.
"""

import signal
import time
from unittest.mock import patch

import pytest

from omniparser.parsers.pdf.utils import (
    READING_SPEED_WPM,
    count_words,
    estimate_reading_time,
    timeout_context,
)


class TestTimeoutContext:
    """Test timeout_context function."""

    @pytest.mark.skipif(
        not hasattr(signal, "SIGALRM"),
        reason="SIGALRM not available on this platform",
    )
    def test_timeout_context_enforced(self) -> None:
        """Test timeout is enforced when operation takes too long."""
        with pytest.raises(TimeoutError, match="timed out after 1 seconds"):
            with timeout_context(1):
                time.sleep(2)

    @pytest.mark.skipif(
        not hasattr(signal, "SIGALRM"),
        reason="SIGALRM not available on this platform",
    )
    def test_timeout_context_no_timeout(self) -> None:
        """Test timeout context works when operation completes in time."""
        with timeout_context(2):
            time.sleep(0.1)
        # Should complete without exception

    @pytest.mark.skipif(
        hasattr(signal, "SIGALRM"), reason="Test only for platforms without SIGALRM"
    )
    def test_timeout_context_not_available(self) -> None:
        """Test timeout context logs warning on platforms without SIGALRM."""
        with patch("omniparser.parsers.pdf.utils.logger") as mock_logger:
            with timeout_context(1):
                pass
            mock_logger.warning.assert_called_once()

    @pytest.mark.skipif(
        not hasattr(signal, "SIGALRM"),
        reason="SIGALRM not available on this platform",
    )
    def test_timeout_context_restores_handler(self) -> None:
        """Test timeout context restores original signal handler."""
        # Get original handler
        original_handler = signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.signal(signal.SIGALRM, original_handler)

        # Use timeout context
        with timeout_context(1):
            pass

        # Handler should be restored
        current_handler = signal.signal(signal.SIGALRM, signal.SIG_DFL)
        assert current_handler == original_handler


class TestCountWords:
    """Test count_words function."""

    def test_count_words_basic(self) -> None:
        """Test basic word counting."""
        assert count_words("Hello world") == 2
        assert count_words("One two three four five") == 5

    def test_count_words_empty(self) -> None:
        """Test word counting with empty string."""
        assert count_words("") == 0
        assert count_words("   ") == 0
        assert count_words("\n\n\t") == 0

    def test_count_words_with_punctuation(self) -> None:
        """Test word counting with punctuation."""
        assert count_words("Hello, world! How are you?") == 5

    def test_count_words_with_newlines(self) -> None:
        """Test word counting with newlines."""
        text = "Line one\nLine two\nLine three"
        assert count_words(text) == 6

    def test_count_words_with_tabs(self) -> None:
        """Test word counting with tabs."""
        text = "Word1\tWord2\tWord3"
        assert count_words(text) == 3

    def test_count_words_multiple_spaces(self) -> None:
        """Test word counting with multiple spaces."""
        text = "Word1    Word2     Word3"
        assert count_words(text) == 3


class TestEstimateReadingTime:
    """Test estimate_reading_time function."""

    def test_estimate_reading_time_basic(self) -> None:
        """Test basic reading time estimation."""
        # Default reading speed is READING_SPEED_WPM (250 wpm)
        assert estimate_reading_time(250) == 1
        assert estimate_reading_time(500) == 2
        assert estimate_reading_time(1000) == 4

    def test_estimate_reading_time_minimum(self) -> None:
        """Test reading time minimum is 1 minute."""
        assert estimate_reading_time(10) == 1
        assert estimate_reading_time(100) == 1
        assert estimate_reading_time(0) == 1

    def test_estimate_reading_time_custom_rate(self) -> None:
        """Test reading time with custom reading rate."""
        assert estimate_reading_time(400, words_per_minute=200) == 2
        assert estimate_reading_time(600, words_per_minute=300) == 2
        assert estimate_reading_time(1000, words_per_minute=100) == 10

    def test_estimate_reading_time_default_constant(self) -> None:
        """Test reading time uses correct default constant."""
        # Should use READING_SPEED_WPM (250)
        assert estimate_reading_time(READING_SPEED_WPM) == 1
        assert estimate_reading_time(READING_SPEED_WPM * 2) == 2

    def test_estimate_reading_time_rounding(self) -> None:
        """Test reading time rounds down (integer division)."""
        # 375 words / 250 wpm = 1.5, should round down to 1
        assert estimate_reading_time(375) == 1
        # 625 words / 250 wpm = 2.5, should round down to 2
        assert estimate_reading_time(625) == 2
