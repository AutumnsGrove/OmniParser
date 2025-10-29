"""
AI-powered image description generation.

This module provides automatic alt text and description generation for images
found in parsed documents. This is useful for accessibility, SEO, and content
understanding.

Features:
    - Generate descriptive alt text for images
    - Support for vision-capable AI models (Claude Vision, GPT-4 Vision)
    - Batch processing for multiple images
    - Context-aware descriptions

Note:
    Requires vision-capable AI models:
    - Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku
    - OpenAI: gpt-4-vision-preview, gpt-4o
    - Local: Some Ollama vision models (llava, bakllava)

Example:
    >>> from omniparser import parse_document
    >>> from omniparser.processors.ai_image_describer import describe_image
    >>> doc = parse_document("book.epub")
    >>> if doc.images:
    ...     img = doc.images[0]
    ...     description = describe_image(img)
    ...     print(description)
"""

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ai_config import AIConfig
from ..models import Document, ImageReference

logger = logging.getLogger(__name__)

# Maximum image file size in bytes (10MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024


def describe_image(
    image: ImageReference,
    context: Optional[str] = None,
    ai_options: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a descriptive alt text for an image using AI vision.

    Args:
        image: ImageReference object with image path.
        context: Optional context about the image (surrounding text, chapter title, etc.).
        ai_options: AI configuration options. Must use vision-capable model.

    Returns:
        Generated image description suitable for alt text.

    Raises:
        ValueError: If image file_path is None or file doesn't exist.
        ValueError: If AI provider/model doesn't support vision.
        Exception: If AI API call fails.

    Example:
        >>> img = ImageReference(
        ...     image_id="img_001",
        ...     position=100,
        ...     file_path="/tmp/cover.jpg"
        ... )
        >>> description = describe_image(img, context="Book cover image")
        >>> print(description)
        'A vibrant illustration showing...'

        >>> # Use specific vision model
        >>> description = describe_image(
        ...     img,
        ...     ai_options={
        ...         'ai_provider': 'anthropic',
        ...         'ai_model': 'claude-3-haiku-20240307'
        ...     }
        ... )
    """
    if not image.file_path:
        raise ValueError("Image file_path is required for AI description")

    image_path = Path(image.file_path)
    if not image_path.exists():
        raise ValueError(f"Image file not found: {image.file_path}")

    # Check file size to avoid memory issues
    file_size = image_path.stat().st_size
    if file_size > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image file too large: {file_size / (1024 * 1024):.1f}MB. "
            f"Maximum size: {MAX_IMAGE_SIZE / (1024 * 1024)}MB"
        )

    try:
        ai_config = AIConfig(ai_options)
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize AI config: {e}")
        raise

    # Build prompt
    system_prompt = (
        "You are an image description expert. Generate concise, descriptive "
        "alt text for images that would be useful for accessibility and SEO. "
        "Describe what you see clearly and objectively. Keep descriptions under 150 characters "
        "unless the image is complex."
    )

    # Context-aware prompt
    if context:
        user_prompt = f"""Describe this image.

Context: {context}

Generate a clear, concise description suitable for alt text:"""
    else:
        user_prompt = "Describe this image clearly and concisely for use as alt text:"

    # For Anthropic Claude with vision
    if ai_config.provider.value == "anthropic":
        description = _describe_image_anthropic(
            ai_config, image_path, user_prompt, system_prompt
        )
    else:
        # For OpenAI and OpenAI-compatible APIs
        description = _describe_image_openai(
            ai_config, image_path, user_prompt, system_prompt
        )

    logger.info(f"Generated description for image: {image.image_id}")
    return description.strip()


def _describe_image_anthropic(
    ai_config: AIConfig, image_path: Path, user_prompt: str, system_prompt: str
) -> str:
    """Generate image description using Anthropic Claude Vision."""
    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Determine media type
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(image_path.suffix.lower(), "image/jpeg")

    try:
        message = ai_config.client.messages.create(
            model=ai_config.model,
            max_tokens=ai_config.max_tokens,
            temperature=ai_config.temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Anthropic vision API call failed: {e}")
        raise


def _describe_image_openai(
    ai_config: AIConfig, image_path: Path, user_prompt: str, system_prompt: str
) -> str:
    """Generate image description using OpenAI Vision (or compatible API)."""
    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Determine media type
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(image_path.suffix.lower(), "image/jpeg")

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_data}"},
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        )

        response = ai_config.client.chat.completions.create(
            model=ai_config.model,
            max_tokens=ai_config.max_tokens,
            temperature=ai_config.temperature,
            messages=messages,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"OpenAI vision API call failed: {e}")
        raise


def describe_document_images(
    document: Document, ai_options: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Generate descriptions for all images in a document.

    Args:
        document: Parsed document with images.
        ai_options: AI configuration options.

    Returns:
        Dictionary mapping image_id to description.

    Example:
        >>> doc = parse_document("illustrated_book.epub")
        >>> descriptions = describe_document_images(doc)
        >>> for img_id, desc in descriptions.items():
        ...     print(f"{img_id}: {desc}")
    """
    descriptions: Dict[str, str] = {}

    if not document.images:
        logger.info("No images found in document")
        return descriptions

    logger.info(f"Describing {len(document.images)} images...")

    for image in document.images:
        try:
            # Get context from surrounding text
            context = _get_image_context(document, image)

            # Generate description
            description = describe_image(image, context=context, ai_options=ai_options)
            descriptions[image.image_id] = description

        except Exception as e:
            logger.error(f"Failed to describe image {image.image_id}: {e}")
            descriptions[image.image_id] = f"[Description failed: {str(e)}]"

    logger.info(f"Successfully described {len(descriptions)} images")
    return descriptions


def _get_image_context(document: Document, image: ImageReference) -> str:
    """
    Extract context text surrounding an image.

    Args:
        document: Document containing the image.
        image: Image reference to get context for.

    Returns:
        Context text (up to 200 characters before/after image position).
    """
    if not document.content or image.position < 0:
        return ""

    # Get text before and after image position
    start = max(0, image.position - 200)
    end = min(len(document.content), image.position + 200)

    context = document.content[start:end].strip()

    # If image has existing alt text, include it
    if image.alt_text:
        context = f"Existing alt text: '{image.alt_text}'. " + context

    return context


def update_image_descriptions(
    document: Document, ai_options: Optional[Dict[str, Any]] = None
) -> Document:
    """
    Update all image alt_text fields in document with AI-generated descriptions.

    Modifies the document in place by updating ImageReference.alt_text.

    Args:
        document: Parsed document with images.
        ai_options: AI configuration options.

    Returns:
        The same document with updated image descriptions.

    Example:
        >>> doc = parse_document("book.epub")
        >>> doc = update_image_descriptions(doc)
        >>> # All images now have AI-generated alt text
        >>> for img in doc.images:
        ...     print(f"{img.image_id}: {img.alt_text}")
    """
    descriptions = describe_document_images(document, ai_options)

    # Update ImageReference objects
    for image in document.images:
        if image.image_id in descriptions:
            image.alt_text = descriptions[image.image_id]

    logger.info(f"Updated {len(descriptions)} image descriptions in document")
    return document
