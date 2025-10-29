"""
AI-powered content quality assessment.

This module provides automated quality scoring for parsed documents using
AI language models. Quality assessment includes multiple dimensions like
readability, structure, completeness, and overall quality.

Features:
    - Multi-dimensional quality scoring (0-100 scale)
    - Actionable improvement suggestions
    - Support for all AI providers
    - Detailed quality breakdown

Example:
    >>> from omniparser import parse_document
    >>> from omniparser.processors.ai_quality import score_quality
    >>> doc = parse_document("article.md")
    >>> quality = score_quality(doc)
    >>> print(f"Overall: {quality['overall_score']}/100")
    >>> print(f"Readability: {quality['readability']}/100")
"""

import logging
import re
from typing import Any, Dict, List, Optional

from ..ai_config import AIConfig
from ..models import Document

logger = logging.getLogger(__name__)


def score_quality(
    document: Document, ai_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Assess document quality using AI analysis.

    Evaluates the document across multiple quality dimensions and provides
    actionable suggestions for improvement.

    Quality Dimensions:
        - Overall Score (0-100): Weighted average of all dimensions
        - Readability (0-100): Clarity, sentence structure, word choice
        - Structure (0-100): Organization, headings, logical flow
        - Completeness (0-100): Depth, coverage, thoroughness
        - Coherence (0-100): Consistency, transitions, unity

    Args:
        document: Parsed document to assess.
        ai_options: AI configuration options (see AIConfig for details).

    Returns:
        Dictionary with quality scores and suggestions:
            - overall_score (int): Overall quality score (0-100)
            - readability (int): Readability score (0-100)
            - structure (int): Structure score (0-100)
            - completeness (int): Completeness score (0-100)
            - coherence (int): Coherence score (0-100)
            - suggestions (List[str]): List of improvement suggestions
            - strengths (List[str]): List of document strengths

    Raises:
        ValueError: If AI provider API key is not set.
        Exception: If AI API call fails.

    Example:
        >>> doc = parse_document("technical_doc.md")
        >>> quality = score_quality(doc)
        >>> print(f"Overall Quality: {quality['overall_score']}/100")
        >>> print(f"\\nStrengths:")
        >>> for strength in quality['strengths']:
        ...     print(f"  - {strength}")
        >>> print(f"\\nSuggestions:")
        >>> for suggestion in quality['suggestions']:
        ...     print(f"  - {suggestion}")

        >>> # Use local model
        >>> quality = score_quality(
        ...     doc,
        ...     ai_options={'ai_provider': 'ollama'}
        ... )
    """
    try:
        ai_config = AIConfig(ai_options)
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize AI config: {e}")
        raise

    # Prepare content sample (first 3000 chars for quality assessment)
    content_sample = document.content[:3000] if document.content else ""

    system_prompt = """You are a content quality analyst. Evaluate document quality across multiple dimensions.

Return your assessment in this EXACT format (use exact labels):

OVERALL_SCORE: [0-100]
READABILITY: [0-100]
STRUCTURE: [0-100]
COMPLETENESS: [0-100]
COHERENCE: [0-100]

STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]

SUGGESTIONS:
- [suggestion 1]
- [suggestion 2]
- [suggestion 3]

Be specific and actionable in your suggestions."""

    user_prompt = f"""Evaluate this document's quality:

Document Information:
- Title: {document.metadata.title or 'Unknown'}
- Word Count: {document.word_count}
- Chapters: {len(document.chapters)}
- Reading Time: {document.estimated_reading_time} minutes

Content Sample (first 3000 characters):
{content_sample}

