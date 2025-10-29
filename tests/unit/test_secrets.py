"""
Unit tests for secrets management module.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from omniparser.utils.secrets import (
    load_secrets,
    get_secret,
    validate_secrets,
    create_secrets_template,
    get_cached_secrets,
    clear_secrets_cache,
)


@pytest.fixture
def temp_secrets_dir(tmp_path):
    """Create temporary directory for secrets files."""
    secrets_dir = tmp_path / "test_project"
    secrets_dir.mkdir()
    # Create fake pyproject.toml to mark as project root
    (secrets_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
    return secrets_dir


@pytest.fixture
def secrets_data():
    """Sample secrets data."""
    return {
        "anthropic_api_key": "sk-ant-test123",
        "openai_api_key": "sk-test456",
        "ollama_base_url": "http://localhost:11434/v1",
    }


class TestLoadSecrets:
    """Tests for load_secrets function."""

    def test_load_secrets_from_file(self, temp_secrets_dir, secrets_data):
        """Test loading secrets from secrets.json."""
        secrets_path = temp_secrets_dir / "secrets.json"
        with open(secrets_path, "w") as f:
            json.dump(secrets_data, f)

        secrets = load_secrets(temp_secrets_dir)

        assert secrets["anthropic_api_key"] == "sk-ant-test123"
        assert secrets["openai_api_key"] == "sk-test456"
        assert secrets["ollama_base_url"] == "http://localhost:11434/v1"

    def test_load_secrets_local_overrides(self, temp_secrets_dir, secrets_data):
        """Test that secrets_local.json overrides secrets.json."""
        # Write secrets.json
        secrets_path = temp_secrets_dir / "secrets.json"
        with open(secrets_path, "w") as f:
            json.dump(secrets_data, f)

        # Write secrets_local.json with override
        local_data = {"anthropic_api_key": "sk-ant-local999"}
        local_path = temp_secrets_dir / "secrets_local.json"
        with open(local_path, "w") as f:
            json.dump(local_data, f)

        secrets = load_secrets(temp_secrets_dir)

        # Local should override
        assert secrets["anthropic_api_key"] == "sk-ant-local999"
        # Other keys should remain from secrets.json
        assert secrets["openai_api_key"] == "sk-test456"

    def test_load_secrets_from_env(self, temp_secrets_dir, monkeypatch):
        """Test loading secrets from environment variables."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env123")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env456")

        secrets = load_secrets(temp_secrets_dir)

        assert secrets["anthropic_api_key"] == "sk-ant-env123"
        assert secrets["openai_api_key"] == "sk-env456"

    def test_file_takes_precedence_over_env(self, temp_secrets_dir, secrets_data, monkeypatch):
        """Test that secrets.json takes precedence over environment variables."""
        # Set env var
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env123")

        # Write secrets.json
        secrets_path = temp_secrets_dir / "secrets.json"
        with open(secrets_path, "w") as f:
            json.dump(secrets_data, f)

        secrets = load_secrets(temp_secrets_dir)

        # File should take precedence
        assert secrets["anthropic_api_key"] == "sk-ant-test123"

    def test_load_secrets_no_files_no_env(self, temp_secrets_dir):
        """Test loading secrets when no files or env vars exist."""
        secrets = load_secrets(temp_secrets_dir)
        assert secrets == {}

    def test_load_secrets_malformed_json(self, temp_secrets_dir):
        """Test handling of malformed JSON."""
        secrets_path = temp_secrets_dir / "secrets.json"
        secrets_path.write_text("{invalid json")

        # Should not crash, just return empty dict
        secrets = load_secrets(temp_secrets_dir)
        assert secrets == {}


class TestGetSecret:
    """Tests for get_secret function."""

    def test_get_secret_existing(self, temp_secrets_dir, secrets_data):
        """Test getting an existing secret."""
        secrets_path = temp_secrets_dir / "secrets.json"
        with open(secrets_path, "w") as f:
            json.dump(secrets_data, f)

        value = get_secret("anthropic_api_key", secrets=load_secrets(temp_secrets_dir))
        assert value == "sk-ant-test123"

    def test_get_secret_missing_required(self, temp_secrets_dir):
        """Test getting a required secret that doesn't exist."""
        secrets = load_secrets(temp_secrets_dir)

        with pytest.raises(ValueError, match="Required secret 'missing_key' not found"):
            get_secret("missing_key", secrets=secrets, required=True)

    def test_get_secret_missing_optional(self, temp_secrets_dir):
        """Test getting an optional secret that doesn't exist."""
        secrets = load_secrets(temp_secrets_dir)
        value = get_secret("missing_key", secrets=secrets, required=False)
        assert value is None

    def test_get_secret_with_default(self, temp_secrets_dir):
        """Test getting a secret with default value."""
        secrets = load_secrets(temp_secrets_dir)
        value = get_secret("missing_key", secrets=secrets, default="fallback")
        assert value == "fallback"

    def test_get_secret_empty_string_is_missing(self, temp_secrets_dir):
        """Test that empty strings are treated as missing."""
        secrets_path = temp_secrets_dir / "secrets.json"
        with open(secrets_path, "w") as f:
            json.dump({"anthropic_api_key": ""}, f)

        secrets = load_secrets(temp_secrets_dir)

        with pytest.raises(ValueError):
            get_secret("anthropic_api_key", secrets=secrets, required=True)


