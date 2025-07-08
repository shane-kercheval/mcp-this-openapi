"""Main server for mcp-this-openapi."""

import sys
from fastmcp import FastMCP
import asyncio

from .config.models import Config, ServerConfig, OpenAPIConfig, AuthenticationConfig
from .config.loader import load_config
from .openapi.fetcher import fetch_openapi_spec
from .openapi.filter import filter_openapi_paths
from .openapi.auth import create_authenticated_client
from .openapi.url_utils import extract_base_url


async def create_mcp_server(config: Config) -> FastMCP:
    """
    Create an MCP server from OpenAPI configuration.

    Args:
        config: Configuration object

    Returns:
        Configured FastMCP server

    Raises:
        ValueError: If OpenAPI spec is invalid or missing required fields
    """
    # Fetch OpenAPI spec
    spec = await fetch_openapi_spec(config.openapi.spec_url)

    # Always apply filtering (includes GET-only default when no method filtering specified)
    spec = filter_openapi_paths(
        spec,
        config.include_patterns,
        config.exclude_patterns,
        config.include_methods,
        config.exclude_methods,
    )

    # Extract base URL from spec
    base_url = extract_base_url(spec, config.openapi.spec_url)

    # Create authenticated client
    client = create_authenticated_client(config.authentication, base_url)

    # Create FastMCP server
    return FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name=config.server.name,
    )


def run_server(config_path: str) -> None:
    """
    Run the MCP server with the given configuration.

    Args:
        config_path: Path to the configuration file

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """

    async def _run_server():  # noqa: ANN202
        # Load configuration
        config = load_config(config_path)

        # Log to stderr so it doesn't interfere with MCP protocol
        print(f"Starting MCP server '{config.server.name}' with OpenAPI spec from {config.openapi.spec_url}", file=sys.stderr)  # noqa: E501

        # Create server
        server = await create_mcp_server(config)

        print(f"🚀 MCP server '{config.server.name}' is running", file=sys.stderr)
        return server

    # Run async setup and then start server
    server = asyncio.run(_run_server())
    server.run()


def run_server_from_args(openapi_spec_url: str, server_name: str) -> None:
    """
    Run the MCP server with direct CLI arguments.

    Args:
        openapi_spec_url: URL to the OpenAPI specification
        server_name: Name for the MCP server

    Raises:
        ValueError: If arguments are invalid
    """

    async def _run_server():  # noqa: ANN202
        # Create a minimal config from arguments
        config = Config(
            server=ServerConfig(name=server_name),
            openapi=OpenAPIConfig(spec_url=openapi_spec_url),
            authentication=AuthenticationConfig(type="none"),
        )

        # Log to stderr so it doesn't interfere with MCP protocol
        print(f"Starting MCP server '{config.server.name}' with OpenAPI spec from {config.openapi.spec_url}", file=sys.stderr)  # noqa: E501

        # Create server
        server = await create_mcp_server(config)

        print(f"🚀 MCP server '{config.server.name}' is running", file=sys.stderr)
        return server

    # Run async setup and then start server
    server = asyncio.run(_run_server())
    server.run()
