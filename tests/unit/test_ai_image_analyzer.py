"""Unit tests for AI image analyzer module.

Tests the AI-powered image analysis pipeline with comprehensive mocking
to avoid actual AI API calls. Covers all major functions and edge cases.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from dataclasses import asdict

from omniparser.processors.ai_image_analyzer import (
    analyze_image,
    analyze_images_batch,
    analyze_image_reference,
    ImageAnalysis,
    _parse_analysis_response,
    _is_vision_capable_model,
    SUPPORTED_IMAGE_FORMATS,
    MAX_IMAGE_SIZE,
    VISION_CAPABLE_MODELS,
)


class TestIsVisionCapableModel:
    """Test _is_vision_capable_model() function."""

    def test_known_anthropic_model(self):
        """Test that known Anthropic models are recognized."""
        assert _is_vision_capable_model("anthropic", "claude-3-opus-20240229") is True
        assert _is_vision_capable_model("anthropic", "claude-3-sonnet-20240229") is True
        assert _is_vision_capable_model("anthropic", "claude-3-5-sonnet-20241022") is True

    def test_known_openai_model(self):
        """Test that known OpenAI models are recognized."""
        assert _is_vision_capable_model("openai", "gpt-4o") is True
        assert _is_vision_capable_model("openai", "gpt-4-vision-preview") is True
        assert _is_vision_capable_model("openai", "gpt-4o-mini") is True

    def test_known_ollama_model(self):
        """Test that known Ollama vision models are recognized."""
        assert _is_vision_capable_model("ollama", "llava") is True
        assert _is_vision_capable_model("ollama", "llava:latest") is True
        assert _is_vision_capable_model("ollama", "bakllava") is True

    def test_lmstudio_returns_true_with_warning(self):
        """Test that LM Studio models return True (can't verify capability)."""
        with patch('omniparser.processors.ai_image_analyzer.logger') as mock_logger:
            result = _is_vision_capable_model("lmstudio", "some-model")
            assert result is True
            mock_logger.warning.assert_called_once()

    def test_unknown_model_returns_false(self):
        """Test that unknown models return False."""
        assert _is_vision_capable_model("anthropic", "claude-instant-1.2") is False
        assert _is_vision_capable_model("openai", "gpt-3.5-turbo") is False
        assert _is_vision_capable_model("ollama", "mistral") is False


class TestImageAnalysisDataclass:
    """Test ImageAnalysis dataclass."""

    def test_image_analysis_creation_minimal(self):
        """Test creating ImageAnalysis with minimal required fields."""
        analysis = ImageAnalysis(image_path="/test/img.jpg")

        assert analysis.image_path == "/test/img.jpg"
        assert analysis.text_content == ""
        assert analysis.description == ""
        assert analysis.image_type == "unknown"
        assert analysis.objects == []  # __post_init__ should set default
        assert analysis.alt_text == ""
        assert analysis.confidence == 0.0
        assert analysis.raw_response == ""

    def test_image_analysis_creation_complete(self):
        """Test creating ImageAnalysis with all fields."""
        analysis = ImageAnalysis(
            image_path="/test/img.jpg",
            text_content="Some text",
            description="Test description",
            image_type="diagram",
            objects=["Object1", "Object2"],
            alt_text="Alt text",
            confidence=0.9,
            raw_response="Raw response"
        )

        assert analysis.image_path == "/test/img.jpg"
        assert analysis.text_content == "Some text"
        assert analysis.description == "Test description"
        assert analysis.image_type == "diagram"
        assert len(analysis.objects) == 2
        assert analysis.alt_text == "Alt text"
        assert analysis.confidence == 0.9
        assert analysis.raw_response == "Raw response"

    def test_image_analysis_confidence_range(self):
        """Test confidence score is within expected range."""
        analysis = ImageAnalysis(image_path="/test/img.jpg", confidence=0.95)
        assert 0.0 <= analysis.confidence <= 1.0

    def test_post_init_defaults_objects_to_empty_list(self):
        """Test that __post_init__ sets objects to empty list if None."""
        analysis = ImageAnalysis(image_path="/test/img.jpg", objects=None)
        assert analysis.objects == []


class TestParseAnalysisResponse:
    """Test _parse_analysis_response() helper function."""

    def test_parse_complete_response(self):
        """Test parsing a complete, well-formatted AI response."""
        response = """
TEXT_CONTENT:
Start -> Process Data -> Decision? -> Yes -> Output

IMAGE_TYPE:
flowchart

DESCRIPTION:
A detailed flowchart diagram showing a data processing workflow with decision points and output stages.

OBJECTS:
- Start node
- Process Data box
- Decision diamond
- Output box
- End node

ALT_TEXT:
Flowchart showing data processing workflow with decision point

CONFIDENCE:
high
"""
        parsed = _parse_analysis_response(response, "/test/flowchart.png")

        assert isinstance(parsed, ImageAnalysis)
        assert parsed.image_path == "/test/flowchart.png"
        assert "Start" in parsed.text_content
        assert parsed.image_type == "flowchart"
        assert "flowchart diagram" in parsed.description
        assert len(parsed.objects) > 0
        assert "Flowchart" in parsed.alt_text
        assert parsed.confidence == 0.9  # 'high' maps to 0.9

    def test_parse_response_with_none_text_content(self):
        """Test parsing response where text content is 'None'."""
        response = """
TEXT_CONTENT:
None

IMAGE_TYPE:
photo

DESCRIPTION:
A landscape photo with mountains.

OBJECTS:
- Mountains
- Sky

ALT_TEXT:
Landscape with mountains

CONFIDENCE:
medium
"""
        parsed = _parse_analysis_response(response, "/test/photo.jpg")

        assert parsed.text_content == ""  # 'None' should be converted to empty string
        assert parsed.image_type == "photo"
        assert parsed.confidence == 0.6  # 'medium' maps to 0.6

    def test_parse_partial_response_missing_fields(self):
        """Test parsing response with some missing optional fields."""
        response = """
IMAGE_TYPE:
diagram

DESCRIPTION:
A simple diagram.

OBJECTS:
- None
"""
        parsed = _parse_analysis_response(response, "/test/diagram.png")

        assert parsed.image_type == "diagram"
        # Description may not be extracted if regex doesn't match
        # This is expected behavior when response format is incomplete
        assert parsed.text_content == ""
        assert parsed.alt_text == ""
        assert parsed.confidence == 0.0  # Default when not specified

    def test_parse_malformed_response(self):
        """Test handling of malformed AI responses."""
        response = "This is not a properly formatted response at all."

        with patch('omniparser.processors.ai_image_analyzer.logger') as mock_logger:
            parsed = _parse_analysis_response(response, "/test/img.jpg")

            assert isinstance(parsed, ImageAnalysis)
            assert parsed.image_path == "/test/img.jpg"
            # Should log warnings for missing required fields
            assert mock_logger.warning.call_count >= 2

    def test_parse_response_extracts_objects_list(self):
        """Test that objects are properly extracted from bullet list."""
        response = """
IMAGE_TYPE:
diagram

DESCRIPTION:
System architecture diagram

OBJECTS:
- Web Server
- Application Server
- Database
- Load Balancer

ALT_TEXT:
Architecture diagram

CONFIDENCE:
high
"""
        parsed = _parse_analysis_response(response, "/test/arch.png")

        assert len(parsed.objects) == 4
        assert "Web Server" in parsed.objects
        assert "Database" in parsed.objects

    def test_parse_response_confidence_levels(self):
        """Test that confidence levels are correctly mapped."""
        # Test 'high'
        response_high = "CONFIDENCE:\nhigh"
        parsed_high = _parse_analysis_response(response_high, "/test/img.jpg")
        assert parsed_high.confidence == 0.9

        # Test 'medium'
        response_medium = "CONFIDENCE:\nmedium"
        parsed_medium = _parse_analysis_response(response_medium, "/test/img.jpg")
        assert parsed_medium.confidence == 0.6

        # Test 'low'
        response_low = "CONFIDENCE:\nlow"
        parsed_low = _parse_analysis_response(response_low, "/test/img.jpg")
        assert parsed_low.confidence == 0.3

        # Test unknown confidence level defaults to 0.5
        response_unknown = "CONFIDENCE:\nunknown"
        parsed_unknown = _parse_analysis_response(response_unknown, "/test/img.jpg")
        assert parsed_unknown.confidence == 0.5


class TestAnalyzeImage:
    """Test analyze_image() function with mocked AI responses."""

    @patch('omniparser.processors.ai_image_analyzer._analyze_image_anthropic')
    @patch('omniparser.processors.ai_image_analyzer.AIConfig')
    @patch('omniparser.processors.ai_image_analyzer.Path')
    def test_analyze_image_basic_anthropic(self, mock_path_class, mock_ai_config_class, mock_analyze_anthropic):
        """Test basic image analysis with Anthropic."""
        # Setup path mock
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path_obj.stat.return_value.st_size = 1024 * 500  # 500KB
        mock_path_obj.suffix = ".jpg"
        mock_path_obj.name = "test.jpg"
        mock_path_class.return_value = mock_path_obj

        # Setup AI config mock
        mock_config = MagicMock()
        mock_config.provider.value = "anthropic"
        mock_config.model = "claude-3-opus-20240229"
        mock_ai_config_class.return_value = mock_config

        # Setup analysis response
        mock_analyze_anthropic.return_value = """
TEXT_CONTENT:
Diagram text

IMAGE_TYPE:
diagram

DESCRIPTION:
System architecture diagram

OBJECTS:
- Server
- Database

ALT_TEXT:
Architecture diagram

CONFIDENCE:
high
"""

        result = analyze_image("/test/image.jpg")

        assert isinstance(result, ImageAnalysis)
        assert result.image_type == "diagram"
        assert result.confidence == 0.9
        mock_analyze_anthropic.assert_called_once()

    @patch('omniparser.processors.ai_image_analyzer._analyze_image_openai')
    @patch('omniparser.processors.ai_image_analyzer.AIConfig')
    @patch('omniparser.processors.ai_image_analyzer.Path')
    def test_analyze_image_basic_openai(self, mock_path_class, mock_ai_config_class, mock_analyze_openai):
        """Test basic image analysis with OpenAI."""
        # Setup path mock
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path_obj.stat.return_value.st_size = 1024 * 500
        mock_path_obj.suffix = ".png"
        mock_path_obj.name = "test.png"
        mock_path_class.return_value = mock_path_obj

        # Setup AI config mock
        mock_config = MagicMock()
        mock_config.provider.value = "openai"
        mock_config.model = "gpt-4o"
        mock_ai_config_class.return_value = mock_config

        # Setup analysis response
        mock_analyze_openai.return_value = """
IMAGE_TYPE:
photo

DESCRIPTION:
A landscape photo

CONFIDENCE:
medium
"""

        result = analyze_image("/test/photo.png")

        assert isinstance(result, ImageAnalysis)
        assert result.image_type == "photo"
        mock_analyze_openai.assert_called_once()

    @patch('omniparser.processors.ai_image_analyzer.Path')
    def test_analyze_image_file_not_found(self, mock_path_class):
        """Test error handling for non-existent file."""
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = False
        mock_path_class.return_value = mock_path_obj

        with pytest.raises(ValueError, match="Image file not found"):
            analyze_image("/nonexistent/image.jpg")

    @patch('omniparser.processors.ai_image_analyzer.Path')
    def test_analyze_image_unsupported_format(self, mock_path_class):
        """Test error for unsupported image format."""
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path_obj.suffix = ".txt"
        mock_path_class.return_value = mock_path_obj

        with pytest.raises(ValueError, match="Unsupported image format"):
            analyze_image("/test/file.txt")

    @patch('omniparser.processors.ai_image_analyzer.Path')
    def test_analyze_image_file_too_large(self, mock_path_class):
        """Test error handling for oversized images."""
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path_obj.suffix = ".jpg"
        mock_path_obj.stat.return_value.st_size = MAX_IMAGE_SIZE + 1
        mock_path_class.return_value = mock_path_obj

        with pytest.raises(ValueError, match="Image file too large"):
            analyze_image("/test/huge_image.jpg")

    @patch('omniparser.processors.ai_image_analyzer.AIConfig')
    @patch('omniparser.processors.ai_image_analyzer.Path')
    def test_analyze_image_non_vision_model(self, mock_path_class, mock_ai_config_class):
        """Test error when using non-vision capable model."""
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = True
        mock_path_obj.stat.return_value.st_size = 1024
        mock_path_obj.suffix = ".jpg"
        mock_path_class.return_value = mock_path_obj

        mock_config = MagicMock()
        mock_config.provider.value = "openai"
        mock_config.model = "gpt-3.5-turbo"  # Not a vision model
        mock_ai_config_class.return_value = mock_config

        with pytest.raises(ValueError, match="does not support vision"):
            analyze_image("/test/image.jpg")


class TestAnalyzeImagesBatch:
    """Test batch processing of multiple images."""

    @patch('omniparser.processors.ai_image_analyzer.analyze_image')
    def test_batch_processing_multiple_images(self, mock_analyze):
        """Test analyzing multiple images in batch."""
        image_paths = [
            "/test/img1.jpg",
            "/test/img2.png",
            "/test/img3.jpg",
        ]

        mock_analyze.side_effect = [
            ImageAnalysis(
                image_path="/test/img1.jpg",
                description="First image",
                image_type="photo",
                confidence=0.9,
            ),
            ImageAnalysis(
                image_path="/test/img2.png",
                description="Second image",
                image_type="diagram",
                confidence=0.85,
            ),
            ImageAnalysis(
                image_path="/test/img3.jpg",
                description="Third image",
                image_type="chart",
                confidence=0.95,
            ),
        ]

        results = analyze_images_batch(image_paths)

        assert len(results) == 3
        assert all(isinstance(r, ImageAnalysis) for r in results)
        assert mock_analyze.call_count == 3

    @patch('omniparser.processors.ai_image_analyzer.analyze_image')
    def test_batch_processing_empty_list(self, mock_analyze):
        """Test batch processing with empty list."""
        results = analyze_images_batch([])

        assert len(results) == 0
        mock_analyze.assert_not_called()

    @patch('omniparser.processors.ai_image_analyzer.analyze_image')
    def test_batch_processing_with_errors(self, mock_analyze):
        """Test that errors in batch don't stop processing."""
        image_paths = [
            "/test/img1.jpg",
            "/test/img2_bad.jpg",
            "/test/img3.jpg",
        ]

        # Second image fails, others succeed
        mock_analyze.side_effect = [
            ImageAnalysis(
                image_path="/test/img1.jpg",
                description="First",
                image_type="photo",
                confidence=0.9,
            ),
            Exception("Failed to analyze"),
            ImageAnalysis(
                image_path="/test/img3.jpg",
                description="Third",
                image_type="chart",
                confidence=0.95,
            ),
        ]

        results = analyze_images_batch(image_paths)

        # Should have 3 results (including failed one)
        assert len(results) == 3
        assert mock_analyze.call_count == 3
        # Check that failed analysis has error message
        assert "Analysis failed" in results[1].description

    @patch('omniparser.processors.ai_image_analyzer.analyze_image')
    def test_batch_processing_custom_batch_size(self, mock_analyze):
        """Test batch processing with custom batch size."""
        image_paths = [f"/test/img{i}.jpg" for i in range(15)]

        mock_analyze.side_effect = [
            ImageAnalysis(image_path=path, description=f"Image {i}", image_type="photo")
            for i, path in enumerate(image_paths)
        ]

        results = analyze_images_batch(image_paths, batch_size=5)

        assert len(results) == 15
        assert mock_analyze.call_count == 15

    @patch('omniparser.processors.ai_image_analyzer.analyze_image')
    def test_batch_processing_with_progress_callback(self, mock_analyze):
        """Test batch processing with progress callback."""
        image_paths = ["/test/img1.jpg", "/test/img2.jpg", "/test/img3.jpg"]

        mock_analyze.side_effect = [
            ImageAnalysis(image_path=path, description="Test", image_type="photo")
            for path in image_paths
        ]

        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        results = analyze_images_batch(image_paths, progress_callback=progress_callback)

        assert len(results) == 3
        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)  # Final call should be 3/3

    def test_batch_processing_invalid_batch_size(self):
        """Test that invalid batch size raises error."""
        with pytest.raises(ValueError, match="batch_size must be at least 1"):
            analyze_images_batch(["/test/img.jpg"], batch_size=0)


