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
    >>> # SECURITY WARNING: Never hardcode API keys in source code!
    >>> # Always use environment variables or secure secret management.
    >>> # The examples below show the format but should use real env vars.
    >>>
    >>> # Cloud provider
    >>> os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-...'  # Example only - use real env!
    >>> config = AIConfig({'ai_provider': 'anthropic'})
    >>> response = config.generate("What is 2+2?", system="You are a math tutor")

    >>> # Local model via Ollama (no API key needed)
    >>> config = AIConfig({
    ...     'ai_provider': 'ollama',
    ...     'ai_model': 'llama3.2:latest'
    ... })
    >>> response = config.generate("Summarize this...")
"""

import logging
import os
import time
from enum import Enum
from typing import Any, Dict, Optional, Union

from omniparser.utils.secrets import get_cached_secrets

logger = logging.getLogger(__name__)

# Load secrets once at module level for performance
_SECRETS = get_cached_secrets()


class AIProvider(Enum):
    """Supported AI providers for OmniParser features."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    CLOUDFLARE = "cloudflare"


# Type aliases for better type safety
try:
    import anthropic  # type: ignore[import-not-found]

    AnthropicClient = anthropic.Anthropic
except ImportError:
    AnthropicClient = Any  # type: ignore[misc, assignment]

try:
    import openai  # type: ignore[import-not-found]

    OpenAIClient = openai.OpenAI
except ImportError:
    OpenAIClient = Any  # type: ignore[misc, assignment]

AIClient = Union[AnthropicClient, OpenAIClient]


