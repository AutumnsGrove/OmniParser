"""
Configuration management for OmniParser.

This module handles loading and merging configuration from multiple sources:
1. config.json (primary, checked into git with defaults)
2. config_local.json (local overrides, gitignored)
3. User-provided options dictionaries (highest priority)

Example:
    >>> config = load_config()
    >>> ai_options = config["ai"]["anthropic"]
    >>> # {'model': 'claude-3-haiku-20240307', 'max_tokens': 1024, ...}

    >>> # Merge with user options
    >>> user_opts = {"max_tokens": 2048}
    >>> final_opts = merge_options(ai_options, user_opts)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


# Default configuration schema
DEFAULT_CONFIG = {
    "ai": {
        "default_provider": "anthropic",
        "anthropic": {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "temperature": 0.3,
            "timeout": 60,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
        "openai": {
            "model": "gpt-3.5-turbo",
            "max_tokens": 1024,
            "temperature": 0.3,
            "timeout": 60,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
        "openrouter": {
            "model": "meta-llama/llama-3.2-3b-instruct:free",
            "max_tokens": 1024,
            "temperature": 0.3,
            "timeout": 60,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
        "ollama": {
            "base_url": "http://localhost:11434/v1",
            "model": "llama3.2:latest",
            "max_tokens": 1024,
            "temperature": 0.3,
            "timeout": 60,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
        "lmstudio": {
            "base_url": "http://localhost:1234/v1",
            "model": "local-model",
            "max_tokens": 1024,
            "temperature": 0.3,
            "timeout": 60,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
    },
    "parsing": {
        "extract_images": True,
        "image_output_dir": None,  # None = use temp directory
        "clean_text": True,
        "detect_chapters": True,
        # HTML-specific options
        "html": {
            "timeout": 10,
            "min_chapter_level": 1,
            "max_chapter_level": 2,
        },
        # EPUB-specific options
        "epub": {
            "use_toc": True,
            "fallback_to_spine": True,
        },
        # PDF-specific options (for future implementation)
        "pdf": {
            "extract_tables": True,
            "ocr_images": False,
        },
        # DOCX-specific options (for future implementation)
        "docx": {
            "extract_comments": False,
            "preserve_formatting": True,
        },
    },
    "ai_features": {
        "enabled": False,  # Global toggle for AI features
        "auto_tag": False,  # Auto-generate tags during parsing
        "auto_summarize": False,  # Auto-generate summaries during parsing
        "auto_describe_images": False,  # Auto-describe images during parsing
        "quality_check": False,  # Run quality checks after parsing
    },
}


def load_config(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from JSON files with local overrides.

    This function implements a layered configuration system:
    1. Start with DEFAULT_CONFIG (hardcoded defaults)
    2. Override with config.json (project defaults)
    3. Override with config_local.json (local customizations)

    Args:
        config_dir: Directory containing config files. If None, uses project root
                   (determined by walking up from this file's location).

    Returns:
        Dictionary containing merged configuration from all sources.

    Example:
        >>> config = load_config()
        >>> print(config["ai"]["default_provider"])
        anthropic
    """
    if config_dir is None:
        # Find project root (directory containing pyproject.toml)
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "pyproject.toml").exists():
                config_dir = parent
                break
        else:
            # Fallback to current directory
            config_dir = Path.cwd()

    # Start with default config
    config = deepcopy(DEFAULT_CONFIG)

    # Try loading config.json (project defaults)
    config_path = config_dir / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                loaded = json.load(f)
                config = _deep_merge(config, loaded)
                logger.info(f"✅ Loaded config from {config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing {config_path}: {e}")
        except Exception as e:
            logger.error(f"❌ Error reading {config_path}: {e}")
    else:
        logger.info(f"ℹ️  No config.json found at {config_path}, using defaults")

    # Try loading config_local.json (local overrides)
    config_local_path = config_dir / "config_local.json"
    if config_local_path.exists():
        try:
            with open(config_local_path, "r") as f:
                loaded = json.load(f)
                config = _deep_merge(config, loaded)
                logger.info(f"✅ Loaded local config from {config_local_path}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing {config_local_path}: {e}")
        except Exception as e:
            logger.error(f"❌ Error reading {config_local_path}: {e}")

    return config


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries (override takes precedence).

    Args:
        base: Base dictionary.
        override: Override dictionary (values take precedence).

    Returns:
        Merged dictionary.
    """
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = _deep_merge(result[key], value)
        else:
            # Override value
            result[key] = value

    return result


def merge_options(
    config_options: Dict[str, Any], user_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge config-based options with user-provided options.

    User options take precedence over config options.

    Args:
        config_options: Options from config file.
        user_options: User-provided options (highest priority).

    Returns:
        Merged options dictionary.

    Example:
        >>> config_opts = {"model": "claude-3-haiku", "max_tokens": 1024}
        >>> user_opts = {"max_tokens": 2048}
        >>> merged = merge_options(config_opts, user_opts)
        >>> print(merged["max_tokens"])
        2048
    """
    if user_options is None:
        return deepcopy(config_options)

    return _deep_merge(config_options, user_options)


