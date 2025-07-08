#!/usr/bin/env python3
"""
Entry point for mcp-this-openapi - MCP Server for OpenAPI/Swagger specifications.

This module provides the main entry point for the mcp-this-openapi package, which creates
an MCP server that generates tools from OpenAPI/Swagger specifications.
"""

import sys
import argparse
import pathlib

from .server import run_server


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
    parser.add_argument(
        "--config-path",
        "--config_path",
        dest="config_path",
        type=str,
        help="Path to YAML configuration file",
    )
    args = parser.parse_args()

    # Set config path from argument or look for default config
    config_path = args.config_path

    if not config_path:
        config_path = find_default_config()

    if not config_path:
        print("Error: No configuration found. Please provide one using:")
        print("  1. --config-path argument (YAML file)")
        print("  2. Place a config in ~/.config/mcp-this-openapi/config.yaml")
        print("  3. Use the example petstore config in examples/configs/")
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
