"""
Integration tests for MarkdownParser.

Tests parser with real markdown files from fixtures directory.
Validates end-to-end parsing functionality including:
- Various markdown structures
- Frontmatter handling
- Image extraction
- Chapter detection
- Normalization
"""

from pathlib import Path

import pytest

from omniparser import parse_document
from omniparser.models import Document
from omniparser.parsers.markdown_parser import MarkdownParser

# Get fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "markdown"


class TestMarkdownParserIntegrationBasic:
    """Basic integration tests with fixture files."""

    def test_parse_simple_markdown(self):
        """Test parsing simple.md fixture."""
        file_path = FIXTURES_DIR / "simple.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        assert isinstance(doc, Document)
        assert doc.metadata.original_format == "markdown"
        # Should have chapters: Introduction, Background, Conclusion
        assert len(doc.chapters) >= 2
        assert doc.chapters[0].title == "Introduction"
        assert doc.word_count > 0
        assert doc.estimated_reading_time > 0

    def test_parse_with_frontmatter(self):
        """Test parsing with_frontmatter.md fixture."""
        file_path = FIXTURES_DIR / "with_frontmatter.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Verify frontmatter was extracted
        assert doc.metadata.title == "Sample Document with Frontmatter"
        assert doc.metadata.author == "John Doe"
        assert doc.metadata.tags is not None
        assert "python" in doc.metadata.tags
        assert "markdown" in doc.metadata.tags
        assert doc.metadata.description is not None
        assert doc.metadata.language == "en"

        # Verify chapters (both H1 and H2 are detected by default)
        assert len(doc.chapters) == 4
        assert doc.chapters[0].title == "Chapter 1"
        assert doc.chapters[1].title == "Section 1.1"
        assert doc.chapters[2].title == "Chapter 2"
        assert doc.chapters[3].title == "Section 2.1"

    def test_parse_no_frontmatter(self):
        """Test parsing no_frontmatter.md fixture."""
        file_path = FIXTURES_DIR / "no_frontmatter.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Should use filename as title
        assert doc.metadata.title == "no_frontmatter"
        assert doc.metadata.author is None

        # Should still detect chapters
        assert len(doc.chapters) >= 1
        assert doc.chapters[0].title == "Document Without Frontmatter"

    def test_parse_with_images(self):
        """Test parsing with_images.md fixture."""
        file_path = FIXTURES_DIR / "with_images.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Verify frontmatter
        assert doc.metadata.title == "Document with Images"
        assert doc.metadata.author == "Jane Smith"

        # Verify images were extracted
        assert len(doc.images) >= 3
        # Check first image
        assert doc.images[0].alt_text == "Sample Image"
        assert "sample.png" in doc.images[0].file_path
        # Check formats
        image_formats = [img.format for img in doc.images]
        assert "png" in image_formats
        assert "jpg" in image_formats


class TestMarkdownParserIntegrationAdvanced:
    """Advanced integration tests."""

    def test_parse_complex_structure(self):
        """Test parsing complex_structure.md fixture."""
        file_path = FIXTURES_DIR / "complex_structure.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Verify frontmatter with multiple authors
        assert doc.metadata.title == "Complex Document Structure"
        assert doc.metadata.author == "Bob Johnson"
        assert doc.metadata.authors == ["Bob Johnson", "Alice Williams"]
        assert doc.metadata.publisher == "Tech Publishing"

        # Verify custom fields
        assert doc.metadata.custom_fields is not None
        assert doc.metadata.custom_fields.get("custom_field") == "custom_value"

        # Should detect main chapters (H1 and H2)
        assert len(doc.chapters) >= 3

    def test_parse_underline_headings(self):
        """Test parsing underline_headings.md fixture."""
        file_path = FIXTURES_DIR / "underline_headings.md"
        parser = MarkdownParser({"normalize_headings": True})

        doc = parser.parse(file_path)

        # After normalization, should detect chapters
        assert len(doc.chapters) >= 1
        # First chapter should be "Main Title"
        assert "Main Title" in doc.chapters[0].title

    def test_parse_obsidian_style(self):
        """Test parsing obsidian_style.md fixture."""
        file_path = FIXTURES_DIR / "obsidian_style.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Verify frontmatter
        assert doc.metadata.title == "Obsidian Style Document"
        assert "obsidian" in doc.metadata.tags

        # Should have chapters
        assert len(doc.chapters) >= 1

        # Should find image
        assert len(doc.images) >= 1


class TestMarkdownParserIntegrationOptions:
    """Test parser with different options."""

    def test_parse_without_frontmatter_extraction(self):
        """Test parsing with frontmatter extraction disabled."""
        file_path = FIXTURES_DIR / "with_frontmatter.md"
        parser = MarkdownParser({"extract_frontmatter": False})

        doc = parser.parse(file_path)

        # Should use filename as title
        assert doc.metadata.title == "with_frontmatter"
        # Frontmatter should not be extracted
        assert doc.metadata.author is None

    def test_parse_without_normalization(self):
        """Test parsing without heading normalization."""
        file_path = FIXTURES_DIR / "underline_headings.md"
        parser = MarkdownParser({"normalize_headings": False})

        doc = parser.parse(file_path)

        # Without normalization, underline headings might not be detected
        # Content should still be present
        assert doc.content is not None
        assert len(doc.content) > 0

    def test_parse_without_chapter_detection(self):
        """Test parsing with chapter detection disabled."""
        file_path = FIXTURES_DIR / "simple.md"
        parser = MarkdownParser({"detect_chapters": False})

        doc = parser.parse(file_path)

        # No chapters should be detected
        assert len(doc.chapters) == 0
        # But content should still be present
        assert doc.content is not None
        assert doc.word_count > 0

    def test_parse_with_custom_chapter_levels(self):
        """Test parsing with custom chapter levels."""
        file_path = FIXTURES_DIR / "complex_structure.md"
        # Only H1 headings are chapters
        parser = MarkdownParser({"min_chapter_level": 1, "max_chapter_level": 1})

        doc = parser.parse(file_path)

        # Should only have H1 chapters
        assert len(doc.chapters) >= 1
        # All chapters should be level 1
        for chapter in doc.chapters:
            assert chapter.level == 1

    def test_parse_with_text_cleaning(self):
        """Test parsing with text cleaning enabled."""
        file_path = FIXTURES_DIR / "simple.md"
        parser = MarkdownParser({"clean_text": True})

        doc = parser.parse(file_path)

        # Should parse successfully
        assert isinstance(doc, Document)
        assert doc.word_count > 0


