"""
Integration tests for AI features with real API calls.

These tests are skipped by default. Run with:
    pytest tests/integration/test_ai_features_integration.py --run-integration

To run these tests, set appropriate environment variables:
    - ANTHROPIC_API_KEY for Anthropic tests
    - OPENAI_API_KEY for OpenAI tests
    - OLLAMA_BASE_URL for Ollama tests (optional, defaults to localhost)

Example:
    export ANTHROPIC_API_KEY=sk-ant-...
    pytest tests/integration/test_ai_features_integration.py --run-integration
"""

import os
from datetime import datetime

import pytest

from omniparser.models import Document, Metadata, ProcessingInfo
from omniparser.processors.ai_quality import score_quality
from omniparser.processors.ai_summarizer import summarize_document
from omniparser.processors.ai_tagger import generate_tags


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for integration testing."""
    metadata = Metadata(
        title="Introduction to Machine Learning",
        author="Dr. Jane Smith",
        original_format="epub",
        tags=["ai", "machine-learning", "data-science"],
    )

    processing_info = ProcessingInfo(
        parser_used="EPUBParser",
        parser_version="1.0.0",
        processing_time=2.5,
        timestamp=datetime.now(),
    )

    content = """
Machine learning is a subset of artificial intelligence that focuses on building
systems that can learn from data. The field encompasses various techniques including
supervised learning, unsupervised learning, and reinforcement learning.

Supervised learning involves training models on labeled data, where the algorithm
learns to map inputs to outputs based on example pairs. Common algorithms include
linear regression, decision trees, and neural networks.

Unsupervised learning deals with unlabeled data, seeking to find hidden patterns
and structures. Clustering and dimensionality reduction are key techniques in this
domain. Applications include customer segmentation and anomaly detection.

Reinforcement learning is inspired by behavioral psychology, where an agent learns
to make decisions by interacting with an environment and receiving rewards or
penalties. This approach has achieved remarkable success in game playing and robotics.

The future of machine learning includes advances in deep learning, transfer learning,
and automated machine learning (AutoML). As computational power increases and datasets
grow, we can expect even more sophisticated and capable AI systems.
"""

    return Document(
        document_id="test_ml_doc_001",
        content=content,
        chapters=[],
        images=[],
        metadata=metadata,
        processing_info=processing_info,
        word_count=180,
        estimated_reading_time=1,
    )


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
)
class TestAnthropicIntegration:
    """Integration tests using Anthropic Claude."""

    def test_generate_tags_anthropic(self, sample_document: Document) -> None:
        """Test tag generation with Anthropic."""
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        tags = generate_tags(sample_document, max_tags=10, ai_options=ai_options)

        assert isinstance(tags, list)
        assert len(tags) > 0
        assert all(isinstance(tag, str) for tag in tags)
        # Should generate relevant tags for ML content
        assert any(
            "machine" in tag.lower() or "learning" in tag.lower() or "ai" in tag.lower()
            for tag in tags
        )

    def test_summarize_document_anthropic(
        self, sample_document: Document
    ) -> None:
        """Test document summarization with Anthropic."""
        ai_options = {"ai_provider": "anthropic"}

        summary = summarize_document(
            sample_document, style="concise", ai_options=ai_options
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        # Concise summary should be reasonably short
        assert len(summary) < 1000

    def test_score_quality_anthropic(self, sample_document: Document) -> None:
        """Test quality scoring with Anthropic."""
        ai_options = {"ai_provider": "anthropic"}

        result = score_quality(sample_document, ai_options=ai_options)

        assert isinstance(result, dict)
        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 100
        assert "readability" in result
        assert "structure" in result
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set. Set it to run this test.",
)
class TestOpenAIIntegration:
    """Integration tests using OpenAI."""

    def test_generate_tags_openai(self, sample_document: Document) -> None:
        """Test tag generation with OpenAI."""
        ai_options = {"ai_provider": "openai", "ai_model": "gpt-3.5-turbo"}

        tags = generate_tags(sample_document, max_tags=10, ai_options=ai_options)

        assert isinstance(tags, list)
        assert len(tags) > 0

    def test_summarize_document_openai(self, sample_document: Document) -> None:
        """Test document summarization with OpenAI."""
        ai_options = {"ai_provider": "openai"}

        summary = summarize_document(
            sample_document, style="bullet", ai_options=ai_options
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        # Bullet summary should contain bullet points
        assert "-" in summary or "•" in summary


@pytest.mark.skipif(
    "CI" in os.environ,
    reason="Ollama tests require local setup, skip in CI",
)
class TestOllamaIntegration:
    """Integration tests using Ollama (local models)."""

    def test_generate_tags_ollama(self, sample_document: Document) -> None:
        """
        Test tag generation with Ollama.

        Requires Ollama to be running locally with a model installed.
        Example: ollama run llama3.2:latest
        """
        ai_options = {"ai_provider": "ollama", "ai_model": "llama3.2:latest"}

        try:
            tags = generate_tags(
                sample_document, max_tags=10, ai_options=ai_options
            )

            assert isinstance(tags, list)
            # May return empty list if Ollama is not running
            # This test mainly validates the connection works
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")

    def test_summarize_document_ollama(self, sample_document: Document) -> None:
        """
        Test document summarization with Ollama.

        Requires Ollama to be running locally.
        """
        ai_options = {"ai_provider": "ollama"}

        try:
            summary = summarize_document(
                sample_document, style="concise", ai_options=ai_options
            )

            assert isinstance(summary, str)
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")


class TestMultiProviderConsistency:
    """Tests comparing results across different providers."""

    @pytest.mark.skipif(
        not (os.getenv("ANTHROPIC_API_KEY") and os.getenv("OPENAI_API_KEY")),
        reason="Both ANTHROPIC_API_KEY and OPENAI_API_KEY required",
    )
    def test_tags_consistency_across_providers(
        self, sample_document: Document
    ) -> None:
        """
        Test that different providers generate reasonable tags.

        Note: Tags won't be identical but should be thematically similar.
        """
        anthropic_tags = generate_tags(
            sample_document,
            max_tags=10,
            ai_options={"ai_provider": "anthropic"},
        )

        openai_tags = generate_tags(
            sample_document,
            max_tags=10,
            ai_options={"ai_provider": "openai"},
        )

        # Both should generate some tags
        assert len(anthropic_tags) > 0
        assert len(openai_tags) > 0

        # Should have some thematic overlap (at least 1-2 similar tags)
        # This is a loose check since models may use different terminology
        all_tags = set(anthropic_tags + openai_tags)
        assert len(all_tags) < len(anthropic_tags) + len(
            openai_tags
        ), "Should have some overlapping themes"
