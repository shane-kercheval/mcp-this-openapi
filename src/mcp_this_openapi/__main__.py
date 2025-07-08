#!/usr/bin/env python3
"""
Entry point for mcp-this-openapi - MCP Server for OpenAPI/Swagger specifications.

This module provides the main entry point for the mcp-this-openapi package, which creates
an MCP server that generates tools from OpenAPI/Swagger specifications.
"""

import sys
import argparse
import pathlib

from .server import run_server, run_server_from_args


def find_default_config() -> str | None:
    """
    Find the default configuration file in standard locations.

    Returns:
        Optional[str]: Path to the default configuration file, or None if not found
    """
    # Check package examples directory and common locations
    package_dir = pathlib.Path(__file__).parent.parent.parent
    locations = [
        package_dir / "examples" / "configs" / "default.yaml",
        package_dir / "examples" / "configs" / "petstore.yaml",
        pathlib.Path.home() / ".config" / "mcp-this-openapi" / "config.yaml",
        pathlib.Path("/etc/mcp-this-openapi/config.yaml"),
    ]
    for location in locations:
        if location.exists():
            return str(location)
    return None


def main() -> None:
    """Run the MCP server with the specified configuration."""
    parser = argparse.ArgumentParser(description="OpenAPI/Swagger MCP Server")

    # Create mutually exclusive group for config methods
    config_group = parser.add_mutually_exclusive_group(required=False)

    config_group.add_argument(
        "--config-path",
        "--config_path",
        dest="config_path",
        type=str,
        help="Path to YAML configuration file",
    )

    config_group.add_argument(
        "--openapi-spec-url",
        dest="openapi_spec_url",
        type=str,
        help="URL to OpenAPI/Swagger specification (JSON or YAML)",
    )

    parser.add_argument(
        "--server-name",
        dest="server_name",
        type=str,
        help="Name for the MCP server (optional, defaults to 'openapi-server')",
    )

    args = parser.parse_args()

    # Handle direct CLI arguments
    if args.openapi_spec_url:
        server_name = args.server_name or "openapi-server"
        try:
            run_server_from_args(args.openapi_spec_url, server_name)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Handle config file
    config_path = args.config_path
    if not config_path:
        config_path = find_default_config()

    if not config_path:
        print("Error: No configuration found. Please provide one using:")
        print("  1. --openapi-spec-url URL [--server-name NAME]")
        print("  2. --config-path PATH (YAML file)")
        print("  3. Place a config in ~/.config/mcp-this-openapi/config.yaml")
        sys.exit(1)

    try:
        # Run the MCP server with the configuration
        run_server(config_path)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