def _import_sdk(package_name: str) -> Any:
    """
    Import SDK package with helpful error message.

    Args:
        package_name: Name of package to import ("anthropic" or "openai").

    Returns:
        Imported module.

    Raises:
        ImportError: If package is not installed.
    """
    try:
        if package_name == "anthropic":
            import anthropic  # type: ignore[import-not-found]

            return anthropic
        elif package_name == "openai":
            import openai  # type: ignore[import-not-found]

            return openai
        else:
            raise ValueError(f"Unknown SDK package: {package_name}")
    except ImportError:
        raise ImportError(
            f"{package_name} package not installed. "
            f"Install with: pip install 'omniparser[ai]'"
        )


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
        timeout: Request timeout in seconds (default: 60).
        max_retries: Maximum number of retries for failed requests (default: 3).
        retry_delay: Initial delay between retries in seconds (default: 1).
        client: Initialized API client.

    Example:
        >>> # Cloud provider (Anthropic)
        >>> config = AIConfig({
        ...     'ai_provider': 'anthropic',
        ...     'ai_model': 'claude-3-haiku-20240307',
        ...     'max_tokens': 1024,
        ...     'temperature': 0.3,
        ...     'timeout': 60,
        ...     'max_retries': 3
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
                - timeout (int): Request timeout in seconds (default: 60)
                - max_retries (int): Maximum retry attempts (default: 3)
                - retry_delay (float): Initial retry delay in seconds (default: 1.0)
                - base_url (str): Custom base URL for OpenAI-compatible APIs
                  (overrides provider defaults for ollama/lmstudio)

        Raises:
            ValueError: If required API key is not set in environment.
            ValueError: If provider is not supported.
            ImportError: If required SDK is not installed.
        """
        self.options = options or {}
        self.provider = self._get_provider()
        self.model = self._get_model()
        self.max_tokens = self.options.get("max_tokens", 1024)
        self.temperature = self.options.get("temperature", 0.3)
        self.timeout = self.options.get("timeout", 60)
        self.max_retries = self.options.get("max_retries", 3)
        self.retry_delay = self.options.get("retry_delay", 1.0)

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
            return str(self.options["ai_model"])

        # Provider defaults (fast, cost-effective models)
        provider_defaults = {
            AIProvider.ANTHROPIC: "claude-3-haiku-20240307",
            AIProvider.OPENAI: "gpt-3.5-turbo",
            AIProvider.OPENROUTER: "meta-llama/llama-3.2-3b-instruct:free",
            AIProvider.OLLAMA: "llama3.2:latest",
            AIProvider.LMSTUDIO: "local-model",
            AIProvider.CLOUDFLARE: "@cf/meta/llama-3.2-11b-vision-instruct",
        }
        return provider_defaults.get(self.provider, "gpt-3.5-turbo")

    def _init_client(self) -> AIClient:
        """
        Initialize API client for selected provider.

        Returns:
            Initialized client object (anthropic.Anthropic or openai.OpenAI).

        Raises:
            ValueError: If required API key is not set.
            ImportError: If required SDK is not installed.
        """
        if self.provider == AIProvider.ANTHROPIC:
            anthropic_sdk = _import_sdk("anthropic")

            # Check secrets.json first, then environment variable
            api_key = _SECRETS.get("anthropic_api_key") or os.getenv(
                "ANTHROPIC_API_KEY"
            )
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not found. "
                    "Add to secrets.json or set environment variable: export ANTHROPIC_API_KEY='sk-ant-...'"
                )

            logger.info("Initialized Anthropic client with model: %s", self.model)
            return anthropic_sdk.Anthropic(api_key=api_key, timeout=self.timeout)  # type: ignore[return-value, no-any-return]

        elif self.provider == AIProvider.OPENAI:
            openai_sdk = _import_sdk("openai")

            # Check secrets.json first, then environment variable
            api_key = _SECRETS.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not found. "
                    "Add to secrets.json or set environment variable: export OPENAI_API_KEY='sk-...'"
                )

            logger.info("Initialized OpenAI client with model: %s", self.model)
            return openai_sdk.OpenAI(api_key=api_key, timeout=self.timeout)  # type: ignore[return-value, no-any-return]

        elif self.provider == AIProvider.OPENROUTER:
            openai_sdk = _import_sdk("openai")

            # Check secrets.json first, then environment variable
            api_key = _SECRETS.get("openrouter_api_key") or os.getenv(
                "OPENROUTER_API_KEY"
            )
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY not found. "
                    "Add to secrets.json or set environment variable: export OPENROUTER_API_KEY='sk-or-...'"
                )

            logger.info("Initialized OpenRouter client with model: %s", self.model)
            return openai_sdk.OpenAI(  # type: ignore[return-value, no-any-return]
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=self.timeout,
            )

        elif self.provider == AIProvider.OLLAMA:
            openai_sdk = _import_sdk("openai")

            # Check options first, then secrets.json, then environment variable
            base_url = (
                self.options.get("base_url")
                or _SECRETS.get("ollama_base_url")
                or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            )

            logger.info(
                "Initialized Ollama client with model: %s at %s", self.model, base_url
            )
            # Ollama doesn't require API key
            return openai_sdk.OpenAI(  # type: ignore[return-value, no-any-return]
                api_key="ollama", base_url=base_url, timeout=self.timeout
            )

        elif self.provider == AIProvider.LMSTUDIO:
            openai_sdk = _import_sdk("openai")

            # Check options first, then secrets.json, then environment variable
            base_url = (
                self.options.get("base_url")
                or _SECRETS.get("lmstudio_base_url")
                or os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
            )

            logger.info(
                "Initialized LM Studio client with model: %s at %s",
                self.model,
                base_url,
            )
            # LM Studio doesn't require API key
            return openai_sdk.OpenAI(  # type: ignore[return-value, no-any-return]
                api_key="lmstudio", base_url=base_url, timeout=self.timeout
            )

        elif self.provider == AIProvider.CLOUDFLARE:
            # Cloudflare Workers AI uses a custom REST API
            # We store credentials and return a placeholder client
            # Actual API calls are made via requests in _generate_cloudflare

            # Check secrets.json first, then environment variables
            self._cloudflare_account_id = (
                self.options.get("cloudflare_account_id")
                or _SECRETS.get("cloudflare_account_id")
                or os.getenv("CLOUDFLARE_ACCOUNT_ID")
            )
            self._cloudflare_api_token = (
                self.options.get("cloudflare_api_token")
                or _SECRETS.get("cloudflare_api_token")
                or os.getenv("CLOUDFLARE_API_TOKEN")
            )

            if not self._cloudflare_account_id:
                raise ValueError(
                    "CLOUDFLARE_ACCOUNT_ID not found. "
                    "Add to secrets.json or set environment variable."
                )
            if not self._cloudflare_api_token:
                raise ValueError(
                    "CLOUDFLARE_API_TOKEN not found. "
                    "Add to secrets.json or set environment variable."
                )

            logger.info("Initialized Cloudflare Workers AI with model: %s", self.model)
            # Return None as we use requests directly for Cloudflare
            return None  # type: ignore[return-value]

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate text using configured AI provider with retry logic.

        Args:
            prompt: User prompt/question to send to the model.
            system: Optional system prompt to guide model behavior.

        Returns:
            Generated text response from the model.

        Raises:
            Exception: If API call fails after all retries.

        Example:
            >>> config = AIConfig()
            >>> response = config.generate(
            ...     "What are the main themes?",
            ...     system="You are a literary analyst"
            ... )
        """
        for attempt in range(self.max_retries):
            try:
                if self.provider == AIProvider.ANTHROPIC:
                    return self._generate_anthropic(prompt, system)
                elif self.provider == AIProvider.CLOUDFLARE:
                    return self._generate_cloudflare(prompt, system)
                else:
                    # OpenAI, OpenRouter, Ollama, and LM Studio all use OpenAI-compatible API
                    return self._generate_openai(prompt, system)
            except (ConnectionError, TimeoutError, OSError) as e:
                # Network errors - always retry
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Network error (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Network error after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                # API errors - check if retriable
                error_type = type(e).__name__
                is_retriable = self._is_retriable_error(e)

                if attempt < self.max_retries - 1 and is_retriable:
                    # Exponential backoff
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"API error {error_type} (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                elif not is_retriable:
                    # Non-retriable error (e.g., invalid API key, bad request)
                    logger.error(f"Non-retriable error {error_type}: {e}")
                    raise
                else:
                    logger.error(
                        f"API error {error_type} after {attempt + 1} attempts: {e}"
                    )
                    raise

        # Should not reach here, but for type safety
        raise RuntimeError("Unexpected error in retry logic")

    def _is_retriable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retriable.

        Checks for:
        - Rate limit errors (429)
        - Server errors (500, 502, 503, 504)
        - Timeout errors
        - Connection errors

        Non-retriable errors include:
        - Authentication errors (401, 403)
        - Bad request errors (400)
        - Not found errors (404)

        Args:
            error: Exception to check.

        Returns:
            True if error is retriable (rate limit, timeout, server error).
        """
        error_str = str(error).lower()

        # Check for non-retriable errors first
        non_retriable_indicators = [
            "401",
            "403",
            "400",
            "404",
            "invalid api key",
            "authentication",
            "unauthorized",
            "forbidden",
        ]
        if any(indicator in error_str for indicator in non_retriable_indicators):
            return False

        # Check for retriable errors
        retriable_indicators = [
            "rate limit",
            "429",  # Rate limit
            "500",  # Internal server error
            "502",  # Bad gateway
            "503",  # Service unavailable
            "504",  # Gateway timeout
            "timeout",
            "connection",
            "network",
        ]
        return any(indicator in error_str for indicator in retriable_indicators)

    def _generate_anthropic(self, prompt: str, system: Optional[str]) -> str:
        """
        Generate text using Anthropic Claude.

        Args:
            prompt: User prompt.
            system: System prompt (optional).

        Returns:
            Generated text.

        Raises:
            anthropic.APIError: If API call fails.
        """
        message = self.client.messages.create(  # type: ignore[union-attr]
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text  # type: ignore[union-attr]

    def _generate_openai(self, prompt: str, system: Optional[str]) -> str:
        """
        Generate text using OpenAI GPT or compatible API.

        Args:
            prompt: User prompt.
            system: System prompt (optional).

        Returns:
            Generated text.

        Raises:
            openai.APIError: If API call fails.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(  # type: ignore[union-attr]
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,  # type: ignore[arg-type]
        )
        return response.choices[0].message.content or ""

    def _generate_cloudflare(self, prompt: str, system: Optional[str]) -> str:
        """
        Generate text using Cloudflare Workers AI.

        Uses Cloudflare's REST API for inference. Supports both text and
        vision models (e.g., @cf/meta/llama-3.2-11b-vision-instruct).

        Args:
            prompt: User prompt.
            system: System prompt (optional).

        Returns:
            Generated text.

        Raises:
            requests.RequestException: If API call fails.
            ValueError: If response format is unexpected.
        """
        import requests

        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self._cloudflare_account_id}/ai/run/{self.model}"
        )

        headers = {
            "Authorization": f"Bearer {self._cloudflare_api_token}",
            "Content-Type": "application/json",
        }

        # Build messages array
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "max_tokens": self.max_tokens,
        }

        response = requests.post(
            url, headers=headers, json=payload, timeout=self.timeout
        )
        response.raise_for_status()

        result = response.json()
        if not result.get("success"):
            errors = result.get("errors", [])
            raise ValueError(f"Cloudflare API error: {errors}")

        # Extract response text
        ai_result = result.get("result", {})
        if isinstance(ai_result, dict):
            return ai_result.get("response", "")
        return str(ai_result)
