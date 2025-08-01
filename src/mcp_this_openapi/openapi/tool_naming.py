"""Tool naming utilities for OpenAPI operations with smart clash detection."""

import re
from typing import Any
from collections import defaultdict


def extract_version_from_path(path: str) -> tuple[str, str]:
    """
    Extract version identifier from a path and return the path without version.

    Args:
        path: API endpoint path like "/api/v1/users/" or "/v2/posts/"

    Returns:
        Tuple of (version, path_without_version)

    Examples:
        "/api/v1/users/" -> ("v1", "/api/users/")
        "/v2/posts/" -> ("v2", "/posts/")
        "/users/" -> ("", "/users/")
    """
    # Common version patterns
    version_patterns = [
        r'/v(\d+)/',           # /v1/, /v2/, etc.
        r'/api/v(\d+)/',       # /api/v1/, /api/v2/, etc.
        r'/(\d{4}-\d{2}-\d{2})/',  # Date-based versions like /2023-01-01/
    ]

    for pattern in version_patterns:
        match = re.search(pattern, path)
        if match:
            version = f"v{match.group(1)}" if pattern.startswith(r'/v(\d+)') else match.group(1)
            # Remove the version part from the path
            path_without_version = re.sub(pattern, '/', path)
            # Clean up double slashes
            path_without_version = re.sub(r'/+', '/', path_without_version)
            return version, path_without_version

    return "", path


def generate_base_tool_name_from_path(method: str, path: str) -> str:
    """
    Generate a clean base tool name from HTTP method and path (without version).

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path (should have version already stripped)

    Returns:
        Clean base tool name

    Examples:
        >>> generate_base_tool_name_from_path("GET", "/users/")
        'get_users'
        >>> generate_base_tool_name_from_path("POST", "/api/users/")
        'post_users'
        >>> generate_base_tool_name_from_path("PUT", "/users/{user_id}/")
        'put_users'
        >>> generate_base_tool_name_from_path("DELETE", "/users/{user_id}/posts/{post_id}/")
        'delete_users_posts'
        >>> generate_base_tool_name_from_path("GET", "/user-profiles/")
        'get_user_profiles'
        >>> generate_base_tool_name_from_path("PATCH", "/api/health-checks/status/")
        'patch_health_checks_status'
    """
    # Remove leading/trailing slashes and split
    parts = path.strip('/').split('/')

    # Filter out common API prefixes and path parameters
    filtered_parts = []
    for part in parts:
        # Skip common prefixes and path parameters
        if (part not in ['api'] and
            not part.startswith('{') and
            not part.endswith('}') and
            part != ''):  # Skip empty parts from double slashes
            # Replace hyphens with underscores for valid Python names
            filtered_parts.append(part.replace('-', '_'))

    # Combine method and filtered parts
    name_parts = [method.lower(), *filtered_parts]
    name = '_'.join(name_parts)

    # Clean up any double underscores
    while '__' in name:
        name = name.replace('__', '_')

    return name


def generate_mcp_names_with_clash_detection(spec: dict[str, Any]) -> dict[str, str]:  # noqa: PLR0912
    """
    Generate MCP tool names with smart clash detection and version handling.

    Uses a two-pass algorithm:
    1. Generate base names (without versions)
    2. Detect clashes and add versions only where needed

    Args:
        spec: OpenAPI specification

    Returns:
        Dictionary mapping operationId to final tool names
    """
    # Data structures for the two-pass algorithm
    operations = []  # List of (operation_id, method, path, version, base_name)
    base_name_to_operations = defaultdict(list)  # Map base names to operations that use them
    final_names = {}  # Final result

    # Pass 1: Extract all operations and generate base names
    paths = spec.get('paths', {})
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            # Skip non-HTTP method keys
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                continue

            operation_id = operation.get('operationId')
            if not operation_id:
                continue

            # Extract version and generate base name
            version, path_without_version = extract_version_from_path(path)
            base_name = generate_base_tool_name_from_path(method, path_without_version)

            # Store operation info
            op_info = {
                'operation_id': operation_id,
                'method': method,
                'path': path,
                'version': version,
                'base_name': base_name,
            }
            operations.append(op_info)
            base_name_to_operations[base_name].append(op_info)

    # Pass 2: Resolve clashes by adding versions where needed
    for base_name, ops_with_same_name in base_name_to_operations.items():
        if len(ops_with_same_name) == 1:
            # No clash, use base name
            op = ops_with_same_name[0]
            final_names[op['operation_id']] = base_name
        else:
            # Clash detected - check if any operations have versions
            versions_present = [op['version'] for op in ops_with_same_name if op['version']]

            if not versions_present:
                # No versions available, use base name for all (they'll still clash, but we tried)
                for op in ops_with_same_name:
                    final_names[op['operation_id']] = base_name
            else:
                # Add versions to distinguish operations
                for op in ops_with_same_name:
                    if op['version']:
                        final_names[op['operation_id']] = f"{op['version']}_{base_name}"
                    else:
                        # Operation without version in a clash - keep base name
                        final_names[op['operation_id']] = base_name

    return final_names


def generate_mcp_names_from_spec(
        spec: dict[str, Any],
        use_operation_id: bool = True,
    ) -> dict[str, str]:
    """
    Generate MCP tool names mapping from OpenAPI spec.

    Args:
        spec: OpenAPI specification
        use_operation_id: If True, use operationId; if False, use smart auto-generation

    Returns:
        Dictionary mapping operationId to tool names
    """
    if use_operation_id:
        # Default strategy: Use operationId with basic cleanup
        names = {}
        paths = spec.get('paths', {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # Skip non-HTTP method keys
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:  # noqa: E501
                    continue

                operation_id = operation.get('operationId')
                if not operation_id:
                    continue

                # Use the operationId but clean it up
                # Remove double underscore suffixes (e.g., __get, __post)
                name = operation_id.split('__')[0]
                names[operation_id] = name

        return names
    # Auto strategy: Smart generation with clash detection
    return generate_mcp_names_with_clash_detection(spec)
