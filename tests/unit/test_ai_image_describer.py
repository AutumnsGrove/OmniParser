"""Unit tests for AI image describer module."""

import base64
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime

from omniparser.processors.ai_image_describer import (
    describe_image,
    describe_document_images,
    update_image_descriptions,
    _is_vision_capable_model,
    _get_image_context,
    _describe_image_anthropic,
    _describe_image_openai,
    MAX_IMAGE_SIZE,
    SUPPORTED_IMAGE_FORMATS,
)
from omniparser.models import (
    Document,
    Chapter,
    ImageReference,
    Metadata,
    ProcessingInfo,
)


class TestVisionModelCapability:
    """Test vision model detection."""

    def test_anthropic_claude_3_is_vision_capable(self):
        """Test that Claude 3 models are recognized as vision-capable."""
        assert _is_vision_capable_model("anthropic", "claude-3-haiku-20240307")
        assert _is_vision_capable_model("anthropic", "claude-3-sonnet-20240229")
        assert _is_vision_capable_model("anthropic", "claude-3-opus-20240229")
        assert _is_vision_capable_model("anthropic", "claude-3-5-sonnet-20240620")

    def test_openai_gpt4_vision_is_capable(self):
        """Test that GPT-4 vision models are recognized."""
        assert _is_vision_capable_model("openai", "gpt-4o")
        assert _is_vision_capable_model("openai", "gpt-4o-mini")
        assert _is_vision_capable_model("openai", "gpt-4-vision-preview")
        assert _is_vision_capable_model("openai", "gpt-4-turbo")

    def test_ollama_llava_is_capable(self):
        """Test that Ollama vision models are recognized."""
        assert _is_vision_capable_model("ollama", "llava")
        assert _is_vision_capable_model("ollama", "llava:latest")
        assert _is_vision_capable_model("ollama", "bakllava")
        assert _is_vision_capable_model("ollama", "bakllava:latest")

    def test_non_vision_models_not_capable(self):
        """Test that non-vision models are correctly identified."""
        assert not _is_vision_capable_model("anthropic", "claude-2.1")
        assert not _is_vision_capable_model("openai", "gpt-3.5-turbo")
        assert not _is_vision_capable_model("openai", "text-davinci-003")

    def test_ollama_with_vision_prefix(self):
        """Test Ollama model detection by prefix."""
        assert _is_vision_capable_model("ollama", "llava:13b")
        assert _is_vision_capable_model("ollama", "bakllava-custom")

    def test_lmstudio_always_returns_true_with_warning(self, caplog):
        """Test LM Studio models return True with warning."""
        result = _is_vision_capable_model("lmstudio", "unknown-model")
        assert result is True
        assert "Cannot verify vision capability" in caplog.text


