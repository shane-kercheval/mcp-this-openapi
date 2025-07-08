"""Tests for configuration module."""

import os
import tempfile
from pydantic import ValidationError
import pytest
from pathlib import Path

from mcp_this_openapi.config.loader import load_config, expand_env_vars


def test_expand_env_vars():
    """Test environment variable expansion."""
    os.environ["TEST_VAR"] = "test_value"

    # Test basic expansion
    result = expand_env_vars("${TEST_VAR}")
    assert result == "test_value"

    # Test expansion in larger string
    result = expand_env_vars("prefix_${TEST_VAR}_suffix")
    assert result == "prefix_test_value_suffix"

    # Test no expansion needed
    result = expand_env_vars("no_vars_here")
    assert result == "no_vars_here"

    # Test missing environment variable
    with pytest.raises(ValueError, match="Environment variable 'MISSING_VAR' not found"):
        expand_env_vars("${MISSING_VAR}")


def test_load_config_basic():
    """Test basic config loading."""
    config_content = """
server:
  name: "test-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
authentication:
  type: "none"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config.server.name == "test-server"
        assert config.openapi.spec_url == "https://api.example.com/openapi.json"
        assert config.authentication.type == "none"
    finally:
        os.unlink(temp_path)


def test_load_config_with_env_vars():
    """Test config loading with environment variables."""
    os.environ["TEST_TOKEN"] = "secret_token"
    os.environ["TEST_SERVER_NAME"] = "env-server"

    config_content = """
server:
  name: "${TEST_SERVER_NAME}"
openapi:
  spec_url: "https://api.example.com/openapi.json"
authentication:
  type: "bearer"
  token: "${TEST_TOKEN}"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config.server.name == "env-server"
        assert config.authentication.token == "secret_token"
    finally:
        os.unlink(temp_path)


def test_load_config_with_patterns():
    """Test config loading with include/exclude patterns."""
    config_content = """
server:
  name: "pattern-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
authentication:
  type: "none"
include_patterns: ["^/api", "^/users"]
exclude_patterns: ["^/admin"]
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config.include_patterns == ["^/api", "^/users"]
        assert config.exclude_patterns == ["^/admin"]
    finally:
        os.unlink(temp_path)


def test_load_config_file_not_found():
    """Test error when config file doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config("/nonexistent/path.yaml")


def test_load_config_empty_file():
    """Test error when config file is empty."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Configuration file is empty"):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_config_invalid_yaml():
    """Test error when YAML is invalid."""
    config_content = """
server:
  name: "test-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
authentication:
  type: "invalid_type"  # This will fail Pydantic validation
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        with pytest.raises(ValidationError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_fixture_configs():
    """Test loading the fixture configs."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "configs"

    # Test petstore config
    petstore_config = load_config(str(fixtures_dir / "petstore.yaml"))
    assert petstore_config.server.name == "petstore-test"
    assert petstore_config.authentication.type == "none"

    # Test github config (will fail if GITHUB_TOKEN not set, which is expected)
    if "GITHUB_TOKEN" in os.environ:
        github_config = load_config(str(fixtures_dir / "github.yaml"))
        assert github_config.server.name == "github-test"
        assert github_config.authentication.type == "bearer"
        assert github_config.include_patterns == ["^/repos", "^/user"]
        assert github_config.exclude_patterns == ["^/admin"]
