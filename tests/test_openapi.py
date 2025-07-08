"""Tests for OpenAPI module."""

import json
import pytest
import respx
import httpx
from pathlib import Path

from mcp_this_openapi.openapi.fetcher import fetch_openapi_spec
from mcp_this_openapi.openapi.filter import filter_openapi_paths
from mcp_this_openapi.openapi.auth import create_authenticated_client
from mcp_this_openapi.config.models import AuthenticationConfig


@pytest.fixture
def simple_spec():
    """Load the simple OpenAPI spec fixture."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "openapi_specs"
    with open(fixtures_dir / "simple.json") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_fetch_openapi_spec_json():
    """Test fetching OpenAPI spec as JSON."""
    spec = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

    with respx.mock:
        respx.get("https://api.example.com/openapi.json").mock(
            return_value=httpx.Response(200, json=spec),
        )

        result = await fetch_openapi_spec("https://api.example.com/openapi.json")
        assert result == spec


@pytest.mark.asyncio
async def test_fetch_openapi_spec_yaml():
    """Test fetching OpenAPI spec as YAML."""
    yaml_content = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
"""

    with respx.mock:
        respx.get("https://api.example.com/openapi.yaml").mock(
            return_value=httpx.Response(
                200,
                content=yaml_content,
                headers={"content-type": "application/yaml"},
            ),
        )

        result = await fetch_openapi_spec("https://api.example.com/openapi.yaml")
        assert result["openapi"] == "3.0.0"
        assert result["info"]["title"] == "Test API"


@pytest.mark.asyncio
async def test_fetch_openapi_spec_http_error():
    """Test handling HTTP errors when fetching spec."""
    with respx.mock:
        respx.get("https://api.example.com/openapi.json").mock(
            return_value=httpx.Response(404),
        )

        with pytest.raises(httpx.HTTPError):
            await fetch_openapi_spec("https://api.example.com/openapi.json")


@pytest.mark.asyncio
async def test_fetch_openapi_spec_invalid_json():
    """Test handling invalid JSON response."""
    with respx.mock:
        respx.get("https://api.example.com/openapi.json").mock(
            return_value=httpx.Response(
                200,
                content="{ invalid json syntax",
                headers={"content-type": "application/json"},
            ),
        )

        with pytest.raises(json.JSONDecodeError):
            await fetch_openapi_spec("https://api.example.com/openapi.json")


def test_filter_openapi_paths_include_only(simple_spec):  # noqa: ANN001
    """Test filtering paths with include patterns only."""
    result = filter_openapi_paths(simple_spec, include_patterns=["^/users"])

    # Should include /users and /users/{userId} but not /admin/settings
    assert "/users" in result["paths"]
    assert "/users/{userId}" in result["paths"]
    assert "/admin/settings" not in result["paths"]


def test_filter_openapi_paths_exclude_only(simple_spec):  # noqa: ANN001
    """Test filtering paths with exclude patterns only."""
    result = filter_openapi_paths(simple_spec, exclude_patterns=["^/admin"])

    # Should exclude /admin/settings but include others
    assert "/users" in result["paths"]
    assert "/users/{userId}" in result["paths"]
    assert "/admin/settings" not in result["paths"]


def test_filter_openapi_paths_include_and_exclude(simple_spec):  # noqa: ANN001
    """Test filtering paths with both include and exclude patterns."""
    result = filter_openapi_paths(
        simple_spec,
        include_patterns=["^/users", "^/admin"],
        exclude_patterns=["^/admin"],
    )

    # Should include /users paths but exclude /admin paths
    assert "/users" in result["paths"]
    assert "/users/{userId}" in result["paths"]
    assert "/admin/settings" not in result["paths"]


def test_filter_openapi_paths_no_patterns(simple_spec):  # noqa: ANN001
    """Test filtering paths with no patterns (should return all)."""
    result = filter_openapi_paths(simple_spec)

    # Should include all paths
    assert "/users" in result["paths"]
    assert "/users/{userId}" in result["paths"]
    assert "/admin/settings" in result["paths"]


