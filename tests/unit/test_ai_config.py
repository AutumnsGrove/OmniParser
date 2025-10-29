"""
Unit tests for AI configuration module.

Tests all AI provider initialization and generation methods with mocked responses.
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from omniparser.ai_config import AIConfig, AIProvider


class TestAIProvider:
    """Tests for AIProvider enum."""

    def test_provider_values(self) -> None:
        """Test that all provider values are defined."""
        assert AIProvider.ANTHROPIC.value == "anthropic"
        assert AIProvider.OPENAI.value == "openai"
        assert AIProvider.OPENROUTER.value == "openrouter"
        assert AIProvider.OLLAMA.value == "ollama"
        assert AIProvider.LMSTUDIO.value == "lmstudio"


class TestAIConfigInitialization:
    """Tests for AIConfig initialization."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    @patch("omniparser.ai_config.anthropic")
    def test_init_anthropic_default(self, mock_anthropic: Mock) -> None:
        """Test initialization with Anthropic (default provider)."""
        config = AIConfig()

        assert config.provider == AIProvider.ANTHROPIC
        assert config.model == "claude-3-haiku-20240307"
        assert config.max_tokens == 1024
        assert config.temperature == 0.3
        mock_anthropic.Anthropic.assert_called_once()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"})
    @patch("omniparser.ai_config.openai")
    def test_init_openai(self, mock_openai: Mock) -> None:
        """Test initialization with OpenAI."""
        config = AIConfig({"ai_provider": "openai"})

        assert config.provider == AIProvider.OPENAI
        assert config.model == "gpt-3.5-turbo"
        mock_openai.OpenAI.assert_called_once()

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test123"})
    @patch("omniparser.ai_config.openai")
    def test_init_openrouter(self, mock_openai: Mock) -> None:
        """Test initialization with OpenRouter."""
        config = AIConfig({"ai_provider": "openrouter"})

        assert config.provider == AIProvider.OPENROUTER
        assert config.model == "meta-llama/llama-3.2-3b-instruct:free"
        mock_openai.OpenAI.assert_called_once()

    @patch("omniparser.ai_config.openai")
    def test_init_ollama_no_key_required(self, mock_openai: Mock) -> None:
        """Test initialization with Ollama (no API key required)."""
        config = AIConfig({"ai_provider": "ollama"})

        assert config.provider == AIProvider.OLLAMA
        assert config.model == "llama3.2:latest"
        # Verify it uses default base URL
        call_args = mock_openai.OpenAI.call_args
        assert call_args[1]["base_url"] == "http://localhost:11434/v1"

    @patch("omniparser.ai_config.openai")
    def test_init_lmstudio_no_key_required(self, mock_openai: Mock) -> None:
        """Test initialization with LM Studio (no API key required)."""
        config = AIConfig({"ai_provider": "lmstudio"})

        assert config.provider == AIProvider.LMSTUDIO
        assert config.model == "local-model"
        call_args = mock_openai.OpenAI.call_args
        assert call_args[1]["base_url"] == "http://localhost:1234/v1"

    @patch.dict(os.environ, {}, clear=True)
    @patch("omniparser.ai_config.anthropic")
    def test_init_missing_api_key(self, mock_anthropic: Mock) -> None:
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            AIConfig({"ai_provider": "anthropic"})

    def test_init_invalid_provider(self) -> None:
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported AI provider"):
            AIConfig({"ai_provider": "invalid_provider"})

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    @patch("omniparser.ai_config.anthropic")
    def test_init_custom_options(self, mock_anthropic: Mock) -> None:
        """Test initialization with custom options."""
        config = AIConfig(
            {
                "ai_provider": "anthropic",
                "ai_model": "claude-3-opus-20240229",
                "max_tokens": 2048,
                "temperature": 0.7,
            }
        )

        assert config.model == "claude-3-opus-20240229"
        assert config.max_tokens == 2048
        assert config.temperature == 0.7

    @patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://custom-ollama:11434/v1"})
    @patch("omniparser.ai_config.openai")
    def test_init_ollama_custom_base_url(self, mock_openai: Mock) -> None:
        """Test Ollama with custom base URL from environment."""
        config = AIConfig({"ai_provider": "ollama"})

        call_args = mock_openai.OpenAI.call_args
        assert call_args[1]["base_url"] == "http://custom-ollama:11434/v1"

    @patch("omniparser.ai_config.openai")
    def test_init_ollama_base_url_in_options(self, mock_openai: Mock) -> None:
        """Test Ollama with base URL in options."""
        config = AIConfig(
            {
                "ai_provider": "ollama",
                "base_url": "http://options-ollama:11434/v1",
            }
        )

        call_args = mock_openai.OpenAI.call_args
        assert call_args[1]["base_url"] == "http://options-ollama:11434/v1"


class TestAIConfigGeneration:
    """Tests for text generation with different providers."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    @patch("omniparser.ai_config.anthropic")
    def test_generate_anthropic(self, mock_anthropic: Mock) -> None:
        """Test generation with Anthropic."""
        # Mock the response
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Generated response")]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.Anthropic.return_value = mock_client

        config = AIConfig({"ai_provider": "anthropic"})
        response = config.generate("Test prompt", system="You are a helpful assistant")

        assert response == "Generated response"
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["system"] == "You are a helpful assistant"
        assert call_args[1]["messages"][0]["content"] == "Test prompt"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"})
    @patch("omniparser.ai_config.openai")
    def test_generate_openai(self, mock_openai: Mock) -> None:
        """Test generation with OpenAI."""
        # Mock the response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Generated response"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client

        config = AIConfig({"ai_provider": "openai"})
        response = config.generate("Test prompt", system="You are a helpful assistant")

        assert response == "Generated response"
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test prompt"

    @patch("omniparser.ai_config.openai")
    def test_generate_ollama(self, mock_openai: Mock) -> None:
        """Test generation with Ollama (OpenAI-compatible)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Local model response"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client

        config = AIConfig({"ai_provider": "ollama"})
        response = config.generate("Test prompt")

        assert response == "Local model response"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    @patch("omniparser.ai_config.anthropic")
    def test_generate_without_system_prompt(self, mock_anthropic: Mock) -> None:
        """Test generation without system prompt."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.Anthropic.return_value = mock_client

        config = AIConfig({"ai_provider": "anthropic"})
        response = config.generate("Test prompt")

        assert response == "Response"
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["system"] == ""


class TestAIConfigErrorHandling:
    """Tests for error handling in AIConfig."""

    @patch("omniparser.ai_config.anthropic", side_effect=ImportError)
    def test_missing_anthropic_package(self, mock_anthropic: Mock) -> None:
        """Test error when anthropic package is not installed."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            with pytest.raises(ImportError, match="anthropic package not installed"):
                AIConfig({"ai_provider": "anthropic"})

    @patch("omniparser.ai_config.openai", side_effect=ImportError)
    def test_missing_openai_package(self, mock_openai: Mock) -> None:
        """Test error when openai package is not installed."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            with pytest.raises(ImportError, match="openai package not installed"):
                AIConfig({"ai_provider": "openai"})

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    @patch("omniparser.ai_config.anthropic")
    def test_api_error_during_generation(self, mock_anthropic: Mock) -> None:
        """Test handling of API errors during generation."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.Anthropic.return_value = mock_client

        config = AIConfig({"ai_provider": "anthropic"})

        with pytest.raises(Exception, match="API Error"):
            config.generate("Test prompt")