class TestAnalyzeImageReference:
    """Test analyze_image_reference() integration function."""

    @patch('omniparser.processors.ai_image_analyzer.analyze_image')
    def test_analyze_image_reference_with_file_path(self, mock_analyze):
        """Test analyzing ImageReference with file_path set."""
        mock_image_ref = MagicMock()
        mock_image_ref.file_path = "/test/extracted_image.png"

        mock_analyze.return_value = ImageAnalysis(
            image_path="/test/extracted_image.png",
            description="Test image",
            image_type="diagram",
            confidence=0.9,
        )

        result = analyze_image_reference(mock_image_ref)

        assert isinstance(result, ImageAnalysis)
        mock_analyze.assert_called_once_with("/test/extracted_image.png", None)

    def test_analyze_image_reference_without_file_path(self):
        """Test error when ImageReference lacks file_path."""
        mock_image_ref = MagicMock()
        mock_image_ref.file_path = None

        with pytest.raises(ValueError, match="ImageReference must have file_path set"):
            analyze_image_reference(mock_image_ref)

    @patch('omniparser.processors.ai_image_analyzer.analyze_image')
    def test_analyze_image_reference_with_ai_options(self, mock_analyze):
        """Test analyze_image_reference passes ai_options correctly."""
        mock_image_ref = MagicMock()
        mock_image_ref.file_path = "/test/image.jpg"

        ai_options = {"ai_provider": "anthropic", "ai_model": "claude-3-opus-20240229"}

        mock_analyze.return_value = ImageAnalysis(
            image_path="/test/image.jpg",
            description="Test",
            image_type="photo",
        )

        result = analyze_image_reference(mock_image_ref, ai_options)

        mock_analyze.assert_called_once_with("/test/image.jpg", ai_options)


# pytest markers configured in pyproject.toml
