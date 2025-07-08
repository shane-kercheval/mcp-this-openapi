"""Utilities for handling OpenAPI URLs."""

from typing import Any
from urllib.parse import urlparse


def extract_base_url(spec: dict[str, Any], spec_url: str) -> str:
    """
    Extract the base URL from an OpenAPI specification.

    If the spec contains a servers field, use the first server's URL.
    If not, use the host from the spec URL itself.
    Handle relative URLs by combining with the spec URL's host.

    Args:
        spec: The OpenAPI specification dictionary
        spec_url: The URL where the OpenAPI spec was fetched from

    Returns:
        The base URL for API calls
    """
    if "servers" not in spec or not spec["servers"]:
        # If no servers defined, use the host from the spec URL
        parsed_spec_url = urlparse(spec_url)
        return f"{parsed_spec_url.scheme}://{parsed_spec_url.netloc}"

    base_url = spec["servers"][0]["url"]

    # Handle relative URLs by using the spec URL's host
    if base_url.startswith("/"):
        parsed_spec_url = urlparse(spec_url)
        base_url = f"{parsed_spec_url.scheme}://{parsed_spec_url.netloc}{base_url}"

    return base_url
