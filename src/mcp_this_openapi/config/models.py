"""Configuration models for mcp-this-openapi."""

from typing import Literal
from pydantic import BaseModel


class ServerConfig(BaseModel):
    """Configuration for the MCP server."""

    name: str


class OpenAPIConfig(BaseModel):
    """Configuration for OpenAPI specification."""

    spec_url: str


class AuthenticationConfig(BaseModel):
    """Configuration for API authentication."""

    type: Literal["bearer", "api_key", "basic", "none"]
    token: str | None = None
    api_key: str | None = None
    header_name: str | None = "X-API-Key"
    username: str | None = None
    password: str | None = None


class Config(BaseModel):
    """Main configuration model."""

    server: ServerConfig
    openapi: OpenAPIConfig
    authentication: AuthenticationConfig | None = None
    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = None
    include_methods: list[str] | None = None
    exclude_methods: list[str] | None = None
