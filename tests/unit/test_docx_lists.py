"""
Unit tests for DOCX list detection and formatting module.

Tests the list.py module functions for detecting and formatting list items
from DOCX documents into markdown.
"""

from unittest.mock import Mock, MagicMock
import pytest

from omniparser.parsers.docx.lists import (
    is_list_item,
    get_list_level,
    is_numbered_list,
    format_list_item,
)


class TestIsListItem:
    """Tests for is_list_item() function."""

    def test_detects_list_bullet_style(self):
        """Should detect paragraph with 'List Bullet' style."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Bullet"
        para._element = None

        assert is_list_item(para) is True

    def test_detects_list_number_style(self):
        """Should detect paragraph with 'List Number' style."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Number"
        para._element = None

        assert is_list_item(para) is True

    def test_detects_list_style_variants(self):
        """Should detect various list style names."""
        list_styles = [
            "List",
            "List 2",
            "List Bullet 2",
            "List Number 3",
            "List Continue",
        ]

        for style_name in list_styles:
            para = Mock()
            para.style = Mock()
            para.style.name = style_name
            para._element = None

            assert is_list_item(para) is True, f"Failed to detect: {style_name}"

    def test_ignores_no_list_style(self):
        """Should not detect 'No List' style."""
        para = Mock()
        para.style = Mock()
        para.style.name = "No List"
        para._element = None

        assert is_list_item(para) is False

    def test_detects_numpr_property(self):
        """Should detect paragraph with numPr XML property."""
        para = Mock()
        para.style = Mock()
        para.style.name = "Normal"

        # Mock XML structure with numPr
        pPr = Mock()
        pPr.numPr = Mock()  # Has numbering properties

        para._element = Mock()
        para._element.pPr = pPr

        assert is_list_item(para) is True

    def test_non_list_paragraph(self):
        """Should not detect normal paragraph as list."""
        para = Mock()
        para.style = Mock()
        para.style.name = "Normal"
        para._element = Mock()
        para._element.pPr = None

        assert is_list_item(para) is False

    def test_handles_missing_style(self):
        """Should handle paragraph with no style gracefully."""
        para = Mock()
        para.style = None
        para._element = Mock()
        para._element.pPr = None

        assert is_list_item(para) is False


class TestGetListLevel:
    """Tests for get_list_level() function."""

    def test_level_from_ilvl_property(self):
        """Should extract level from numPr.ilvl XML property."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List"

        # Mock XML structure with ilvl = 2
        numPr = Mock()
        numPr.ilvl = Mock()
        numPr.ilvl.val = 2

        pPr = Mock()
        pPr.numPr = numPr

        para._element = Mock()
        para._element.pPr = pPr

        assert get_list_level(para) == 2

    def test_level_from_style_name(self):
        """Should extract level from style name (e.g., 'List 2')."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Bullet 3"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None  # No ilvl, fallback to style

        # "List Bullet 3" -> level 2 (0-based)
        assert get_list_level(para) == 2

    def test_default_level_zero(self):
        """Should default to level 0 for list items without explicit level."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Bullet"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None

        assert get_list_level(para) == 0

    def test_returns_negative_for_non_list(self):
        """Should return -1 for non-list paragraphs."""
        para = Mock()
        para.style = Mock()
        para.style.name = "Normal"
        para._element = Mock()
        para._element.pPr = None

        assert get_list_level(para) == -1

    def test_handles_missing_ilvl(self):
        """Should handle numPr without ilvl property."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List"

        numPr = Mock()
        numPr.ilvl = None  # No ilvl

        pPr = Mock()
        pPr.numPr = numPr

        para._element = Mock()
        para._element.pPr = pPr

        # Should default to 0
        assert get_list_level(para) == 0


class TestIsNumberedList:
    """Tests for is_numbered_list() function."""

    def test_detects_numbered_list(self):
        """Should detect 'List Number' style as numbered."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Number"

        assert is_numbered_list(para) is True

    def test_detects_bulleted_list(self):
        """Should detect 'List Bullet' style as not numbered."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Bullet"

        assert is_numbered_list(para) is False

    def test_defaults_to_bulleted(self):
        """Should default to bulleted (False) for generic list style."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List"

        assert is_numbered_list(para) is False

    def test_handles_missing_style(self):
        """Should handle paragraph with no style."""
        para = Mock()
        para.style = None

        assert is_numbered_list(para) is False


class TestFormatListItem:
    """Tests for format_list_item() function."""

    def test_formats_bullet_level_0(self):
        """Should format level 0 bullet as '- Item'."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Bullet"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None

        result = format_list_item(para, "Item text")
        assert result == "- Item text"

    def test_formats_numbered_level_0(self):
        """Should format level 0 numbered as '1. Item'."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Number"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None

        result = format_list_item(para, "Item text")
        assert result == "1. Item text"

    def test_formats_nested_bullet(self):
        """Should format nested bullet with indentation."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Bullet 2"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None

        # "List Bullet 2" -> level 1 (0-based)
        result = format_list_item(para, "Nested item")
        assert result == "  - Nested item"

    def test_formats_deeply_nested_numbered(self):
        """Should format deeply nested numbered list."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List Number 3"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None

        # "List Number 3" -> level 2 (0-based)
        result = format_list_item(para, "Deep item")
        assert result == "    1. Deep item"

    def test_returns_original_text_for_non_list(self):
        """Should return original text for non-list paragraphs."""
        para = Mock()
        para.style = Mock()
        para.style.name = "Normal"
        para._element = Mock()
        para._element.pPr = None

        result = format_list_item(para, "Normal text")
        assert result == "Normal text"

    def test_handles_negative_level(self):
        """Should handle negative level gracefully (treat as level 0)."""
        para = Mock()
        para.style = Mock()
        para.style.name = "List"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None

        result = format_list_item(para, "Item")
        assert result == "- Item"


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_complete_list_workflow(self):
        """Should handle complete workflow from detection to formatting."""
        # Create a mock numbered list at level 1
        para = Mock()
        para.style = Mock()
        para.style.name = "List Number 2"
        para._element = Mock()
        para._element.pPr = Mock()
        para._element.pPr.numPr = None

        # Verify detection
        assert is_list_item(para) is True

        # Verify level extraction
        level = get_list_level(para)
        assert level == 1

        # Verify type detection
        assert is_numbered_list(para) is True

        # Verify formatting
        result = format_list_item(para, "Second level item")
        assert result == "  1. Second level item"
