"""
AI-powered comprehensive image analysis pipeline.

This module provides a reusable pipeline for analyzing images found in documents.
It extracts text (OCR), generates descriptions, classifies image types, and more.
Designed to be used across all parsers (EPUB, PDF, DOCX, etc.).

Features:
    - Text extraction from images (OCR)
    - Content description and scene analysis
    - Image type classification (diagram, photo, chart, screenshot, etc.)
    - Object and element detection
    - Alt text generation for accessibility
    - Support for vision-capable models (Anthropic, OpenAI, some Ollama models)

Pipeline Stages:
    1. Text Extraction: Extract any readable text from the image
    2. Content Analysis: Describe what's in the image
    3. Type Classification: Classify image type (diagram, chart, photo, etc.)
    4. Accessibility: Generate concise alt text

Example:
    >>> from omniparser.processors.ai_image_analyzer import analyze_image
    >>> analysis = analyze_image("/path/to/image.png")
    >>> print(analysis['text_content'])  # Extracted text
    >>> print(analysis['description'])    # What's in the image
    >>> print(analysis['image_type'])     # diagram/chart/photo/etc
    >>> print(analysis['alt_text'])       # Accessibility text
"""

import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..ai_config import AIConfig

if TYPE_CHECKING:
    from ..models import ImageReference

logger = logging.getLogger(__name__)


@dataclass
class ImageAnalysis:
    """
    Complete analysis results for an image.

    Attributes:
        image_path: Path to the analyzed image.
        text_content: Text extracted from the image (OCR).
        description: Detailed description of image content.
        image_type: Classification (diagram, chart, photo, screenshot, illustration, etc.).
        objects: List of detected objects/elements in the image.
        alt_text: Concise alt text for accessibility.
        confidence: Confidence score for the analysis (0.0-1.0).
        raw_response: Raw AI response for debugging.
    """

    image_path: str
    text_content: str = ""
    description: str = ""
    image_type: str = "unknown"
    objects: Optional[List[str]] = None
    alt_text: str = ""
    confidence: float = 0.0
    raw_response: str = ""

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.objects is None:
            self.objects = []


def analyze_image(
    image_path: str, ai_options: Optional[Dict[str, Any]] = None
) -> ImageAnalysis:
    """
    Perform comprehensive AI analysis on an image.

    This is the main entry point for the image analysis pipeline. It performs
    all analysis stages and returns a complete ImageAnalysis object.

    Args:
        image_path: Path to the image file to analyze.
        ai_options: AI configuration options. Recommended models:
            - Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku
            - OpenAI: gpt-4o, gpt-4-vision-preview
            - Ollama: llava, bakllava (vision models)

    Returns:
        ImageAnalysis object with complete analysis results.

    Raises:
        ValueError: If image file doesn't exist.
        ValueError: If AI provider/model doesn't support vision.
        Exception: If AI API call fails.

    Example:
        >>> # Analyze a diagram from a PDF
        >>> analysis = analyze_image("figure_3_2.png")
        >>> print(f"Type: {analysis.image_type}")
        >>> print(f"Text: {analysis.text_content}")
        >>> print(f"Description: {analysis.description}")

        >>> # Use specific model
        >>> analysis = analyze_image(
        ...     "chart.png",
        ...     ai_options={
        ...         'ai_provider': 'anthropic',
        ...         'ai_model': 'claude-3-opus-20240229'
        ...     }
        ... )

        >>> # Use local model via Ollama
        >>> analysis = analyze_image(
        ...     "photo.jpg",
        ...     ai_options={
        ...         'ai_provider': 'ollama',
        ...         'ai_model': 'llava:latest'
        ...     }
        ... )
    """
    path = Path(image_path)
    if not path.exists():
        raise ValueError(f"Image file not found: {image_path}")

    try:
        ai_config = AIConfig(ai_options)
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize AI config: {e}")
        raise

    system_prompt = """You are an expert image analyst. Analyze images comprehensively.

Return your analysis in this EXACT format:

TEXT_CONTENT:
[Any text visible in the image, or "None" if no text]

IMAGE_TYPE:
[One of: diagram, flowchart, chart, graph, table, screenshot, photo, illustration, map, icon, other]

DESCRIPTION:
[Detailed description of the image content, objects, layout, colors, etc.]

OBJECTS:
- [object 1]
- [object 2]
- [object 3]

ALT_TEXT:
[Concise alt text suitable for accessibility, under 150 characters]

CONFIDENCE:
[Your confidence in this analysis: high/medium/low]"""

    user_prompt = """Analyze this image comprehensively. Extract any text, classify the image type,
describe the content in detail, list main objects/elements, and generate alt text.

Provide analysis:"""

    # Perform vision analysis
    if ai_config.provider.value == "anthropic":
        response = _analyze_image_anthropic(ai_config, path, user_prompt, system_prompt)
    else:
        response = _analyze_image_openai(ai_config, path, user_prompt, system_prompt)

    # Parse response into ImageAnalysis object
    analysis = _parse_analysis_response(response, str(image_path))

    logger.info(
        f"Analyzed image {path.name}: type={analysis.image_type}, "
        f"text_length={len(analysis.text_content)}, confidence={analysis.confidence}"
    )

    return analysis


