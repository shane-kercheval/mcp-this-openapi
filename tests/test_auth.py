"""Tests for authentication module."""

import pytest
import httpx

from mcp_this_openapi.config.models import AuthenticationConfig
from mcp_this_openapi.openapi.auth import create_authenticated_client


class TestAuthenticationClient:
    """Test authentication client creation."""

    def test_create_client_no_auth(self):
        """Test creating client with no authentication."""
        client = create_authenticated_client(None, "https://api.example.com")

        assert isinstance(client, httpx.AsyncClient)
        assert str(client.base_url) == "https://api.example.com"
        assert "Authorization" not in client.headers

    def test_create_client_none_auth(self):
        """Test creating client with explicit none authentication."""
        auth_config = AuthenticationConfig(type="none")
        client = create_authenticated_client(auth_config, "https://api.example.com")

        assert isinstance(client, httpx.AsyncClient)
        assert str(client.base_url) == "https://api.example.com"
        assert "Authorization" not in client.headers

    def test_create_client_bearer_auth(self):
        """Test creating client with bearer authentication."""
        auth_config = AuthenticationConfig(type="bearer", token="test-token-123")
        client = create_authenticated_client(auth_config, "https://api.example.com")

        assert isinstance(client, httpx.AsyncClient)
        assert str(client.base_url) == "https://api.example.com"
        assert client.headers["Authorization"] == "Bearer test-token-123"

    def test_create_client_api_key_auth(self):
        """Test creating client with API key authentication."""
        auth_config = AuthenticationConfig(type="api_key", api_key="secret-key")
        client = create_authenticated_client(auth_config, "https://api.example.com")

        assert isinstance(client, httpx.AsyncClient)
        assert str(client.base_url) == "https://api.example.com"
        assert client.headers["X-API-Key"] == "secret-key"

    def test_create_client_api_key_custom_header(self):
        """Test creating client with API key and custom header name."""
        auth_config = AuthenticationConfig(
            type="api_key",
            api_key="secret-key",
            header_name="Custom-API-Key",
        )
        client = create_authenticated_client(auth_config, "https://api.example.com")

        assert isinstance(client, httpx.AsyncClient)
        assert str(client.base_url) == "https://api.example.com"
        assert client.headers["Custom-API-Key"] == "secret-key"
        assert "X-API-Key" not in client.headers

    def test_create_client_basic_auth(self):
        """Test creating client with basic authentication."""
        auth_config = AuthenticationConfig(
            type="basic",
            username="testuser",
            password="testpass",
        )
        client = create_authenticated_client(auth_config, "https://api.example.com")

        assert isinstance(client, httpx.AsyncClient)
        assert str(client.base_url) == "https://api.example.com"
        assert client.auth is not None
        assert isinstance(client.auth, httpx.BasicAuth)

    def test_bearer_auth_missing_token(self):
        """Test error when bearer token is missing."""
        auth_config = AuthenticationConfig(type="bearer")

        with pytest.raises(ValueError, match="Bearer token is required"):
            create_authenticated_client(auth_config, "https://api.example.com")

    def test_api_key_auth_missing_key(self):
        """Test error when API key is missing."""
        auth_config = AuthenticationConfig(type="api_key")

        with pytest.raises(ValueError, match="API key is required"):
            create_authenticated_client(auth_config, "https://api.example.com")

    def test_basic_auth_missing_username(self):
        """Test error when basic auth username is missing."""
        auth_config = AuthenticationConfig(type="basic", password="testpass")

        with pytest.raises(ValueError, match="Username and password are required"):
            create_authenticated_client(auth_config, "https://api.example.com")

    def test_basic_auth_missing_password(self):
        """Test error when basic auth password is missing."""
        auth_config = AuthenticationConfig(type="basic", username="testuser")

        with pytest.raises(ValueError, match="Username and password are required"):
            create_authenticated_client(auth_config, "https://api.example.com")

    def test_client_timeout_configuration(self):
        """Test that client is configured with proper timeout."""
        auth_config = AuthenticationConfig(type="none")
        client = create_authenticated_client(auth_config, "https://api.example.com")

        assert client.timeout.connect == 30.0
        assert client.timeout.read == 30.0
        assert client.timeout.write == 30.0
        assert client.timeout.pool == 30.0

    def test_client_base_url_trailing_slash(self):
        """Test client with base URL that has trailing slash."""
        auth_config = AuthenticationConfig(type="none")
        client = create_authenticated_client(auth_config, "https://api.example.com/")

        assert str(client.base_url) == "https://api.example.com/"

    def test_client_base_url_with_path(self):
        """Test client with base URL that includes a path."""
        auth_config = AuthenticationConfig(type="none")
        client = create_authenticated_client(auth_config, "https://api.example.com/v1")

        # httpx may add trailing slash, so check that the path is preserved
        assert str(client.base_url).startswith("https://api.example.com/v1")
