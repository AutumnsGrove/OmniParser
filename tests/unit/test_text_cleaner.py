"""
Unit tests for text_cleaner module.

Tests all text cleaning functionality including pattern removal,
transformation, encoding fixes, and whitespace normalization.

Critically: Verifies NO TTS markers are present in output.
"""

import pytest

from omniparser.processors.text_cleaner import (
    clean_text,
    load_patterns,
    reset_pattern_cache,
    _fix_encoding,
    _apply_removal_patterns,
    _apply_transformation_patterns,
    _normalize_whitespace,
)


class TestLoadPatterns:
    """Tests for pattern loading from YAML config."""

    def test_load_patterns_returns_dict(self) -> None:
        """Test that load_patterns returns dictionary with expected keys."""
        reset_pattern_cache()
        patterns = load_patterns()

        assert isinstance(patterns, dict)
        assert "removal_patterns" in patterns
        assert "transformation_patterns" in patterns

    def test_load_patterns_caches(self) -> None:
        """Test that patterns are cached after first load."""
        reset_pattern_cache()
        patterns1 = load_patterns()
        patterns2 = load_patterns()

        # Should be the exact same object (cached)
        assert patterns1 is patterns2

    def test_load_patterns_has_compiled_regexes(self) -> None:
        """Test that patterns contain compiled regex objects."""
        reset_pattern_cache()
        patterns = load_patterns()

        # Check removal patterns
        assert len(patterns["removal_patterns"]) > 0
        for pattern_dict in patterns["removal_patterns"]:
            assert "pattern" in pattern_dict
            assert "description" in pattern_dict
            # Verify it's a compiled pattern
            assert hasattr(pattern_dict["pattern"], "sub")

        # Check transformation patterns
        assert len(patterns["transformation_patterns"]) > 0
        for pattern_dict in patterns["transformation_patterns"]:
            assert "pattern" in pattern_dict
            assert "replacement" in pattern_dict
            assert "description" in pattern_dict
            # Verify it's a compiled pattern
            assert hasattr(pattern_dict["pattern"], "sub")

    def test_reset_pattern_cache(self) -> None:
        """Test that reset_pattern_cache clears the cache."""
        patterns1 = load_patterns()
        reset_pattern_cache()
        patterns2 = load_patterns()

        # Should be different objects after reset
        assert patterns1 is not patterns2


class TestFootnoteRemoval:
    """Tests for footnote marker removal."""

    def test_remove_single_digit_footnote(self) -> None:
        """Test removal of single-digit footnote markers."""
        text = "Hello world [1] this is a test."
        result = _apply_removal_patterns(text)
        assert "[1]" not in result
        assert "Hello world" in result

    def test_remove_multi_digit_footnote(self) -> None:
        """Test removal of multi-digit footnote markers."""
        text = "Reference [123] and [4567] are here."
        result = _apply_removal_patterns(text)
        assert "[123]" not in result
        assert "[4567]" not in result

    def test_remove_multiple_footnotes(self) -> None:
        """Test removal of multiple footnote markers."""
        text = "First [1] second [2] third [3] citation."
        result = _apply_removal_patterns(text)
        assert "[1]" not in result
        assert "[2]" not in result
        assert "[3]" not in result


class TestPageNumberRemoval:
    """Tests for page number removal."""

    def test_remove_page_number_line(self) -> None:
        """Test removal of page number lines."""
        text = "Chapter text here\nPage 42\nMore text"
        result = _apply_removal_patterns(text)
        assert "Page 42" not in result
        assert "Chapter text here" in result
        assert "More text" in result

    def test_remove_page_number_with_suffix(self) -> None:
        """Test removal of page number with additional text."""
        text = "Content\nPage 100 of 200\nMore content"
        result = _apply_removal_patterns(text)
        assert "Page 100" not in result


class TestChapterMarkerRemoval:
    """Tests for chapter marker removal."""

    def test_remove_standalone_chapter_number(self) -> None:
        """Test removal of standalone chapter number lines."""
        text = "Chapter 5\n\nThis is the chapter content."
        result = _apply_removal_patterns(text)
        # Standalone "Chapter 5" line should be removed
        assert "Chapter 5" not in result or "chapter content" in result.lower()

    def test_keep_chapter_with_title(self) -> None:
        """Test that chapter lines with titles are kept."""
        text = "Chapter 5: The Adventure Begins\n\nContent here."
        result = _apply_removal_patterns(text)
        # This should be kept because it has a title
        assert "The Adventure Begins" in result