def _analyze_image_anthropic(
    ai_config: AIConfig, image_path: Path, user_prompt: str, system_prompt: str
) -> str:
    """Analyze image using Anthropic Claude Vision."""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

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


def _analyze_image_openai(
    ai_config: AIConfig, image_path: Path, user_prompt: str, system_prompt: str
) -> str:
    """Analyze image using OpenAI Vision or compatible API."""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

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


def _parse_analysis_response(response: str, image_path: str) -> ImageAnalysis:
    """
    Parse AI analysis response into ImageAnalysis object.

    Args:
        response: Raw AI response text.
        image_path: Path to the analyzed image.

    Returns:
        ImageAnalysis object with parsed data.
    """
    import re

    analysis = ImageAnalysis(image_path=image_path, raw_response=response)

    try:
        # Extract text content
        text_match = re.search(
            r"TEXT_CONTENT:\s*\n(.+?)(?=\n\n|\nIMAGE_TYPE:)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if text_match:
            text = text_match.group(1).strip()
            analysis.text_content = "" if text.lower() == "none" else text

        # Extract image type
        type_match = re.search(
            r"IMAGE_TYPE:\s*\n?(.+?)(?=\n\n|\nDESCRIPTION:)",
            response,
            re.IGNORECASE,
        )
        if type_match:
            analysis.image_type = type_match.group(1).strip().lower()

        # Extract description
        desc_match = re.search(
            r"DESCRIPTION:\s*\n(.+?)(?=\n\n|\nOBJECTS:)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if desc_match:
            analysis.description = desc_match.group(1).strip()

        # Extract objects
        objects_match = re.search(
            r"OBJECTS:\s*\n((?:^[-*]\s*.+$\n?)+)",
            response,
            re.MULTILINE | re.IGNORECASE,
        )
        if objects_match:
            objects_text = objects_match.group(1)
            objects = [
                line.strip("- *").strip()
                for line in objects_text.split("\n")
                if line.strip()
            ]
            analysis.objects = [obj for obj in objects if obj]

        # Extract alt text
        alt_match = re.search(
            r"ALT_TEXT:\s*\n?(.+?)(?=\n\n|\nCONFIDENCE:)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if alt_match:
            analysis.alt_text = alt_match.group(1).strip()

        # Extract confidence
        conf_match = re.search(r"CONFIDENCE:\s*\n?(.+)", response, re.IGNORECASE)
        if conf_match:
            conf_str = conf_match.group(1).strip().lower()
            confidence_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
            analysis.confidence = confidence_map.get(conf_str, 0.5)

    except Exception as e:
        logger.warning(f"Error parsing analysis response: {e}")
        logger.debug(f"Raw response: {response}")

    return analysis


def analyze_images_batch(
    image_paths: List[str], ai_options: Optional[Dict[str, Any]] = None
) -> List[ImageAnalysis]:
    """
    Analyze multiple images in batch.

    Args:
        image_paths: List of image file paths to analyze.
        ai_options: AI configuration options.

    Returns:
        List of ImageAnalysis objects (one per image).

    Example:
        >>> images = ["fig1.png", "fig2.png", "fig3.png"]
        >>> analyses = analyze_images_batch(images)
        >>> for analysis in analyses:
        ...     print(f"{analysis.image_path}: {analysis.image_type}")
    """
    results = []

    for image_path in image_paths:
        try:
            analysis = analyze_image(image_path, ai_options)
            results.append(analysis)
        except Exception as e:
            logger.error(f"Failed to analyze {image_path}: {e}")
            # Add failed analysis
            results.append(
                ImageAnalysis(
                    image_path=image_path,
                    description=f"[Analysis failed: {str(e)}]",
                )
            )

    logger.info(f"Analyzed {len(results)} images")
    return results


# Integration with existing ImageReference model
def analyze_image_reference(
    image: "ImageReference", ai_options: Optional[Dict[str, Any]] = None
) -> ImageAnalysis:
    """
    Analyze an ImageReference object from a parsed document.

    This is a convenience wrapper that extracts the file path from an
    ImageReference and performs analysis.

    Args:
        image: ImageReference object from a Document.
        ai_options: AI configuration options.

    Returns:
        ImageAnalysis object.

    Example:
        >>> from omniparser import parse_document
        >>> doc = parse_document("book.epub")
        >>> for img in doc.images:
        ...     analysis = analyze_image_reference(img)
        ...     print(f"{img.image_id}: {analysis.description}")
    """
    if not image.file_path:
        raise ValueError("ImageReference must have file_path set")

    return analyze_image(image.file_path, ai_options)
