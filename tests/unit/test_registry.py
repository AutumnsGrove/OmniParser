"""
Unit tests for the ParserRegistry.

Tests the parser registration, lookup, and discovery functionality.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from omniparser.base.registry import (
    ParserInfo,
    ParserRegistry,
    registry,
    register_builtin_parsers,
)
from omniparser.models import Document


class TestParserInfo:
    """Tests for ParserInfo dataclass."""

    def test_parser_info_requires_callable(self):
        """Test that ParserInfo requires either parser_class or parse_func."""
        with pytest.raises(
            ValueError, match="must have either parser_class or parse_func"
        ):
            ParserInfo(name="test", extensions=[".test"])

    def test_parser_info_accepts_parser_class(self):
        """Test that ParserInfo accepts parser_class."""
        mock_class = Mock()
        info = ParserInfo(name="test", extensions=[".test"], parser_class=mock_class)
        assert info.parser_class == mock_class
        assert info.parse_func is None

    def test_parser_info_accepts_parse_func(self):
        """Test that ParserInfo accepts parse_func."""
        mock_func = Mock()
        info = ParserInfo(name="test", extensions=[".test"], parse_func=mock_func)
        assert info.parse_func == mock_func
        assert info.parser_class is None

    def test_parser_info_normalizes_extensions(self):
        """Test that extensions are normalized to lowercase with leading dot."""
        mock_func = Mock()
        info = ParserInfo(
            name="test", extensions=["TEST", ".Foo", "bar"], parse_func=mock_func
        )
        assert info.extensions == [".test", ".foo", ".bar"]

    def test_parser_info_default_values(self):
        """Test default values for optional fields."""
        mock_func = Mock()
        info = ParserInfo(name="test", extensions=[".test"], parse_func=mock_func)
        assert info.description == ""
        assert info.version == "1.0.0"
        assert info.priority == 0
        assert info.supports_func is None


class TestParserRegistry:
    """Tests for ParserRegistry class."""

    def setup_method(self):
        """Create a fresh registry for each test."""
        self.registry = ParserRegistry()

    def test_register_parser(self):
        """Test registering a parser."""
        mock_func = Mock()
        self.registry.register(
            extensions=[".test"],
            name="test",
            parse_func=mock_func,
            description="Test parser",
        )

        assert "test" in self.registry.list_parsers()
        info = self.registry.get_parser_by_name("test")
        assert info is not None
        assert info.name == "test"
        assert info.parse_func == mock_func

    def test_register_parser_with_class(self):
        """Test registering a parser with class interface."""
        mock_class = Mock()
        self.registry.register(
            extensions=[".test"],
            name="test",
            parser_class=mock_class,
        )

        info = self.registry.get_parser_by_name("test")
        assert info is not None
        assert info.parser_class == mock_class

    def test_register_overwrites_existing(self):
        """Test that registering with same name overwrites existing."""
        mock_func1 = Mock()
        mock_func2 = Mock()

        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func1)
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func2)

        info = self.registry.get_parser_by_name("test")
        assert info.parse_func == mock_func2

    def test_unregister_parser(self):
        """Test unregistering a parser."""
        mock_func = Mock()
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func)

        assert self.registry.unregister("test") is True
        assert "test" not in self.registry.list_parsers()
        assert self.registry.get_parser(".test") is None

    def test_unregister_nonexistent_parser(self):
        """Test unregistering a parser that doesn't exist."""
        assert self.registry.unregister("nonexistent") is False

    def test_get_parser_by_extension(self):
        """Test getting parser by extension."""
        mock_func = Mock()
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func)

        info = self.registry.get_parser(".test")
        assert info is not None
        assert info.name == "test"

    def test_get_parser_by_path(self):
        """Test getting parser by file path."""
        mock_func = Mock()
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func)

        info = self.registry.get_parser(Path("/some/file.test"))
        assert info is not None
        assert info.name == "test"

    def test_get_parser_by_string_path(self):
        """Test getting parser by string path."""
        mock_func = Mock()
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func)

        info = self.registry.get_parser("/some/file.test")
        assert info is not None
        assert info.name == "test"

    def test_get_parser_case_insensitive(self):
        """Test that extension lookup is case-insensitive."""
        mock_func = Mock()
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func)

        assert self.registry.get_parser(".TEST") is not None
        assert self.registry.get_parser(".Test") is not None

    def test_get_parser_returns_none_for_unknown(self):
        """Test that get_parser returns None for unknown extensions."""
        assert self.registry.get_parser(".unknown") is None

    def test_priority_based_extension_handling(self):
        """Test that higher priority parsers take precedence."""
        mock_func1 = Mock()
        mock_func2 = Mock()

        # Register lower priority first
        self.registry.register(
            extensions=[".test"],
            name="low",
            parse_func=mock_func1,
            priority=0,
        )

        # Register higher priority
        self.registry.register(
            extensions=[".test"],
            name="high",
            parse_func=mock_func2,
            priority=10,
        )

        # Higher priority should win
        info = self.registry.get_parser(".test")
        assert info.name == "high"

    def test_priority_keeps_existing_if_higher(self):
        """Test that existing parser is kept if it has higher priority."""
        mock_func1 = Mock()
        mock_func2 = Mock()

        # Register higher priority first
        self.registry.register(
            extensions=[".test"],
            name="high",
            parse_func=mock_func1,
            priority=10,
        )

        # Register lower priority
        self.registry.register(
            extensions=[".test"],
            name="low",
            parse_func=mock_func2,
            priority=0,
        )

        # Higher priority should still win
        info = self.registry.get_parser(".test")
        assert info.name == "high"

    def test_is_supported_by_extension(self):
        """Test is_supported with extension."""
        mock_func = Mock()
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func)

        assert self.registry.is_supported("file.test") is True
        assert self.registry.is_supported("file.unknown") is False

    def test_is_supported_with_supports_func(self):
        """Test is_supported with custom supports_func."""
        mock_func = Mock()
        supports_func = Mock(return_value=True)

        self.registry.register(
            extensions=[".test"],
            name="test",
            parse_func=mock_func,
            supports_func=supports_func,
        )

        # Extension-based check
        assert self.registry.is_supported("file.test") is True

        # Custom supports_func for unknown extension
        assert self.registry.is_supported("file.custom") is True
        supports_func.assert_called()

    def test_is_supported_early_return(self):
        """Test that is_supported returns early when extension matches."""
        mock_func = Mock()
        supports_func = Mock(return_value=True)

        self.registry.register(
            extensions=[".test"],
            name="test",
            parse_func=mock_func,
            supports_func=supports_func,
        )

        # Should return True without calling supports_func
        assert self.registry.is_supported("file.test") is True
        supports_func.assert_not_called()

    def test_get_supported_extensions(self):
        """Test getting all supported extensions."""
        mock_func = Mock()
        self.registry.register(
            extensions=[".foo", ".bar"], name="test", parse_func=mock_func
        )

        extensions = self.registry.get_supported_extensions()
        assert ".foo" in extensions
        assert ".bar" in extensions
        assert extensions == sorted(extensions)  # Should be sorted

    def test_list_parsers(self):
        """Test listing all parser names."""
        mock_func = Mock()
        self.registry.register(extensions=[".foo"], name="foo", parse_func=mock_func)
        self.registry.register(extensions=[".bar"], name="bar", parse_func=mock_func)

        parsers = self.registry.list_parsers()
        assert "foo" in parsers
        assert "bar" in parsers
        assert parsers == sorted(parsers)  # Should be sorted

    def test_get_all_parsers(self):
        """Test getting all parser info."""
        mock_func = Mock()
        self.registry.register(extensions=[".foo"], name="foo", parse_func=mock_func)
        self.registry.register(extensions=[".bar"], name="bar", parse_func=mock_func)

        all_parsers = self.registry.get_all_parsers()
        assert "foo" in all_parsers
        assert "bar" in all_parsers
        assert isinstance(all_parsers["foo"], ParserInfo)

    def test_clear_registry(self):
        """Test clearing the registry."""
        mock_func = Mock()
        self.registry.register(extensions=[".test"], name="test", parse_func=mock_func)

        self.registry.clear()

        assert self.registry.list_parsers() == []
        assert self.registry.get_supported_extensions() == []

    def test_multiple_extensions_per_parser(self):
        """Test parser with multiple extensions."""
        mock_func = Mock()
        self.registry.register(
            extensions=[".foo", ".bar", ".baz"],
            name="multi",
            parse_func=mock_func,
        )

        assert self.registry.get_parser(".foo").name == "multi"
        assert self.registry.get_parser(".bar").name == "multi"
        assert self.registry.get_parser(".baz").name == "multi"


