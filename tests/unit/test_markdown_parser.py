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
from omniparser.parsers.markdown.frontmatter import (
    extract_frontmatter,
    parse_frontmatter_to_metadata,
    _validate_custom_fields,
)
from omniparser.parsers.markdown.content import normalize_markdown_content
from omniparser.parsers.markdown.images import extract_image_references, _extract_image_format
from omniparser.parsers.markdown.utils import count_words, estimate_reading_time
from omniparser.parsers.markdown.validation import validate_markdown_file


class TestMarkdownParserInit:
    """Test MarkdownParser initialization."""

    def test_init_default_options(self):
        """Test parser initialization with default options."""
        parser = MarkdownParser()

        assert parser.options["extract_frontmatter"] is True
        assert parser.options["extract_images"] is True
        assert parser.options["normalize_headings"] is True
        assert parser.options["detect_chapters"] is True
        assert parser.options["min_chapter_level"] == 1
        assert parser.options["max_chapter_level"] == 2

    def test_init_custom_options(self):
        """Test parser initialization with custom options."""
        options = {
            "extract_frontmatter": False,
            "extract_images": False,
            "normalize_headings": False,
            "detect_chapters": False,
            "min_chapter_level": 1,
            "max_chapter_level": 3,
        }
        parser = MarkdownParser(options)

        assert parser.options["extract_frontmatter"] is False
        assert parser.options["extract_images"] is False
        assert parser.options["normalize_headings"] is False
        assert parser.options["detect_chapters"] is False
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
        text = """---
title: Test Document
author: John Doe
tags: [test, markdown]
---

# Content

This is the content.
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        assert frontmatter["author"] == "John Doe"
        assert frontmatter["tags"] == ["test", "markdown"]
        assert "# Content" in content
        assert "---" not in content

    def test_extract_frontmatter_no_frontmatter(self):
        """Test handling markdown without frontmatter."""
        text = """# Content

This is the content.
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter == {}
        assert content == text

    def test_extract_frontmatter_invalid_yaml(self):
        """Test handling invalid YAML frontmatter."""
        text = """---
title: Test
invalid yaml: [unclosed bracket
---

# Content
"""
        frontmatter, content = extract_frontmatter(text)

        # Should return None and original text on YAML error
        assert frontmatter == {}
        assert content == text

    def test_extract_frontmatter_not_dict(self):
        """Test handling frontmatter that's not a dictionary."""
        text = """---
- item1
- item2
---

# Content
"""
        frontmatter, content = extract_frontmatter(text)

        # Should return None if frontmatter is not a dict
        assert frontmatter == {}

    def test_extract_frontmatter_empty(self):
        """Test handling empty frontmatter."""
        text = """---
---

# Content
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter == {} or frontmatter == {}


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

        metadata = parse_frontmatter_to_metadata(frontmatter, file_path)

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

        metadata = parse_frontmatter_to_metadata(frontmatter, file_path)

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

        metadata = parse_frontmatter_to_metadata(frontmatter, file_path)

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

        metadata = parse_frontmatter_to_metadata(frontmatter, file_path)

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

        metadata = parse_frontmatter_to_metadata(frontmatter, file_path)

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
        text = """Main Title
==========

Content here.
"""
        normalized = normalize_markdown_content(text)

        assert "# Main Title" in normalized
        assert "=" not in normalized

    def test_normalize_markdown_underline_h2(self):
        """Test converting underline-style H2 to ## style."""
        text = """Subtitle
--------

Content here.
"""
        normalized = normalize_markdown_content(text)

        assert "## Subtitle" in normalized
        # Should not remove all dashes, only underline ones
        assert normalized.count("-") == 0 or "--------" not in normalized

    def test_normalize_markdown_list_markers(self):
        """Test normalizing list markers from * to -."""
        text = """# List Test

* Item 1
* Item 2
  * Nested item
"""
        normalized = normalize_markdown_content(text)

        assert "- Item 1" in normalized
        assert "- Item 2" in normalized
        assert "  - Nested item" in normalized
        assert "*" not in normalized or "**" in normalized  # Allow bold

    def test_normalize_markdown_excessive_blank_lines(self):
        """Test removing excessive blank lines."""
        text = """# Title


Content here.



More content.
"""
        normalized = normalize_markdown_content(text)

        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in normalized


