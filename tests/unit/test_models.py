"""
Tests for data models.

This module provides comprehensive tests for all 5 dataclasses
(ImageReference, Chapter, Metadata, ProcessingInfo, Document)
and all 6 Document helper methods (get_chapter, get_text_range,
to_dict, from_dict, save_json, load_json).
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from src.omniparser.models import (
    ImageReference,
    Chapter,
    Metadata,
    ProcessingInfo,
    Document,
)


class TestImageReference:
    """Tests for ImageReference model."""

    def test_create_with_required_fields(self):
        """Test creating ImageReference with only required fields."""
        img = ImageReference(image_id="img_001", position=100)
        assert img.image_id == "img_001"
        assert img.position == 100
        assert img.format == "unknown"

    def test_optional_fields_default_none(self):
        """Test that optional fields default to None."""
        img = ImageReference(image_id="img_001", position=100)
        assert img.file_path is None
        assert img.alt_text is None
        assert img.size is None

    def test_with_all_fields(self):
        """Test creating with all fields."""
        img = ImageReference(
            image_id="img_001",
            position=100,
            file_path="/tmp/img.png",
            alt_text="Test image",
            size=(800, 600),
            format="png",
        )
        assert img.image_id == "img_001"
        assert img.position == 100
        assert img.file_path == "/tmp/img.png"
        assert img.alt_text == "Test image"
        assert img.size == (800, 600)
        assert img.format == "png"

    def test_format_default_unknown(self):
        """Test that format defaults to 'unknown'."""
        img = ImageReference(image_id="img_001", position=100)
        assert img.format == "unknown"

    def test_position_zero(self):
        """Test creating ImageReference at position 0."""
        img = ImageReference(image_id="img_001", position=0)
        assert img.position == 0

    def test_negative_position(self):
        """Test creating ImageReference with negative position."""
        img = ImageReference(image_id="img_001", position=-1)
        assert img.position == -1

    def test_various_image_formats(self):
        """Test various image formats."""
        formats = ["png", "jpg", "jpeg", "webp", "gif", "svg"]
        for fmt in formats:
            img = ImageReference(image_id=f"img_{fmt}", position=0, format=fmt)
            assert img.format == fmt

    def test_size_tuple(self):
        """Test size as (width, height) tuple."""
        img = ImageReference(
            image_id="img_001",
            position=0,
            size=(1920, 1080),
        )
        assert img.size == (1920, 1080)
        assert img.size[0] == 1920  # width
        assert img.size[1] == 1080  # height


class TestChapter:
    """Tests for Chapter model."""

    def test_create_with_required_fields(self, sample_chapter):
        """Test creating Chapter with required fields."""
        assert sample_chapter.chapter_id == 1
        assert sample_chapter.title == "Chapter 1"
        assert sample_chapter.word_count == 50

    def test_position_tracking(self, sample_chapter):
        """Test chapter position tracking."""
        assert sample_chapter.start_position == 0
        assert sample_chapter.end_position == 100

    def test_default_level(self):
        """Test that level defaults to 1."""
        chapter = Chapter(
            chapter_id=1,
            title="Test",
            content="Content",
            start_position=0,
            end_position=10,
            word_count=5,
        )
        assert chapter.level == 1

    def test_with_metadata(self):
        """Test chapter with custom metadata."""
        chapter = Chapter(
            chapter_id=1,
            title="Test",
            content="Content",
            start_position=0,
            end_position=10,
            word_count=5,
            level=2,
            metadata={"custom": "value", "author": "Test"},
        )
        assert chapter.metadata == {"custom": "value", "author": "Test"}
        assert chapter.level == 2

    def test_metadata_default_none(self):
        """Test that metadata defaults to None."""
        chapter = Chapter(
            chapter_id=1,
            title="Test",
            content="Content",
            start_position=0,
            end_position=10,
            word_count=5,
        )
        assert chapter.metadata is None

    def test_different_heading_levels(self):
        """Test chapters with different heading levels."""
        for level in range(1, 7):  # Test levels 1-6
            chapter = Chapter(
                chapter_id=level,
                title=f"Level {level} Chapter",
                content="Content",
                start_position=0,
                end_position=10,
                word_count=5,
                level=level,
            )
            assert chapter.level == level

    def test_empty_content(self):
        """Test chapter with empty content."""
        chapter = Chapter(
            chapter_id=1,
            title="Empty Chapter",
            content="",
            start_position=0,
            end_position=0,
            word_count=0,
        )
        assert chapter.content == ""
        assert chapter.word_count == 0

    def test_long_content(self):
        """Test chapter with long content."""
        long_content = "word " * 10000
        chapter = Chapter(
            chapter_id=1,
            title="Long Chapter",
            content=long_content,
            start_position=0,
            end_position=len(long_content),
            word_count=10000,
        )
        assert len(chapter.content) == len(long_content)
        assert chapter.word_count == 10000

    def test_position_range(self):
        """Test that end_position is greater than start_position."""
        chapter = Chapter(
            chapter_id=1,
            title="Test",
            content="Content",
            start_position=100,
            end_position=200,
            word_count=20,
        )
        assert chapter.end_position > chapter.start_position
        assert chapter.end_position - chapter.start_position == 100


class TestMetadata:
    """Tests for Metadata model."""

    def test_create_empty(self):
        """Test creating empty Metadata."""
        meta = Metadata()
        assert meta.title is None
        assert meta.author is None
        assert meta.file_size == 0

    def test_create_with_all_fields(self, sample_metadata):
        """Test creating with all fields."""
        assert sample_metadata.title == "Test Document"
        assert sample_metadata.author == "Test Author"
        assert len(sample_metadata.authors) == 2
        assert sample_metadata.isbn == "978-1234567890"

    def test_publication_date_datetime(self, sample_metadata):
        """Test that publication_date is datetime object."""
        assert isinstance(sample_metadata.publication_date, datetime)
        assert sample_metadata.publication_date.year == 2025

    def test_custom_fields(self, sample_metadata):
        """Test custom metadata fields."""
        assert sample_metadata.custom_fields["custom"] == "value"

    def test_file_size_default_zero(self):
        """Test that file_size defaults to 0."""
        meta = Metadata()
        assert meta.file_size == 0

    def test_optional_fields_default_none(self):
        """Test that all optional fields default to None."""
        meta = Metadata()
        assert meta.title is None
        assert meta.author is None
        assert meta.authors is None
        assert meta.publisher is None
        assert meta.publication_date is None
        assert meta.language is None
        assert meta.isbn is None
        assert meta.description is None
        assert meta.tags is None
        assert meta.original_format is None
        assert meta.custom_fields is None

    def test_multiple_authors(self):
        """Test metadata with multiple authors."""
        meta = Metadata(
            authors=["Author 1", "Author 2", "Author 3"],
        )
        assert len(meta.authors) == 3
        assert "Author 2" in meta.authors

    def test_multiple_tags(self):
        """Test metadata with multiple tags."""
        meta = Metadata(
            tags=["fiction", "sci-fi", "adventure", "space"],
        )
        assert len(meta.tags) == 4
        assert "sci-fi" in meta.tags

    def test_various_formats(self):
        """Test different original_format values."""
        formats = ["epub", "pdf", "txt", "docx", "html", "markdown"]
        for fmt in formats:
            meta = Metadata(original_format=fmt)
            assert meta.original_format == fmt

    def test_language_codes(self):
        """Test various language codes."""
        languages = ["en", "fr", "de", "es", "ja", "zh"]
        for lang in languages:
            meta = Metadata(language=lang)
            assert meta.language == lang

    def test_large_file_size(self):
        """Test metadata with large file size."""
        meta = Metadata(file_size=1024 * 1024 * 100)  # 100 MB
        assert meta.file_size == 104857600

    def test_custom_fields_dictionary(self):
        """Test custom_fields with various data types."""
        meta = Metadata(
            custom_fields={
                "string": "value",
                "number": 42,
                "boolean": True,
                "list": [1, 2, 3],
                "nested": {"key": "value"},
            }
        )
        assert meta.custom_fields["string"] == "value"
        assert meta.custom_fields["number"] == 42
        assert meta.custom_fields["boolean"] is True
        assert meta.custom_fields["list"] == [1, 2, 3]
        assert meta.custom_fields["nested"]["key"] == "value"


class TestProcessingInfo:
    """Tests for ProcessingInfo model."""

    def test_create_with_required_fields(self):
        """Test creating ProcessingInfo with required fields."""
        info = ProcessingInfo(
            parser_used="epub",
            parser_version="1.0.0",
            processing_time=1.5,
            timestamp=datetime.now(),
        )
        assert info.parser_used == "epub"
        assert info.parser_version == "1.0.0"
        assert info.processing_time == 1.5

    def test_warnings_default_empty_list(self):
        """Test that warnings defaults to empty list."""
        info = ProcessingInfo(
            parser_used="epub",
            parser_version="1.0.0",
            processing_time=1.5,
            timestamp=datetime.now(),
        )
        assert info.warnings == []
        assert isinstance(info.warnings, list)

    def test_options_used_default_empty_dict(self):
        """Test that options_used defaults to empty dict."""
        info = ProcessingInfo(
            parser_used="epub",
            parser_version="1.0.0",
            processing_time=1.5,
            timestamp=datetime.now(),
        )
        assert info.options_used == {}
        assert isinstance(info.options_used, dict)

    def test_with_warnings(self, sample_processing_info):
        """Test processing info with warnings."""
        assert len(sample_processing_info.warnings) == 2
        assert "Warning 1" in sample_processing_info.warnings
        assert "Warning 2" in sample_processing_info.warnings

    def test_with_options(self, sample_processing_info):
        """Test processing info with options."""
        assert sample_processing_info.options_used["extract_images"] is True

    def test_timestamp_datetime(self, sample_processing_info):
        """Test that timestamp is datetime object."""
        assert isinstance(sample_processing_info.timestamp, datetime)

    def test_zero_processing_time(self):
        """Test processing info with zero processing time."""
        info = ProcessingInfo(
            parser_used="epub",
            parser_version="1.0.0",
            processing_time=0.0,
            timestamp=datetime.now(),
        )
        assert info.processing_time == 0.0

    def test_multiple_warnings(self):
        """Test processing info with multiple warnings."""
        warnings = [
            "Missing cover image",
            "Invalid chapter link",
            "Encoding issue",
            "Missing metadata field",
        ]
        info = ProcessingInfo(
            parser_used="epub",
            parser_version="1.0.0",
            processing_time=1.5,
            timestamp=datetime.now(),
            warnings=warnings,
        )
        assert len(info.warnings) == 4
        assert all(w in info.warnings for w in warnings)

    def test_various_options(self):
        """Test processing info with various options."""
        options = {
            "extract_images": True,
            "parse_toc": True,
            "clean_text": False,
            "max_image_size": 1024,
            "output_format": "markdown",
        }
        info = ProcessingInfo(
            parser_used="epub",
            parser_version="1.0.0",
            processing_time=1.5,
            timestamp=datetime.now(),
            options_used=options,
        )
        assert info.options_used == options
        assert info.options_used["extract_images"] is True
        assert info.options_used["max_image_size"] == 1024

    def test_version_string_formats(self):
        """Test various version string formats."""
        versions = ["1.0.0", "2.1.3", "0.0.1", "1.0.0-beta", "2.0.0-rc1"]
        for version in versions:
            info = ProcessingInfo(
                parser_used="epub",
                parser_version=version,
                processing_time=1.5,
                timestamp=datetime.now(),
            )
            assert info.parser_version == version


class TestDocument:
    """Tests for Document model and helper methods."""

    def test_create_document(self, sample_document):
        """Test creating a Document."""
        assert sample_document.document_id == "doc_001"
        assert sample_document.word_count == 50
        assert len(sample_document.chapters) == 1

    def test_document_structure(self, sample_document):
        """Test document structure and relationships."""
        assert isinstance(sample_document.chapters, list)
        assert isinstance(sample_document.images, list)
        assert isinstance(sample_document.metadata, Metadata)
        assert isinstance(sample_document.processing_info, ProcessingInfo)

    # Helper Method Tests

    def test_get_chapter_existing(self, sample_document):
        """Test retrieving an existing chapter."""
        chapter = sample_document.get_chapter(1)
        assert chapter is not None
        assert chapter.chapter_id == 1
        assert chapter.title == "Chapter 1"

    def test_get_chapter_nonexistent(self, sample_document):
        """Test retrieving non-existent chapter returns None."""
        chapter = sample_document.get_chapter(999)
        assert chapter is None

    def test_get_chapter_zero(self, sample_document):
        """Test retrieving chapter with ID 0."""
        chapter = sample_document.get_chapter(0)
        assert chapter is None

    def test_get_chapter_negative(self, sample_document):
        """Test retrieving chapter with negative ID."""
        chapter = sample_document.get_chapter(-1)
        assert chapter is None

    def test_get_text_range(self, sample_document):
        """Test extracting text range."""
        text = sample_document.get_text_range(0, 10)
        assert text == "# Chapter "
        assert len(text) == 10

    def test_get_text_range_full(self, sample_document):
        """Test extracting full text."""
        text = sample_document.get_text_range(0, len(sample_document.content))
        assert text == sample_document.content

    def test_get_text_range_middle(self, sample_document):
        """Test extracting text from middle of content."""
        text = sample_document.get_text_range(2, 9)
        assert text == "Chapter"

    def test_get_text_range_empty(self, sample_document):
        """Test extracting empty text range."""
        text = sample_document.get_text_range(5, 5)
        assert text == ""

    def test_get_text_range_beyond_content(self, sample_document):
        """Test extracting text range beyond content length."""
        text = sample_document.get_text_range(0, 10000)
        assert text == sample_document.content

    def test_to_dict(self, sample_document):
        """Test serializing Document to dict."""
        data = sample_document.to_dict()
        assert isinstance(data, dict)
        assert data["document_id"] == "doc_001"
        assert data["word_count"] == 50
        assert "chapters" in data
        assert "metadata" in data
        assert "processing_info" in data
        assert "images" in data

    def test_to_dict_chapters_serialized(self, sample_document):
        """Test that chapters are serialized as dicts."""
        data = sample_document.to_dict()
        assert isinstance(data["chapters"], list)
        assert len(data["chapters"]) == 1
        assert isinstance(data["chapters"][0], dict)
        assert data["chapters"][0]["title"] == "Chapter 1"

    def test_to_dict_metadata_serialized(self, sample_document):
        """Test that metadata is serialized as dict."""
        data = sample_document.to_dict()
        assert isinstance(data["metadata"], dict)
        assert data["metadata"]["title"] == "Test Document"

    def test_from_dict(self, sample_document):
        """Test deserializing Document from dict."""
        data = sample_document.to_dict()
        doc = Document.from_dict(data)
        assert doc.document_id == sample_document.document_id
        assert doc.word_count == sample_document.word_count
        assert len(doc.chapters) == len(sample_document.chapters)

    def test_from_dict_nested_objects(self, sample_document):
        """Test that nested objects are properly deserialized."""
        data = sample_document.to_dict()
        doc = Document.from_dict(data)
        assert isinstance(doc.metadata, Metadata)
        assert isinstance(doc.processing_info, ProcessingInfo)
        assert isinstance(doc.chapters[0], Chapter)
        if doc.images:
            assert isinstance(doc.images[0], ImageReference)

    def test_round_trip_serialization(self, sample_document):
        """Test that to_dict/from_dict round trip preserves data."""
        data = sample_document.to_dict()
        doc = Document.from_dict(data)

        assert doc.document_id == sample_document.document_id
        assert doc.content == sample_document.content
        assert doc.word_count == sample_document.word_count
        assert len(doc.chapters) == len(sample_document.chapters)
        assert doc.chapters[0].title == sample_document.chapters[0].title
        assert doc.metadata.title == sample_document.metadata.title

    def test_save_json(self, sample_document, temp_json_file):
        """Test saving Document to JSON file."""
        sample_document.save_json(str(temp_json_file))

        assert temp_json_file.exists()

        with open(temp_json_file, "r") as f:
            data = json.load(f)

        assert data["document_id"] == "doc_001"
        assert "chapters" in data

    def test_save_json_creates_file(self, sample_document):
        """Test that save_json creates a new file."""
        temp_path = Path("/tmp/test_save_json.json")
        if temp_path.exists():
            temp_path.unlink()

        sample_document.save_json(str(temp_path))

        assert temp_path.exists()

        # Cleanup
        temp_path.unlink()

    def test_load_json(self, sample_document, temp_json_file):
        """Test loading Document from JSON file."""
        sample_document.save_json(str(temp_json_file))

        loaded_doc = Document.load_json(str(temp_json_file))

        assert loaded_doc.document_id == sample_document.document_id
        assert loaded_doc.word_count == sample_document.word_count
        assert len(loaded_doc.chapters) == len(sample_document.chapters)

    def test_json_round_trip(self, sample_document, temp_json_file):
        """Test that save/load JSON preserves all data."""
        sample_document.save_json(str(temp_json_file))
        loaded = Document.load_json(str(temp_json_file))

        assert loaded.document_id == sample_document.document_id
        assert loaded.content == sample_document.content
        assert loaded.word_count == sample_document.word_count
        assert loaded.chapters[0].title == sample_document.chapters[0].title
        assert loaded.metadata.title == sample_document.metadata.title
        assert (
            loaded.processing_info.parser_used
            == sample_document.processing_info.parser_used
        )

    def test_datetime_serialization(self, sample_document, temp_json_file):
        """Test that datetime objects are properly serialized."""
        sample_document.save_json(str(temp_json_file))

        with open(temp_json_file, "r") as f:
            data = json.load(f)

        # Check datetime is serialized as ISO string
        assert isinstance(data["metadata"]["publication_date"], str)
        assert isinstance(data["processing_info"]["timestamp"], str)
        assert "T" in data["metadata"]["publication_date"]  # ISO format
        assert "T" in data["processing_info"]["timestamp"]  # ISO format

    def test_datetime_deserialization(self, sample_document, temp_json_file):
        """Test that datetime strings are properly deserialized."""
        sample_document.save_json(str(temp_json_file))
        loaded = Document.load_json(str(temp_json_file))

        # Check datetime is deserialized back to datetime object
        assert isinstance(loaded.metadata.publication_date, datetime)
        assert isinstance(loaded.processing_info.timestamp, datetime)
        assert (
            loaded.metadata.publication_date
            == sample_document.metadata.publication_date
        )
        assert (
            loaded.processing_info.timestamp
            == sample_document.processing_info.timestamp
        )

    def test_json_utf8_encoding(self, temp_json_file):
        """Test that JSON files are saved with UTF-8 encoding."""
        doc = Document(
            document_id="doc_utf8",
            content="Content with unicode: Hello مرحبا שלום",
            chapters=[],
            images=[],
            metadata=Metadata(title="Unicode Title: 日本語"),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=5,
            estimated_reading_time=1,
        )

        doc.save_json(str(temp_json_file))
        loaded = Document.load_json(str(temp_json_file))

        assert loaded.content == doc.content
        assert loaded.metadata.title == doc.metadata.title

    def test_json_pretty_formatted(self, sample_document, temp_json_file):
        """Test that JSON is pretty-formatted with indentation."""
        sample_document.save_json(str(temp_json_file))

        with open(temp_json_file, "r") as f:
            content = f.read()

        # Check for indentation (pretty printing)
        assert "  " in content  # Should have indentation
        assert "\n" in content  # Should have newlines

    def test_empty_chapters_list(self):
        """Test document with empty chapters list."""
        doc = Document(
            document_id="doc_empty",
            content="Content without chapters",
            chapters=[],
            images=[],
            metadata=Metadata(),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=3,
            estimated_reading_time=1,
        )

        assert len(doc.chapters) == 0
        assert doc.get_chapter(1) is None

    def test_multiple_chapters(self):
        """Test document with multiple chapters."""
        chapters = [
            Chapter(
                chapter_id=i,
                title=f"Chapter {i}",
                content=f"Content {i}",
                start_position=i * 100,
                end_position=(i + 1) * 100,
                word_count=20,
            )
            for i in range(1, 6)
        ]

        doc = Document(
            document_id="doc_multi",
            content="Full content",
            chapters=chapters,
            images=[],
            metadata=Metadata(),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=100,
            estimated_reading_time=1,
        )

        assert len(doc.chapters) == 5
        assert doc.get_chapter(3).title == "Chapter 3"
        assert doc.get_chapter(5).title == "Chapter 5"

    def test_estimated_reading_time(self, sample_document):
        """Test estimated reading time calculation."""
        assert sample_document.estimated_reading_time == 1
        assert isinstance(sample_document.estimated_reading_time, int)

    def test_document_with_images(self, sample_document):
        """Test document with image references."""
        assert isinstance(sample_document.images, list)
        if sample_document.images:
            assert isinstance(sample_document.images[0], ImageReference)


# Edge Cases and Error Handling Tests


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_chapter_at_boundary_positions(self):
        """Test chapter with boundary position values."""
        chapter = Chapter(
            chapter_id=1,
            title="Boundary Chapter",
            content="x" * 1000000,  # 1 million characters
            start_position=0,
            end_position=1000000,
            word_count=200000,
        )
        assert chapter.end_position == 1000000

    def test_document_with_special_characters(self):
        """Test document with special characters in content."""
        special_content = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        doc = Document(
            document_id="doc_special",
            content=special_content,
            chapters=[],
            images=[],
            metadata=Metadata(),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=5,
            estimated_reading_time=1,
        )
        assert doc.content == special_content

    def test_metadata_with_very_long_title(self):
        """Test metadata with very long title."""
        long_title = "A" * 10000
        meta = Metadata(title=long_title)
        assert len(meta.title) == 10000

    def test_processing_info_with_very_long_processing_time(self):
        """Test processing info with very long processing time."""
        info = ProcessingInfo(
            parser_used="test",
            parser_version="1.0.0",
            processing_time=3600.0,  # 1 hour
            timestamp=datetime.now(),
        )
        assert info.processing_time == 3600.0

    def test_document_id_with_special_characters(self):
        """Test document ID with special characters."""
        doc = Document(
            document_id="doc_2024-01-01_v1.0_final",
            content="Content",
            chapters=[],
            images=[],
            metadata=Metadata(),
            processing_info=ProcessingInfo(
                parser_used="test",
                parser_version="1.0.0",
                processing_time=1.0,
                timestamp=datetime.now(),
            ),
            word_count=1,
            estimated_reading_time=1,
        )
        assert doc.document_id == "doc_2024-01-01_v1.0_final"