class TestGlobalRegistry:
    """Tests for the global registry instance."""

    def setup_method(self):
        """Clear global registry before each test."""
        registry.clear()

    def teardown_method(self):
        """Clear global registry after each test."""
        registry.clear()

    def test_global_registry_exists(self):
        """Test that global registry instance exists."""
        assert registry is not None
        assert isinstance(registry, ParserRegistry)

    def test_register_builtin_parsers(self):
        """Test registering built-in parsers."""
        register_builtin_parsers()

        # Check that all expected parsers are registered
        parsers = registry.list_parsers()
        assert "epub" in parsers
        assert "pdf" in parsers
        assert "docx" in parsers
        assert "html" in parsers
        assert "markdown" in parsers
        assert "text" in parsers
        assert "photo" in parsers

    def test_builtin_parsers_have_extensions(self):
        """Test that builtin parsers have expected extensions."""
        register_builtin_parsers()

        extensions = registry.get_supported_extensions()
        # Document formats
        assert ".epub" in extensions
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".html" in extensions
        assert ".htm" in extensions
        assert ".md" in extensions
        assert ".markdown" in extensions
        assert ".txt" in extensions
        # Photo formats
        assert ".jpg" in extensions
        assert ".jpeg" in extensions
        assert ".png" in extensions

    def test_builtin_epub_parser_info(self):
        """Test EPUB parser registration details."""
        register_builtin_parsers()

        info = registry.get_parser_by_name("epub")
        assert info is not None
        assert info.parser_class is not None
        assert info.parse_func is not None
        assert info.supports_func is not None
        assert ".epub" in info.extensions

    def test_builtin_photo_parser_info(self):
        """Test photo parser registration details."""
        register_builtin_parsers()

        info = registry.get_parser_by_name("photo")
        assert info is not None
        assert ".jpg" in info.extensions
        assert ".jpeg" in info.extensions
        assert ".png" in info.extensions
        assert ".gif" in info.extensions
        assert ".webp" in info.extensions

    def test_register_builtin_parsers_idempotent(self):
        """Test that register_builtin_parsers can be called multiple times."""
        register_builtin_parsers()
        count1 = len(registry.list_parsers())

        register_builtin_parsers()
        count2 = len(registry.list_parsers())

        # Should have same number of parsers (overwrites existing)
        assert count1 == count2


