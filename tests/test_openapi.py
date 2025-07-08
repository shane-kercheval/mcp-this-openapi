"""Tests for OpenAPI module."""

import json
import pytest
import respx
import httpx
from pathlib import Path

from mcp_this_openapi.openapi.fetcher import fetch_openapi_spec
from mcp_this_openapi.openapi.filter import filter_openapi_paths
from mcp_this_openapi.openapi.auth import create_authenticated_client
from mcp_this_openapi.openapi.url_utils import extract_base_url
from mcp_this_openapi.config.models import AuthenticationConfig


@pytest.fixture
def simple_spec():
    """Load the simple OpenAPI spec fixture."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "openapi_specs"
    with open(fixtures_dir / "simple.json") as f:
        return json.load(f)


@pytest.fixture
def multi_method_spec():
    """Load the multi-method OpenAPI spec fixture."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "openapi_specs"
    with open(fixtures_dir / "multi_method.json") as f:
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


def test_filter_openapi_methods_include_only(multi_method_spec):  # noqa: ANN001
    """Test filtering methods with include patterns only."""
    result = filter_openapi_paths(multi_method_spec, include_methods=["GET", "POST"])

    # Should include GET and POST methods but not PUT, DELETE, PATCH
    assert "get" in result["paths"]["/users"]
    assert "post" in result["paths"]["/users"]

    assert "get" in result["paths"]["/users/{userId}"]
    assert "put" not in result["paths"]["/users/{userId}"]
    assert "delete" not in result["paths"]["/users/{userId}"]

    assert "get" in result["paths"]["/admin/users"]
    assert "post" in result["paths"]["/admin/users"]
    assert "patch" not in result["paths"]["/admin/users"]


def test_filter_openapi_methods_exclude_only(multi_method_spec):  # noqa: ANN001
    """Test filtering methods with exclude patterns only."""
    result = filter_openapi_paths(multi_method_spec, exclude_methods=["DELETE", "PUT"])

    # Should exclude DELETE and PUT methods but include others
    assert "get" in result["paths"]["/users"]
    assert "post" in result["paths"]["/users"]

    assert "get" in result["paths"]["/users/{userId}"]
    assert "put" not in result["paths"]["/users/{userId}"]
    assert "delete" not in result["paths"]["/users/{userId}"]

    assert "get" in result["paths"]["/admin/users"]
    assert "post" in result["paths"]["/admin/users"]
    assert "patch" in result["paths"]["/admin/users"]


def test_filter_openapi_methods_include_and_exclude(multi_method_spec):  # noqa: ANN001
    """Test filtering methods with both include and exclude patterns."""
    result = filter_openapi_paths(
        multi_method_spec,
        include_methods=["GET", "POST", "PUT"],
        exclude_methods=["PUT"],
    )

    # Should include GET and POST but exclude PUT (exclude takes precedence)
    assert "get" in result["paths"]["/users"]
    assert "post" in result["paths"]["/users"]

    assert "get" in result["paths"]["/users/{userId}"]
    assert "put" not in result["paths"]["/users/{userId}"]
    assert "delete" not in result["paths"]["/users/{userId}"]


def test_filter_openapi_methods_case_insensitive(multi_method_spec):  # noqa: ANN001
    """Test that method filtering is case insensitive."""
    result = filter_openapi_paths(multi_method_spec, include_methods=["get", "Post"])

    # Should work with mixed case
    assert "get" in result["paths"]["/users"]
    assert "post" in result["paths"]["/users"]
    assert "get" in result["paths"]["/users/{userId}"]
    assert "put" not in result["paths"]["/users/{userId}"]


def test_filter_openapi_paths_and_methods_combined(multi_method_spec):  # noqa: ANN001
    """Test filtering both paths and methods together."""
    result = filter_openapi_paths(
        multi_method_spec,
        include_patterns=["^/users"],
        exclude_patterns=["^/admin"],
        include_methods=["GET", "POST"],
    )

    # Should include /users paths but exclude /admin paths
    assert "/users" in result["paths"]
    assert "/users/{userId}" in result["paths"]
    assert "/admin/users" not in result["paths"]

    # Should only include GET and POST methods
    assert "get" in result["paths"]["/users"]
    assert "post" in result["paths"]["/users"]
    assert "get" in result["paths"]["/users/{userId}"]
    assert "put" not in result["paths"]["/users/{userId}"]
    assert "delete" not in result["paths"]["/users/{userId}"]


def test_filter_openapi_methods_removes_empty_paths(multi_method_spec):  # noqa: ANN001
    """Test that paths with no remaining methods are removed."""
    result = filter_openapi_paths(multi_method_spec, include_methods=["HEAD"])

    # Since none of the paths have HEAD methods, all paths should be removed
    assert len(result["paths"]) == 0