class TestDescribeImage:
    """Test describe_image() function with mocked AI responses."""

    @patch("omniparser.processors.ai_image_describer.AIConfig")
    @patch("omniparser.processors.ai_image_describer._describe_image_anthropic")
    def test_describe_image_basic_anthropic(self, mock_describe_anthropic, mock_ai_config):
        """Test basic image description with Anthropic."""
        # Setup mock
        mock_config = Mock()
        mock_config.provider.value = "anthropic"
        mock_config.model = "claude-3-haiku-20240307"
        mock_ai_config.return_value = mock_config

        mock_describe_anthropic.return_value = "A diagram showing system architecture."

        # Create test image
        image = ImageReference(
            image_id="img_001",
            position=100,
            file_path="/test/image.jpg",
            format="jpg",
        )

        # Mock file operations
        with patch("omniparser.processors.ai_image_describer.Path") as mock_path:
            mock_path_obj = Mock()
            mock_path_obj.exists.return_value = True
            mock_path_obj.stat.return_value.st_size = 1024
            mock_path_obj.suffix = ".jpg"
            mock_path.return_value = mock_path_obj

            result = describe_image(image)

            assert isinstance(result, str)
            assert "diagram" in result.lower()
            mock_describe_anthropic.assert_called_once()

    @patch("omniparser.processors.ai_image_describer.AIConfig")
    @patch("omniparser.processors.ai_image_describer._describe_image_openai")
    def test_describe_image_with_openai(self, mock_describe_openai, mock_ai_config):
        """Test image description with OpenAI."""
        mock_config = Mock()
        mock_config.provider.value = "openai"
        mock_config.model = "gpt-4o"
        mock_ai_config.return_value = mock_config

        mock_describe_openai.return_value = "Chart showing sales data."

        image = ImageReference(
            image_id="img_002",
            position=200,
            file_path="/test/chart.png",
            format="png",
        )

        with patch("omniparser.processors.ai_image_describer.Path") as mock_path:
            mock_path_obj = Mock()
            mock_path_obj.exists.return_value = True
            mock_path_obj.stat.return_value.st_size = 2048
            mock_path_obj.suffix = ".png"
            mock_path.return_value = mock_path_obj

            result = describe_image(image)

            assert "chart" in result.lower()
            mock_describe_openai.assert_called_once()

    @patch("omniparser.processors.ai_image_describer.AIConfig")
    def test_describe_image_with_context(self, mock_ai_config):
        """Test image description includes context in prompt."""
        mock_config = Mock()
        mock_config.provider.value = "anthropic"
        mock_config.model = "claude-3-haiku-20240307"
        mock_ai_config.return_value = mock_config

        # Mock the Anthropic API
        mock_message = Mock()
        mock_message.content = [Mock(text="Description with context")]
        mock_config.client.messages.create.return_value = mock_message

        image = ImageReference(
            image_id="img_003",
            position=300,
            file_path="/test/diagram.jpg",
            format="jpg",
        )

        with patch("omniparser.processors.ai_image_describer.Path") as mock_path:
            mock_path_obj = Mock()
            mock_path_obj.exists.return_value = True
            mock_path_obj.stat.return_value.st_size = 1024
            mock_path_obj.suffix = ".jpg"
            mock_path.return_value = mock_path_obj

            with patch("builtins.open", mock_open(read_data=b"fake_image_data")):
                result = describe_image(image, context="This is from chapter 5 about APIs")

                # Verify context was included in the prompt
                call_args = mock_config.client.messages.create.call_args
                messages = call_args.kwargs["messages"]
                text_content = [c for c in messages[0]["content"] if c["type"] == "text"][0]
                assert "chapter 5 about APIs" in text_content["text"]

    def test_describe_image_no_file_path(self):
        """Test error when image has no file_path."""
        image = ImageReference(
            image_id="img_004",
            position=400,
            file_path=None,  # No path
            format="jpg",
        )

        with pytest.raises(ValueError, match="file_path is required"):
            describe_image(image)

    def test_describe_image_file_not_found(self):
        """Test error when image file doesn't exist."""
        image = ImageReference(
            image_id="img_005",
            position=500,
            file_path="/nonexistent/image.jpg",
            format="jpg",
        )

        with patch("omniparser.processors.ai_image_describer.Path") as mock_path:
            mock_path_obj = Mock()
            mock_path_obj.exists.return_value = False
            mock_path.return_value = mock_path_obj

            with pytest.raises(ValueError, match="not found"):
                describe_image(image)

    def test_describe_image_unsupported_format(self):
        """Test error for unsupported image format."""
        image = ImageReference(
            image_id="img_006",
            position=600,
            file_path="/test/file.txt",
            format="txt",
        )

        with patch("omniparser.processors.ai_image_describer.Path") as mock_path:
            mock_path_obj = Mock()
            mock_path_obj.exists.return_value = True
            mock_path_obj.suffix = ".txt"
            mock_path.return_value = mock_path_obj

            with pytest.raises(ValueError, match="Unsupported image format"):
                describe_image(image)

    def test_describe_image_file_too_large(self):
        """Test error when image exceeds size limit."""
        image = ImageReference(
            image_id="img_007",
            position=700,
            file_path="/test/huge.jpg",
            format="jpg",
        )

        with patch("omniparser.processors.ai_image_describer.Path") as mock_path:
            mock_path_obj = Mock()
            mock_path_obj.exists.return_value = True
            mock_path_obj.stat.return_value.st_size = MAX_IMAGE_SIZE + 1
            mock_path_obj.suffix = ".jpg"
            mock_path.return_value = mock_path_obj

            with pytest.raises(ValueError, match="too large"):
                describe_image(image)

    @patch("omniparser.processors.ai_image_describer.AIConfig")
    def test_describe_image_non_vision_model(self, mock_ai_config):
        """Test error when using non-vision-capable model."""
        mock_config = Mock()
        mock_config.provider.value = "openai"
        mock_config.model = "gpt-3.5-turbo"  # Not vision-capable
        mock_ai_config.return_value = mock_config

        image = ImageReference(
            image_id="img_008",
            position=800,
            file_path="/test/image.jpg",
            format="jpg",
        )

        with patch("omniparser.processors.ai_image_describer.Path") as mock_path:
            mock_path_obj = Mock()
            mock_path_obj.exists.return_value = True
            mock_path_obj.stat.return_value.st_size = 1024
            mock_path_obj.suffix = ".jpg"
            mock_path.return_value = mock_path_obj

            with pytest.raises(ValueError, match="does not support vision"):
                describe_image(image)