class TestMarkdownParserImageExtraction:
    """Test image reference extraction."""

    def test_extract_image_references_basic(self, tmp_path):
        """Test extracting basic image references."""
        text = """# Document

![Alt text](image.png)

Some content.

![Another image](photo.jpg)
"""
        file_path = tmp_path / "test.md"
        images = extract_image_references(text, file_path)

        assert len(images) == 2
        assert images[0].image_id == "img_001"
        assert images[0].alt_text == "Alt text"
        # Paths are resolved to absolute paths
        assert "image.png" in images[0].file_path
        assert images[0].format == "png"
        assert images[1].image_id == "img_002"
        assert images[1].alt_text == "Another image"
        assert "photo.jpg" in images[1].file_path
        assert images[1].format == "jpg"

    def test_extract_image_references_no_alt_text(self, tmp_path):
        """Test extracting images without alt text."""
        text = """![](image.png)"""
        file_path = tmp_path / "test.md"
        images = extract_image_references(text, file_path)

        assert len(images) == 1
        assert images[0].alt_text is None

    def test_extract_image_references_urls(self, tmp_path):
        """Test extracting image URLs."""
        text = """![Remote](https://example.com/image.png)"""
        file_path = tmp_path / "test.md"
        images = extract_image_references(text, file_path)

        assert len(images) == 1
        assert images[0].file_path == "https://example.com/image.png"
        assert images[0].format == "png"

    def test_extract_image_references_no_images(self, tmp_path):
        """Test handling text with no images."""
        text = """# Document

Just text, no images.
"""
        file_path = tmp_path / "test.md"
        images = extract_image_references(text, file_path)

        assert len(images) == 0