def test_filter_openapi_paths_no_paths():
    """Test filtering spec with no paths section."""
    spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}}

    with pytest.raises(ValueError, match="OpenAPI specification must contain a 'paths' section"):
        filter_openapi_paths(spec)


def test_filter_openapi_paths_preserves_other_sections(simple_spec):  # noqa: ANN001
    """Test that filtering preserves other sections of the spec."""
    result = filter_openapi_paths(simple_spec, include_patterns=["^/users"])

    # Should preserve info and servers sections
    assert result["openapi"] == simple_spec["openapi"]
    assert result["info"] == simple_spec["info"]
    assert result["servers"] == simple_spec["servers"]


def test_create_authenticated_client_none():
    """Test creating client with no authentication."""
    client = create_authenticated_client(None, "https://api.example.com")
    assert client.base_url == "https://api.example.com"
    assert "Authorization" not in client.headers


def test_create_authenticated_client_bearer():
    """Test creating client with bearer authentication."""
    auth_config = AuthenticationConfig(type="bearer", token="test_token")
    client = create_authenticated_client(auth_config, "https://api.example.com")

    assert client.base_url == "https://api.example.com"
    assert client.headers["Authorization"] == "Bearer test_token"


def test_create_authenticated_client_api_key():
    """Test creating client with API key authentication."""
    auth_config = AuthenticationConfig(type="api_key", api_key="test_key")
    client = create_authenticated_client(auth_config, "https://api.example.com")

    assert client.base_url == "https://api.example.com"
    assert client.headers["X-API-Key"] == "test_key"


def test_create_authenticated_client_api_key_custom_header():
    """Test creating client with API key authentication and custom header."""
    auth_config = AuthenticationConfig(
        type="api_key",
        api_key="test_key",
        header_name="Custom-API-Key",
    )
    client = create_authenticated_client(auth_config, "https://api.example.com")

    assert client.base_url == "https://api.example.com"
    assert client.headers["Custom-API-Key"] == "test_key"


def test_create_authenticated_client_basic():
    """Test creating client with basic authentication."""
    auth_config = AuthenticationConfig(
        type="basic",
        username="test_user",
        password="test_pass",
    )
    client = create_authenticated_client(auth_config, "https://api.example.com")

    assert client.base_url == "https://api.example.com"
    assert client.auth is not None
    assert isinstance(client.auth, httpx.BasicAuth)


def test_create_authenticated_client_bearer_missing_token():
    """Test error when bearer token is missing."""
    auth_config = AuthenticationConfig(type="bearer")

    with pytest.raises(ValueError, match="Bearer token is required"):
        create_authenticated_client(auth_config, "https://api.example.com")


def test_create_authenticated_client_api_key_missing_key():
    """Test error when API key is missing."""
    auth_config = AuthenticationConfig(type="api_key")

    with pytest.raises(ValueError, match="API key is required"):
        create_authenticated_client(auth_config, "https://api.example.com")


def test_create_authenticated_client_basic_missing_credentials():
    """Test error when basic auth credentials are missing."""
    auth_config = AuthenticationConfig(type="basic", username="test_user")

    with pytest.raises(ValueError, match="Username and password are required"):
        create_authenticated_client(auth_config, "https://api.example.com")


def test_create_authenticated_client_invalid_type():
    """Test error with invalid authentication type."""
    # This should fail at Pydantic validation level, but let's test the auth module
    # by creating a mock config with an invalid type
    auth_config = AuthenticationConfig(type="bearer")  # Valid for model creation
    auth_config.type = "invalid_type"  # Manually set invalid type

    with pytest.raises(ValueError, match="Unsupported authentication type"):
        create_authenticated_client(auth_config, "https://api.example.com")
