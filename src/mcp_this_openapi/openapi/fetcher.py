"""OpenAPI specification fetcher for mcp-this-openapi."""

import json
from typing import Any
import httpx
import yaml


async def fetch_openapi_spec(url: str) -> dict[str, Any]:
    """
    Fetch OpenAPI specification from a URL.

    Args:
        url: URL to fetch the OpenAPI specification from

    Returns:
        OpenAPI specification as a dictionary

    Raises:
        httpx.HTTPError: If HTTP request fails
        json.JSONDecodeError: If JSON parsing fails
        yaml.YAMLError: If YAML parsing fails
        ValueError: If the response is neither valid JSON nor YAML
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to fetch OpenAPI spec from {url}: {e}")

        content = response.text
        content_type = response.headers.get('content-type', '').lower()

        # Try to parse as JSON first
        if 'json' in content_type or content.strip().startswith('{'):
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Failed to parse JSON from {url}: {e.msg}",
                    e.doc,
                    e.pos,
                ) from e

        # Try to parse as YAML
        try:
            spec = yaml.safe_load(content)
            if spec is None:
                raise ValueError(f"Empty or invalid OpenAPI spec from {url}")
            return spec
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML from {url}: {e}") from e

        # If neither JSON nor YAML worked, raise an error
        raise ValueError(f"Response from {url} is neither valid JSON nor YAML")
