"""
Shared AI configuration and client management for OmniParser.

This module provides a unified interface for interacting with AI providers
(cloud and local) for optional AI-powered features like auto-tagging,
summarization, and quality scoring.

Supported Providers:
    - Anthropic Claude (cloud, via anthropic SDK)
    - OpenAI GPT (cloud, via openai SDK)
    - OpenRouter (cloud aggregator, OpenAI-compatible API)
    - Ollama (local models, OpenAI-compatible API)
    - LM Studio (local models, OpenAI-compatible API)

Environment Variables:
    - ANTHROPIC_API_KEY: API key for Anthropic Claude
    - OPENAI_API_KEY: API key for OpenAI GPT
    - OPENROUTER_API_KEY: API key for OpenRouter
    - OLLAMA_BASE_URL: Base URL for Ollama (default: http://localhost:11434/v1)
    - LMSTUDIO_BASE_URL: Base URL for LM Studio (default: http://localhost:1234/v1)

Example:
    >>> import os
    >>> # Cloud provider
    >>> os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-...'
    >>> config = AIConfig({'ai_provider': 'anthropic'})
    >>> response = config.generate("What is 2+2?", system="You are a math tutor")

    >>> # Local model via Ollama
    >>> config = AIConfig({
    ...     'ai_provider': 'ollama',
    ...     'ai_model': 'llama3.2:latest'
    ... })
    >>> response = config.generate("Summarize this...")
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers for OmniParser features."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"


class AIConfig:
    """
    Configuration and client management for AI-powered features.

    This class handles initialization and interaction with AI providers (cloud and local),
    providing a unified interface regardless of the underlying provider.

    Attributes:
        provider: Selected AI provider (Anthropic, OpenAI, OpenRouter, Ollama, LM Studio).
        model: Model name to use for generation.
        max_tokens: Maximum tokens per request.
        temperature: Sampling temperature (0.0-1.0).
        client: Initialized API client.

    Example:
        >>> # Cloud provider (Anthropic)
        >>> config = AIConfig({
        ...     'ai_provider': 'anthropic',
        ...     'ai_model': 'claude-3-haiku-20240307',
        ...     'max_tokens': 1024,
        ...     'temperature': 0.3
        ... })
        >>> response = config.generate("Summarize this text...")

        >>> # Local model (Ollama)
        >>> config = AIConfig({
        ...     'ai_provider': 'ollama',
        ...     'ai_model': 'llama3.2:latest'
        ... })
        >>> response = config.generate("Analyze this document...")
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize AI configuration.

        Args:
            options: Configuration options dictionary with keys:
                - ai_provider (str): Provider name - "anthropic", "openai", "openrouter",
                  "ollama", or "lmstudio" (default: "anthropic")
                - ai_model (str): Model name (provider-specific default if not set)
                - max_tokens (int): Max tokens per request (default: 1024)
                - temperature (float): Sampling temperature (default: 0.3)
                - base_url (str): Custom base URL for OpenAI-compatible APIs
                  (overrides provider defaults for ollama/lmstudio)

        Raises:
            ValueError: If required API key is not set in environment.
            ValueError: If provider is not supported.
        """
        self.options = options or {}
        self.provider = self._get_provider()
        self.model = self._get_model()
        self.max_tokens = self.options.get("max_tokens", 1024)
        self.temperature = self.options.get("temperature", 0.3)

        # Initialize client
        self.client = self._init_client()

    def _get_provider(self) -> AIProvider:
        """
        Get AI provider from options or use default.

        Returns:
            AIProvider enum value.

        Raises:
            ValueError: If provider string is not valid.
        """
        provider_str = self.options.get("ai_provider", "anthropic")
        try:
            return AIProvider(provider_str)
        except ValueError:
            raise ValueError(
                f"Unsupported AI provider: {provider_str}. "
                f"Must be one of: {[p.value for p in AIProvider]}"
            )

    def _get_model(self) -> str:
        """
        Get model name from options or use provider default.

        Returns:
            Model name string.
        """
        if "ai_model" in self.options:
            return self.options["ai_model"]

        # Provider defaults (fast, cost-effective models)
        provider_defaults = {
            AIProvider.ANTHROPIC: "claude-3-haiku-20240307",
            AIProvider.OPENAI: "gpt-3.5-turbo",
            AIProvider.OPENROUTER: "meta-llama/llama-3.2-3b-instruct:free",
            AIProvider.OLLAMA: "llama3.2:latest",
            AIProvider.LMSTUDIO: "local-model",
        }
        return provider_defaults.get(self.provider, "gpt-3.5-turbo")

    def _init_client(self) -> Any:
        """
        Initialize API client for selected provider.

        Returns:
            Initialized client object (anthropic.Anthropic or openai.OpenAI).

        Raises:
            ValueError: If required API key is not set.
            ImportError: If required SDK is not installed.
        """
        if self.provider == AIProvider.ANTHROPIC:
            try:
                import anthropic  # type: ignore[import-not-found]
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install 'omniparser[ai]'"
                )

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it with: export ANTHROPIC_API_KEY='sk-ant-...'"
                )

            logger.info("Initialized Anthropic client with model: %s", self.model)
            return anthropic.Anthropic(api_key=api_key)

        elif self.provider == AIProvider.OPENAI:
            try:
                import openai  # type: ignore[import-not-found]
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install 'omniparser[ai]'"
                )

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable not set. "
                    "Set it with: export OPENAI_API_KEY='sk-...'"
                )

            logger.info("Initialized OpenAI client with model: %s", self.model)
            return openai.OpenAI(api_key=api_key)

        elif self.provider == AIProvider.OPENROUTER:
            try:
                import openai  # type: ignore[import-not-found]
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install 'omniparser[ai]'"
                )

            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY environment variable not set. "
                    "Set it with: export OPENROUTER_API_KEY='sk-or-...'"
                )

            logger.info("Initialized OpenRouter client with model: %s", self.model)
            return openai.OpenAI(
                api_key=api_key, base_url="https://openrouter.ai/api/v1"
            )

        elif self.provider == AIProvider.OLLAMA:
            try:
                import openai  # type: ignore[import-not-found]
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install 'omniparser[ai]'"
                )

            base_url = self.options.get("base_url") or os.getenv(
                "OLLAMA_BASE_URL", "http://localhost:11434/v1"
            )

            logger.info(
                "Initialized Ollama client with model: %s at %s", self.model, base_url
            )
            # Ollama doesn't require API key
            return openai.OpenAI(api_key="ollama", base_url=base_url)

        elif self.provider == AIProvider.LMSTUDIO:
            try:
                import openai  # type: ignore[import-not-found]
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install 'omniparser[ai]'"
                )

            base_url = self.options.get("base_url") or os.getenv(
                "LMSTUDIO_BASE_URL", "http://localhost:1234/v1"
            )

            logger.info(
                "Initialized LM Studio client with model: %s at %s",
                self.model,
                base_url,
            )
            # LM Studio doesn't require API key
            return openai.OpenAI(api_key="lmstudio", base_url=base_url)

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate text using configured AI provider.

        Args:
            prompt: User prompt/question to send to the model.
            system: Optional system prompt to guide model behavior.

        Returns:
            Generated text response from the model.

        Raises:
            Exception: If API call fails (provider-specific exceptions).

        Example:
            >>> config = AIConfig()
            >>> response = config.generate(
            ...     "What are the main themes?",
            ...     system="You are a literary analyst"
            ... )
        """
        if self.provider == AIProvider.ANTHROPIC:
            return self._generate_anthropic(prompt, system)
        else:
            # OpenAI, OpenRouter, Ollama, and LM Studio all use OpenAI-compatible API
            return self._generate_openai(prompt, system)

    def _generate_anthropic(self, prompt: str, system: Optional[str]) -> str:
        """
        Generate text using Anthropic Claude.

        Args:
            prompt: User prompt.
            system: System prompt (optional).

        Returns:
            Generated text.
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    def _generate_openai(self, prompt: str, system: Optional[str]) -> str:
        """
        Generate text using OpenAI GPT.

        Args:
            prompt: User prompt.
            system: System prompt (optional).

        Returns:
            Generated text.
        """
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
