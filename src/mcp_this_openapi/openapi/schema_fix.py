"""
Schema fixing utilities for FastMCP OpenAPI integration.

FastMCP performs JSON schema validation on API responses to ensure they match the OpenAPI
specification. However, this validation can fail when OpenAPI specs have:

1. Broken schema references (e.g., #/components/schemas/ vs #/$defs/ mismatches)
2. Complex cross-version references (e.g., v1 schemas referenced in v2 endpoints)
3. Long namespaced schema names that cause resolution issues
4. External references that can't be resolved

When these issues occur, users get "PointerToNowhere" or similar schema resolution errors that
prevent API calls from working, even though the underlying API is functional.

This module provides utilities to disable or fix problematic schema validation while preserving
the core API call functionality.
"""


def create_schema_fixing_component_fn(disable_validation: bool = False) -> callable:
    """
    Create a component function that disables schema validation for problematic OpenAPI specs.

    FastMCP calls this function during tool creation via the mcp_component_fn parameter. It allows
    us to modify each tool's configuration before it's finalized. By setting
    `component.output_schema = None`, we tell FastMCP to skip response validation for that tool
    while keeping the API call functionality intact.

    This is necessary because some OpenAPI specs have broken schema references that cause FastMCP's
    schema resolution to fail with "PointerToNowhere" errors, even though the actual API endpoints
    work fine.

    Args:
        disable_validation: If True, disable all output schema validation for all tools

    Returns:
        Function that can be passed as mcp_component_fn to FastMCP.from_openapi()

    Example:
        >>> component_fn = create_schema_fixing_component_fn(disable_validation=True)
        >>> server = FastMCP.from_openapi(spec, client, mcp_component_fn=component_fn)
    """
    def fix_component_schemas(route, component) -> None:  # noqa: ANN001, ARG001
        """
        Disable schema validation entirely when flag is set.

        This function is called by FastMCP for each tool/component created from the OpenAPI spec.
        """
        if disable_validation and hasattr(component, 'output_schema'):
            component.output_schema = None

    return fix_component_schemas
