"""
Unit tests for metadata_builder module.

Tests the MetadataBuilder helper class used by all parsers.
"""

from datetime import datetime

import pytest

from omniparser.models import Metadata
from omniparser.processors.metadata_builder import MetadataBuilder


class TestMetadataBuilder:
    """Test suite for MetadataBuilder class."""

    def test_build_with_all_fields(self):
        """Test building metadata with all fields specified."""
        # Arrange
        pub_date = datetime(2025, 1, 15)
        custom = {"extra_field": "value"}
        tags = ["python", "parsing"]
        authors = ["Author One", "Author Two"]

        # Act
        metadata = MetadataBuilder.build(
            title="Test Document",
            author="Author One",
            authors=authors,
            publisher="Test Publisher",
            publication_date=pub_date,
            language="en",
            isbn="978-1234567890",
            description="Test description",
            tags=tags,
            original_format="pdf",
            file_size=1024000,
            custom_fields=custom,
        )

        # Assert
        assert isinstance(metadata, Metadata)
        assert metadata.title == "Test Document"
        assert metadata.author == "Author One"
        assert metadata.authors == authors
        assert metadata.publisher == "Test Publisher"
        assert metadata.publication_date == pub_date
        assert metadata.language == "en"
        assert metadata.isbn == "978-1234567890"
        assert metadata.description == "Test description"
        assert metadata.tags == tags
        assert metadata.original_format == "pdf"
        assert metadata.file_size == 1024000
        assert metadata.custom_fields == custom

    def test_build_with_minimal_fields(self):
        """Test building metadata with only required fields."""
        # Act
        metadata = MetadataBuilder.build(
            title="Minimal Doc",
            original_format="txt",
        )

        # Assert
        assert metadata.title == "Minimal Doc"
        assert metadata.author is None
        assert metadata.authors is None
        assert metadata.publisher is None
        assert metadata.publication_date is None
        assert metadata.language is None
        assert metadata.isbn is None
        assert metadata.description is None
        assert metadata.tags is None
        assert metadata.original_format == "txt"
        assert metadata.file_size == 0
        assert metadata.custom_fields is None

    def test_build_with_none_values(self):
        """Test that None values are passed through correctly."""
        # Act
        metadata = MetadataBuilder.build(
            title=None,
            author=None,
            language=None,
            original_format="md",
        )

        # Assert
        assert metadata.title is None
        assert metadata.author is None
        assert metadata.language is None
        assert metadata.original_format == "md"

    def test_build_epub_style(self):
        """Test building metadata in EPUB parser style."""
        # Arrange - typical EPUB metadata
        authors = ["F. Scott Fitzgerald"]
        tags = ["fiction", "classic"]
        pub_date = datetime(1925, 4, 10)

        # Act
        metadata = MetadataBuilder.build(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            authors=authors,
            publisher="Scribner",
            publication_date=pub_date,
            language="en",
            isbn="978-0743273565",
            description="A novel set in Jazz Age America.",
            tags=tags,
            original_format="epub",
            file_size=1024000,
            custom_fields={},
        )

        # Assert
        assert metadata.title == "The Great Gatsby"
        assert metadata.author == "F. Scott Fitzgerald"
        assert metadata.authors == authors
        assert metadata.publisher == "Scribner"
        assert metadata.publication_date == pub_date
        assert metadata.language == "en"
        assert metadata.isbn == "978-0743273565"
        assert metadata.description is not None
        assert metadata.tags == tags
        assert metadata.original_format == "epub"

    def test_build_pdf_style(self):
        """Test building metadata in PDF parser style."""
        # Arrange - typical PDF metadata
        creation_date = datetime(2024, 7, 9, 5, 0, 0)
        tags = ["python", "documentation"]
        custom_fields = {
            "page_count": 42,
            "creator": "LaTeX",
            "producer": "pdfTeX",
            "pdf_version": "1.5",
        }

        # Act
        metadata = MetadataBuilder.build(
            title="Python Guide",
            author="John Doe",
            description="Complete Python reference",
            publication_date=creation_date,
            tags=tags,
            original_format="pdf",
            file_size=2048000,
            custom_fields=custom_fields,
        )

        # Assert
        assert metadata.title == "Python Guide"
        assert metadata.author == "John Doe"
        assert metadata.description == "Complete Python reference"
        assert metadata.publication_date == creation_date
        assert metadata.tags == tags
        assert metadata.original_format == "pdf"
        assert metadata.file_size == 2048000
        assert metadata.custom_fields == custom_fields
        assert metadata.custom_fields["page_count"] == 42

    def test_build_docx_style(self):
        """Test building metadata in DOCX parser style."""
        # Arrange - typical DOCX metadata (often missing fields)
        pub_date = datetime(2025, 1, 10)
        tags = ["report", "quarterly"]

        # Act
        metadata = MetadataBuilder.build(
            title="Q1 Report",
            author="Jane Smith",
            authors=["Jane Smith"],
            publisher=None,  # DOCX doesn't have publisher
            publication_date=pub_date,
            language=None,  # DOCX doesn't expose language
            isbn=None,
            description="Quarterly business report",
            tags=tags,
            original_format="docx",
            file_size=512000,
            custom_fields={
                "last_modified_by": "John Admin",
                "modified": "2025-01-11T14:30:00",
            },
        )

        # Assert
        assert metadata.title == "Q1 Report"
        assert metadata.author == "Jane Smith"
        assert metadata.authors == ["Jane Smith"]
        assert metadata.publisher is None
        assert metadata.language is None
        assert metadata.isbn is None
        assert metadata.original_format == "docx"
        assert metadata.custom_fields["last_modified_by"] == "John Admin"

    def test_build_text_style(self):
        """Test building metadata in text parser style."""
        # Arrange - minimal text file metadata
        custom_fields = {
            "encoding": "utf-8",
            "line_count": 145,
        }

        # Act
        metadata = MetadataBuilder.build(
            title="notes",
            author=None,
            authors=None,
            publisher=None,
            publication_date=None,
            language=None,
            isbn=None,
            description=None,
            tags=None,
            original_format="text",
            file_size=8192,
            custom_fields=custom_fields,
        )

        # Assert
        assert metadata.title == "notes"
        assert metadata.author is None
        assert metadata.original_format == "text"
        assert metadata.file_size == 8192
        assert metadata.custom_fields == custom_fields

    def test_build_markdown_style(self):
        """Test building metadata in markdown parser style."""
        # Arrange - markdown with frontmatter
        authors = ["Alice", "Bob"]
        tags = ["tutorial", "beginner"]
        pub_date = datetime(2025, 1, 15)

        # Act
        metadata = MetadataBuilder.build(
            title="Markdown Tutorial",
            author="Alice",
            authors=authors,
            publisher="DevDocs",
            publication_date=pub_date,
            language="en",
            isbn=None,  # Markdown doesn't have ISBN
            description="Learn markdown syntax",
            tags=tags,
            original_format="markdown",
            file_size=16384,
            custom_fields={"draft": False, "featured": True},
        )

        # Assert
        assert metadata.title == "Markdown Tutorial"
        assert metadata.author == "Alice"
        assert metadata.authors == authors
        assert metadata.publisher == "DevDocs"
        assert metadata.publication_date == pub_date
        assert metadata.language == "en"
        assert metadata.isbn is None
        assert metadata.original_format == "markdown"
        assert metadata.custom_fields["draft"] is False

    def test_build_returns_metadata_instance(self):
        """Test that build() always returns a Metadata instance."""
        # Act
        metadata = MetadataBuilder.build(original_format="test")

        # Assert
        assert isinstance(metadata, Metadata)

    def test_build_default_file_size(self):
        """Test that file_size defaults to 0 when not specified."""
        # Act
        metadata = MetadataBuilder.build(title="Test")

        # Assert
        assert metadata.file_size == 0

    def test_build_empty_custom_fields(self):
        """Test building with empty custom_fields dict."""
        # Act
        metadata = MetadataBuilder.build(
            title="Test",
            custom_fields={},
        )

        # Assert
        assert metadata.custom_fields == {}

    def test_build_complex_custom_fields(self):
        """Test building with complex nested custom_fields."""
        # Arrange
        custom_fields = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "bool": True,
            "number": 42,
        }

        # Act
        metadata = MetadataBuilder.build(
            title="Complex",
            custom_fields=custom_fields,
        )

        # Assert
        assert metadata.custom_fields == custom_fields
        assert metadata.custom_fields["nested"]["key"] == "value"
        assert metadata.custom_fields["list"] == [1, 2, 3]
