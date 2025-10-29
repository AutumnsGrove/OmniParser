"""
AI-powered document summarization.

This module provides automatic document summarization using AI language models.
Summaries can be generated in different styles (concise, detailed, bullet-point)
and at various lengths to suit different use cases.

Features:
    - Multiple summary styles (concise, detailed, bullet-point)
    - Configurable summary length
    - Support for all AI providers (Anthropic, OpenAI, OpenRouter, Ollama, LM Studio)
    - Context-aware summarization using document metadata

Example:
    >>> from omniparser import parse_document
    >>> from omniparser.processors.ai_summarizer import summarize_document
    >>> doc = parse_document("book.epub")
    >>> summary = summarize_document(doc, style="concise")
    >>> print(summary)
    'This book explores the theme of...'
"""

import logging
from typing import Any, Dict, Optional

from ..ai_config import AIConfig
from ..models import Document

logger = logging.getLogger(__name__)


def summarize_document(
    document: Document,
    max_length: int = 500,
    style: str = "concise",
    ai_options: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a summary of a document using AI.

    Analyzes document content and metadata to produce a high-quality summary
    that captures the main themes, ideas, and conclusions.

    Args:
        document: Parsed document to summarize.
        max_length: Maximum summary length in words (default: 500, range: 1-10000).
        style: Summary style - "concise", "detailed", or "bullet" (default: "concise").
            - "concise": 2-3 sentence overview
            - "detailed": Comprehensive summary up to max_length words
            - "bullet": Bullet-point summary of key points
        ai_options: AI configuration options (see AIConfig for details).

    Returns:
        Document summary as a string.

    Raises:
        ValueError: If max_length is invalid, style is invalid, or document has no content.
        ValueError: If AI provider API key is not set.
        Exception: If AI API call fails.

    Example:
        >>> doc = parse_document("research_paper.pdf")
        >>> # Concise summary
        >>> summary = summarize_document(doc, style="concise")
        >>> print(summary)

        >>> # Detailed summary
        >>> summary = summarize_document(doc, max_length=1000, style="detailed")

        >>> # Bullet-point summary
        >>> summary = summarize_document(doc, style="bullet")

        >>> # Use local model via Ollama
        >>> summary = summarize_document(
        ...     doc,
        ...     ai_options={'ai_provider': 'ollama', 'ai_model': 'llama3.2:latest'}
        ... )
    """
    # Validate inputs
    valid_styles = ["concise", "detailed", "bullet"]
    if style not in valid_styles:
        raise ValueError(f"Invalid style '{style}'. Must be one of: {valid_styles}")

    if max_length <= 0:
        raise ValueError("max_length must be positive")
    if max_length > 10000:
        raise ValueError("max_length must not exceed 10000 words")

    if not document.content or len(document.content.strip()) == 0:
        raise ValueError("Document has no content to summarize")

    try:
        ai_config = AIConfig(ai_options)
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize AI config: {e}")
        raise

    # Prepare content sample (first 5000 chars for better context)
    content_sample = document.content[:5000] if document.content else ""

    # Build style-specific instructions
    style_instructions = {
        "concise": (
            "Write a concise 2-3 sentence summary that captures the essence "
            "of the document. Focus on the main theme or argument."
        ),
        "detailed": (
            f"Write a detailed summary of up to {max_length} words. "
            "Cover the main themes, key points, and important conclusions. "
            "Be comprehensive but avoid unnecessary details."
        ),
        "bullet": (
            "Write a bullet-point summary with 5-7 key points. "
            "Each bullet should be a complete sentence. "
            "Format:\n- Point 1\n- Point 2\n- Point 3\netc."
        ),
    }

    system_prompt = (
        "You are a document summarization expert. Create clear, accurate summaries "
        "that capture the essential information from documents. "
        + style_instructions[style]
    )

    user_prompt = f"""Summarize this document:

Document Information:
- Title: {document.metadata.title or 'Unknown'}
- Author: {document.metadata.author or 'Unknown'}
- Format: {document.metadata.original_format or 'Unknown'}
- Word Count: {document.word_count}
- Estimated Reading Time: {document.estimated_reading_time} minutes
- Chapters: {len(document.chapters)}

Content Preview (first 5000 characters):
{content_sample}

Generate a {style} summary of this document:"""

    try:
        logger.info(f"Generating {style} summary for document: {document.document_id}")
        response = ai_config.generate(user_prompt, system_prompt)

        # Clean up response
        summary = response.strip()

        logger.info(f"Generated {len(summary)} character summary ({style} style)")
        return summary

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise


def summarize_chapter(
    document: Document,
    chapter_id: int,
    style: str = "concise",
    ai_options: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a summary of a specific chapter.

    Args:
        document: Parsed document containing the chapter.
        chapter_id: ID of the chapter to summarize.
        style: Summary style - "concise", "detailed", or "bullet".
        ai_options: AI configuration options.

    Returns:
        Chapter summary as a string.

    Raises:
        ValueError: If chapter_id is not found.
        Exception: If AI API call fails.

    Example:
        >>> doc = parse_document("book.epub")
        >>> # Summarize chapter 3
        >>> summary = summarize_chapter(doc, chapter_id=3)
        >>> print(summary)
    """
    chapter = document.get_chapter(chapter_id)
    if not chapter:
        raise ValueError(f"Chapter {chapter_id} not found in document")

    try:
        ai_config = AIConfig(ai_options)
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize AI config: {e}")
        raise

    # Use full chapter content (no truncation for single chapter)
    content = chapter.content

    style_instructions = {
        "concise": "Write a concise 2-3 sentence summary of this chapter.",
        "detailed": "Write a detailed summary covering all key points in this chapter.",
        "bullet": "Write a bullet-point summary (5-7 points) of this chapter.",
    }

    system_prompt = (
        "You are a document summarization expert. Summarize this chapter accurately. "
        + style_instructions.get(style, style_instructions["concise"])
    )

    user_prompt = f"""Summarize this chapter:

Chapter Information:
- Title: {chapter.title}
- Word Count: {chapter.word_count}
- Chapter {chapter.chapter_id} of {len(document.chapters)}

Content:
{content}

Generate a {style} summary:"""

    try:
        logger.info(f"Generating summary for chapter {chapter_id}: {chapter.title}")
        response = ai_config.generate(user_prompt, system_prompt)

        summary = response.strip()
        logger.info(f"Generated chapter summary: {len(summary)} characters")
        return summary

    except Exception as e:
        logger.error(f"Chapter summarization failed: {e}")
        raise
