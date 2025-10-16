"""Pytest configuration and fixtures for OmniParser tests."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from src.omniparser.models import (
    ImageReference,
    Chapter,
    Metadata,
    ProcessingInfo,
    Document,
)


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
