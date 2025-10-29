"""
Integration tests for AI vision features with real API calls.

These tests validate the image analysis and description functionality
using actual vision-capable AI models. They are skipped by default.

Run with:
    pytest tests/integration/test_ai_vision_integration.py --run-integration

Requirements:
    - ANTHROPIC_API_KEY environment variable or secrets.json
    - Test images in tests/fixtures/images/
    - Vision-capable model (e.g., claude-3-haiku-20240307)

Example:
    export ANTHROPIC_API_KEY=sk-ant-...
    pytest tests/integration/test_ai_vision_integration.py --run-integration -v
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List

import pytest

from omniparser.models import Chapter, Document, ImageReference, Metadata, ProcessingInfo
from omniparser.processors.ai_image_analyzer import (
    ImageAnalysis,
    analyze_image,
    analyze_images_batch,
)
from omniparser.processors.ai_image_describer import (
    describe_document_images,
    describe_image,
    update_image_descriptions,
)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "images"


@pytest.fixture
def test_images() -> List[Path]:
    """
    Get list of test images from fixtures directory.

    User should add test images to tests/fixtures/images/ before running.
    Expected mix: diagrams, charts, photos, screenshots.
    """
    if not FIXTURES_DIR.exists():
        pytest.skip(f"Test images directory not found: {FIXTURES_DIR}")

    # Find all image files
    image_files = []
    for pattern in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp"]:
        image_files.extend(FIXTURES_DIR.glob(pattern))

    if not image_files:
        pytest.skip(f"No test images found in {FIXTURES_DIR}")

    return sorted(image_files)[:10]  # Limit to first 10 images


@pytest.fixture
def sample_document_with_images(test_images: List[Path]) -> Document:
    """Create a sample document with image references for testing."""
    metadata = Metadata(
        title="Test Document with Images",
        author="Test Author",
        original_format="test",
    )

    processing_info = ProcessingInfo(
        parser_used="TestParser",
        parser_version="1.0.0",
        processing_time=1.0,
        timestamp=datetime.now(),
    )

    # Create image references
    images = []
    for idx, img_path in enumerate(test_images[:3]):  # Use first 3 images
        img_ref = ImageReference(
            image_id=f"img_{idx:03d}",
            file_path=str(img_path),
            format=img_path.suffix[1:].upper(),  # .png -> PNG
            width=800,
            height=600,
            file_size=img_path.stat().st_size,
        )
        images.append(img_ref)

    # Create chapter with image references
    chapter = Chapter(
        chapter_id="ch_001",
        title="Chapter with Images",
        content=f"""
This chapter contains several images for testing.

[Image 1 here]

Some text describing the first image and its context.

[Image 2 here]

More text providing context for the second image.

[Image 3 here]

