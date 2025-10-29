"""
Secrets management for OmniParser.

This module handles loading API keys and sensitive configuration from multiple sources:
1. secrets.json (primary, gitignored)
2. secrets_local.json (local overrides, gitignored)
3. Environment variables (fallback)

Example:
    >>> secrets = load_secrets()
    >>> api_key = secrets.get("anthropic_api_key")
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def load_secrets(secrets_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load secrets from JSON files with environment variable fallback.

    This function implements a fallback chain for loading secrets:
    1. secrets_local.json (highest priority, for local development)
    2. secrets.json (primary secrets file)
    3. Environment variables (fallback)

    Args:
        secrets_dir: Directory containing secrets files. If None, uses project root
                    (determined by walking up from this file's location).

    Returns:
        Dictionary containing all secrets from all sources (merged).

    Example:
        >>> secrets = load_secrets()
        >>> api_key = secrets.get("anthropic_api_key")
        >>> if not api_key:
        ...     print("Warning: No API key found")
    """
    if secrets_dir is None:
        # Find project root (directory containing pyproject.toml)
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "pyproject.toml").exists():
                secrets_dir = parent
                break
        else:
            # Fallback to current directory
            secrets_dir = Path.cwd()

    secrets: Dict[str, Any] = {}

    # Try loading secrets.json (primary)
    secrets_path = secrets_dir / "secrets.json"
    if secrets_path.exists():
        try:
            with open(secrets_path, "r") as f:
                loaded = json.load(f)
                secrets.update(loaded)
                logger.info(f"✅ Loaded secrets from {secrets_path}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing {secrets_path}: {e}")
        except Exception as e:
            logger.error(f"❌ Error reading {secrets_path}: {e}")
    else:
        logger.info(f"ℹ️  No secrets.json found at {secrets_path}")

    # Try loading secrets_local.json (overrides)
    secrets_local_path = secrets_dir / "secrets_local.json"
    if secrets_local_path.exists():
        try:
            with open(secrets_local_path, "r") as f:
                loaded = json.load(f)
                secrets.update(loaded)  # Overrides secrets.json
                logger.info(f"✅ Loaded local secrets from {secrets_local_path}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing {secrets_local_path}: {e}")
        except Exception as e:
            logger.error(f"❌ Error reading {secrets_local_path}: {e}")

    # Add environment variables as fallback (don't override file-based secrets)
    env_keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "OLLAMA_BASE_URL",
        "LMSTUDIO_BASE_URL",
    ]

    for key in env_keys:
        # Convert to lowercase for consistency
        secret_key = key.lower()

        # Only use env var if not already set from files
        if secret_key not in secrets:
            env_value = os.getenv(key)
            if env_value:
                secrets[secret_key] = env_value
                logger.debug(f"Using {key} from environment variable")

    if not secrets:
        logger.warning(
            "⚠️  No secrets loaded from any source. "
            "Create secrets.json or set environment variables."
        )

    return secrets


def get_secret(
    key: str,
    secrets: Optional[Dict[str, Any]] = None,
    required: bool = False,
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Get a specific secret by key with validation.

    Args:
        key: Secret key to retrieve (e.g., "anthropic_api_key")
        secrets: Pre-loaded secrets dictionary. If None, loads secrets automatically.
        required: If True, raises ValueError when secret is missing.
        default: Default value if secret not found (only used when not required).

    Returns:
        Secret value or None if not found (when not required).

    Raises:
        ValueError: If required=True and secret not found.

    Example:
        >>> api_key = get_secret("anthropic_api_key", required=True)
        >>> optional = get_secret("some_key", default="fallback")
    """
    if secrets is None:
        secrets = load_secrets()

    value = secrets.get(key)

    if value is None or value == "":
        if required:
            raise ValueError(
                f"Required secret '{key}' not found. "
                f"Add it to secrets.json or set {key.upper()} environment variable."
            )
        return default

    return str(value) if value is not None else default


def validate_secrets(
    secrets: Dict[str, Any],
    required_keys: Optional[list[str]] = None,
) -> tuple[bool, list[str]]:
    """
    Validate that required secrets are present and non-empty.

    Args:
        secrets: Secrets dictionary to validate.
        required_keys: List of keys that must be present. If None, no validation.

    Returns:
        Tuple of (is_valid, missing_keys).

    Example:
        >>> secrets = load_secrets()
        >>> valid, missing = validate_secrets(secrets, ["anthropic_api_key"])
        >>> if not valid:
        ...     print(f"Missing keys: {missing}")
    """
    if required_keys is None:
        return True, []

    missing = []
    for key in required_keys:
        value = secrets.get(key)
        if value is None or value == "":
            missing.append(key)

    return len(missing) == 0, missing


def create_secrets_template(output_path: Optional[Path] = None) -> Path:
    """
    Create a secrets_template.json file with all supported keys.

    Args:
        output_path: Where to create the template. If None, uses project root.

    Returns:
        Path to created template file.

    Example:
        >>> template_path = create_secrets_template()
        >>> print(f"Template created at {template_path}")
    """
    if output_path is None:
        # Find project root
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "pyproject.toml").exists():
                output_path = parent / "secrets_template.json"
                break
        else:
            output_path = Path.cwd() / "secrets_template.json"

    template = {
        "comment": "Copy this file to secrets.json or secrets_local.json and add your API keys",
        "anthropic_api_key": "",
        "openai_api_key": "",
        "openrouter_api_key": "",
        "ollama_base_url": "http://localhost:11434/v1",
        "lmstudio_base_url": "http://localhost:1234/v1",
    }

    with open(output_path, "w") as f:
        json.dump(template, f, indent=2)

    logger.info(f"✅ Created secrets template at {output_path}")
    return output_path


# Convenience: Load secrets once at module level
_cached_secrets: Optional[Dict[str, Any]] = None


def get_cached_secrets() -> Dict[str, Any]:
    """
    Get cached secrets (loads once, reuses for subsequent calls).

    Returns:
        Cached secrets dictionary.

    Example:
        >>> secrets = get_cached_secrets()
        >>> api_key = secrets.get("anthropic_api_key")
    """
    global _cached_secrets
    if _cached_secrets is None:
        _cached_secrets = load_secrets()
    return _cached_secrets


def clear_secrets_cache() -> None:
    """
    Clear the cached secrets (useful for testing or reloading).

    Example:
        >>> clear_secrets_cache()
        >>> secrets = get_cached_secrets()  # Reloads from files
    """
    global _cached_secrets
    _cached_secrets = None