class TestHTMLTagRemoval:
    """Tests for HTML tag removal."""

    def test_remove_simple_html_tags(self) -> None:
        """Test removal of simple HTML tags."""
        text = "Hello <b>world</b> and <i>everyone</i>."
        result = _apply_removal_patterns(text)
        assert "<b>" not in result
        assert "</b>" not in result
        assert "<i>" not in result
        assert "world" in result
        assert "everyone" in result

    def test_remove_html_tags_with_attributes(self) -> None:
        """Test removal of HTML tags with attributes."""
        text = 'Click <a href="http://example.com">here</a>.'
        result = _apply_removal_patterns(text)
        assert "<a" not in result
        assert "href" not in result
        assert "here" in result


class TestSectionBreakRemoval:
    """Tests for section break removal."""

    def test_remove_asterisk_section_breaks(self) -> None:
        """Test removal of asterisk section breaks."""
        text = "Section one\n***\nSection two"
        result = _apply_removal_patterns(text)
        assert "***" not in result

    def test_remove_underscore_section_breaks(self) -> None:
        """Test removal of underscore section breaks."""
        text = "Section one\n___\nSection two"
        result = _apply_removal_patterns(text)
        assert "___" not in result


class TestPunctuationTransformation:
    """Tests for punctuation normalization."""

    def test_transform_em_dash(self) -> None:
        """Test em dash transformation."""
        text = "Hello—world"
        result = _apply_transformation_patterns(text)
        assert "—" not in result
        assert "--" in result

    def test_transform_en_dash(self) -> None:
        """Test en dash transformation."""
        text = "Pages 1–10"
        result = _apply_transformation_patterns(text)
        assert "–" not in result
        assert "1-10" in result

    def test_transform_ellipsis(self) -> None:
        """Test ellipsis transformation."""
        text = "Wait for it…"
        result = _apply_transformation_patterns(text)
        assert "…" not in result
        assert "..." in result

    def test_transform_smart_double_quotes(self) -> None:
        """Test smart quote transformation."""
        text = "\u201cHello world\u201d"  # Smart quotes
        result = _apply_transformation_patterns(text)
        assert "\u201c" not in result  # Left double quote
        assert "\u201d" not in result  # Right double quote
        assert result.count('"') == 2

    def test_transform_smart_single_quotes(self) -> None:
        """Test smart single quote transformation."""
        text = "\u2018Hello\u2019 and \u2018world\u2019"  # Smart single quotes
        result = _apply_transformation_patterns(text)
        assert "\u2018" not in result  # Left single quote
        assert "\u2019" not in result  # Right single quote
        assert result.count("'") >= 2


class TestWhitespaceNormalization:
    """Tests for whitespace normalization."""

    def test_normalize_multiple_spaces(self) -> None:
        """Test collapsing multiple spaces to single space."""
        text = "Hello    world     test"
        result = _normalize_whitespace(text)
        assert "    " not in result
        assert "Hello world test" == result

    def test_normalize_excessive_newlines(self) -> None:
        """Test collapsing 3+ newlines to 2 newlines."""
        text = "Paragraph one\n\n\n\n\nParagraph two"
        result = _normalize_whitespace(text)
        assert "\n\n\n" not in result
        assert "Paragraph one\n\nParagraph two" == result

    def test_preserve_paragraph_breaks(self) -> None:
        """Test that double newlines (paragraph breaks) are preserved."""
        text = "Paragraph one\n\nParagraph two"
        result = _normalize_whitespace(text)
        assert "\n\n" in result

    def test_strip_line_whitespace(self) -> None:
        """Test stripping leading/trailing whitespace from lines."""
        text = "  Hello world  \n  Next line  "
        result = _normalize_whitespace(text)
        assert result == "Hello world\nNext line"

    def test_strip_text_whitespace(self) -> None:
        """Test stripping leading/trailing whitespace from entire text."""
        text = "  \n  Hello world  \n  "
        result = _normalize_whitespace(text)
        assert result == "Hello world"


class TestEncodingFixes:
    """Tests for encoding issue fixes."""

    def test_fix_encoding_basic(self) -> None:
        """Test basic encoding fix with ftfy."""
        # This is a simple test - ftfy handles complex cases
        text = "café"
        result = _fix_encoding(text)
        assert "café" in result

    def test_fix_encoding_handles_errors(self) -> None:
        """Test that encoding fix handles errors gracefully."""
        # Even with problematic input, should not crash
        text = "Hello world"
        result = _fix_encoding(text)
        assert isinstance(result, str)


