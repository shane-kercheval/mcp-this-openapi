"""OpenAPI specification filtering for mcp-this-openapi."""

import re
from typing import Any
from copy import deepcopy


def filter_openapi_paths(  # noqa: PLR0912
    spec: dict[str, Any],
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    include_methods: list[str] | None = None,
    exclude_methods: list[str] | None = None,
) -> dict[str, Any]:
    """
    Filter OpenAPI specification paths based on include/exclude patterns and HTTP methods.

    Args:
        spec: OpenAPI specification dictionary
        include_patterns: List of regex patterns for paths to include
        exclude_patterns: List of regex patterns for paths to exclude
        include_methods: List of HTTP methods to include (e.g., ["GET", "POST"])
        exclude_methods: List of HTTP methods to exclude (e.g., ["DELETE", "PUT"])

    Returns:
        Modified OpenAPI specification with filtered paths and methods

    Raises:
        ValueError: If no paths section exists in the spec
    """
    if "paths" not in spec:
        raise ValueError("OpenAPI specification must contain a 'paths' section")

    # Create a deep copy to avoid modifying the original
    filtered_spec = deepcopy(spec)
    original_paths = filtered_spec["paths"]
    filtered_paths = {}

    # Normalize method names to uppercase for consistent comparison
    # Default to GET-only for safety if no method filtering is specified
    if include_methods is None and exclude_methods is None:
        include_methods_upper = ['GET']
    else:
        include_methods_upper = [m.upper() for m in include_methods] if include_methods else None
    exclude_methods_upper = [m.upper() for m in exclude_methods] if exclude_methods else None

    for path, path_spec in original_paths.items():
        # Apply path-level filtering first
        should_include_path = True

        # Apply include patterns - if specified, path must match at least one
        if include_patterns:
            should_include_path = any(
                re.match(pattern, path) for pattern in include_patterns
            )

        # Apply exclude patterns - if path matches any exclude pattern, remove it
        if should_include_path and exclude_patterns:
            should_include_path = not any(
                re.match(pattern, path) for pattern in exclude_patterns
            )

        if should_include_path:
            # Filter methods within this path
            filtered_path_spec = {}

            for method, method_spec in path_spec.items():
                # Skip non-HTTP method keys (like 'parameters', 'summary', etc.)
                http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
                if method.upper() not in http_methods:
                    # Keep non-method properties as-is
                    filtered_path_spec[method] = method_spec
                    continue

                should_include_method = True
                method_upper = method.upper()

                # Apply include methods - if specified, method must be in the list
                if include_methods_upper:
                    should_include_method = method_upper in include_methods_upper

                # Apply exclude methods - if method is in exclude list, remove it
                if should_include_method and exclude_methods_upper:
                    should_include_method = method_upper not in exclude_methods_upper

                if should_include_method:
                    filtered_path_spec[method] = method_spec

            # Only include the path if it has at least one method remaining
            if any(key.upper() in http_methods for key in filtered_path_spec):
                filtered_paths[path] = filtered_path_spec

    filtered_spec["paths"] = filtered_paths

    return filtered_spec