Provide quality assessment:"""

    try:
        logger.info(f"Assessing quality for document: {document.document_id}")
        response = ai_config.generate(user_prompt, system_prompt)

        # Parse the structured response
        quality_data = _parse_quality_response(response)

        logger.info(
            f"Quality assessment complete. Overall score: {quality_data['overall_score']}/100"
        )
        return quality_data

    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        raise


def _parse_quality_response(response: str) -> Dict[str, Any]:
    """
    Parse AI quality assessment response.

    Args:
        response: Raw AI response text in structured format.

    Returns:
        Dictionary with parsed quality scores and suggestions.
    """
    # Initialize result with defaults
    result: Dict[str, Any] = {
        "overall_score": 0,
        "readability": 0,
        "structure": 0,
        "completeness": 0,
        "coherence": 0,
        "suggestions": [],
        "strengths": [],
    }

    try:
        # Extract scores using regex
        overall_match = re.search(r"OVERALL_SCORE:\s*(\d+)", response, re.IGNORECASE)
        if overall_match:
            result["overall_score"] = int(overall_match.group(1))

        readability_match = re.search(r"READABILITY:\s*(\d+)", response, re.IGNORECASE)
        if readability_match:
            result["readability"] = int(readability_match.group(1))

        structure_match = re.search(r"STRUCTURE:\s*(\d+)", response, re.IGNORECASE)
        if structure_match:
            result["structure"] = int(structure_match.group(1))

        completeness_match = re.search(
            r"COMPLETENESS:\s*(\d+)", response, re.IGNORECASE
        )
        if completeness_match:
            result["completeness"] = int(completeness_match.group(1))

        coherence_match = re.search(r"COHERENCE:\s*(\d+)", response, re.IGNORECASE)
        if coherence_match:
            result["coherence"] = int(coherence_match.group(1))

        # Extract strengths
        strengths_section = re.search(
            r"STRENGTHS:\s*\n((?:^[-*]\s*.+$\n?)+)",
            response,
            re.MULTILINE | re.IGNORECASE,
        )
        if strengths_section:
            strengths_text = strengths_section.group(1)
            strengths = [
                line.strip("- *").strip()
                for line in strengths_text.split("\n")
                if line.strip()
            ]
            result["strengths"] = [s for s in strengths if s]

        # Extract suggestions
        suggestions_section = re.search(
            r"SUGGESTIONS:\s*\n((?:^[-*]\s*.+$\n?)+)",
            response,
            re.MULTILINE | re.IGNORECASE,
        )
        if suggestions_section:
            suggestions_text = suggestions_section.group(1)
            suggestions = [
                line.strip("- *").strip()
                for line in suggestions_text.split("\n")
                if line.strip()
            ]
            result["suggestions"] = [s for s in suggestions if s]

        # Clamp scores to 0-100 range
        for key in [
            "overall_score",
            "readability",
            "structure",
            "completeness",
            "coherence",
        ]:
            result[key] = max(0, min(100, result[key]))

    except Exception as e:
        logger.warning(f"Error parsing quality response: {e}")
        logger.debug(f"Raw response: {response}")

    # Validate that required fields were extracted
    if result["overall_score"] == 0:
        logger.warning(
            f"Failed to extract overall score from response. "
            f"Response preview: {response[:200]}..."
        )

    # Check if all dimension scores are still at defaults (0)
    if all(
        result[key] == 0
        for key in ["readability", "structure", "completeness", "coherence"]
    ):
        logger.warning(
            f"Failed to extract any dimension scores from response. "
            f"Response preview: {response[:200]}..."
        )

    if not result["suggestions"]:
        logger.warning(
            f"Failed to extract suggestions from response. "
            f"Response preview: {response[:200]}..."
        )

    if not result["strengths"]:
        logger.warning(
            f"Failed to extract strengths from response. "
            f"Response preview: {response[:200]}..."
        )

    return result


def compare_quality(
    document1: Document,
    document2: Document,
    ai_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compare quality of two documents.

    Args:
        document1: First document to compare.
        document2: Second document to compare.
        ai_options: AI configuration options.

    Returns:
        Dictionary with comparative analysis:
            - doc1_scores: Quality scores for document 1
            - doc2_scores: Quality scores for document 2
            - comparison: Comparative insights
            - winner: ID of higher-quality document

    Example:
        >>> doc1 = parse_document("draft_v1.md")
        >>> doc2 = parse_document("draft_v2.md")
        >>> comparison = compare_quality(doc1, doc2)
        >>> print(f"Winner: {comparison['winner']}")
        >>> print(f"Comparison: {comparison['comparison']}")
    """
    # Score both documents
    scores1 = score_quality(document1, ai_options)
    scores2 = score_quality(document2, ai_options)

    # Determine winner
    winner = (
        document1.document_id
        if scores1["overall_score"] >= scores2["overall_score"]
        else document2.document_id
    )

    # Generate comparison summary
    score_diff = abs(scores1["overall_score"] - scores2["overall_score"])
    comparison = (
        f"Document {winner} has higher quality " f"(+{score_diff} points overall). "
    )

    # Add dimension-specific insights
    if scores1["readability"] > scores2["readability"]:
        comparison += f"Doc1 is more readable (+{scores1['readability'] - scores2['readability']}). "
    elif scores2["readability"] > scores1["readability"]:
        comparison += f"Doc2 is more readable (+{scores2['readability'] - scores1['readability']}). "

    if scores1["structure"] > scores2["structure"]:
        comparison += f"Doc1 is better structured (+{scores1['structure'] - scores2['structure']}). "
    elif scores2["structure"] > scores1["structure"]:
        comparison += f"Doc2 is better structured (+{scores2['structure'] - scores1['structure']}). "

    return {
        "doc1_scores": scores1,
        "doc2_scores": scores2,
        "comparison": comparison,
        "winner": winner,
    }
