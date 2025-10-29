"""
Unit tests for configuration management module.
"""

import json
from pathlib import Path
from copy import deepcopy
import pytest

from omniparser.utils.config import (
    DEFAULT_CONFIG,
    load_config,
    merge_options,
    get_ai_options,
    get_parsing_options,
    create_config_template,
    validate_config,
    get_cached_config,
    clear_config_cache,
    _deep_merge,
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary directory for config files."""
    config_dir = tmp_path / "test_project"
    config_dir.mkdir()
    # Create fake pyproject.toml to mark as project root
    (config_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
    return config_dir


@pytest.fixture
def custom_config():
    """Sample custom configuration."""
    return {
        "ai": {
            "default_provider": "openai",
            "anthropic": {
                "model": "claude-3-opus-20240229",
                "max_tokens": 2048,
            },
        },
        "parsing": {
            "extract_images": False,
            "clean_text": False,
        },
    }


class TestDeepMerge:
    """Tests for _deep_merge helper function."""

    def test_deep_merge_simple(self):
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self):
        """Test merging nested dictionaries."""
        base = {"ai": {"anthropic": {"model": "haiku", "tokens": 1024}}}
        override = {"ai": {"anthropic": {"tokens": 2048}}}
        result = _deep_merge(base, override)

        # Should merge nested dicts, not replace
        assert result["ai"]["anthropic"]["model"] == "haiku"
        assert result["ai"]["anthropic"]["tokens"] == 2048

    def test_deep_merge_no_mutation(self):
        """Test that original dictionaries are not mutated."""
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)

        assert base == {"a": 1}  # Unchanged
        assert override == {"b": 2}  # Unchanged
        assert result == {"a": 1, "b": 2}

    def test_deep_merge_override_with_non_dict(self):
        """Test overriding nested dict with non-dict value."""
        base = {"ai": {"model": {"name": "haiku"}}}
        override = {"ai": {"model": "opus"}}
        result = _deep_merge(base, override)

        # Override should replace the nested dict
        assert result["ai"]["model"] == "opus"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_defaults_only(self, temp_config_dir):
        """Test loading config with no files (uses defaults)."""
        config = load_config(temp_config_dir)

        # Should match DEFAULT_CONFIG
        assert config["ai"]["default_provider"] == DEFAULT_CONFIG["ai"]["default_provider"]
        assert config["parsing"]["extract_images"] == DEFAULT_CONFIG["parsing"]["extract_images"]

    def test_load_config_from_file(self, temp_config_dir, custom_config):
        """Test loading config from config.json."""
        config_path = temp_config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(custom_config, f)

        config = load_config(temp_config_dir)

        # Should merge with defaults
        assert config["ai"]["default_provider"] == "openai"  # From custom
        assert config["ai"]["anthropic"]["model"] == "claude-3-opus-20240229"  # From custom
        assert config["ai"]["anthropic"]["temperature"] == 0.3  # From defaults
        assert config["parsing"]["extract_images"] is False  # From custom

    def test_load_config_local_overrides(self, temp_config_dir, custom_config):
        """Test that config_local.json overrides config.json."""
        # Write config.json
        config_path = temp_config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(custom_config, f)

        # Write config_local.json with override
        local_config = {
            "ai": {
                "anthropic": {"max_tokens": 4096}
            }
        }
        local_path = temp_config_dir / "config_local.json"
        with open(local_path, "w") as f:
            json.dump(local_config, f)

        config = load_config(temp_config_dir)

        # Local should override
        assert config["ai"]["anthropic"]["max_tokens"] == 4096
        # Other values should remain
        assert config["ai"]["anthropic"]["model"] == "claude-3-opus-20240229"

    def test_load_config_malformed_json(self, temp_config_dir):
        """Test handling of malformed JSON."""
        config_path = temp_config_dir / "config.json"
        config_path.write_text("{invalid json")

        # Should not crash, just use defaults
        config = load_config(temp_config_dir)
        assert config == DEFAULT_CONFIG


class TestMergeOptions:
    """Tests for merge_options function."""

    def test_merge_options_with_user_options(self):
        """Test merging config options with user options."""
        config_opts = {"model": "haiku", "max_tokens": 1024, "temperature": 0.3}
        user_opts = {"max_tokens": 2048, "timeout": 120}

        result = merge_options(config_opts, user_opts)

        assert result["model"] == "haiku"  # From config
        assert result["max_tokens"] == 2048  # From user (overridden)
        assert result["temperature"] == 0.3  # From config
        assert result["timeout"] == 120  # From user (new key)

    def test_merge_options_no_user_options(self):
        """Test merge_options with None user options."""
        config_opts = {"model": "haiku", "max_tokens": 1024}
        result = merge_options(config_opts, None)

        assert result == config_opts
        assert result is not config_opts  # Should be a copy

    def test_merge_options_nested(self):
        """Test merging nested options."""
        config_opts = {"ai": {"model": "haiku", "tokens": 1024}}
        user_opts = {"ai": {"tokens": 2048}}

        result = merge_options(config_opts, user_opts)

        assert result["ai"]["model"] == "haiku"
        assert result["ai"]["tokens"] == 2048


class TestGetAIOptions:
    """Tests for get_ai_options function."""

    def test_get_ai_options_anthropic(self, temp_config_dir):
        """Test getting AI options for Anthropic."""
        config = load_config(temp_config_dir)
        ai_options = get_ai_options("anthropic", config)

        assert ai_options["ai_provider"] == "anthropic"
        assert ai_options["model"] == "claude-3-haiku-20240307"
        assert ai_options["max_tokens"] == 1024
        assert ai_options["temperature"] == 0.3

    def test_get_ai_options_with_user_overrides(self, temp_config_dir):
        """Test getting AI options with user overrides."""
        config = load_config(temp_config_dir)
        user_opts = {"max_tokens": 2048, "temperature": 0.7}

        ai_options = get_ai_options("anthropic", config, user_opts)

        assert ai_options["max_tokens"] == 2048  # Overridden
        assert ai_options["temperature"] == 0.7  # Overridden
        assert ai_options["model"] == "claude-3-haiku-20240307"  # From config

    def test_get_ai_options_ollama(self, temp_config_dir):
        """Test getting AI options for Ollama."""
        config = load_config(temp_config_dir)
        ai_options = get_ai_options("ollama", config)

        assert ai_options["ai_provider"] == "ollama"
        assert ai_options["base_url"] == "http://localhost:11434/v1"
        assert ai_options["model"] == "llama3.2:latest"

    def test_get_ai_options_auto_load_config(self):
        """Test that get_ai_options auto-loads config if not provided."""
        ai_options = get_ai_options("anthropic", config=None)

        # Should use defaults
        assert ai_options["ai_provider"] == "anthropic"
        assert "model" in ai_options


class TestGetParsingOptions:
    """Tests for get_parsing_options function."""

    def test_get_parsing_options_global(self, temp_config_dir):
        """Test getting global parsing options."""
        config = load_config(temp_config_dir)
        parsing_options = get_parsing_options(config=config)

        assert parsing_options["extract_images"] is True
        assert parsing_options["clean_text"] is True
        assert parsing_options["detect_chapters"] is True

    def test_get_parsing_options_format_specific(self, temp_config_dir):
        """Test getting format-specific parsing options."""
        config = load_config(temp_config_dir)
        epub_options = get_parsing_options(format="epub", config=config)

        # Should merge global + format-specific
        assert epub_options["extract_images"] is True  # Global
        assert epub_options["use_toc"] is True  # EPUB-specific
        assert epub_options["fallback_to_spine"] is True  # EPUB-specific

    def test_get_parsing_options_with_user_overrides(self, temp_config_dir):
        """Test getting parsing options with user overrides."""
        config = load_config(temp_config_dir)
        user_opts = {"extract_images": False, "custom_option": "value"}

        options = get_parsing_options(config=config, user_options=user_opts)

        assert options["extract_images"] is False  # Overridden
        assert options["custom_option"] == "value"  # New from user
        assert options["clean_text"] is True  # From config

    def test_get_parsing_options_html_specific(self, temp_config_dir):
        """Test getting HTML-specific parsing options."""
        config = load_config(temp_config_dir)
        html_options = get_parsing_options(format="html", config=config)

        assert html_options["timeout"] == 10
        assert html_options["min_chapter_level"] == 1
        assert html_options["max_chapter_level"] == 2


class TestCreateConfigTemplate:
    """Tests for create_config_template function."""

    def test_create_config_template(self, temp_config_dir):
        """Test creating config template file."""
        output_path = temp_config_dir / "config_template.json"
        result = create_config_template(output_path)

        assert result == output_path
        assert output_path.exists()

        # Load and verify content
        with open(output_path, "r") as f:
            template = json.load(f)

        assert "ai" in template
        assert "parsing" in template
        assert "ai_features" in template
        assert template == DEFAULT_CONFIG


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_config_valid(self):
        """Test validation of valid config."""
        valid, errors = validate_config(DEFAULT_CONFIG)

        assert valid is True
        assert errors == []

    def test_validate_config_missing_top_level_key(self):
        """Test validation with missing top-level key."""
        config = {"ai": {}, "parsing": {}}  # Missing ai_features
        valid, errors = validate_config(config)

        assert valid is False
        assert any("ai_features" in error for error in errors)

    def test_validate_config_missing_provider(self):
        """Test validation with missing AI provider."""
        config = deepcopy(DEFAULT_CONFIG)
        del config["ai"]["anthropic"]
        valid, errors = validate_config(config)

        assert valid is False
        assert any("anthropic" in error for error in errors)

    def test_validate_config_missing_provider_field(self):
        """Test validation with missing field in provider config."""
        config = deepcopy(DEFAULT_CONFIG)
        del config["ai"]["anthropic"]["model"]
        valid, errors = validate_config(config)

        assert valid is False
        assert any("model" in error and "anthropic" in error for error in errors)

    def test_validate_config_missing_parsing_option(self):
        """Test validation with missing parsing option."""
        config = deepcopy(DEFAULT_CONFIG)
        del config["parsing"]["extract_images"]
        valid, errors = validate_config(config)

        assert valid is False
        assert any("extract_images" in error for error in errors)


class TestCachedConfig:
    """Tests for cached config functions."""

    def test_get_cached_config(self, temp_config_dir, monkeypatch):
        """Test getting cached config."""
        clear_config_cache()

        # Mock load_config to return our test data
        test_config = {"test": "data"}
        monkeypatch.setattr(
            "omniparser.utils.config.load_config",
            lambda config_dir=None: test_config,
        )

        # First call should load
        config1 = get_cached_config()
        # Second call should use cache
        config2 = get_cached_config()

        assert config1 == test_config
        assert config1 is config2  # Same object reference

    def test_clear_config_cache(self, monkeypatch):
        """Test clearing config cache."""
        clear_config_cache()

        call_count = 0

        def mock_load_config(config_dir=None):
            nonlocal call_count
            call_count += 1
            return {"version": call_count}

        monkeypatch.setattr("omniparser.utils.config.load_config", mock_load_config)

        # First call
        config1 = get_cached_config()
        assert call_count == 1

        # Second call (cached)
        config2 = get_cached_config()
        assert call_count == 1  # Not called again

        # Clear cache and call again
        clear_config_cache()
        config3 = get_cached_config()
        assert call_count == 2  # Called again
        assert config3 != config1  # Different values


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_config_workflow(self, temp_config_dir):
        """Test complete config loading and usage workflow."""
        # Create custom config (will be merged with defaults)
        custom = {
            "ai": {
                "default_provider": "ollama",
                "ollama": {"model": "llama3.2:8b"},
            },
            "parsing": {
                "extract_images": False,
                "epub": {"use_toc": False},
            },
        }
        config_path = temp_config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(custom, f)

        # Load config (will merge with defaults, so all providers will be present)
        config = load_config(temp_config_dir)

        # Validate (should pass because defaults fill in missing providers)
        valid, errors = validate_config(config)
        if not valid:
            print(f"Validation errors: {errors}")
        assert valid is True

        # Get AI options for Ollama
        ai_options = get_ai_options("ollama", config)
        assert ai_options["ai_provider"] == "ollama"
        assert ai_options["model"] == "llama3.2:8b"
        assert ai_options["base_url"] == "http://localhost:11434/v1"  # From default

        # Get parsing options for EPUB
        epub_options = get_parsing_options(format="epub", config=config)
        assert epub_options["extract_images"] is False  # Custom
        assert epub_options["use_toc"] is False  # Custom EPUB-specific
        assert epub_options["clean_text"] is True  # From default

        # Merge with user options
        user_opts = {"max_tokens": 2048}
        final_ai_opts = get_ai_options("ollama", config, user_opts)
        assert final_ai_opts["max_tokens"] == 2048
        assert final_ai_opts["model"] == "llama3.2:8b"

    def test_layered_config_priority(self, temp_config_dir):
        """Test that config priority is respected: user > local > config > defaults."""
        # Write config.json
        config_data = {
            "ai": {"anthropic": {"max_tokens": 1024}}
        }
        config_path = temp_config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        # Write config_local.json
        local_data = {
            "ai": {"anthropic": {"max_tokens": 2048}}
        }
        local_path = temp_config_dir / "config_local.json"
        with open(local_path, "w") as f:
            json.dump(local_data, f)

        # Load config
        config = load_config(temp_config_dir)

        # Get options without user override
        ai_opts = get_ai_options("anthropic", config)
        assert ai_opts["max_tokens"] == 2048  # From local

        # Get options with user override
        user_opts = {"max_tokens": 4096}
        ai_opts_with_user = get_ai_options("anthropic", config, user_opts)
        assert ai_opts_with_user["max_tokens"] == 4096  # User takes precedence
