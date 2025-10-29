"""
Unit tests for AI-powered summarization processor.

Tests summarization with mocked AI responses.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from omniparser.models import Chapter, Document, Metadata, ProcessingInfo
from omniparser.processors.ai_summarizer import (
    summarize_chapter,
    summarize_document,
)


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    metadata = Metadata(
        title="The Art of Programming",
        author="Jane Smith",
        original_format="epub",
    )

    chapter = Chapter(
        chapter_id=1,
        title="Introduction",
        content="This chapter introduces the fundamental concepts of programming.",
        start_position=0,
        end_position=100,
        word_count=50,
        level=1,
    )

    processing_info = ProcessingInfo(
        parser_used="EPUBParser",
        parser_version="1.0.0",
        processing_time=1.0,
        timestamp=datetime.now(),
    )

    return Document(
        document_id="test_doc_001",
        content="A comprehensive guide to programming covering algorithms, data structures, "
        "and software design patterns. Perfect for beginners and experienced developers.",
        chapters=[chapter],
        images=[],
        metadata=metadata,
        processing_info=processing_info,
        word_count=1000,
        estimated_reading_time=5,
    )


class TestSummarizeDocument:
    """Tests for summarize_document function."""

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_concise(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test concise summarization."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = (
            "This book is a comprehensive programming guide covering "
            "algorithms and design patterns for developers."
        )
        mock_ai_config.return_value = mock_instance

        summary = summarize_document(sample_document, style="concise")

        assert isinstance(summary, str)
        assert len(summary) > 0
        mock_instance.generate.assert_called_once()

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_detailed(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test detailed summarization."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = (
            "This comprehensive programming guide covers fundamental concepts "
            "including algorithms, data structures, and software design patterns. "
            "The book is suitable for both beginners learning programming basics "
            "and experienced developers looking to deepen their knowledge."
        )
        mock_ai_config.return_value = mock_instance

        summary = summarize_document(sample_document, style="detailed")

        assert isinstance(summary, str)
        assert len(summary) > 0

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_bullet(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test bullet-point summarization."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = """- Covers programming fundamentals
- Explains algorithms and data structures
- Discusses software design patterns
- Suitable for beginners and experienced developers"""
        mock_ai_config.return_value = mock_instance

        summary = summarize_document(sample_document, style="bullet")

        assert isinstance(summary, str)
        assert "-" in summary  # Should contain bullet points

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_invalid_style(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test that invalid style raises ValueError."""
        with pytest.raises(ValueError, match="Invalid style"):
            summarize_document(sample_document, style="invalid_style")

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_with_custom_ai_options(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test summarization with custom AI options."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Summary text"
        mock_ai_config.return_value = mock_instance

        ai_options = {"ai_provider": "ollama", "ai_model": "llama3.2:latest"}
        summary = summarize_document(sample_document, ai_options=ai_options)

        mock_ai_config.assert_called_once_with(ai_options)
        assert isinstance(summary, str)

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_uses_metadata(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test that summarization includes document metadata in prompt."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Summary"
        mock_ai_config.return_value = mock_instance

        summarize_document(sample_document)

        call_args = mock_instance.generate.call_args
        prompt = call_args[0][0]

        assert sample_document.metadata.title in prompt
        assert sample_document.metadata.author in prompt


class TestSummarizeChapter:
    """Tests for summarize_chapter function."""

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_chapter_success(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test successful chapter summarization."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = (
            "This chapter introduces fundamental programming concepts."
        )
        mock_ai_config.return_value = mock_instance

        summary = summarize_chapter(sample_document, chapter_id=1)

        assert isinstance(summary, str)
        assert len(summary) > 0

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_chapter_not_found(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test error when chapter is not found."""
        with pytest.raises(ValueError, match="Chapter .* not found"):
            summarize_chapter(sample_document, chapter_id=999)

    @patch("omniparser.processors.ai_summarizer.AIConfig")
    def test_summarize_chapter_uses_full_content(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test that chapter summary uses full chapter content."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Summary"
        mock_ai_config.return_value = mock_instance

        summarize_chapter(sample_document, chapter_id=1)

        call_args = mock_instance.generate.call_args
        prompt = call_args[0][0]

        # Should include chapter content
        chapter = sample_document.get_chapter(1)
        assert chapter.content in prompt