def test_filter_openapi_methods_preserves_non_method_properties(multi_method_spec):  # noqa: ANN001
    """Test that non-HTTP method properties are preserved."""
    # Add a non-method property to test preservation
    test_spec = multi_method_spec.copy()
    test_spec["paths"]["/users"]["summary"] = "Users endpoint"
    test_spec["paths"]["/users"]["description"] = "Manages user resources"

    result = filter_openapi_paths(test_spec, include_methods=["GET"])

    # Should preserve non-method properties
    assert result["paths"]["/users"]["summary"] == "Users endpoint"
    assert result["paths"]["/users"]["description"] == "Manages user resources"
    assert "get" in result["paths"]["/users"]
    assert "post" not in result["paths"]["/users"]


def test_filter_openapi_methods_no_methods_specified(multi_method_spec):  # noqa: ANN001
    """Test that when no method filters are specified, defaults to GET-only for safety."""
    result = filter_openapi_paths(multi_method_spec)

    # Should default to GET-only when no method filtering is specified
    assert "get" in result["paths"]["/users"]
    assert "post" not in result["paths"]["/users"]
    assert "get" in result["paths"]["/users/{userId}"]
    assert "put" not in result["paths"]["/users/{userId}"]
    assert "delete" not in result["paths"]["/users/{userId}"]
    assert "get" in result["paths"]["/admin/users"]
    assert "patch" not in result["paths"]["/admin/users"]


def test_filter_openapi_methods_explicit_all_methods(multi_method_spec):  # noqa: ANN001
    """Test that users can explicitly include all methods to override GET-only default."""
    result = filter_openapi_paths(
        multi_method_spec,
        include_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )

    # Should include all methods when explicitly specified
    assert "get" in result["paths"]["/users"]
    assert "post" in result["paths"]["/users"]
    assert "get" in result["paths"]["/users/{userId}"]
    assert "put" in result["paths"]["/users/{userId}"]
    assert "delete" in result["paths"]["/users/{userId}"]
    assert "get" in result["paths"]["/admin/users"]
    assert "patch" in result["paths"]["/admin/users"]


def test_filter_openapi_methods_exclude_overrides_default(multi_method_spec):  # noqa: ANN001
    """Test that exclude_methods overrides the GET-only default."""
    result = filter_openapi_paths(multi_method_spec, exclude_methods=["GET"])

    # Should exclude GET and include all other methods when exclude is specified
    assert "get" not in result["paths"]["/users"]
    assert "post" in result["paths"]["/users"]
    assert "get" not in result["paths"]["/users/{userId}"]
    assert "put" in result["paths"]["/users/{userId}"]
    assert "delete" in result["paths"]["/users/{userId}"]


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


def test_extract_base_url_with_servers():
    """Test extracting base URL when servers field is present."""
    spec = {
        "servers": [
            {"url": "https://api.example.com/v1"},
            {"url": "https://api.example.com/v2"},
        ],
    }

    result = extract_base_url(spec, "https://docs.example.com/openapi.json")
    assert result == "https://api.example.com/v1"


def test_extract_base_url_with_relative_server():
    """Test extracting base URL when server URL is relative."""
    spec = {
        "servers": [
            {"url": "/api/v1"},
        ],
    }

    result = extract_base_url(spec, "https://docs.example.com/openapi.json")
    assert result == "https://docs.example.com/api/v1"


def test_extract_base_url_no_servers():
    """Test extracting base URL when no servers field exists."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
    }

    result = extract_base_url(spec, "https://api.example.com/openapi.json")
    assert result == "https://api.example.com"


def test_extract_base_url_empty_servers():
    """Test extracting base URL when servers field is empty array."""
    spec = {
        "servers": [],
    }

    result = extract_base_url(spec, "https://api.example.com/docs/openapi.json")
    assert result == "https://api.example.com"


def test_extract_base_url_complex_spec_url():
    """Test extracting base URL from complex spec URL with path."""
    spec = {
        "openapi": "3.0.0",
    }

    result = extract_base_url(
        spec,
        "https://my-service-dev.my_server-12345.westus.apps.io/openapi.json",
    )
    assert result == "https://my-service-dev.my_server-12345.westus.apps.io"


def test_extract_base_url_with_port():
    """Test extracting base URL that includes port number."""
    spec = {}

    result = extract_base_url(spec, "https://api.example.com:8080/openapi.json")
    assert result == "https://api.example.com:8080"


def test_extract_base_url_http_scheme():
    """Test extracting base URL with HTTP scheme."""
    spec = {}

    result = extract_base_url(spec, "http://api.example.com/openapi.json")
    assert result == "http://api.example.com"
