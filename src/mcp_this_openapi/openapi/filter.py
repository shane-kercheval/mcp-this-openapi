"""OpenAPI specification filtering for mcp-this-openapi."""

import re
from typing import Any
from copy import deepcopy


def filter_openapi_paths(
    spec: dict[str, Any],
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """
    Filter OpenAPI specification paths based on include/exclude patterns.

    Args:
        spec: OpenAPI specification dictionary
        include_patterns: List of regex patterns for paths to include
        exclude_patterns: List of regex patterns for paths to exclude

    Returns:
        Modified OpenAPI specification with filtered paths

    Raises:
        ValueError: If no paths section exists in the spec
    """
    if "paths" not in spec:
        raise ValueError("OpenAPI specification must contain a 'paths' section")

    # Create a deep copy to avoid modifying the original
    filtered_spec = deepcopy(spec)
    original_paths = filtered_spec["paths"]
    filtered_paths = {}

    for path, path_spec in original_paths.items():
        should_include = True

        # Apply include patterns - if specified, path must match at least one
        if include_patterns:
            should_include = any(
                re.match(pattern, path) for pattern in include_patterns
            )

        # Apply exclude patterns - if path matches any exclude pattern, remove it
        if should_include and exclude_patterns:
            should_include = not any(
                re.match(pattern, path) for pattern in exclude_patterns
            )

        if should_include:
            filtered_paths[path] = path_spec

    filtered_spec["paths"] = filtered_paths

    return filtered_spec
