"""Post-processing components for OmniParser."""

from .chapter_detector import detect_chapters
from .markdown_converter import html_to_markdown
from .metadata_extractor import extract_html_metadata
from .text_cleaner import clean_text

# AI processors (optional - require AI provider configuration)
from .ai_image_analyzer import ImageAnalysis, analyze_image, analyze_images_batch
from .ai_photo_analyzer import analyze_photo, analyze_photos_batch

__all__ = [
    "detect_chapters",
    "html_to_markdown",
    "extract_html_metadata",
    "clean_text",
    # AI processors
    "ImageAnalysis",
    "analyze_image",
    "analyze_images_batch",
    "analyze_photo",
    "analyze_photos_batch",
]
