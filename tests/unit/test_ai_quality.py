"""
Unit tests for AI-powered quality scoring processor.

Tests quality assessment with mocked AI responses.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from omniparser.models import Document, Metadata, ProcessingInfo
from omniparser.processors.ai_quality import (
    _parse_quality_response,
    compare_quality,
    score_quality,
)


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    metadata = Metadata(title="Sample Document", author="Test Author")
    processing_info = ProcessingInfo(
        parser_used="Parser",
        parser_version="1.0",
        processing_time=1.0,
        timestamp=datetime.now(),
    )

    return Document(
        document_id="test_doc_001",
        content="This is a well-written document with clear structure and good flow.",
        chapters=[],
        images=[],
        metadata=metadata,
        processing_info=processing_info,
        word_count=500,
        estimated_reading_time=3,
    )


class TestParseQualityResponse:
    """Tests for _parse_quality_response helper function."""

    def test_parse_complete_response(self) -> None:
        """Test parsing a complete quality response."""
        response = """
OVERALL_SCORE: 85
READABILITY: 90
STRUCTURE: 80
COMPLETENESS: 85
COHERENCE: 88

STRENGTHS:
- Clear writing style
- Well-organized content
- Good examples

SUGGESTIONS:
- Add more headings
- Improve paragraph transitions
- Include visual aids
"""

        result = _parse_quality_response(response)

        assert result["overall_score"] == 85
        assert result["readability"] == 90
        assert result["structure"] == 80
        assert result["completeness"] == 85
        assert result["coherence"] == 88
        assert len(result["strengths"]) == 3
        assert "Clear writing style" in result["strengths"]
        assert len(result["suggestions"]) == 3
        assert "Add more headings" in result["suggestions"]

    def test_parse_case_insensitive(self) -> None:
        """Test that parsing is case-insensitive."""
        response = """
overall_score: 75
readability: 80
structure: 70
completeness: 75
coherence: 72
"""

        result = _parse_quality_response(response)

        assert result["overall_score"] == 75
        assert result["readability"] == 80

    def test_parse_missing_fields(self) -> None:
        """Test parsing with missing fields returns defaults."""
        response = """
OVERALL_SCORE: 80
"""

        result = _parse_quality_response(response)

        assert result["overall_score"] == 80
        assert result["readability"] == 0
        assert result["structure"] == 0
        assert result["suggestions"] == []
        assert result["strengths"] == []

    def test_parse_clamps_scores(self) -> None:
        """Test that scores are clamped to 0-100 range."""
        response = """
OVERALL_SCORE: 150
READABILITY: -10
STRUCTURE: 50
"""

        result = _parse_quality_response(response)

        assert result["overall_score"] == 100  # Clamped to 100
        assert result["readability"] == 0  # Clamped to 0
        assert result["structure"] == 50  # Within range


class TestScoreQuality:
    """Tests for score_quality function."""

    @patch("omniparser.processors.ai_quality.AIConfig")
    def test_score_quality_success(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test successful quality scoring."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = """
OVERALL_SCORE: 85
READABILITY: 90
STRUCTURE: 80
COMPLETENESS: 85
COHERENCE: 88

STRENGTHS:
- Clear writing
- Good structure

SUGGESTIONS:
- Add headings
- Improve flow
"""
        mock_ai_config.return_value = mock_instance

        result = score_quality(sample_document)

        assert isinstance(result, dict)
        assert result["overall_score"] == 85
        assert result["readability"] == 90
        assert len(result["strengths"]) == 2
        assert len(result["suggestions"]) == 2

    @patch("omniparser.processors.ai_quality.AIConfig")
    def test_score_quality_with_custom_ai_options(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test quality scoring with custom AI options."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "OVERALL_SCORE: 80"
        mock_ai_config.return_value = mock_instance

        ai_options = {"ai_provider": "openai", "ai_model": "gpt-4"}
        result = score_quality(sample_document, ai_options=ai_options)

        mock_ai_config.assert_called_once_with(ai_options)
        assert isinstance(result, dict)

    @patch("omniparser.processors.ai_quality.AIConfig")
    def test_score_quality_api_error(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test handling of API errors."""
        mock_instance = MagicMock()
        mock_instance.generate.side_effect = Exception("API Error")
        mock_ai_config.return_value = mock_instance

        with pytest.raises(Exception, match="API Error"):
            score_quality(sample_document)


class TestCompareQuality:
    """Tests for compare_quality function."""

    @patch("omniparser.processors.ai_quality.score_quality")
    def test_compare_quality_success(
        self, mock_score_quality: MagicMock, sample_document: Document
    ) -> None:
        """Test successful quality comparison."""
        # Create two documents
        doc1 = sample_document
        doc2 = Document(
            document_id="test_doc_002",
            content="Another document",
            chapters=[],
            images=[],
            metadata=Metadata(),
            processing_info=ProcessingInfo(
                parser_used="Parser",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=300,
            estimated_reading_time=2,
        )

        # Mock scores
        mock_score_quality.side_effect = [
            {
                "overall_score": 85,
                "readability": 90,
                "structure": 80,
                "completeness": 85,
                "coherence": 88,
                "strengths": [],
                "suggestions": [],
            },
            {
                "overall_score": 70,
                "readability": 75,
                "structure": 65,
                "completeness": 70,
                "coherence": 68,
                "strengths": [],
                "suggestions": [],
            },
        ]

        result = compare_quality(doc1, doc2)

        assert isinstance(result, dict)
        assert result["winner"] == "test_doc_001"
        assert result["doc1_scores"]["overall_score"] == 85
        assert result["doc2_scores"]["overall_score"] == 70
        assert isinstance(result["comparison"], str)

    @patch("omniparser.processors.ai_quality.score_quality")
    def test_compare_quality_tie(
        self, mock_score_quality: MagicMock, sample_document: Document
    ) -> None:
        """Test comparison when scores are equal."""
        doc1 = sample_document
        doc2 = Document(
            document_id="test_doc_002",
            content="Another document",
            chapters=[],
            images=[],
            metadata=Metadata(),
            processing_info=ProcessingInfo(
                parser_used="Parser",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=300,
            estimated_reading_time=2,
        )

        # Mock equal scores
        mock_score_quality.return_value = {
            "overall_score": 80,
            "readability": 80,
            "structure": 80,
            "completeness": 80,
            "coherence": 80,
            "strengths": [],
            "suggestions": [],
        }

        result = compare_quality(doc1, doc2)

        # First document wins in case of tie
        assert result["winner"] == "test_doc_001"
