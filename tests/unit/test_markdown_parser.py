"""
Unit tests for MarkdownParser.

Tests all core functionality of the Markdown parser including:
- Format detection
- Frontmatter extraction
- Metadata parsing
- Markdown normalization
- Image reference extraction
- Chapter detection integration
- Error handling
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from omniparser.exceptions import FileReadError, ParsingError, ValidationError
from omniparser.models import Chapter, Document, ImageReference, Metadata
from omniparser.parsers.markdown_parser import MarkdownParser


class TestMarkdownParserInit:
    """Test MarkdownParser initialization."""

    def test_init_default_options(self):
        """Test parser initialization with default options."""
        parser = MarkdownParser()

        assert parser.options["extract_frontmatter"] is True
        assert parser.options["normalize_headings"] is True
        assert parser.options["detect_chapters"] is True
        assert parser.options["clean_text"] is False
        assert parser.options["min_chapter_level"] == 1
        assert parser.options["max_chapter_level"] == 2

    def test_init_custom_options(self):
        """Test parser initialization with custom options."""
        options = {
            "extract_frontmatter": False,
            "normalize_headings": False,
            "detect_chapters": False,
            "clean_text": True,
            "min_chapter_level": 1,
            "max_chapter_level": 3,
        }
        parser = MarkdownParser(options)

        assert parser.options["extract_frontmatter"] is False
        assert parser.options["normalize_headings"] is False
        assert parser.options["detect_chapters"] is False
        assert parser.options["clean_text"] is True
        assert parser.options["min_chapter_level"] == 1
        assert parser.options["max_chapter_level"] == 3


class TestMarkdownParserFormatDetection:
    """Test format detection."""

    def test_supports_format_md_extension(self):
        """Test .md extension is supported."""
        parser = MarkdownParser()
        assert parser.supports_format(Path("test.md")) is True

    def test_supports_format_markdown_extension(self):
        """Test .markdown extension is supported."""
        parser = MarkdownParser()
        assert parser.supports_format(Path("test.markdown")) is True

    def test_supports_format_string_path(self):
        """Test format detection with string path."""
        parser = MarkdownParser()
        assert parser.supports_format("test.md") is True
        assert parser.supports_format("test.markdown") is True

    def test_supports_format_case_insensitive(self):
        """Test format detection is case insensitive."""
        parser = MarkdownParser()
        assert parser.supports_format(Path("test.MD")) is True
        assert parser.supports_format(Path("test.MARKDOWN")) is True

    def test_supports_format_unsupported_extensions(self):
        """Test unsupported extensions return False."""
        parser = MarkdownParser()
        assert parser.supports_format(Path("test.txt")) is False
        assert parser.supports_format(Path("test.pdf")) is False
        assert parser.supports_format(Path("test.epub")) is False


class TestMarkdownParserFrontmatterExtraction:
    """Test YAML frontmatter extraction."""

    def test_extract_frontmatter_valid_yaml(self):
        """Test extracting valid YAML frontmatter."""
        parser = MarkdownParser()
        text = """---
title: Test Document
author: John Doe
tags: [test, markdown]
---

# Content

This is the content.
"""
        frontmatter, content = parser._extract_frontmatter(text)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        assert frontmatter["author"] == "John Doe"
        assert frontmatter["tags"] == ["test", "markdown"]
        assert "# Content" in content
        assert "---" not in content

    def test_extract_frontmatter_no_frontmatter(self):
        """Test handling markdown without frontmatter."""
        parser = MarkdownParser()
        text = """# Content

This is the content.
"""
        frontmatter, content = parser._extract_frontmatter(text)

        assert frontmatter is None
        assert content == text

    def test_extract_frontmatter_invalid_yaml(self):
        """Test handling invalid YAML frontmatter."""
        parser = MarkdownParser()
        text = """---
