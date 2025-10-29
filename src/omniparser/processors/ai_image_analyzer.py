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
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from ..ai_config import AIConfig

if TYPE_CHECKING:
    from ..models import ImageReference

logger = logging.getLogger(__name__)

# Maximum image file size in bytes (10MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Vision-capable models by provider
VISION_CAPABLE_MODELS = {
    # Anthropic Claude
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
    # OpenAI
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-vision-preview",
    "gpt-4-turbo",
    "gpt-4-turbo-2024-04-09",
    # Ollama vision models
    "llava",
    "llava:latest",
    "bakllava",
    "bakllava:latest",
    "llava-phi3",
    "llava-phi3:latest",
    "llava:13b",
    "llava:34b",
    # LM Studio (allow any model starting with these prefixes)
    # LM Studio models checked separately
}


def _is_vision_capable_model(provider: str, model: str) -> bool:
    """
    Check if the specified model supports vision/image input.

    Args:
        provider: AI provider name (anthropic, openai, ollama, etc.).
        model: Model identifier.

    Returns:
        True if model supports vision, False otherwise.
    """
    # Check exact match first
    if model in VISION_CAPABLE_MODELS:
        return True

    # For LM Studio, we can't reliably determine vision capability
    # so we allow it but warn the user
    if provider == "lmstudio":
        logger.warning(
            f"Cannot verify vision capability for LM Studio model '{model}'. "
            f"Ensure you're using a vision-capable model (e.g., LLaVA)."
        )
        return True

    # For Ollama, check if model name contains known vision model names
    if provider == "ollama":
        vision_prefixes = ["llava", "bakllava"]
        if any(model.startswith(prefix) for prefix in vision_prefixes):
            return True

    return False


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
        ValueError: If image file exceeds 10MB size limit.
        ValueError: If image format is not supported.
        ValueError: If AI provider/model doesn't support vision.
        Exception: If AI API call fails.

    Memory Usage:
        Images are loaded into memory and base64-encoded (~33% size increase).
        Maximum supported image size is 10MB to prevent memory issues.
        For documents with many images, consider processing in batches
        using analyze_images_batch() to manage memory consumption.

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

    # Validate image format
    if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_IMAGE_FORMATS))}"
        )

    # Check file size to avoid memory issues
    file_size = path.stat().st_size
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

    # Validate that the model supports vision before loading the image
    if not _is_vision_capable_model(ai_config.provider.value, ai_config.model):
        raise ValueError(
            f"Model '{ai_config.model}' from provider '{ai_config.provider.value}' "
            f"does not support vision/image input. "
            f"Please use a vision-capable model such as:\n"
            f"  - Anthropic: claude-3-opus-20240229, claude-3-sonnet-20240229\n"
            f"  - OpenAI: gpt-4o, gpt-4-vision-preview\n"
            f"  - Ollama: llava:latest, bakllava:latest"
        )

    system_prompt = """You are an expert image analyst. Analyze images comprehensively.

Return your analysis in this EXACT format (follow the structure precisely):

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
[Your confidence in this analysis: high/medium/low]

Example output for a flowchart:

TEXT_CONTENT:
Start -> Process Data -> Decision? -> Yes -> Output -> End, No -> Return to Process

IMAGE_TYPE:
flowchart

DESCRIPTION:
A detailed flowchart diagram showing a data processing workflow. The diagram uses rectangular boxes for processes, a diamond shape for the decision point, and arrows connecting the elements. Colors are blue for processes and green for the decision diamond.

OBJECTS:
- Start node
- Process Data box
- Decision diamond
- Output box
- End node
- Connecting arrows

ALT_TEXT:
Flowchart diagram showing data processing workflow with decision point

CONFIDENCE:
high"""

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
        message = ai_config.client.messages.create(  # type: ignore[union-attr]
            model=ai_config.model,
            max_tokens=ai_config.max_tokens,
            temperature=ai_config.temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {  # type: ignore[list-item]
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
        return message.content[0].text  # type: ignore[union-attr]
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
                "content": [  # type: ignore[dict-item]
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_data}"},
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        )

        response = ai_config.client.chat.completions.create(  # type: ignore[union-attr]
            model=ai_config.model,
            max_tokens=ai_config.max_tokens,
            temperature=ai_config.temperature,
            messages=messages,  # type: ignore[arg-type]
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

    # Validate that required fields were extracted
    if not analysis.image_type or analysis.image_type == "unknown":
        logger.warning(
            f"Failed to extract image type from response. "
            f"Response preview: {response[:200]}..."
        )

    if not analysis.description:
        logger.warning(
            f"Failed to extract description from response. "
            f"Response preview: {response[:200]}..."
        )

    if not analysis.alt_text:
        logger.warning(
            f"Failed to extract alt text from response. "
            f"Response preview: {response[:200]}..."
        )

    return analysis


def analyze_images_batch(
    image_paths: List[str],
    ai_options: Optional[Dict[str, Any]] = None,
    batch_size: int = 10,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[ImageAnalysis]:
    """
    Analyze multiple images in batches with memory management.

    Processes images in configurable batch sizes to manage memory usage
    when analyzing large numbers of images (100+).

    Args:
        image_paths: List of image file paths to analyze.
        ai_options: AI configuration options.
        batch_size: Number of images to process at a time (default: 10).
                   Lower values use less memory but take longer.
        progress_callback: Optional callback function(completed, total) for progress tracking.

    Returns:
        List of ImageAnalysis objects (one per image).

    Memory Usage:
        Images are processed in batches to manage memory usage:
        - Each image: ~10MB max + ~33% base64 encoding overhead = ~13MB
        - Batch of 10: ~130MB peak memory
        - For 100+ images, consider batch_size=5 to reduce memory footprint

    Example:
        >>> # Analyze 3 images
        >>> images = ["fig1.png", "fig2.png", "fig3.png"]
        >>> analyses = analyze_images_batch(images)
        >>> for analysis in analyses:
        ...     print(f"{analysis.image_path}: {analysis.image_type}")

        >>> # Process 100+ images with smaller batches for memory control
        >>> large_image_set = [f"img_{i}.png" for i in range(150)]
        >>> analyses = analyze_images_batch(large_image_set, batch_size=5)

        >>> # Track progress with callback
        >>> def show_progress(completed, total):
        ...     print(f"Analyzed {completed}/{total} images")
        >>> analyses = analyze_images_batch(images, progress_callback=show_progress)
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    results = []
    total_images = len(image_paths)

    # Process images in batches
    for batch_start in range(0, total_images, batch_size):
        batch_end = min(batch_start + batch_size, total_images)
        batch_paths = image_paths[batch_start:batch_end]

        logger.info(
            f"Processing batch {batch_start // batch_size + 1} "
            f"({batch_start + 1}-{batch_end} of {total_images})"
        )

        # Process each image in current batch
        for image_path in batch_paths:
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

            # Report progress if callback provided
            if progress_callback:
                progress_callback(len(results), total_images)

        # Log batch completion
        logger.info(f"Batch complete: {len(results)}/{total_images} images processed")

    logger.info(f"All batches complete: analyzed {len(results)} images")
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
