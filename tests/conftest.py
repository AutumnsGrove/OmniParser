"""Pytest configuration and fixtures for OmniParser tests."""

import pytest
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from src.omniparser.models import (
    ImageReference,
    Chapter,
    Metadata,
    ProcessingInfo,
    Document,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_image_reference():
    """Sample ImageReference for testing."""
    return ImageReference(
        image_id="img_001",
        position=100,
        file_path="/tmp/image.png",
        alt_text="Sample image",
        size=(800, 600),
        format="png",
    )


@pytest.fixture
def sample_chapter():
    """Sample Chapter for testing."""
    return Chapter(
        chapter_id=1,
        title="Chapter 1",
        content="# Chapter 1\n\nThis is the content.",
        start_position=0,
        end_position=100,
        word_count=50,
        level=1,
        metadata={"author": "Test Author"},
    )


@pytest.fixture
def sample_metadata():
    """Sample Metadata for testing."""
    return Metadata(
        title="Test Document",
        author="Test Author",
        authors=["Test Author", "Co-Author"],
        publisher="Test Publisher",
        publication_date=datetime(2025, 1, 1),
        language="en",
        isbn="978-1234567890",
        description="A test document",
        tags=["test", "sample"],
        original_format="epub",
        file_size=1024000,
        custom_fields={"custom": "value"},
    )


@pytest.fixture
def sample_processing_info():
    """Sample ProcessingInfo for testing."""
    return ProcessingInfo(
        parser_used="epub",
        parser_version="1.0.0",
        processing_time=1.5,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        warnings=["Warning 1", "Warning 2"],
        options_used={"extract_images": True},
    )


@pytest.fixture
def sample_document(
    sample_chapter, sample_image_reference, sample_metadata, sample_processing_info
):
    """Sample Document for testing."""
    return Document(
        document_id="doc_001",
        content="# Chapter 1\n\nThis is the content.",
        chapters=[sample_chapter],
        images=[sample_image_reference],
        metadata=sample_metadata,
        processing_info=sample_processing_info,
        word_count=50,
        estimated_reading_time=1,
    )


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Test content")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# AI Provider Configuration Fixtures


def check_lmstudio_available() -> bool:
    """Check if LM Studio server is available."""
    import socket
    try:
        # Quick connection test to LM Studio default port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 1234))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_anthropic_available() -> bool:
    """Check if Anthropic API key is available."""
    # Check environment variable
    if os.getenv("ANTHROPIC_API_KEY"):
        return True

    # Check secrets.json
    try:
        import json
        from pathlib import Path
        secrets_path = Path(__file__).parent.parent / "secrets.json"
        if secrets_path.exists():
            with open(secrets_path) as f:
                secrets = json.load(f)
                return bool(secrets.get("anthropic_api_key"))
    except Exception:
        pass

    return False


@pytest.fixture
def lmstudio_options() -> Dict[str, str]:
    """LM Studio AI configuration options."""
    return {
        "ai_provider": "lmstudio",
        "ai_model": "google/gemma-3n-e4b",
        "base_url": "http://localhost:1234/v1",
    }


@pytest.fixture
def anthropic_options() -> Dict[str, str]:
    """Anthropic AI configuration options."""
    return {
        "ai_provider": "anthropic",
        "ai_model": "claude-3-haiku-20240307",
    }


@pytest.fixture
def ai_options_with_fallback(lmstudio_options, anthropic_options) -> Dict[str, str]:
    """
    AI configuration with automatic fallback.

    Tries LM Studio first, then Anthropic, then skips test.
    Logs which provider is being used for transparency.
    """
    # Try LM Studio first
    if check_lmstudio_available():
        logger.info("✓ Using LM Studio for testing (cost-effective local model)")
        return lmstudio_options

    logger.warning("✗ LM Studio not available, trying Anthropic fallback...")

    # Fallback to Anthropic
    if check_anthropic_available():
        logger.info("✓ Using Anthropic API for testing (fallback)")
        return anthropic_options

    # Both unavailable - skip test
    pytest.skip(
        "No AI provider available. Either start LM Studio on localhost:1234 "
        "or set ANTHROPIC_API_KEY environment variable."
    )


@pytest.fixture
def ai_config_with_fallback(ai_options_with_fallback):
    """
    AIConfig instance with automatic provider fallback.

    Creates a configured AIConfig that's ready to use in tests.
    Includes health check to verify the provider actually works.
    """
    from src.omniparser.ai_config import AIConfig

    try:
        config = AIConfig(options=ai_options_with_fallback)

        # Quick health check with simple prompt
        try:
            response = config.generate(
                "Say 'ready' and nothing else.",
                system="Be concise."
            )
            if response and len(response) > 0:
                logger.info(f"✓ AI provider health check passed: {config.provider.value}")
                return config
        except Exception as e:
            logger.warning(f"✗ Provider health check failed: {e}")

            # If LM Studio failed, try Anthropic
            if ai_options_with_fallback.get("ai_provider") == "lmstudio":
                if check_anthropic_available():
                    logger.info("↻ Retrying with Anthropic fallback...")
                    anthropic_opts = {
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307",
                    }
                    config = AIConfig(options=anthropic_opts)
                    config.generate("Say 'ready' and nothing else.", system="Be concise.")
                    logger.info("✓ Anthropic fallback health check passed")
                    return config

            raise
    except Exception as e:
        pytest.skip(f"AI provider initialization failed: {e}")


@pytest.fixture
def vision_capable_ai_options(ai_options_with_fallback) -> Dict[str, str]:
    """
    AI options for vision-capable models.

    LM Studio local models typically don't support vision,
    so this always uses Anthropic for vision tests.
    """
    if ai_options_with_fallback.get("ai_provider") == "lmstudio":
        logger.info("⚠ Vision test detected - using Anthropic (local models don't support vision)")

        if not check_anthropic_available():
            pytest.skip(
                "Vision tests require Anthropic API. "
                "Set ANTHROPIC_API_KEY to run vision tests."
            )

        return {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307",
        }

    return ai_options_with_fallback
