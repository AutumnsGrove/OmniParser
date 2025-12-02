"""
AI-powered photo analysis with sentiment, mood, and caption generation.

This module provides specialized analysis for photographs, including:
- Sentiment analysis (positive, negative, neutral)
- Mood detection (happy, sad, peaceful, dramatic, etc.)
- Scene classification (landscape, portrait, street, nature, etc.)
- Subject detection (people, animals, objects, etc.)
- Caption generation for social media
- Tag suggestions

Supports all vision-capable AI providers:
- Anthropic Claude (claude-3-opus, claude-3-sonnet, claude-3-5-sonnet)
- OpenAI (gpt-4o, gpt-4-vision-preview)
- OpenRouter (various vision models)
- Ollama (llava, bakllava)
- LM Studio (vision models)
- Cloudflare Workers AI (@cf/meta/llama-3.2-11b-vision-instruct)

Example:
    >>> from omniparser.processors.ai_photo_analyzer import analyze_photo
    >>> analysis = analyze_photo("sunset.jpg")
    >>> print(analysis["sentiment"])  # "positive"
    >>> print(analysis["mood"])  # ["peaceful", "serene", "warm"]
    >>> print(analysis["caption"])  # "Golden hour magic at the beach 🌅"
"""

import base64
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ai_config import AIConfig, AIProvider

logger = logging.getLogger(__name__)

# Maximum image file size in bytes (10MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# Supported image formats
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

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
    # Cloudflare
    "@cf/meta/llama-3.2-11b-vision-instruct",
    "@cf/llava-hf/llava-1.5-7b-hf",
}


def analyze_photo(
    image_path: str,
    ai_options: Optional[Dict[str, Any]] = None,
    include_sentiment: bool = True,
    include_caption: bool = True,
) -> Dict[str, Any]:
    """
    Perform comprehensive AI analysis on a photograph.

    Analyzes the photo for sentiment, mood, subjects, scene type, and generates
    a caption and tags suitable for social media or documentation.

    Args:
        image_path: Path to the image file.
        ai_options: AI configuration options:
            - ai_provider (str): Provider name (anthropic, openai, cloudflare, etc.)
            - ai_model (str): Model name
            - max_tokens (int): Max response tokens
            - temperature (float): Sampling temperature
        include_sentiment: Include sentiment/mood analysis. Default: True
        include_caption: Generate social media caption. Default: True

    Returns:
        Dictionary with analysis results:
            - description (str): Detailed description of the photo
            - sentiment (str): Overall sentiment (positive/negative/neutral)
            - mood (List[str]): Mood descriptors (peaceful, dramatic, etc.)
            - subjects (List[str]): Main subjects in the photo
            - scene_type (str): Type of scene (landscape, portrait, etc.)
            - caption (str): Social media caption
            - tags (List[str]): Suggested hashtags/tags
            - alt_text (str): Accessibility alt text
            - confidence (float): Analysis confidence (0.0-1.0)

    Raises:
        ValueError: If image file doesn't exist or is invalid.
        Exception: If AI API call fails.

    Example:
        >>> analysis = analyze_photo(
        ...     "beach_sunset.jpg",
        ...     ai_options={"ai_provider": "anthropic"}
        ... )
        >>> print(f"Sentiment: {analysis['sentiment']}")
        >>> print(f"Mood: {', '.join(analysis['mood'])}")
        >>> print(f"Caption: {analysis['caption']}")
    """
    path = Path(image_path)

    # Validate file
    if not path.exists():
        raise ValueError(f"Image file not found: {image_path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    file_size = path.stat().st_size
    if file_size > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image file too large: {file_size / (1024 * 1024):.1f}MB. "
            f"Maximum: {MAX_IMAGE_SIZE / (1024 * 1024)}MB"
        )

    # Initialize AI config
    try:
        ai_config = AIConfig(ai_options)
    except (ValueError, ImportError) as e:
        logger.error(f"Failed to initialize AI config: {e}")
        raise

    # Build the analysis prompt
    system_prompt = _build_system_prompt(include_sentiment, include_caption)
    user_prompt = _build_user_prompt(include_sentiment, include_caption)

    # Perform vision analysis
    try:
        if ai_config.provider == AIProvider.ANTHROPIC:
            response = _analyze_anthropic(ai_config, path, user_prompt, system_prompt)
        elif ai_config.provider == AIProvider.CLOUDFLARE:
            response = _analyze_cloudflare(ai_config, path, user_prompt, system_prompt)
        else:
            # OpenAI-compatible providers
            response = _analyze_openai(ai_config, path, user_prompt, system_prompt)

        # Parse response
        analysis = _parse_analysis_response(response, include_sentiment, include_caption)

        logger.info(
            f"Photo analysis complete: sentiment={analysis.get('sentiment')}, "
            f"mood={analysis.get('mood')}, subjects={len(analysis.get('subjects', []))}"
        )

        return analysis

    except Exception as e:
        logger.error(f"Photo analysis failed: {e}")
        raise