class TestDescribeDocumentImages:
    """Test describe_document_images() batch processing."""

    @patch("omniparser.processors.ai_image_describer.describe_image")
    @patch("omniparser.processors.ai_image_describer._get_image_context")
    def test_describe_all_images_in_document(self, mock_get_context, mock_describe):
        """Test describing all images in a document."""
        mock_get_context.return_value = "Chapter context"
        mock_describe.side_effect = ["Description 1", "Description 2", "Description 3"]

        images = [
            ImageReference(image_id="img_001", position=100, file_path="/test/img1.jpg", format="jpg"),
            ImageReference(image_id="img_002", position=200, file_path="/test/img2.png", format="png"),
            ImageReference(image_id="img_003", position=300, file_path="/test/img3.jpg", format="jpg"),
        ]

        doc = Document(
            document_id="test_doc",
            content="Test content with images",
            chapters=[],
            images=images,
            metadata=Metadata(title="Test Document"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=100,
            estimated_reading_time=1,
        )

        result = describe_document_images(doc)

        assert len(result) == 3
        assert result["img_001"] == "Description 1"
        assert result["img_002"] == "Description 2"
        assert result["img_003"] == "Description 3"
        assert mock_describe.call_count == 3

    @patch("omniparser.processors.ai_image_describer.describe_image")
    def test_describe_document_no_images(self, mock_describe):
        """Test handling document with no images."""
        doc = Document(
            document_id="test_doc",
            content="Test content without images",
            chapters=[],
            images=[],  # No images
            metadata=Metadata(title="Test Document"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=100,
            estimated_reading_time=1,
        )

        result = describe_document_images(doc)

        assert len(result) == 0
        mock_describe.assert_not_called()

    @patch("omniparser.processors.ai_image_describer.describe_image")
    @patch("omniparser.processors.ai_image_describer._get_image_context")
    def test_describe_document_partial_failure(self, mock_get_context, mock_describe):
        """Test handling when some image descriptions fail."""
        mock_get_context.return_value = "Context"
        mock_describe.side_effect = [
            "Success 1",
            Exception("API error"),
            "Success 3",
        ]

        images = [
            ImageReference(image_id="img_001", position=100, file_path="/test/img1.jpg", format="jpg"),
            ImageReference(image_id="img_002", position=200, file_path="/test/img2.jpg", format="jpg"),
            ImageReference(image_id="img_003", position=300, file_path="/test/img3.jpg", format="jpg"),
        ]

        doc = Document(
            document_id="test_doc",
            content="Test content",
            chapters=[],
            images=images,
            metadata=Metadata(title="Test"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=100,
            estimated_reading_time=1,
        )

        result = describe_document_images(doc)

        assert len(result) == 3
        assert result["img_001"] == "Success 1"
        assert "[Description failed:" in result["img_002"]
        assert result["img_003"] == "Success 3"


class TestGetImageContext:
    """Test _get_image_context() helper function."""

    def test_get_context_from_document_content(self):
        """Test extracting context from document content."""
        doc = Document(
            document_id="test_doc",
            content="This is text before the image. [IMAGE HERE] This is text after the image.",
            chapters=[],
            images=[],
            metadata=Metadata(title="Test"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=20,
            estimated_reading_time=1,
        )

        image = ImageReference(
            image_id="img_001",
            position=40,  # Position of [IMAGE HERE]
            file_path="/test/img.jpg",
            format="jpg",
        )

        context = _get_image_context(doc, image)

        assert isinstance(context, str)
        assert len(context) > 0
        assert "text before" in context or "text after" in context

    def test_get_context_with_existing_alt_text(self):
        """Test that existing alt text is included in context."""
        doc = Document(
            document_id="test_doc",
            content="Some document content here.",
            chapters=[],
            images=[],
            metadata=Metadata(title="Test"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=10,
            estimated_reading_time=1,
        )

        image = ImageReference(
            image_id="img_001",
            position=10,
            file_path="/test/img.jpg",
            format="jpg",
            alt_text="Existing description",
        )

        context = _get_image_context(doc, image)

        assert "Existing alt text" in context
        assert "Existing description" in context

    def test_get_context_no_content(self):
        """Test handling when document has no content."""
        doc = Document(
            document_id="test_doc",
            content=None,  # No content
            chapters=[],
            images=[],
            metadata=Metadata(title="Test"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=0,
            estimated_reading_time=0,
        )

        image = ImageReference(
            image_id="img_001",
            position=10,
            file_path="/test/img.jpg",
            format="jpg",
        )

        context = _get_image_context(doc, image)
        assert context == ""

    def test_get_context_invalid_position(self):
        """Test handling negative image position."""
        doc = Document(
            document_id="test_doc",
            content="Some content",
            chapters=[],
            images=[],
            metadata=Metadata(title="Test"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=10,
            estimated_reading_time=1,
        )

        image = ImageReference(
            image_id="img_001",
            position=-1,  # Invalid position
            file_path="/test/img.jpg",
            format="jpg",
        )

        context = _get_image_context(doc, image)
        assert context == ""


class TestUpdateImageDescriptions:
    """Test update_image_descriptions() function."""

    @patch("omniparser.processors.ai_image_describer.describe_document_images")
    def test_update_all_images(self, mock_describe_doc):
        """Test updating all image alt_text fields."""
        mock_describe_doc.return_value = {
            "img_001": "Updated description 1",
            "img_002": "Updated description 2",
        }

        images = [
            ImageReference(image_id="img_001", position=100, file_path="/test/img1.jpg", format="jpg"),
            ImageReference(image_id="img_002", position=200, file_path="/test/img2.jpg", format="jpg"),
        ]

        doc = Document(
            document_id="test_doc",
            content="Test content",
            chapters=[],
            images=images,
            metadata=Metadata(title="Test"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=100,
            estimated_reading_time=1,
        )

        result = update_image_descriptions(doc)

        assert result is doc  # Same object returned
        assert result.images[0].alt_text == "Updated description 1"
        assert result.images[1].alt_text == "Updated description 2"

    @patch("omniparser.processors.ai_image_describer.describe_document_images")
    def test_update_preserves_missing_images(self, mock_describe_doc):
        """Test that images without descriptions are not modified."""
        mock_describe_doc.return_value = {
            "img_001": "Description 1",
            # img_002 missing
        }

        images = [
            ImageReference(image_id="img_001", position=100, file_path="/test/img1.jpg", format="jpg"),
            ImageReference(
                image_id="img_002",
                position=200,
                file_path="/test/img2.jpg",
                format="jpg",
                alt_text="Original alt text",
            ),
        ]

        doc = Document(
            document_id="test_doc",
            content="Test",
            chapters=[],
            images=images,
            metadata=Metadata(title="Test"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=10,
            estimated_reading_time=1,
        )

        result = update_image_descriptions(doc)

        assert result.images[0].alt_text == "Description 1"
        assert result.images[1].alt_text == "Original alt text"  # Unchanged
