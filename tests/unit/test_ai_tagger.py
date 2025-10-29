"""
Unit tests for AI-powered auto-tagging processor.

Tests tag generation with mocked AI responses.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from omniparser.models import Document, Metadata, ProcessingInfo
from omniparser.processors.ai_tagger import (
    _parse_tags,
    generate_tags,
    generate_tags_batch,
)


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    metadata = Metadata(
        title="Python Programming Guide",
        author="John Doe",
        original_format="epub",
    )

    processing_info = ProcessingInfo(
        parser_used="EPUBParser",
        parser_version="1.0.0",
        processing_time=1.0,
        timestamp=datetime.now(),
    )

    return Document(
        document_id="test_doc_001",
        content="This is a comprehensive guide to Python programming. "
        "It covers topics like data structures, algorithms, and web development.",
        chapters=[],
        images=[],
        metadata=metadata,
        processing_info=processing_info,
        word_count=500,
        estimated_reading_time=3,
    )


class TestParseTags:
    """Unit tests for _parse_tags helper function."""

    def test_parse_simple_tags(self) -> None:
        """Test parsing simple comma-separated tags."""
        response = "python, programming, tutorial, guide, beginner"
        tags = _parse_tags(response, max_tags=10)

        assert len(tags) == 5
        assert "python" in tags
        assert "programming" in tags
        assert "tutorial" in tags

    def test_parse_tags_with_whitespace(self) -> None:
        """Test parsing tags with extra whitespace."""
        response = "  python  ,   programming  ,  tutorial  "
        tags = _parse_tags(response, max_tags=10)

        assert len(tags) == 3
        assert tags == ["python", "programming", "tutorial"]

    def test_parse_tags_with_quotes(self) -> None:
        """Test parsing tags that include quotes."""
        response = '"python", "programming", "data science"'
        tags = _parse_tags(response, max_tags=10)

        assert "python" in tags
        assert "programming" in tags
        assert "data science" in tags

    def test_parse_tags_max_limit(self) -> None:
        """Test that max_tags limit is enforced."""
        response = "tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8"
        tags = _parse_tags(response, max_tags=5)

        assert len(tags) == 5
        assert tags == ["tag1", "tag2", "tag3", "tag4", "tag5"]

    def test_parse_tags_removes_duplicates(self) -> None:
        """Test that duplicate tags are removed."""
        response = "python, programming, python, coding, programming"
        tags = _parse_tags(response, max_tags=10)

        assert len(tags) == 3
        assert tags.count("python") == 1
        assert tags.count("programming") == 1

    def test_parse_tags_lowercase(self) -> None:
        """Test that tags are converted to lowercase."""
        response = "Python, PROGRAMMING, Tutorial"
        tags = _parse_tags(response, max_tags=10)

        assert all(tag.islower() for tag in tags)
        assert "python" in tags
        assert "programming" in tags

    def test_parse_tags_removes_empty(self) -> None:
        """Test that empty tags are removed."""
        response = "python, , programming, , tutorial"
        tags = _parse_tags(response, max_tags=10)

        assert "" not in tags
        assert len(tags) == 3

    def test_parse_tags_removes_very_long(self) -> None:
        """Test that very long tags (>50 chars) are removed."""
        response = "python, " + "a" * 60 + ", programming"
        tags = _parse_tags(response, max_tags=10)

        assert len(tags) == 2
        assert "python" in tags
        assert "programming" in tags


class TestGenerateTags:
    """Tests for generate_tags function."""

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_success(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test successful tag generation."""
        # Mock AI response
        mock_instance = MagicMock()
        mock_instance.generate.return_value = (
            "python, programming, tutorial, algorithms, web-development"
        )
        mock_ai_config.return_value = mock_instance

        tags = generate_tags(sample_document, max_tags=10)

        assert len(tags) == 5
        assert "python" in tags
        assert "programming" in tags
        assert "tutorial" in tags
        mock_instance.generate.assert_called_once()

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_respects_max_tags(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test that max_tags limit is respected."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = (
            "tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8, tag9, tag10"
        )
        mock_ai_config.return_value = mock_instance

        tags = generate_tags(sample_document, max_tags=5)

        assert len(tags) <= 5

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_with_custom_ai_options(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test tag generation with custom AI options."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "python, programming"
        mock_ai_config.return_value = mock_instance

        ai_options = {"ai_provider": "openai", "ai_model": "gpt-4"}
        tags = generate_tags(sample_document, ai_options=ai_options)

        # Verify AIConfig was initialized with options
        mock_ai_config.assert_called_once_with(ai_options)
        assert isinstance(tags, list)

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_uses_document_metadata(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test that document metadata is included in prompt."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "python, programming"
        mock_ai_config.return_value = mock_instance

        generate_tags(sample_document)

        # Verify that generate was called with a prompt containing metadata
        call_args = mock_instance.generate.call_args
        prompt = call_args[0][0]  # First positional argument

        assert sample_document.metadata.title in prompt
        assert sample_document.metadata.author in prompt
        assert str(sample_document.word_count) in prompt

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_handles_empty_response(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test handling of empty AI response."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = ""
        mock_ai_config.return_value = mock_instance

        tags = generate_tags(sample_document)

        assert isinstance(tags, list)
        assert len(tags) == 0

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_api_error(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test handling of API errors."""
        mock_instance = MagicMock()
        mock_instance.generate.side_effect = Exception("API Error")
        mock_ai_config.return_value = mock_instance

        with pytest.raises(Exception, match="API Error"):
            generate_tags(sample_document)

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_initialization_error(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test handling of AIConfig initialization errors."""
        mock_ai_config.side_effect = ValueError("API key not set")

        with pytest.raises(ValueError, match="API key not set"):
            generate_tags(sample_document)


class TestGenerateTagsBatch:
    """Tests for generate_tags_batch function."""

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_batch_success(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test successful batch tag generation."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "python, programming"
        mock_ai_config.return_value = mock_instance

        # Create multiple documents
        doc1 = sample_document
        doc2 = Document(
            document_id="test_doc_002",
            content="JavaScript tutorial",
            chapters=[],
            images=[],
            metadata=Metadata(title="JS Guide"),
            processing_info=ProcessingInfo(
                parser_used="Parser",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=200,
            estimated_reading_time=1,
        )

        results = generate_tags_batch([doc1, doc2], max_tags=5)

        assert len(results) == 2
        assert "test_doc_001" in results
        assert "test_doc_002" in results
        assert isinstance(results["test_doc_001"], list)
        assert isinstance(results["test_doc_002"], list)

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_batch_handles_errors(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test that batch processing handles individual errors gracefully."""
        mock_instance = MagicMock()
        # First call succeeds, second fails
        mock_instance.generate.side_effect = [
            "python, programming",
            Exception("API Error"),
        ]
        mock_ai_config.return_value = mock_instance

        doc1 = sample_document
        doc2 = Document(
            document_id="test_doc_002",
            content="Test",
            chapters=[],
            images=[],
            metadata=Metadata(),
            processing_info=ProcessingInfo(
                parser_used="Parser",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=100,
            estimated_reading_time=1,
        )

        results = generate_tags_batch([doc1, doc2])

        # First should succeed, second should have empty list
        assert len(results) == 2
        assert len(results["test_doc_001"]) > 0
        assert len(results["test_doc_002"]) == 0

    @patch("omniparser.processors.ai_tagger.AIConfig")
    def test_generate_tags_batch_empty_list(self, mock_ai_config: MagicMock) -> None:
        """Test batch processing with empty document list."""
        results = generate_tags_batch([])

        assert isinstance(results, dict)
        assert len(results) == 0
