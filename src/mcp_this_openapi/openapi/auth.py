"""Authentication handler for mcp-this-openapi."""

import httpx

from ..config.models import AuthenticationConfig


def create_authenticated_client(
    auth_config: AuthenticationConfig | None,
    base_url: str,
) -> httpx.AsyncClient:
    """
    Create an authenticated HTTP client for API requests.

    Args:
        auth_config: Authentication configuration
        base_url: Base URL for the API

    Returns:
        Configured httpx.AsyncClient with authentication

    Raises:
        ValueError: If authentication configuration is invalid
    """
    headers = {}
    auth = None

    if auth_config is None or auth_config.type == "none":
        # No authentication
        pass
    elif auth_config.type == "bearer":
        if not auth_config.token:
            raise ValueError("Bearer token is required for bearer authentication")
        headers["Authorization"] = f"Bearer {auth_config.token}"
    elif auth_config.type == "api_key":
        if not auth_config.api_key:
            raise ValueError("API key is required for API key authentication")
        header_name = auth_config.header_name or "X-API-Key"
        headers[header_name] = auth_config.api_key
    elif auth_config.type == "basic":
        if not auth_config.username or not auth_config.password:
            raise ValueError("Username and password are required for basic authentication")
        auth = httpx.BasicAuth(auth_config.username, auth_config.password)
    else:
        raise ValueError(f"Unsupported authentication type: {auth_config.type}")

    return httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        auth=auth,
        timeout=30.0,
    )
