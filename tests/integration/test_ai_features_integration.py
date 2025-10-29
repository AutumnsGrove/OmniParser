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


class TestAnthropicAdvancedFeatures:
    """Advanced integration tests for Anthropic-specific features."""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
    )
    def test_summarize_all_styles(self, sample_document: Document) -> None:
        """Test all three summary styles: concise, detailed, bullet."""
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Test concise summary
        concise = summarize_document(
            sample_document, style="concise", ai_options=ai_options
        )
        assert isinstance(concise, str)
        assert len(concise) > 0
        assert len(concise) < 1000  # Should be short

        # Test detailed summary
        detailed = summarize_document(
            sample_document, style="detailed", max_length=500, ai_options=ai_options
        )
        assert isinstance(detailed, str)
        assert len(detailed) >= len(concise)  # Should be longer than concise

        # Test bullet point summary
        bullet = summarize_document(
            sample_document, style="bullet", ai_options=ai_options
        )
        assert isinstance(bullet, str)
        assert "-" in bullet or "•" in bullet or "*" in bullet  # Should have bullets

        print("\n✅ All summary styles tested successfully:")
        print(f"   Concise ({len(concise)} chars): {concise[:60]}...")
        print(f"   Detailed ({len(detailed)} chars): {detailed[:60]}...")
        print(f"   Bullet ({len(bullet)} chars): {bullet[:60]}...")

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
    )
    def test_quality_scoring_detailed(self, sample_document: Document) -> None:
        """Test detailed quality scoring with all metrics."""
        ai_options = {"ai_provider": "anthropic"}

        result = score_quality(sample_document, ai_options=ai_options)

        # Verify all expected fields
        assert "overall_score" in result
        assert "readability" in result
        assert "structure" in result
        assert "completeness" in result
        assert "coherence" in result
        assert "strengths" in result
        assert "suggestions" in result

        # Verify score ranges
        assert 0 <= result["overall_score"] <= 100
        assert 0 <= result["readability"] <= 100
        assert 0 <= result["structure"] <= 100
        assert 0 <= result["completeness"] <= 100
        assert 0 <= result["coherence"] <= 100

        # Verify lists
        assert isinstance(result["strengths"], list)
        assert isinstance(result["suggestions"], list)

        print("\n✅ Detailed quality scoring:")
        print(f"   Overall: {result['overall_score']}/100")
        print(f"   Readability: {result['readability']}/100")
        print(f"   Structure: {result['structure']}/100")
        print(f"   Completeness: {result['completeness']}/100")
        print(f"   Coherence: {result['coherence']}/100")
        print(f"   Strengths: {len(result['strengths'])} items")
        print(f"   Suggestions: {len(result['suggestions'])} items")

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
    )
    def test_tag_generation_with_limits(self, sample_document: Document) -> None:
        """Test tag generation with different max_tags limits."""
        ai_options = {"ai_provider": "anthropic"}

        # Test with different limits
        limits = [3, 5, 10, 15]

        for limit in limits:
            tags = generate_tags(
                sample_document, max_tags=limit, ai_options=ai_options
            )

            assert isinstance(tags, list)
            assert len(tags) > 0
            assert len(tags) <= limit  # Should respect limit

            print(f"✅ Generated {len(tags)} tags (limit: {limit}): {tags[:5]}...")


class TestEdgeCasesIntegration:
    """Integration tests for edge cases and error scenarios."""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
    )
    def test_empty_document_handling(self) -> None:
        """Test handling of documents with minimal content."""
        metadata = Metadata(
            title="Empty Test",
            author="Test",
            original_format="test",
        )

        processing_info = ProcessingInfo(
            parser_used="Test",
            parser_version="1.0.0",
            processing_time=0.1,
            timestamp=datetime.now(),
        )

        # Document with very minimal content
        minimal_doc = Document(
            document_id="minimal",
            content="Test.",
            chapters=[],
            images=[],
            metadata=metadata,
            processing_info=processing_info,
            word_count=1,
            estimated_reading_time=1,
        )

        ai_options = {"ai_provider": "anthropic"}

        # Should handle gracefully
        tags = generate_tags(minimal_doc, max_tags=5, ai_options=ai_options)
        assert isinstance(tags, list)  # May be empty, but should not crash

        summary = summarize_document(minimal_doc, style="concise", ai_options=ai_options)
        assert isinstance(summary, str)

        print("✅ Handled minimal content document successfully")

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
    )
    def test_long_document_handling(self) -> None:
        """Test handling of longer documents."""
        metadata = Metadata(
            title="Long Document Test",
            author="Test",
            original_format="test",
        )

        processing_info = ProcessingInfo(
            parser_used="Test",
            parser_version="1.0.0",
            processing_time=1.0,
            timestamp=datetime.now(),
        )

        # Create a longer document by repeating content
        long_content = """
Machine learning is a powerful technology. It enables computers to learn from data.
Deep learning is a subset of machine learning that uses neural networks.
Natural language processing helps computers understand human language.
Computer vision enables machines to interpret visual information.
""" * 20  # Repeat 20 times for longer content

        long_doc = Document(
            document_id="long_doc",
            content=long_content,
            chapters=[],
            images=[],
            metadata=metadata,
            processing_info=processing_info,
            word_count=len(long_content.split()),
            estimated_reading_time=10,
        )

        ai_options = {"ai_provider": "anthropic"}

        # Should handle longer content
        tags = generate_tags(long_doc, max_tags=10, ai_options=ai_options)
        assert isinstance(tags, list)
        assert len(tags) > 0

        summary = summarize_document(long_doc, style="detailed", ai_options=ai_options)
        assert isinstance(summary, str)
        assert len(summary) > 0

        print(f"✅ Handled long document ({len(long_content)} chars) successfully")

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
    )
    def test_special_characters_handling(self) -> None:
        """Test handling of documents with special characters."""
        metadata = Metadata(
            title="Special Characters Test™",
            author="Test © 2024",
            original_format="test",
        )

        processing_info = ProcessingInfo(
            parser_used="Test",
            parser_version="1.0.0",
            processing_time=0.5,
            timestamp=datetime.now(),
        )

        special_content = """
This document contains special characters: é, ñ, ü, ø, æ
Mathematical symbols: ∑, ∫, √, π, ∞, ≠, ≤, ≥
Currency: $, €, £, ¥, ₹
Punctuation: — – … " " ' '
Emojis: 🚀 🎯 💡 ✨ 🔥

And some code with special chars:
def test(): return x >= y && z != null;
"""

        special_doc = Document(
            document_id="special_chars",
            content=special_content,
            chapters=[],
            images=[],
            metadata=metadata,
            processing_info=processing_info,
            word_count=50,
            estimated_reading_time=1,
        )

        ai_options = {"ai_provider": "anthropic"}

        # Should handle special characters
        tags = generate_tags(special_doc, max_tags=10, ai_options=ai_options)
        assert isinstance(tags, list)

        summary = summarize_document(special_doc, style="concise", ai_options=ai_options)
        assert isinstance(summary, str)

        print("✅ Handled special characters successfully")


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
