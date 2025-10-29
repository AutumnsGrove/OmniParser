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

    @patch("omniparser.processors.ai_quality.AIConfig")
    def test_score_quality_config_initialization_error(
        self, mock_ai_config: MagicMock, sample_document: Document
    ) -> None:
        """Test handling of AI config initialization errors."""
        mock_ai_config.side_effect = ValueError("API key not configured")

        with pytest.raises(ValueError, match="API key not configured"):
            score_quality(sample_document)

    @patch("omniparser.processors.ai_quality.AIConfig")
    def test_score_quality_with_empty_document(self, mock_ai_config: MagicMock) -> None:
        """Test quality scoring with empty document content."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = """
OVERALL_SCORE: 20
READABILITY: 10
STRUCTURE: 15
COMPLETENESS: 25
COHERENCE: 20

STRENGTHS:
- Document structure exists

SUGGESTIONS:
- Add content
- Develop main sections
- Include examples
"""
        mock_ai_config.return_value = mock_instance

        empty_doc = Document(
            document_id="empty_doc",
            content="",
            chapters=[],
            images=[],
            metadata=Metadata(title="Empty Document"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=0.1,
                timestamp=datetime.now(),
            ),
            word_count=0,
            estimated_reading_time=0,
        )

        result = score_quality(empty_doc)

        # Should handle empty content gracefully
        assert isinstance(result, dict)
        assert "overall_score" in result
        # Verify empty content was passed to AI
        mock_instance.generate.assert_called_once()

    @patch("omniparser.processors.ai_quality.AIConfig")
    def test_score_quality_long_document_truncation(
        self, mock_ai_config: MagicMock
    ) -> None:
        """Test that long documents are truncated to 3000 characters."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = """
OVERALL_SCORE: 85
READABILITY: 90
STRUCTURE: 85
COMPLETENESS: 80
COHERENCE: 85

STRENGTHS:
- Comprehensive content

SUGGESTIONS:
- Maintain quality throughout
"""
        mock_ai_config.return_value = mock_instance

        # Create document with >3000 character content
        long_content = "This is a test sentence. " * 200  # ~5000 chars
        long_doc = Document(
            document_id="long_doc",
            content=long_content,
            chapters=[],
            images=[],
            metadata=Metadata(title="Long Document"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=len(long_content.split()),
            estimated_reading_time=10,
        )

        result = score_quality(long_doc)

        assert isinstance(result, dict)
        # Verify the prompt contains truncated content (first 3000 chars)
        call_args = mock_instance.generate.call_args[0][0]
        # Content sample should be truncated
        assert len(long_content) > 3000
        # The actual content in the prompt should be limited
        assert "Content Sample (first 3000 characters):" in call_args


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

    @patch("omniparser.processors.ai_quality.score_quality")
    def test_compare_quality_dimension_insights_readability(
        self, mock_score_quality: MagicMock, sample_document: Document
    ) -> None:
        """Test dimension-specific insights for readability differences."""
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

        # Mock scores with readability difference
        mock_score_quality.side_effect = [
            {
                "overall_score": 80,
                "readability": 95,  # Doc1 more readable
                "structure": 75,
                "completeness": 80,
                "coherence": 75,
                "strengths": [],
                "suggestions": [],
            },
            {
                "overall_score": 82,
                "readability": 70,  # Doc2 less readable
                "structure": 90,
                "completeness": 85,
                "coherence": 80,
                "strengths": [],
                "suggestions": [],
            },
        ]

        result = compare_quality(doc1, doc2)

        # Verify readability insight is included
        assert "readable" in result["comparison"].lower()
        # Doc1 should be mentioned as more readable (+25 points)
        assert "Doc1 is more readable (+25)" in result["comparison"]

    @patch("omniparser.processors.ai_quality.score_quality")
    def test_compare_quality_dimension_insights_structure(
        self, mock_score_quality: MagicMock, sample_document: Document
    ) -> None:
        """Test dimension-specific insights for structure differences."""
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

        # Mock scores with structure difference
        mock_score_quality.side_effect = [
            {
                "overall_score": 75,
                "readability": 80,
                "structure": 65,  # Doc1 worse structure
                "completeness": 75,
                "coherence": 70,
                "strengths": [],
                "suggestions": [],
            },
            {
                "overall_score": 85,
                "readability": 80,
                "structure": 90,  # Doc2 better structure
                "completeness": 85,
                "coherence": 85,
                "strengths": [],
                "suggestions": [],
            },
        ]

        result = compare_quality(doc1, doc2)

        # Verify structure insight is included
        assert "structured" in result["comparison"].lower()
        # Doc2 should be mentioned as better structured (+25 points)
        assert "Doc2 is better structured (+25)" in result["comparison"]

    @patch("omniparser.processors.ai_quality.score_quality")
    def test_compare_quality_both_dimensions_differ(
        self, mock_score_quality: MagicMock, sample_document: Document
    ) -> None:
        """Test insights when both readability and structure differ."""
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

        # Mock scores with both differences
        mock_score_quality.side_effect = [
            {
                "overall_score": 85,
                "readability": 90,  # Doc1 more readable
                "structure": 80,  # Doc1 better structured
                "completeness": 85,
                "coherence": 85,
                "strengths": [],
                "suggestions": [],
            },
            {
                "overall_score": 75,
                "readability": 70,  # Doc2 less readable
                "structure": 75,  # Doc2 worse structured
                "completeness": 75,
                "coherence": 75,
                "strengths": [],
                "suggestions": [],
            },
        ]

        result = compare_quality(doc1, doc2)

        # Both insights should be included
        comparison = result["comparison"]
        assert "readable" in comparison.lower()
        assert "structured" in comparison.lower()
        assert "Doc1" in comparison

    @patch("omniparser.processors.ai_quality.score_quality")
    def test_compare_quality_no_dimension_differences(
        self, mock_score_quality: MagicMock, sample_document: Document
    ) -> None:
        """Test when overall score differs but dimensions are equal."""
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

        # Mock scores with equal dimensions but different overall
        mock_score_quality.side_effect = [
            {
                "overall_score": 85,  # Higher overall
                "readability": 80,
                "structure": 80,
                "completeness": 85,
                "coherence": 85,
                "strengths": [],
                "suggestions": [],
            },
            {
                "overall_score": 75,  # Lower overall
                "readability": 80,  # Same readability
                "structure": 80,  # Same structure
                "completeness": 75,
                "coherence": 75,
                "strengths": [],
                "suggestions": [],
            },
        ]

        result = compare_quality(doc1, doc2)

        # Should not include readability/structure insights since they're equal
        comparison = result["comparison"]
        assert "more readable" not in comparison.lower()
        assert "better structured" not in comparison.lower()
        # But should include overall score difference
        assert "10 points overall" in comparison
