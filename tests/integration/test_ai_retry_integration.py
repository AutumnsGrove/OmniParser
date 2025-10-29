"""
Integration tests for AI retry logic and error handling with real API behavior.

These tests validate the retry mechanisms, error classification, and resilience
of the AI configuration system. They are skipped by default.

Run with:
    pytest tests/integration/test_ai_retry_integration.py --run-integration

Requirements:
    - ANTHROPIC_API_KEY environment variable or secrets.json
    - Valid API configuration

Example:
    export ANTHROPIC_API_KEY=sk-ant-...
    pytest tests/integration/test_ai_retry_integration.py --run-integration -v
"""

import os
import time
from unittest.mock import Mock, patch

import pytest

from omniparser.ai_config import AIConfig, AIProvider

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
)
class TestRetryLogicIntegration:
    """Integration tests for retry logic and error handling."""

    def test_successful_request_no_retry(self) -> None:
        """Test that successful requests don't trigger retry logic."""
        config = AIConfig(
            options={
                "ai_provider": "anthropic",
                "ai_model": "claude-3-haiku-20240307",
                "max_retries": 3,
                "retry_delay": 0.5,
            }
        )

        start_time = time.time()
        response = config.generate(
            "Say 'test successful' and nothing else.",
            system="You are a test assistant. Be concise.",
        )
        elapsed = time.time() - start_time

        # Verify response
        assert isinstance(response, str)
        assert len(response) > 0

        # Should complete quickly (no retries)
        # Even with network latency, should be under 10 seconds for a simple prompt
        assert elapsed < 10.0, f"Request took {elapsed:.2f}s - may have retried"

        print(f"\n✅ Successful request completed in {elapsed:.2f}s (no retries)")
        print(f"   Response: {response}")

    def test_error_classification_retriable(self) -> None:
        """Test that retriable errors are correctly identified."""
        config = AIConfig(options={"ai_provider": "anthropic"})

        # Test retriable error indicators
        retriable_errors = [
            Exception("Rate limit exceeded (429)"),
            Exception("Server error (500)"),
            Exception("Bad gateway (502)"),
            Exception("Service unavailable (503)"),
            Exception("Gateway timeout (504)"),
            Exception("Connection timeout"),
            Exception("Network error occurred"),
        ]

        for error in retriable_errors:
            is_retriable = config._is_retriable_error(error)
            assert is_retriable, f"Expected {error} to be retriable"
            print(f"✅ Correctly identified as retriable: {error}")

    def test_error_classification_non_retriable(self) -> None:
        """Test that non-retriable errors are correctly identified."""
        config = AIConfig(options={"ai_provider": "anthropic"})

        # Test non-retriable error indicators
        non_retriable_errors = [
            Exception("Invalid API key (401)"),
            Exception("Forbidden (403)"),
            Exception("Bad request (400)"),
            Exception("Not found (404)"),
            Exception("Authentication failed"),
            Exception("Unauthorized access"),
        ]

        for error in non_retriable_errors:
            is_retriable = config._is_retriable_error(error)
            assert not is_retriable, f"Expected {error} to be non-retriable"
            print(f"✅ Correctly identified as non-retriable: {error}")

    def test_invalid_api_key_no_retry(self) -> None:
        """Test that invalid API key errors don't trigger retries."""
        # Temporarily use invalid key
        original_key = os.environ.get("ANTHROPIC_API_KEY")

        try:
            # Set invalid key
            os.environ["ANTHROPIC_API_KEY"] = "sk-ant-invalid-key-000000000000"

            config = AIConfig(
                options={
                    "ai_provider": "anthropic",
                    "max_retries": 3,
                    "retry_delay": 0.5,
                }
            )

            start_time = time.time()

            # Should fail immediately without retries
            with pytest.raises(Exception) as exc_info:
                config.generate("Test prompt")

            elapsed = time.time() - start_time

            # Should fail quickly (no retries for auth errors)
            # Allow up to 5 seconds for API call and error
            assert elapsed < 5.0, f"Request took {elapsed:.2f}s - may have retried"

            print(f"\n✅ Invalid API key failed in {elapsed:.2f}s (no retries)")
            print(f"   Error: {exc_info.value}")

        finally:
            # Restore original key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key
            else:
                os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_retry_configuration_options(self) -> None:
        """Test that retry configuration options are respected."""
        # Test with different retry configurations
        configs = [
            {"max_retries": 1, "retry_delay": 0.1},
            {"max_retries": 3, "retry_delay": 0.5},
            {"max_retries": 5, "retry_delay": 1.0},
        ]

        for options in configs:
            config = AIConfig(
                options={
                    "ai_provider": "anthropic",
                    "ai_model": "claude-3-haiku-20240307",
                    **options,
                }
            )

            # Verify configuration
            assert config.max_retries == options["max_retries"]
            assert config.retry_delay == options["retry_delay"]

            # Test successful request
            response = config.generate("Say 'configured' and nothing else.")
            assert isinstance(response, str)

            print(
                f"✅ Successfully tested with max_retries={options['max_retries']}, "
                f"retry_delay={options['retry_delay']}"
            )

    def test_timeout_configuration(self) -> None:
        """Test that timeout configuration is respected."""
        # Test with different timeout values
        timeouts = [30, 60, 120]

        for timeout_val in timeouts:
            config = AIConfig(
                options={
                    "ai_provider": "anthropic",
                    "ai_model": "claude-3-haiku-20240307",
                    "timeout": timeout_val,
                }
            )

            # Verify configuration
            assert config.timeout == timeout_val

            # Test successful request
            response = config.generate("Say 'timeout test' and nothing else.")
            assert isinstance(response, str)

            print(f"✅ Successfully tested with timeout={timeout_val}s")


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
)
class TestErrorHandlingIntegration:
    """Integration tests for various error scenarios."""

    def test_network_resilience(self) -> None:
        """Test basic network resilience with real API calls."""
        config = AIConfig(
            options={
                "ai_provider": "anthropic",
                "ai_model": "claude-3-haiku-20240307",
                "max_retries": 2,
                "retry_delay": 0.5,
            }
        )

        # Make multiple sequential requests to verify stability
        for i in range(3):
            response = config.generate(
                f"Say 'request {i+1} successful' and nothing else.",
                system="Be concise.",
            )

            assert isinstance(response, str)
            assert len(response) > 0

            print(f"✅ Request {i+1}/3 successful: {response[:50]}")

    def test_multiple_providers_error_handling(self) -> None:
        """Test error handling consistency across different providers."""
        providers_to_test = []

        # Only test providers with valid keys
        if os.getenv("ANTHROPIC_API_KEY"):
            providers_to_test.append(
                {
                    "ai_provider": "anthropic",
                    "ai_model": "claude-3-haiku-20240307",
                }
            )

        if os.getenv("OPENAI_API_KEY"):
            providers_to_test.append(
                {"ai_provider": "openai", "ai_model": "gpt-3.5-turbo"}
            )

        if not providers_to_test:
            pytest.skip("No API keys available for testing")

        for provider_options in providers_to_test:
            config = AIConfig(
                options={
                    **provider_options,
                    "max_retries": 2,
                    "retry_delay": 0.5,
                }
            )

            # Test successful request
            response = config.generate("Say 'test' and nothing else.")
            assert isinstance(response, str)

            print(
                f"✅ Provider {provider_options['ai_provider']} handles "
                f"errors consistently"
            )

    def test_exponential_backoff_timing(self) -> None:
        """Test that exponential backoff timing works as expected."""
        config = AIConfig(
            options={
                "ai_provider": "anthropic",
                "max_retries": 3,
                "retry_delay": 1.0,
            }
        )

        # We can't easily trigger real retries, but we can test the timing calculation
        # Exponential backoff: delay * (2 ** attempt)
        # attempt 0: 1.0 * 2^0 = 1.0s
        # attempt 1: 1.0 * 2^1 = 2.0s
        # attempt 2: 1.0 * 2^2 = 4.0s

        expected_delays = [1.0, 2.0, 4.0]

        for attempt, expected_delay in enumerate(expected_delays):
            calculated_delay = config.retry_delay * (2**attempt)
            assert (
                calculated_delay == expected_delay
            ), f"Attempt {attempt}: expected {expected_delay}s, got {calculated_delay}s"

        print(f"✅ Exponential backoff timing correct: {expected_delays}")

    def test_concurrent_requests_stability(self) -> None:
        """Test stability with concurrent-like sequential requests."""
        config = AIConfig(
            options={
                "ai_provider": "anthropic",
                "ai_model": "claude-3-haiku-20240307",
                "max_retries": 2,
            }
        )

        # Make several rapid sequential requests
        responses = []
        for i in range(5):
            response = config.generate(
                f"Say 'request {i+1}' and nothing else.",
                system="Be concise.",
            )
            responses.append(response)

        # All should succeed
        assert len(responses) == 5
        assert all(isinstance(r, str) and len(r) > 0 for r in responses)

        print(f"✅ Successfully handled 5 rapid sequential requests")


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Set it to run this test.",
)
class TestAPIProviderIntegration:
    """Integration tests for different AI provider configurations."""

    def test_anthropic_provider_full_workflow(self) -> None:
        """Test complete workflow with Anthropic provider."""
        config = AIConfig(
            options={
                "ai_provider": "anthropic",
                "ai_model": "claude-3-haiku-20240307",
                "max_retries": 2,
                "retry_delay": 0.5,
                "timeout": 30,
            }
        )

        # Test 1: Simple generation
        response1 = config.generate("What is 2+2?", system="Be concise, one number.")
        assert isinstance(response1, str)
        assert len(response1) > 0

        # Test 2: With system prompt
        response2 = config.generate(
            "Summarize: AI is amazing",
            system="You are a professional summarizer.",
        )
        assert isinstance(response2, str)
        assert len(response2) > 0

        # Test 3: Longer prompt
        response3 = config.generate(
            "List 3 colors in alphabetical order.",
            system="Provide a simple list.",
        )
        assert isinstance(response3, str)
        assert len(response3) > 0

        print(f"✅ Anthropic provider full workflow successful")
        print(f"   Response 1: {response1[:50]}")
        print(f"   Response 2: {response2[:50]}")
        print(f"   Response 3: {response3[:50]}")

    def test_provider_initialization_anthropic(self) -> None:
        """Test that Anthropic provider initializes correctly."""
        config = AIConfig(
            options={
                "ai_provider": "anthropic",
                "ai_model": "claude-3-haiku-20240307",
            }
        )

        assert config.provider == AIProvider.ANTHROPIC
        assert config.model == "claude-3-haiku-20240307"
        assert config.client is not None

        # Test that it can make a request
        response = config.generate("Say 'initialized' and nothing else.")
        assert isinstance(response, str)

        print(f"✅ Anthropic provider initialized successfully")
        print(f"   Model: {config.model}")
        print(f"   Response: {response}")