class TestMarkdownParserIntegrationPublicAPI:
    """Test integration with public parse_document API."""

    def test_parse_document_api(self):
        """Test using parse_document() function."""
        file_path = str(FIXTURES_DIR / "with_frontmatter.md")

        doc = parse_document(file_path)

        assert isinstance(doc, Document)
        assert doc.metadata.title == "Sample Document with Frontmatter"
        assert len(doc.chapters) >= 1

    def test_parse_document_with_options(self):
        """Test parse_document() with custom options."""
        file_path = str(FIXTURES_DIR / "complex_structure.md")
        options = {
            "extract_frontmatter": True,
            "normalize_headings": True,
            "min_chapter_level": 1,
            "max_chapter_level": 2,
        }

        doc = parse_document(file_path, options)

        assert isinstance(doc, Document)
        assert doc.metadata.title == "Complex Document Structure"

    def test_parse_document_path_object(self):
        """Test parse_document() with Path object."""
        file_path = FIXTURES_DIR / "simple.md"

        doc = parse_document(file_path)

        assert isinstance(doc, Document)
        assert doc.metadata.original_format == "markdown"


class TestMarkdownParserIntegrationErrorHandling:
    """Test error handling in integration scenarios."""

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file."""
        from omniparser.exceptions import FileReadError

        file_path = FIXTURES_DIR / "nonexistent.md"
        parser = MarkdownParser()

        with pytest.raises(FileReadError):
            parser.parse(file_path)

    def test_parse_empty_file(self):
        """Test parsing empty file."""
        from omniparser.exceptions import ValidationError

        file_path = FIXTURES_DIR / "empty.md"
        parser = MarkdownParser()

        with pytest.raises(ValidationError, match="Empty file"):
            parser.parse(file_path)


class TestMarkdownParserIntegrationChapterDetection:
    """Test chapter detection integration."""

    def test_chapter_positions(self):
        """Test chapter start/end positions are correct."""
        file_path = FIXTURES_DIR / "simple.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Verify chapter positions
        for chapter in doc.chapters:
            assert chapter.start_position >= 0
            assert chapter.end_position > chapter.start_position
            assert chapter.word_count > 0

            # Verify content matches position
            extracted_content = doc.content[
                chapter.start_position : chapter.end_position
            ]
            assert len(extracted_content) > 0

    def test_chapter_word_counts(self):
        """Test chapter word counts are calculated correctly."""
        file_path = FIXTURES_DIR / "with_frontmatter.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Each chapter should have word count
        for chapter in doc.chapters:
            assert chapter.word_count > 0
            # Word count should match split
            actual_words = len(chapter.content.split())
            # Allow small variance due to whitespace handling
            assert abs(chapter.word_count - actual_words) <= 2

    def test_chapter_levels(self):
        """Test chapter levels are detected correctly."""
        file_path = FIXTURES_DIR / "complex_structure.md"
        parser = MarkdownParser({"min_chapter_level": 1, "max_chapter_level": 2})

        doc = parser.parse(file_path)

        # Should have chapters with different levels
        levels = [chapter.level for chapter in doc.chapters]
        assert 1 in levels
        assert 2 in levels


class TestMarkdownParserIntegrationPerformance:
    """Test parser performance characteristics."""

    def test_parsing_time_reasonable(self):
        """Test parsing completes in reasonable time."""
        file_path = FIXTURES_DIR / "complex_structure.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Should complete in under 1 second for fixture files
        assert doc.processing_info.processing_time < 1.0

    def test_memory_efficiency(self):
        """Test parser doesn't create excessive warnings."""
        file_path = FIXTURES_DIR / "simple.md"
        parser = MarkdownParser()

        doc = parser.parse(file_path)

        # Should have minimal warnings for well-formed files
        assert len(doc.processing_info.warnings) < 5


class TestMarkdownParserIntegrationRoundtrip:
    """Test data integrity and roundtrip scenarios."""

    def test_content_preservation(self):
        """Test content is preserved correctly."""
        file_path = FIXTURES_DIR / "simple.md"
        parser = MarkdownParser({"normalize_headings": False, "clean_text": False})

        doc = parser.parse(file_path)

        # Read original file
        with open(file_path, "r", encoding="utf-8") as f:
            original = f.read()

        # Content should be very similar to original
        # (may differ in whitespace)
        assert len(doc.content) > 0
        # Check some content is preserved
        assert "Introduction" in original
        assert "Introduction" in doc.content

    def test_metadata_consistency(self):
        """Test metadata is consistent across parsing."""
        file_path = FIXTURES_DIR / "with_frontmatter.md"
        parser1 = MarkdownParser()
        parser2 = MarkdownParser()

        doc1 = parser1.parse(file_path)
        doc2 = parser2.parse(file_path)

        # Metadata should be identical
        assert doc1.metadata.title == doc2.metadata.title
        assert doc1.metadata.author == doc2.metadata.author
        assert doc1.metadata.tags == doc2.metadata.tags
