"""Configuration loader for mcp-this-openapi."""

import os
import re
import yaml

from .models import Config


def expand_env_vars(value: str) -> str:
    """
    Expand environment variables in configuration values.

    Args:
        value: String that may contain environment variable references

    Returns:
        String with environment variables expanded

    Raises:
        ValueError: If environment variable is not found
    """
    if not isinstance(value, str):
        return value

    # Check for environment variable pattern ${VAR_NAME}
    pattern = r'\$\{([^}]+)\}'
    matches = re.findall(pattern, value)

    for match in matches:
        env_var = match.strip()
        if env_var not in os.environ:
            raise ValueError(f"Environment variable '{env_var}' not found")

        env_value = os.environ[env_var]
        value = value.replace(f"${{{env_var}}}", env_value)

    return value


def _expand_env_vars_recursive(obj: object) -> object:
    """Recursively expand environment variables in nested structures."""
    if isinstance(obj, dict):
        return {key: _expand_env_vars_recursive(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_vars_recursive(item) for item in obj]
    if isinstance(obj, str):
        return expand_env_vars(obj)
    return obj


def load_config(config_path: str) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Validated configuration object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        ValueError: If configuration is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, encoding='utf-8') as file:
        raw_config = yaml.safe_load(file)

    if raw_config is None:
        raise ValueError("Configuration file is empty")

    # Expand environment variables recursively
    processed_config = _expand_env_vars_recursive(raw_config)

    # Validate with Pydantic
    return Config(**processed_config)