def _build_system_prompt(include_sentiment: bool, include_caption: bool) -> str:
    """Build system prompt for photo analysis."""
    prompt = """You are an expert photo analyst and social media content creator.
Analyze photographs to extract meaningful information about their content, mood, and visual appeal.

Your analysis should be:
- Accurate and objective for descriptions
- Emotionally intelligent for sentiment/mood
- Creative but authentic for captions
- Comprehensive for subject detection

Return your analysis in a structured JSON format."""

    return prompt


def _build_user_prompt(include_sentiment: bool, include_caption: bool) -> str:
    """Build user prompt for photo analysis."""
    fields = [
        '"description": "Detailed description of what is shown in the photo (2-3 sentences)"',
        '"subjects": ["list", "of", "main", "subjects"]',
        '"scene_type": "one of: landscape, portrait, street, nature, architecture, food, product, action, abstract, macro, night, event, other"',
        '"alt_text": "Concise accessibility description (under 150 characters)"',
        '"tags": ["relevant", "hashtags", "without", "the", "hash", "symbol"]',
    ]

    if include_sentiment:
        fields.extend(
            [
                '"sentiment": "one of: positive, negative, neutral, mixed"',
                '"mood": ["list", "of", "mood", "descriptors"]',
                '"emotional_impact": "Brief description of emotional response this photo might evoke"',
            ]
        )

    if include_caption:
        fields.append(
            '"caption": "Engaging social media caption (with appropriate emoji)"'
        )

    fields.append('"confidence": "your confidence in this analysis: high, medium, or low"')

    json_structure = "{\n  " + ",\n  ".join(fields) + "\n}"

    prompt = f"""Analyze this photograph comprehensively.

Return ONLY valid JSON in this exact structure:
{json_structure}

Mood descriptors can include: peaceful, dramatic, joyful, melancholic, energetic, serene,
mysterious, romantic, nostalgic, tense, playful, solemn, whimsical, powerful, intimate, etc.

Be specific about subjects - identify people (if any), animals, objects, and environmental elements.
For captions, match the tone to the photo's mood and include 1-3 relevant emojis.

Analyze now:"""

    return prompt


def _analyze_anthropic(
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


def _analyze_openai(
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


def _analyze_cloudflare(
    ai_config: AIConfig, image_path: Path, user_prompt: str, system_prompt: str
) -> str:
    """Analyze image using Cloudflare Workers AI Vision."""
    import requests

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{ai_config._cloudflare_account_id}/ai/run/{ai_config.model}"  # type: ignore[attr-defined]
    )

    headers = {
        "Authorization": f"Bearer {ai_config._cloudflare_api_token}",  # type: ignore[attr-defined]
        "Content-Type": "application/json",
    }

    # Build messages with image
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
            ],
        }
    )

    payload = {
        "messages": messages,
        "max_tokens": ai_config.max_tokens,
    }

    response = requests.post(
        url, headers=headers, json=payload, timeout=ai_config.timeout
    )
    response.raise_for_status()

    result = response.json()
    if not result.get("success"):
        errors = result.get("errors", [])
        raise ValueError(f"Cloudflare API error: {errors}")

    ai_result = result.get("result", {})
    if isinstance(ai_result, dict):
        return ai_result.get("response", "")
    return str(ai_result)