title: Test
invalid yaml: [unclosed bracket
---

# Content
"""
        frontmatter, content = parser._extract_frontmatter(text)

        # Should return None and original text on YAML error
        assert frontmatter is None
        assert content == text

    def test_extract_frontmatter_not_dict(self):
        """Test handling frontmatter that's not a dictionary."""
        parser = MarkdownParser()
        text = """---
- item1
- item2
---

# Content
"""
        frontmatter, content = parser._extract_frontmatter(text)

        # Should return None if frontmatter is not a dict
        assert frontmatter is None

    def test_extract_frontmatter_empty(self):
        """Test handling empty frontmatter."""
        parser = MarkdownParser()
        text = """---
---

# Content
"""
        frontmatter, content = parser._extract_frontmatter(text)

        assert frontmatter is None or frontmatter == {}


class TestMarkdownParserMetadataConversion:
    """Test frontmatter to Metadata conversion."""

    def test_frontmatter_to_metadata_basic_fields(self, tmp_path):
        """Test conversion of basic frontmatter fields."""
        parser = MarkdownParser()
        frontmatter = {
            "title": "Test Document",
            "author": "John Doe",
            "description": "A test document",
            "language": "en",
        }
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")

        metadata = parser._frontmatter_to_metadata(frontmatter, file_path)

        assert metadata.title == "Test Document"
        assert metadata.author == "John Doe"
        assert metadata.description == "A test document"
        assert metadata.language == "en"
        assert metadata.original_format == "markdown"

    def test_frontmatter_to_metadata_authors_list(self, tmp_path):
        """Test handling authors as list."""
        parser = MarkdownParser()
        frontmatter = {
            "authors": ["John Doe", "Jane Smith"],
        }
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")

        metadata = parser._frontmatter_to_metadata(frontmatter, file_path)

        assert metadata.authors == ["John Doe", "Jane Smith"]
        assert metadata.author == "John Doe"

    def test_frontmatter_to_metadata_date_parsing(self, tmp_path):
        """Test date parsing from frontmatter."""
        parser = MarkdownParser()
        frontmatter = {
            "date": "2025-01-15",
        }
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")

        metadata = parser._frontmatter_to_metadata(frontmatter, file_path)

        assert metadata.publication_date is not None
        assert metadata.publication_date.year == 2025
        assert metadata.publication_date.month == 1
        assert metadata.publication_date.day == 15

    def test_frontmatter_to_metadata_tags(self, tmp_path):
        """Test tags extraction."""
        parser = MarkdownParser()
        frontmatter = {
            "tags": ["python", "markdown", "testing"],
        }
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")

        metadata = parser._frontmatter_to_metadata(frontmatter, file_path)

        assert metadata.tags == ["python", "markdown", "testing"]

    def test_frontmatter_to_metadata_custom_fields(self, tmp_path):
        """Test custom fields are preserved."""
        parser = MarkdownParser()
        frontmatter = {
            "title": "Test",
            "custom_field": "custom_value",
            "another_field": 123,
        }
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")

        metadata = parser._frontmatter_to_metadata(frontmatter, file_path)

        assert metadata.custom_fields is not None
        assert metadata.custom_fields["custom_field"] == "custom_value"
        assert metadata.custom_fields["another_field"] == 123

    def test_create_default_metadata(self, tmp_path):
        """Test creating default metadata without frontmatter."""
        parser = MarkdownParser()
        file_path = tmp_path / "test_document.md"
        file_path.write_text("# Test")

        metadata = parser._create_default_metadata(file_path)

        assert metadata.title == "test_document"
        assert metadata.original_format == "markdown"
        assert metadata.author is None


class TestMarkdownParserNormalization:
    """Test markdown normalization."""

    def test_normalize_markdown_underline_h1(self):
        """Test converting underline-style H1 to # style."""
        parser = MarkdownParser()
        text = """Main Title
==========

Content here.
"""
        normalized = parser._normalize_markdown(text)

        assert "# Main Title" in normalized
        assert "=" not in normalized

    def test_normalize_markdown_underline_h2(self):
        """Test converting underline-style H2 to ## style."""
        parser = MarkdownParser()
        text = """Subtitle
--------

Content here.
"""
        normalized = parser._normalize_markdown(text)

        assert "## Subtitle" in normalized
        # Should not remove all dashes, only underline ones
        assert normalized.count("-") == 0 or "--------" not in normalized

    def test_normalize_markdown_list_markers(self):
        """Test normalizing list markers from * to -."""
        parser = MarkdownParser()
        text = """# List Test

* Item 1
* Item 2
  * Nested item
"""
        normalized = parser._normalize_markdown(text)

        assert "- Item 1" in normalized
        assert "- Item 2" in normalized
        assert "  - Nested item" in normalized
        assert "*" not in normalized or "**" in normalized  # Allow bold

    def test_normalize_markdown_excessive_blank_lines(self):
        """Test removing excessive blank lines."""
        parser = MarkdownParser()
        text = """# Title


Content here.



More content.
"""
        normalized = parser._normalize_markdown(text)

        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in normalized


class TestMarkdownParserImageExtraction:
    """Test image reference extraction."""

    def test_extract_image_references_basic(self):
        """Test extracting basic image references."""
        parser = MarkdownParser()
        text = """# Document

![Alt text](image.png)

Some content.

![Another image](photo.jpg)
"""
        images = parser._extract_image_references(text)

        assert len(images) == 2
        assert images[0].image_id == "img_001"
        assert images[0].alt_text == "Alt text"
        assert images[0].file_path == "image.png"
        assert images[0].format == "png"
        assert images[1].image_id == "img_002"
        assert images[1].alt_text == "Another image"
        assert images[1].file_path == "photo.jpg"
        assert images[1].format == "jpg"

    def test_extract_image_references_no_alt_text(self):
        """Test extracting images without alt text."""
        parser = MarkdownParser()
        text = """![](image.png)"""
        images = parser._extract_image_references(text)

        assert len(images) == 1
        assert images[0].alt_text is None

    def test_extract_image_references_urls(self):
        """Test extracting image URLs."""
        parser = MarkdownParser()
        text = """![Remote](https://example.com/image.png)"""
        images = parser._extract_image_references(text)

        assert len(images) == 1
        assert images[0].file_path == "https://example.com/image.png"
        assert images[0].format == "png"

    def test_extract_image_references_no_images(self):
        """Test handling text with no images."""
        parser = MarkdownParser()
        text = """# Document

Just text, no images.
"""
        images = parser._extract_image_references(text)

        assert len(images) == 0


class TestMarkdownParserValidation:
    """Test file validation."""

    def test_validate_markdown_valid_file(self, tmp_path):
        """Test validation of valid markdown file."""
        parser = MarkdownParser()
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")

        # Should not raise
        parser._validate_markdown(file_path)

    def test_validate_markdown_file_not_found(self):
        """Test validation fails for non-existent file."""
        parser = MarkdownParser()
        file_path = Path("/nonexistent/file.md")

        with pytest.raises(FileReadError, match="File not found"):
            parser._validate_markdown(file_path)

    def test_validate_markdown_empty_file(self, tmp_path):
        """Test validation fails for empty file."""
        parser = MarkdownParser()
        file_path = tmp_path / "empty.md"
        file_path.write_text("")

        with pytest.raises(ValidationError, match="Empty file"):
            parser._validate_markdown(file_path)

    def test_validate_markdown_wrong_extension(self, tmp_path):
        """Test validation fails for wrong extension."""
        parser = MarkdownParser()
        file_path = tmp_path / "test.txt"
        file_path.write_text("# Test")

        with pytest.raises(ValidationError, match="Not a Markdown file"):
            parser._validate_markdown(file_path)


class TestMarkdownParserParsing:
    """Test full parsing functionality."""

    def test_parse_simple_markdown(self, tmp_path):
        """Test parsing simple markdown file."""
        parser = MarkdownParser()
        file_path = tmp_path / "simple.md"
        file_path.write_text(
            """# Introduction

This is a simple markdown document.

## Section 1

Content here.
"""
        )

        doc = parser.parse(file_path)

        assert isinstance(doc, Document)
        assert doc.metadata.title == "simple"
        assert doc.metadata.original_format == "markdown"
        assert len(doc.chapters) == 2
        assert doc.chapters[0].title == "Introduction"
        assert doc.chapters[1].title == "Section 1"
        assert doc.word_count > 0
        assert doc.estimated_reading_time > 0

    def test_parse_with_frontmatter(self, tmp_path):
        """Test parsing markdown with frontmatter."""
        parser = MarkdownParser()
        file_path = tmp_path / "frontmatter.md"
        file_path.write_text(
            """---
title: Test Document
author: John Doe
tags: [test, markdown]
---

# Chapter 1

Content here.
"""
        )

        doc = parser.parse(file_path)

        assert doc.metadata.title == "Test Document"
        assert doc.metadata.author == "John Doe"
        assert doc.metadata.tags == ["test", "markdown"]

    def test_parse_with_images(self, tmp_path):
        """Test parsing markdown with images."""
        parser = MarkdownParser()
        file_path = tmp_path / "images.md"
        file_path.write_text(
            """# Document

![Image 1](img1.png)

Some content.

![Image 2](img2.jpg)
"""
        )

        doc = parser.parse(file_path)

        assert len(doc.images) == 2
        assert doc.images[0].file_path == "img1.png"
        assert doc.images[1].file_path == "img2.jpg"

    def test_parse_without_chapter_detection(self, tmp_path):
        """Test parsing with chapter detection disabled."""
        parser = MarkdownParser({"detect_chapters": False})
        file_path = tmp_path / "no_chapters.md"
        file_path.write_text(
            """# Heading 1

Content.

## Heading 2

More content.
"""
        )

        doc = parser.parse(file_path)

        assert len(doc.chapters) == 0

    def test_parse_processing_info(self, tmp_path):
        """Test processing info is populated correctly."""
        parser = MarkdownParser()
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test\n\nContent here.")

        doc = parser.parse(file_path)

        assert doc.processing_info.parser_used == "MarkdownParser"
        assert doc.processing_info.parser_version == "1.0.0"
        assert doc.processing_info.processing_time > 0
        assert isinstance(doc.processing_info.timestamp, datetime)
        assert isinstance(doc.processing_info.warnings, list)


class TestMarkdownParserEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_invalid_utf8(self, tmp_path):
        """Test handling file with invalid UTF-8."""
        parser = MarkdownParser()
        file_path = tmp_path / "invalid.md"
        # Write invalid UTF-8 bytes
        file_path.write_bytes(b"# Test\n\xff\xfe\n\nContent")

        # Should fallback to latin-1 encoding
        doc = parser.parse(file_path)
        assert isinstance(doc, Document)
        assert len(doc.processing_info.warnings) > 0

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error."""
        parser = MarkdownParser()
        file_path = Path("/nonexistent/file.md")

        with pytest.raises(FileReadError):
            parser.parse(file_path)

    def test_count_words(self):
        """Test word counting."""
        parser = MarkdownParser()
        assert parser._count_words("hello world test") == 3
        assert parser._count_words("   ") == 0
        assert parser._count_words("") == 0

    def test_estimate_reading_time(self):
        """Test reading time estimation."""
        parser = MarkdownParser()
        # 225 words = 1 minute
        assert parser._estimate_reading_time(225) == 1
        # 450 words = 2 minutes
        assert parser._estimate_reading_time(450) == 2
        # Small amounts round to 1
        assert parser._estimate_reading_time(10) == 1