def get_ai_options(
    provider: str, config: Optional[Dict[str, Any]] = None, user_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get AI options for a specific provider with config and user overrides.

    This is a convenience function that:
    1. Loads config if not provided
    2. Extracts provider-specific options
    3. Merges with user options

    Args:
        provider: AI provider name (anthropic, openai, ollama, lmstudio, openrouter).
        config: Pre-loaded config. If None, loads config automatically.
        user_options: User-provided options to merge (highest priority).

    Returns:
        Dictionary of AI options for the provider.

    Example:
        >>> opts = get_ai_options("anthropic", user_options={"max_tokens": 2048})
        >>> print(opts["model"])
        claude-3-haiku-20240307
    """
    if config is None:
        config = load_config()

    # Get provider-specific options from config
    provider_config = config.get("ai", {}).get(provider, {})

    # Add the provider name to options
    result = deepcopy(provider_config)
    result["ai_provider"] = provider

    # Merge with user options
    if user_options:
        result = _deep_merge(result, user_options)

    return result


def get_parsing_options(
    format: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    user_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get parsing options with config and user overrides.

    Args:
        format: Document format (epub, html, pdf, docx). If None, returns global parsing options.
        config: Pre-loaded config. If None, loads config automatically.
        user_options: User-provided options to merge (highest priority).

    Returns:
        Dictionary of parsing options.

    Example:
        >>> opts = get_parsing_options("epub", user_options={"extract_images": False})
        >>> print(opts["extract_images"])
        False
    """
    if config is None:
        config = load_config()

    # Get global parsing options
    parsing_config = deepcopy(config.get("parsing", {}))

    # If format specified, merge format-specific options
    if format and format in parsing_config:
        format_config = parsing_config.pop(format)
        parsing_config = _deep_merge(parsing_config, format_config)

    # Merge with user options
    if user_options:
        parsing_config = _deep_merge(parsing_config, user_options)

    return parsing_config


def create_config_template(output_path: Optional[Path] = None) -> Path:
    """
    Create a config_template.json file with default configuration.

    Args:
        output_path: Where to create the template. If None, uses project root.

    Returns:
        Path to created template file.

    Example:
        >>> template_path = create_config_template()
        >>> print(f"Template created at {template_path}")
    """
    if output_path is None:
        # Find project root
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "pyproject.toml").exists():
                output_path = parent / "config_template.json"
                break
        else:
            output_path = Path.cwd() / "config_template.json"

    with open(output_path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)

    logger.info(f"✅ Created config template at {output_path}")
    return output_path


def validate_config(config: Dict[str, Any]) -> tuple[bool, list]:
    """
    Validate configuration structure and values.

    Args:
        config: Configuration dictionary to validate.

    Returns:
        Tuple of (is_valid, error_messages).

    Example:
        >>> config = load_config()
        >>> valid, errors = validate_config(config)
        >>> if not valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """
    errors = []

    # Check required top-level keys
    required_keys = ["ai", "parsing", "ai_features"]
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    # Validate AI provider configs
    if "ai" in config:
        required_providers = ["anthropic", "openai", "ollama", "lmstudio", "openrouter"]
        for provider in required_providers:
            if provider not in config["ai"]:
                errors.append(f"Missing AI provider config: {provider}")
            else:
                provider_config = config["ai"][provider]
                if "model" not in provider_config:
                    errors.append(f"Missing 'model' in {provider} config")
                if "max_tokens" not in provider_config:
                    errors.append(f"Missing 'max_tokens' in {provider} config")

    # Validate parsing options
    if "parsing" in config:
        parsing = config["parsing"]
        if "extract_images" not in parsing:
            errors.append("Missing 'extract_images' in parsing config")
        if "clean_text" not in parsing:
            errors.append("Missing 'clean_text' in parsing config")

    return len(errors) == 0, errors


# Convenience: Load config once at module level
_cached_config: Optional[Dict[str, Any]] = None


def get_cached_config() -> Dict[str, Any]:
    """
    Get cached config (loads once, reuses for subsequent calls).

    Returns:
        Cached configuration dictionary.

    Example:
        >>> config = get_cached_config()
        >>> print(config["ai"]["default_provider"])
    """
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config


def clear_config_cache() -> None:
    """
    Clear the cached config (useful for testing or reloading).

    Example:
        >>> clear_config_cache()
        >>> config = get_cached_config()  # Reloads from files
    """
    global _cached_config
    _cached_config = None