def _parse_analysis_response(
    response: str, include_sentiment: bool, include_caption: bool
) -> Dict[str, Any]:
    """Parse AI analysis response into structured dictionary.

    Args:
        response: Raw AI response text.
        include_sentiment: Whether sentiment was requested.
        include_caption: Whether caption was requested.

    Returns:
        Dictionary with parsed analysis results.
    """
    # Initialize default result
    result: Dict[str, Any] = {
        "description": "",
        "subjects": [],
        "scene_type": "other",
        "alt_text": "",
        "tags": [],
        "confidence": 0.5,
    }

    if include_sentiment:
        result["sentiment"] = "neutral"
        result["mood"] = []
        result["emotional_impact"] = ""

    if include_caption:
        result["caption"] = ""

    # Try to extract JSON from response
    try:
        # Look for JSON in the response
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            json_str = json_match.group()
            parsed = json.loads(json_str)

            # Update result with parsed values
            if isinstance(parsed, dict):
                for key in result.keys():
                    if key in parsed:
                        result[key] = parsed[key]

                # Handle confidence conversion
                if "confidence" in parsed:
                    conf_str = str(parsed["confidence"]).lower()
                    confidence_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
                    result["confidence"] = confidence_map.get(conf_str, 0.5)

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON response: {e}")
        # Try to extract fields manually
        result = _extract_fields_manually(response, result)

    # Ensure lists are lists
    if isinstance(result.get("subjects"), str):
        result["subjects"] = [s.strip() for s in result["subjects"].split(",")]
    if isinstance(result.get("mood"), str):
        result["mood"] = [m.strip() for m in result["mood"].split(",")]
    if isinstance(result.get("tags"), str):
        result["tags"] = [t.strip().lstrip("#") for t in result["tags"].split(",")]

    # Clean up tags (remove # symbols)
    result["tags"] = [t.lstrip("#").strip() for t in result.get("tags", [])]

    return result


def _extract_fields_manually(response: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract fields from non-JSON response using regex.

    Args:
        response: Raw response text.
        result: Default result dictionary.

    Returns:
        Updated result dictionary.
    """
    # Try to extract description
    desc_match = re.search(
        r"description[\"']?\s*[:=]\s*[\"'](.+?)[\"']", response, re.IGNORECASE
    )
    if desc_match:
        result["description"] = desc_match.group(1)

    # Try to extract sentiment
    sent_match = re.search(
        r"sentiment[\"']?\s*[:=]\s*[\"']?(positive|negative|neutral|mixed)[\"']?",
        response,
        re.IGNORECASE,
    )
    if sent_match:
        result["sentiment"] = sent_match.group(1).lower()

    # Try to extract caption
    cap_match = re.search(
        r"caption[\"']?\s*[:=]\s*[\"'](.+?)[\"']", response, re.IGNORECASE
    )
    if cap_match:
        result["caption"] = cap_match.group(1)

    return result


def analyze_photos_batch(
    image_paths: List[str],
    ai_options: Optional[Dict[str, Any]] = None,
    include_sentiment: bool = True,
    include_caption: bool = True,
    batch_size: int = 5,
) -> List[Dict[str, Any]]:
    """
    Analyze multiple photos in batches.

    Args:
        image_paths: List of image file paths.
        ai_options: AI configuration options.
        include_sentiment: Include sentiment analysis.
        include_caption: Generate captions.
        batch_size: Number of images per batch.

    Returns:
        List of analysis dictionaries.

    Example:
        >>> images = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
        >>> analyses = analyze_photos_batch(images)
        >>> for img, analysis in zip(images, analyses):
        ...     print(f"{img}: {analysis['sentiment']}")
    """
    results = []

    for i, image_path in enumerate(image_paths):
        logger.info(f"Analyzing photo {i + 1}/{len(image_paths)}: {image_path}")

        try:
            analysis = analyze_photo(
                image_path,
                ai_options=ai_options,
                include_sentiment=include_sentiment,
                include_caption=include_caption,
            )
            results.append(analysis)
        except Exception as e:
            logger.error(f"Failed to analyze {image_path}: {e}")
            results.append(
                {
                    "description": f"[Analysis failed: {str(e)}]",
                    "error": str(e),
                    "sentiment": "unknown",
                    "mood": [],
                    "subjects": [],
                    "tags": [],
                }
            )

    return results