class TestMarkdownParserValidation:
    """Test file validation."""

    def test_validate_markdown_valid_file(self, tmp_path):
        """Test validation of valid markdown file."""
        parser = MarkdownParser()
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")

        # Should not raise
        validate_markdown_file(file_path, [])

    def test_validate_markdown_file_not_found(self):
        """Test validation fails for non-existent file."""
        parser = MarkdownParser()
        file_path = Path("/nonexistent/file.md")

        with pytest.raises(FileReadError, match="File not found"):
            validate_markdown_file(file_path, [])

    def test_validate_markdown_empty_file(self, tmp_path):
        """Test validation fails for empty file."""
        parser = MarkdownParser()
        file_path = tmp_path / "empty.md"
        file_path.write_text("")

        with pytest.raises(ValidationError, match="Empty file"):
            validate_markdown_file(file_path, [])

    def test_validate_markdown_wrong_extension(self, tmp_path):
        """Test validation fails for wrong extension."""
        parser = MarkdownParser()
        file_path = tmp_path / "test.txt"
        file_path.write_text("# Test")

        with pytest.raises(ValidationError, match="Not a Markdown file"):
            validate_markdown_file(file_path, [])


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
        assert count_words("hello world test") == 3
        assert count_words("   ") == 0
        assert count_words("") == 0

    def test_estimate_reading_time(self):
        """Test reading time estimation."""
        parser = MarkdownParser()
        # 225 words = 1 minute
        assert estimate_reading_time(225) == 1
        # 450 words = 2 minutes
        assert estimate_reading_time(450) == 2
        # Small amounts round to 1
        assert estimate_reading_time(10) == 1

    def test_large_file_warning(self, tmp_path):
        """Test warning for large files (>50MB)."""
        parser = MarkdownParser()
        file_path = tmp_path / "large.md"
        # Create a file larger than 50MB
        # Each iteration writes ~5MB, so 11 iterations = ~55MB
        large_content = "# Test\n\n" + ("word " * 1000000)  # ~5MB of text
        # Write it multiple times to exceed 50MB
        with open(file_path, "w", encoding="utf-8") as f:
            for _ in range(11):
                f.write(large_content)

        # Verify file is actually >50MB
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        assert file_size_mb > 50, f"Test file is only {file_size_mb:.1f}MB"

        doc = parser.parse(file_path)

        # Should have warning about large file
        assert any("Large file size" in w for w in doc.processing_info.warnings)

    def test_windows_line_endings(self, tmp_path):
        """Test handling files with Windows line endings (CRLF)."""
        parser = MarkdownParser()
        file_path = tmp_path / "windows.md"
        # Create markdown with Windows line endings
        content = "# Introduction\r\n\r\nContent here.\r\n\r\n## Section 1\r\n\r\nMore content.\r\n"
        file_path.write_text(content, encoding="utf-8")

        doc = parser.parse(file_path)

        # Should parse successfully
        assert isinstance(doc, Document)
        assert len(doc.chapters) >= 1
        # Content should be preserved (line endings normalized by Python)
        assert "Introduction" in doc.content

    def test_extract_image_format_data_uri(self):
        """Test image format extraction from data URIs."""
        parser = MarkdownParser()

        # PNG data URI
        assert _extract_image_format("data:image/png;base64,iVBOR...") == "png"
        # JPEG data URI
        assert (
            _extract_image_format("data:image/jpeg;base64,/9j/4AA...") == "jpeg"
        )
        # Invalid data URI
        assert _extract_image_format("data:text/plain,hello") == "unknown"

    def test_extract_image_format_query_params(self):
        """Test image format extraction from query parameters."""
        parser = MarkdownParser()

        # format parameter
        assert (
            _extract_image_format("https://example.com/image?format=png")
            == "png"
        )
        # fmt parameter
        assert _extract_image_format("https://cdn.com/abc?fmt=webp") == "webp"
        # Mixed case
        assert (
            _extract_image_format("https://example.com/img?FORMAT=JPEG")
            == "jpeg"
        )

    def test_extract_image_format_no_extension(self):
        """Test image format extraction for URLs without extension."""
        parser = MarkdownParser()

        # No extension
        assert _extract_image_format("https://example.com/image") == "unknown"
        # Just path
        assert _extract_image_format("images/photo") == "unknown"

    def test_extract_image_format_common_extensions(self):
        """Test image format extraction for common extensions."""
        parser = MarkdownParser()

        assert _extract_image_format("image.png") == "png"
        assert _extract_image_format("photo.jpg") == "jpg"
        assert _extract_image_format("photo.JPEG") == "jpeg"
        assert _extract_image_format("icon.svg") == "svg"
        assert _extract_image_format("image.webp") == "webp"
        assert _extract_image_format("graphic.gif") == "gif"

    def test_count_words_with_markdown_syntax(self):
        """Test word counting excludes markdown syntax."""
        parser = MarkdownParser()

        # Should count only actual words, not markdown syntax
        text = "# Heading\n\nThis is **bold** and *italic* text."
        # Should count: Heading, This, is, bold, and, italic, text = 7 words
        # (# is removed but "Heading" is kept)
        assert count_words(text) == 7

        # Test with code blocks
        text_with_code = "Hello\n\n```python\ncode here\n```\n\nworld"
        # Should count: Hello, world = 2 words
        assert count_words(text_with_code) == 2

        # Test with URLs
        text_with_url = "Check out https://example.com for more info"
        # Should count: Check, out, for, more, info = 5 words
        assert count_words(text_with_url) == 5

        # Test with images
        text_with_image = "Here is an image: ![alt text](image.png) in text"
        # Should count: Here, is, an, image, alt, text, in, text = 8 words
        assert count_words(text_with_image) == 8

    def test_normalize_h2_horizontal_rule(self):
        """Test H2 normalization doesn't match horizontal rules."""
        parser = MarkdownParser()

        # Horizontal rule should not be converted to heading
        text = "Some text\n\n---\n\nMore text"
        normalized = normalize_markdown_content(text)

        # Should not contain "## Some text"
        # The horizontal rule should remain because the underline length
        # doesn't match the text length
        assert "## Some text" not in normalized or "---" in normalized

    def test_custom_field_typo_warnings(self, tmp_path):
        """Test warnings for custom field typos."""
        frontmatter = {
            "titel": "Test Document",  # Typo: should be "title"
            "autor": "John Doe",  # Typo: should be "author"
            "custom_field": "valid",  # Not a typo
        }
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test")
        warnings = []

        metadata = parse_frontmatter_to_metadata(frontmatter, file_path, warnings)

        # Should have warnings for typos
        assert any("titel" in w.lower() for w in warnings)
        assert any("autor" in w.lower() for w in warnings)
        # Custom fields should include both typos and valid fields
        assert metadata.custom_fields is not None
        assert "titel" in metadata.custom_fields
        assert "autor" in metadata.custom_fields
        assert "custom_field" in metadata.custom_fields

    def test_frontmatter_ending_without_newline(self):
        """Test frontmatter extraction when document ends with frontmatter."""
        # Document ending with frontmatter (no trailing newline after ---)
        text = """---
title: Test Document
author: John Doe
---"""
        frontmatter, content = extract_frontmatter(text)

        # Should successfully extract frontmatter
        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        assert frontmatter["author"] == "John Doe"
        # Content should be empty (or just the ending marker)
        assert len(content.strip()) == 0

    def test_frontmatter_with_trailing_newline(self):
        """Test frontmatter extraction with trailing newline (standard case)."""
        text = """---
title: Test Document
---

# Content here
"""
        frontmatter, content = extract_frontmatter(text)

        # Should successfully extract frontmatter
        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        # Content should have the markdown
        assert "# Content here" in content

    def test_validate_custom_fields_no_typos(self):
        """Test custom field validation with no typos."""
        custom_fields = {"custom_field1": "value1", "custom_field2": "value2"}
        warnings = []

        # Should not add any warnings
        initial_warnings = len(warnings)
        _validate_custom_fields(custom_fields, warnings)
        assert len(warnings) == initial_warnings

    def test_validate_custom_fields_with_typos(self):
        """Test custom field validation detects typos."""
        custom_fields = {
            "titel": "Test",  # Typo of "title"
            "auther": "John",  # Typo of "author"
            "descripton": "Test desc",  # Typo of "description"
        }
        warnings = []

        initial_warnings = len(warnings)
        _validate_custom_fields(custom_fields, warnings)

        # Should have added 3 warnings
        assert len(warnings) == initial_warnings + 3
        # Check warnings mention the correct field names
        warnings_text = " ".join(warnings)
        assert "titel" in warnings_text.lower()
        assert "auther" in warnings_text.lower()
        assert "descripton" in warnings_text.lower()
