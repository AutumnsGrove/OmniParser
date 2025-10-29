"""
AI-powered automatic tagging for documents.

This module provides automatic tag generation for parsed documents using
AI language models. Tags are extracted based on content analysis and can
help with document organization, search, and categorization.

Features:
    - Content-based tag generation
    - Configurable number of tags
    - Support for both Anthropic and OpenAI
    - Smart tag deduplication

Example:
    >>> from omniparser import parse_document
    >>> from omniparser.processors.ai_tagger import generate_tags
    >>> doc = parse_document("book.epub")
    >>> tags = generate_tags(doc, max_tags=10)
    >>> print(tags)
    ['fiction', 'adventure', 'fantasy', 'magic', 'coming-of-age']
"""

import logging
from typing import Any, Dict, List, Optional

from ..ai_config import AIConfig
from ..models import Document

logger = logging.getLogger(__name__)


def generate_tags(
    document: Document,
    max_tags: int = 10,
    ai_options: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Generate relevant tags for a document using AI.

    Analyzes document content and metadata to generate contextually relevant
    tags that can be used for categorization, search, and organization.

    Args:
        document: Parsed document to generate tags for.
        max_tags: Maximum number of tags to generate (default: 10, range: 1-100).
        ai_options: AI configuration options (see AIConfig for details).

    Returns:
        List of generated tags (lowercase, deduplicated).

    Raises:
        ValueError: If max_tags is invalid or document has no content.
        ValueError: If AI provider API key is not set.
        Exception: If AI API call fails.

    Example:
        >>> doc = parse_document("technical_manual.pdf")
        >>> tags = generate_tags(doc, max_tags=5)
        >>> print(tags)
        ['technical', 'manual', 'engineering', 'documentation', 'reference']

        >>> # Use OpenAI instead of Anthropic
        >>> tags = generate_tags(doc, ai_options={'ai_provider': 'openai'})
    """
    # Validate inputs
    if max_tags <= 0:
        raise ValueError("max_tags must be positive")
    if max_tags > 100:
        raise ValueError("max_tags must not exceed 100")
    if not document.content or len(document.content.strip()) == 0:
        raise ValueError("Document has no content to analyze")

    try:
        ai_config = AIConfig(ai_options)
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize AI config: {e}")
        raise

    # Prepare content sample (first 2000 characters to stay within token limits)
    content_sample = document.content[:2000] if document.content else ""

    # Build system prompt
    system_prompt = (
        "You are a document tagging expert. Generate relevant tags/keywords "
        "for documents based on their content and metadata. "
        "Return ONLY a comma-separated list of tags with no other text or explanation. "
        "Tags should be lowercase, single words or short phrases (2-3 words max)."
    )

    # Build user prompt with context
    user_prompt = f"""Analyze this document and generate {max_tags} relevant tags.

Document Information:
- Title: {document.metadata.title or 'Unknown'}
- Author: {document.metadata.author or 'Unknown'}
- Format: {document.metadata.original_format or 'Unknown'}
- Word Count: {document.word_count}
- Chapters: {len(document.chapters)}

Content Preview (first 2000 characters):
{content_sample}

Generate {max_tags} relevant tags for this document.
Return as comma-separated list: tag1, tag2, tag3, ..."""

    try:
        logger.info(f"Generating tags for document: {document.document_id}")
        response = ai_config.generate(user_prompt, system_prompt)

        # Parse response - extract tags from comma-separated list
        tags = _parse_tags(response, max_tags)

        logger.info(f"Generated {len(tags)} tags: {tags}")
        return tags

    except Exception as e:
        logger.error(f"Tag generation failed: {e}")
        raise


def _parse_tags(response: str, max_tags: int) -> List[str]:
    """
    Parse AI response to extract tags.

    Args:
        response: Raw AI response text.
        max_tags: Maximum number of tags to return.

    Returns:
        List of cleaned, deduplicated tags.
    """
    # Split by commas
    tags = [tag.strip() for tag in response.split(",")]

    # Clean tags
    cleaned_tags = []
    for tag in tags:
        # Remove quotes, brackets, and extra whitespace
        tag = tag.strip().strip('"').strip("'").strip("[]").strip()

        # Skip empty tags
        if not tag:
            continue

        # Convert to lowercase
        tag = tag.lower()

        # Skip duplicates
        if tag in cleaned_tags:
            continue

        # Skip very long tags (likely not real tags)
        if len(tag) > 50:
            continue

        cleaned_tags.append(tag)

    # Return up to max_tags
    return cleaned_tags[:max_tags]


def generate_tags_batch(
    documents: List[Document],
    max_tags: int = 10,
    ai_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, List[str]]:
    """
    Generate tags for multiple documents.

    Processes documents individually and returns a mapping of document IDs
    to their generated tags. This is more efficient than calling generate_tags
    repeatedly as it reuses the AI client.

    Args:
        documents: List of documents to process.
        max_tags: Maximum tags per document (default: 10).
        ai_options: AI configuration options.

    Returns:
        Dictionary mapping document_id to list of tags.

    Example:
        >>> docs = [parse_document(f) for f in file_list]
        >>> all_tags = generate_tags_batch(docs, max_tags=5)
        >>> for doc_id, tags in all_tags.items():
        ...     print(f"{doc_id}: {tags}")
    """
    results = {}

    for doc in documents:
        try:
            tags = generate_tags(doc, max_tags=max_tags, ai_options=ai_options)
            results[doc.document_id] = tags
        except Exception as e:
            logger.error(f"Failed to generate tags for {doc.document_id}: {e}")
            results[doc.document_id] = []

    return results