class TestValidateSecrets:
    """Tests for validate_secrets function."""

    def test_validate_secrets_all_present(self, secrets_data):
        """Test validation when all required keys present."""
        required = ["anthropic_api_key", "openai_api_key"]
        valid, missing = validate_secrets(secrets_data, required)

        assert valid is True
        assert missing == []

    def test_validate_secrets_some_missing(self, secrets_data):
        """Test validation when some keys are missing."""
        required = ["anthropic_api_key", "missing_key", "another_missing"]
        valid, missing = validate_secrets(secrets_data, required)

        assert valid is False
        assert "missing_key" in missing
        assert "another_missing" in missing
        assert "anthropic_api_key" not in missing

    def test_validate_secrets_empty_string_is_invalid(self):
        """Test that empty string values are considered invalid."""
        secrets = {"api_key": ""}
        required = ["api_key"]
        valid, missing = validate_secrets(secrets, required)

        assert valid is False
        assert "api_key" in missing

    def test_validate_secrets_no_required_keys(self, secrets_data):
        """Test validation with no required keys (should always pass)."""
        valid, missing = validate_secrets(secrets_data, None)

        assert valid is True
        assert missing == []


class TestCreateSecretsTemplate:
    """Tests for create_secrets_template function."""

    def test_create_secrets_template(self, temp_secrets_dir):
        """Test creating secrets template file."""
        output_path = temp_secrets_dir / "secrets_template.json"
        result = create_secrets_template(output_path)

        assert result == output_path
        assert output_path.exists()

        # Load and verify content
        with open(output_path, "r") as f:
            template = json.load(f)

        assert "anthropic_api_key" in template
        assert "openai_api_key" in template
        assert "ollama_base_url" in template
        assert template["anthropic_api_key"] == ""  # Should be empty


class TestCachedSecrets:
    """Tests for cached secrets functions."""

    def test_get_cached_secrets(self, temp_secrets_dir, secrets_data, monkeypatch):
        """Test getting cached secrets."""
        # Clear any existing cache
        clear_secrets_cache()

        # Mock load_secrets to return our test data
        monkeypatch.setattr(
            "omniparser.utils.secrets.load_secrets",
            lambda secrets_dir=None: secrets_data,
        )

        # First call should load
        secrets1 = get_cached_secrets()
        # Second call should use cache (same object)
        secrets2 = get_cached_secrets()

        assert secrets1 == secrets_data
        assert secrets1 is secrets2  # Same object reference

    def test_clear_secrets_cache(self, monkeypatch):
        """Test clearing secrets cache."""
        clear_secrets_cache()

        call_count = 0

        def mock_load_secrets(secrets_dir=None):
            nonlocal call_count
            call_count += 1
            return {"key": f"value_{call_count}"}

        monkeypatch.setattr("omniparser.utils.secrets.load_secrets", mock_load_secrets)

        # First call
        secrets1 = get_cached_secrets()
        assert call_count == 1

        # Second call (cached)
        secrets2 = get_cached_secrets()
        assert call_count == 1  # Not called again
        assert secrets1 is secrets2

        # Clear cache and call again
        clear_secrets_cache()
        secrets3 = get_cached_secrets()
        assert call_count == 2  # Called again
        assert secrets3 != secrets1  # Different values


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_secrets_workflow(self, temp_secrets_dir, secrets_data, monkeypatch):
        """Test complete secrets loading workflow with all sources."""
        # Set environment variable
        monkeypatch.setenv("LMSTUDIO_BASE_URL", "http://env:5678/v1")

        # Create secrets.json
        secrets_path = temp_secrets_dir / "secrets.json"
        with open(secrets_path, "w") as f:
            json.dump(secrets_data, f)

        # Create secrets_local.json with override
        local_path = temp_secrets_dir / "secrets_local.json"
        with open(local_path, "w") as f:
            json.dump({"openai_api_key": "sk-local-override"}, f)

        # Load secrets
        secrets = load_secrets(temp_secrets_dir)

        # Verify priority: local > file > env
        assert secrets["openai_api_key"] == "sk-local-override"  # From local
        assert secrets["anthropic_api_key"] == "sk-ant-test123"  # From secrets.json
        assert secrets["lmstudio_base_url"] == "http://env:5678/v1"  # From env

        # Test validation
        required = ["anthropic_api_key", "openai_api_key"]
        valid, missing = validate_secrets(secrets, required)
        assert valid is True

        # Test get_secret
        api_key = get_secret("anthropic_api_key", secrets=secrets, required=True)
        assert api_key == "sk-ant-test123"