Final section with the third image.
""",
        order=1,
        images=images,
    )

    return Document(
        document_id="test_doc_with_images",
        content="Document with test images for AI vision analysis.",
        chapters=[chapter],
        images=images,
        metadata=metadata,
        processing_info=processing_info,
        word_count=50,
        estimated_reading_time=1,
    )


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
)
class TestImageAnalysisIntegration:
    """Integration tests for AI image analysis with real API calls."""

    def test_analyze_single_image_anthropic(self, test_images: List[Path]) -> None:
        """Test analyzing a single image with Anthropic Claude."""
        if not test_images:
            pytest.skip("No test images available")

        image_path = test_images[0]

        # Use Anthropic with Haiku (fast and cost-effective for testing)
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        result = analyze_image(image_path, ai_options=ai_options)

        # Verify result structure
        assert isinstance(result, ImageAnalysis)
        assert hasattr(result, "text_content")
        assert hasattr(result, "description")
        assert hasattr(result, "image_type")
        assert hasattr(result, "alt_text")
        assert hasattr(result, "confidence")

        # Verify types
        assert isinstance(result.text_content, str)
        assert isinstance(result.description, str)
        assert isinstance(result.image_type, str)
        assert isinstance(result.alt_text, str)
        assert isinstance(result.confidence, (int, float))

        # Verify confidence is in valid range (0.0-1.0)
        assert 0 <= result.confidence <= 1.0

        # Verify image_type is one of the expected types
        valid_types = {
            "diagram", "chart", "photo", "screenshot", "flowchart",
            "infographic", "map", "illustration", "other"
        }
        assert result.image_type.lower() in valid_types

        print(f"\n✅ Image Analysis Result for {image_path.name}:")
        print(f"   Type: {result.image_type}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Description: {result.description[:100]}...")
        print(f"   Text Content: {result.text_content[:50] if result.text_content else '(no text)'}...")
        print(f"   Alt Text: {result.alt_text}")

    def test_analyze_multiple_image_types(self, test_images: List[Path]) -> None:
        """Test analyzing different types of images."""
        if len(test_images) < 3:
            pytest.skip("Need at least 3 test images")

        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        results = []
        for image_path in test_images[:3]:  # Test first 3 images
            result = analyze_image(image_path, ai_options=ai_options)
            results.append(result)

            # Each result should be valid
            assert result.image_type in {
                "diagram", "chart", "photo", "screenshot", "flowchart",
                "infographic", "map", "illustration", "other"
            }
            assert 0 <= result.confidence <= 1.0

        # Should identify different types (unless all images are same type)
        image_types = [r.image_type for r in results]
        print(f"\n✅ Analyzed {len(results)} images:")
        for idx, (img, result) in enumerate(zip(test_images[:3], results)):
            print(f"   {idx+1}. {img.name}: {result.image_type} (confidence: {result.confidence})")

    def test_analyze_batch_processing(self, test_images: List[Path]) -> None:
        """Test batch processing multiple images."""
        if len(test_images) < 2:
            pytest.skip("Need at least 2 test images")

        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Test batch processing with first 5 images (or fewer if not available)
        batch_images = test_images[:min(5, len(test_images))]
        results = analyze_images_batch(batch_images, ai_options=ai_options)

        # Should return results for all images
        assert len(results) == len(batch_images)

        # Each result should be valid
        for image_path, result in zip(batch_images, results):
            assert isinstance(result, ImageAnalysis)
            assert hasattr(result, "text_content")
            assert hasattr(result, "description")
            assert hasattr(result, "image_type")
            assert 0 <= result.confidence <= 1.0

        print(f"\n✅ Batch processed {len(results)} images successfully")

    def test_analyze_image_with_text_extraction(self, test_images: List[Path]) -> None:
        """Test text extraction from images (OCR)."""
        if not test_images:
            pytest.skip("No test images available")

        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Analyze all available images
        text_found_count = 0
        for image_path in test_images:
            result = analyze_image(image_path, ai_options=ai_options)

            if result.text_content and result.text_content.strip():
                text_found_count += 1
                print(f"\n✅ Text found in {image_path.name}:")
                print(f"   {result.text_content[:200]}")

        # At least report results (some images may not have text)
        print(f"\n📊 Text extraction summary: {text_found_count}/{len(test_images)} images contained text")

    def test_analyze_image_error_handling_invalid_file(self) -> None:
        """Test error handling for invalid image file."""
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Try analyzing non-existent file
        with pytest.raises((FileNotFoundError, ValueError)):
            analyze_image(Path("/nonexistent/image.png"), ai_options=ai_options)

    def test_analyze_image_error_handling_unsupported_format(self, tmp_path: Path) -> None:
        """Test error handling for unsupported image format."""
        # Create a fake .txt file
        fake_image = tmp_path / "not_an_image.txt"
        fake_image.write_text("This is not an image")

        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Should raise error for unsupported format
        with pytest.raises(ValueError, match="Unsupported image format"):
            analyze_image(fake_image, ai_options=ai_options)


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
)
class TestImageDescriptionIntegration:
    """Integration tests for AI image description with real API calls."""

    def test_describe_single_image_anthropic(self, test_images: List[Path]) -> None:
        """Test generating description for a single image."""
        if not test_images:
            pytest.skip("No test images available")

        image_path = test_images[0]

        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        description = describe_image(
            image_path,
            context="This image appears in a technical document about data visualization.",
            ai_options=ai_options,
        )

        # Verify description
        assert isinstance(description, str)
        assert len(description) > 0
        assert len(description) <= 150  # Should be concise for alt text

        print(f"\n✅ Image Description for {image_path.name}:")
        print(f"   {description}")

    def test_describe_image_with_context(self, test_images: List[Path]) -> None:
        """Test that context influences the description."""
        if not test_images:
            pytest.skip("No test images available")

        image_path = test_images[0]

        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Test with different contexts
        context1 = "This diagram illustrates the software architecture."
        context2 = "This chart shows sales data over time."

        desc1 = describe_image(image_path, context=context1, ai_options=ai_options)
        desc2 = describe_image(image_path, context=context2, ai_options=ai_options)

        # Both should be valid descriptions
        assert isinstance(desc1, str) and len(desc1) > 0
        assert isinstance(desc2, str) and len(desc2) > 0

        print(f"\n✅ Descriptions with different contexts:")
        print(f"   Context 1: {desc1}")
        print(f"   Context 2: {desc2}")

    def test_describe_document_images_batch(
        self, sample_document_with_images: Document
    ) -> None:
        """Test batch description of all images in a document."""
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        descriptions = describe_document_images(
            sample_document_with_images,
            ai_options=ai_options,
        )

        # Should return descriptions for all images
        assert len(descriptions) == len(sample_document_with_images.images)

        # Each description should be valid
        for img_id, desc in descriptions.items():
            assert isinstance(desc, str)
            assert len(desc) > 0
            assert len(desc) <= 150

        print(f"\n✅ Generated descriptions for {len(descriptions)} images in document")
        for img_id, desc in descriptions.items():
            print(f"   {img_id}: {desc}")

    def test_update_image_descriptions_in_document(
        self, sample_document_with_images: Document
    ) -> None:
        """Test updating image descriptions in a document."""
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Initially, images should not have alt_text
        for img in sample_document_with_images.images:
            assert img.alt_text is None or img.alt_text == ""

        # Update descriptions
        updated_doc = update_image_descriptions(
            sample_document_with_images,
            ai_options=ai_options,
        )

        # Now images should have alt_text
        for img in updated_doc.images:
            assert img.alt_text is not None
            assert len(img.alt_text) > 0
            assert len(img.alt_text) <= 150

        print(f"\n✅ Updated alt text for {len(updated_doc.images)} images:")
        for img in updated_doc.images:
            print(f"   {img.image_id}: {img.alt_text}")

    def test_describe_image_error_handling(self) -> None:
        """Test error handling for image description."""
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        # Try describing non-existent file
        with pytest.raises((FileNotFoundError, ValueError)):
            describe_image(
                Path("/nonexistent/image.png"),
                ai_options=ai_options,
            )


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
)
class TestVisionModelValidation:
    """Integration tests for vision model validation."""

    def test_vision_capable_model_works(self, test_images: List[Path]) -> None:
        """Test that vision-capable models work correctly."""
        if not test_images:
            pytest.skip("No test images available")

        # Test with known vision-capable model
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

        result = analyze_image(test_images[0], ai_options=ai_options)

        # Should succeed without errors
        assert result is not None
        assert "description" in result

        print(f"\n✅ Vision-capable model (claude-3-haiku-20240307) works correctly")

    def test_non_vision_model_fails_gracefully(self, test_images: List[Path]) -> None:
        """Test that non-vision models fail with clear error message."""
        if not test_images:
            pytest.skip("No test images available")

        # Try with a non-vision model (this should be caught and raise an error)
        ai_options = {
            "ai_provider": "anthropic",
            "ai_model": "claude-2.1",  # Non-vision model
        }

        # Should raise ValueError about unsupported model
        with pytest.raises(ValueError, match="does not support vision"):
            analyze_image(test_images[0], ai_options=ai_options)

        print(f"\n✅ Non-vision model correctly rejected with clear error")