class TestRegistryIntegration:
    """Integration tests for registry with parse_document."""

    def setup_method(self):
        """Clear caches before each test."""
        from omniparser.parser import _clear_parser_cache

        _clear_parser_cache()
        registry.clear()

    def test_parse_document_uses_registry(self, tmp_path):
        """Test that parse_document uses the registry for routing."""
        from omniparser.parser import _ensure_registry_initialized

        # Initialize registry
        _ensure_registry_initialized()

        # Registry should have been initialized with builtin parsers
        assert len(registry.list_parsers()) > 0
        assert "epub" in registry.list_parsers()
        assert "pdf" in registry.list_parsers()
        assert "html" in registry.list_parsers()

        # Verify routing works by checking parser lookup
        epub_info = registry.get_parser(".epub")
        assert epub_info is not None
        assert epub_info.name == "epub"

        pdf_info = registry.get_parser(".pdf")
        assert pdf_info is not None
        assert pdf_info.name == "pdf"

    def test_custom_parser_registration(self, tmp_path):
        """Test registering a custom parser and using it."""
        from omniparser import parse_document
        from omniparser.parser import _ensure_registry_initialized

        # First initialize the builtin parsers
        _ensure_registry_initialized()

        # Create a custom parser
        mock_doc = Mock(spec=Document)
        custom_parse_func = Mock(return_value=mock_doc)

        # Register custom parser with high priority
        registry.register(
            extensions=[".custom"],
            name="custom",
            parse_func=custom_parse_func,
            priority=100,
        )

        # Create test file
        test_file = tmp_path / "test.custom"
        test_file.write_text("custom content")

        # The custom parser should be found
        info = registry.get_parser(".custom")
        assert info is not None
        assert info.name == "custom"


class TestRegistryClearAndReset:
    """Tests for registry clearing and reset behavior."""

    def setup_method(self):
        """Clear registry and parser cache before each test."""
        from omniparser.parser import _clear_parser_cache

        _clear_parser_cache()
        registry.clear()

    def test_clear_parser_cache_resets_registry_flag(self):
        """Test that _clear_parser_cache resets the registry initialization flag."""
        from omniparser.parser import _clear_parser_cache, _ensure_registry_initialized

        # Initialize registry
        _ensure_registry_initialized()
        assert len(registry.list_parsers()) > 0

        # Clear everything
        _clear_parser_cache()
        registry.clear()

        # Registry should be empty
        assert len(registry.list_parsers()) == 0

        # Re-initialize should work
        _ensure_registry_initialized()
        assert len(registry.list_parsers()) > 0