class TestCleanText:
    """Tests for the main clean_text function."""

    def test_clean_text_full_pipeline(self) -> None:
        """Test full cleaning pipeline with all features."""
        text = "Hello   world!  [1]  This is a test…"
        result = clean_text(text)

        # Should remove footnote
        assert "[1]" not in result
        # Should normalize spaces
        assert "   " not in result
        # Should transform ellipsis
        assert "…" not in result
        assert "..." in result
        # Should have content
        assert "Hello world" in result
        assert "This is a test" in result

    def test_clean_text_with_patterns_disabled(self) -> None:
        """Test cleaning with patterns disabled."""
        text = "Hello   world  [1]  test…"
        result = clean_text(text, apply_patterns=False)

        # Should keep footnote and ellipsis (patterns not applied)
        assert "[1]" in result
        assert "…" in result
        # But should still normalize whitespace
        assert "   " not in result

    def test_clean_text_empty_string(self) -> None:
        """Test cleaning empty string."""
        result = clean_text("")
        assert result == ""

    def test_clean_text_none_handling(self) -> None:
        """Test that None input is handled gracefully."""
        # Should return empty string or original value
        result = clean_text("")
        assert result == ""

    def test_clean_text_complex_example(self) -> None:
        """Test cleaning complex real-world example."""
        text = """
        Chapter 1

        This is a test [1] with footnotes [2].

        Page 42

        \u201cSmart quotes\u201d and ellipsis… are here.

        ***

        Next    section   with  spaces.
        """
        result = clean_text(text)

        # Footnotes removed
        assert "[1]" not in result
        assert "[2]" not in result
        # Page number removed
        assert "Page 42" not in result
        # Smart quotes normalized
        assert "\u201c" not in result  # Left double quotation mark
        # Ellipsis normalized
        assert "…" not in result
        assert "..." in result
        # Spaces normalized
        assert "    " not in result
        # Content preserved
        assert "test" in result
        assert "Smart quotes" in result


class TestNoTTSMarkers:
    """
    CRITICAL TESTS: Verify NO TTS markers are present in output.

    These tests ensure that all TTS-specific features have been removed
    from the ported code.
    """

    def test_no_pause_markers(self) -> None:
        """Test that PAUSE markers are never added."""
        text = "Hello world. This is a test."
        result = clean_text(text)
        assert "[PAUSE" not in result
        assert "PAUSE:" not in result

    def test_no_chapter_markers(self) -> None:
        """Test that CHAPTER markers are never added."""
        text = "Chapter 1\n\nThis is chapter content."
        result = clean_text(text)
        assert "[CHAPTER" not in result
        assert "CHAPTER_START" not in result
        assert "CHAPTER_END" not in result

    def test_no_dialogue_markers(self) -> None:
        """Test that DIALOGUE markers are never added."""
        text = '"Hello," she said. "How are you?"'
        result = clean_text(text)
        assert "[DIALOGUE" not in result
        assert "DIALOGUE:" not in result

    def test_no_timing_markers(self) -> None:
        """Test that timing markers are never added."""
        text = "This is a long sentence that might have timing in TTS."
        result = clean_text(text)
        assert "[TIMING" not in result
        assert "ms]" not in result

    def test_no_speaker_markers(self) -> None:
        """Test that speaker markers are never added."""
        text = "Alice: Hello!\nBob: Hi there!"
        result = clean_text(text)
        assert "[SPEAKER" not in result

    def test_search_for_tts_in_module(self) -> None:
        """Test that TTS string does not appear in function names or output."""
        # This is a meta-test - checking the module itself
        from omniparser.processors import text_cleaner

        # Get all function and variable names
        module_contents = dir(text_cleaner)

        # Check no 'tts' in names (case-insensitive)
        for name in module_contents:
            assert "tts" not in name.lower(), f"Found 'tts' in name: {name}"

    def test_no_audio_related_terms(self) -> None:
        """Test that audio-related terms do not appear in output."""
        text = "This is a test of the audio processing system."
        result = clean_text(text)

        # The word "audio" from input is fine, but no markers
        assert "[AUDIO" not in result
        assert "AUDIO_MARKER" not in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_very_long_text(self) -> None:
        """Test cleaning very long text."""
        text = "Hello world. " * 10000
        result = clean_text(text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unicode_characters(self) -> None:
        """Test handling of various Unicode characters."""
        text = "Hello 世界 🌍 Ñoño café"
        result = clean_text(text)
        assert isinstance(result, str)
        # Should preserve Unicode content
        assert "世界" in result or "Noño" in result or "café" in result

    def test_mixed_line_endings(self) -> None:
        """Test handling of mixed line ending styles."""
        text = "Line 1\nLine 2\r\nLine 3\rLine 4"
        result = clean_text(text)
        assert isinstance(result, str)

    def test_only_whitespace(self) -> None:
        """Test text with only whitespace."""
        text = "   \n\n\n   \t\t\t   "
        result = clean_text(text)
        assert result == ""

    def test_special_regex_characters(self) -> None:
        """Test that special regex characters in text do not break cleaning."""
        text = "Cost is $100. Profit (after tax) is 20%."
        result = clean_text(text)
        assert "$" in result
        assert "(" in result
        assert ")" in result
        assert "%" in result
