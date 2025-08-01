"""
Component fixes for FastMCP OpenAPI integration.

This module provides fixes for two common issues with FastMCP's OpenAPI integration:

1. **Parameter Type Conversion**: FastMCP converts all parameters to strings. This module
   automatically converts them back to their correct types based on the OpenAPI schema.

2. **Schema Validation Errors**: FastMCP performs JSON schema validation on API responses to
   ensure they match the OpenAPI specification. However, this validation can fail when OpenAPI
   specs have:
   - Broken schema references (e.g., #/components/schemas/ vs #/$defs/ mismatches)
   - Complex cross-version references (e.g., v1 schemas referenced in v2 endpoints)
   - Long namespaced schema names that cause resolution issues
   - External references that can't be resolved

   When these issues occur, users get "PointerToNowhere" or similar schema resolution errors that
   prevent API calls from working, even though the underlying API is functional.

The main function `create_component_fixes` handles both parameter type conversion and
optional schema validation disabling.
"""

import json
from typing import Any


def create_component_fixes(disable_output_validation: bool = False) -> callable:
    """
    Create a component function that handles parameter type conversion and optionally
    disables output validation.

    This function intercepts MCP tool calls and converts parameters to their correct
    types based on the OpenAPI schema before FastMCP processes them. It also
    provides the option to disable output validation for problematic schemas.

    FastMCP calls this function during tool creation via the mcp_component_fn parameter. It allows
    us to modify each tool's configuration before it's finalized. By setting
    `component.output_schema = None`, we tell FastMCP to skip response validation for that tool
    while keeping the API call functionality intact.

    This is necessary because some OpenAPI specs have broken schema references that cause FastMCP's
    schema resolution to fail with "PointerToNowhere" errors, even though the actual API endpoints
    work fine.

    Args:
        disable_output_validation: If True, disable output schema validation for all tools

    Returns:
        Function that can be passed as mcp_component_fn to FastMCP.from_openapi()

    Example:
        >>> component_fn = create_component_fixes(disable_output_validation=True)
        >>> server = FastMCP.from_openapi(spec, client, mcp_component_fn=component_fn)
    """

    def component_modifier(route_info, component) -> None:  # noqa: ANN001, ARG001
        """
        Modify the component to handle parameter conversion and validation.
        Note: route_info is required by FastMCP's component function signature but not used here.
        """
        # Handle output validation
        if disable_output_validation and hasattr(component, "output_schema"):
            component.output_schema = None

        # Always enable parameter type conversion
        if hasattr(component, "input_schema") and hasattr(component, "fn") and component.fn:
            # Store the original input schema for type conversion
            original_schema = component.input_schema
            original_fn = component.fn

            async def type_converting_wrapper(**kwargs) -> object:  # noqa: ANN003
                """Convert parameter types before calling the original function."""
                if original_schema and "properties" in original_schema:
                    converted_kwargs = convert_parameters_by_schema(
                        kwargs, original_schema["properties"],
                    )
                else:
                    converted_kwargs = kwargs

                return await original_fn(**converted_kwargs)

            component.fn = type_converting_wrapper

    return component_modifier


def convert_parameters_by_schema(
    params: dict[str, Any], schema_properties: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert parameters based on their schema definitions.

    Args:
        params: Raw parameters from MCP call
        schema_properties: OpenAPI schema properties for the parameters

    Returns:
        Dictionary with properly typed parameters
    """
    converted = {}

    for param_name, param_value in params.items():
        if param_name in schema_properties:
            schema = schema_properties[param_name]
            converted[param_name] = convert_value_by_type(param_value, schema)
        else:
            converted[param_name] = param_value

    return converted


def convert_value_by_type(value: object, schema: dict[str, object]) -> object:  # noqa
    """
    Convert a value to the correct type based on its schema.

    Args:
        value: The value to convert
        schema: OpenAPI schema for this parameter

    Returns:
        Value converted to the correct type
    """
    if not isinstance(schema, dict):
        return value

    # Get the type from the schema
    param_type = schema.get("type")
    if not param_type:
        return value

    # If value is None, keep it as None
    if value is None:
        return value

    # Convert based on type
    try:
        if param_type == "integer":
            if isinstance(value, str):
                # Handle string representation of integers
                return int(value)
            if isinstance(value, float):
                # Handle float to int conversion
                return int(value)
            if isinstance(value, int):
                # Already correct type
                return value

        elif param_type == "number":
            if isinstance(value, str):
                # Try int first, then float
                try:
                    return int(value)
                except ValueError:
                    return float(value)
            elif isinstance(value, int | float):
                # Already correct type
                return value

        elif param_type == "boolean":
            if isinstance(value, str):
                # Handle string representations of booleans
                return value.lower() in ("true", "1", "yes", "on", "t", "y")
            if isinstance(value, bool):
                # Already correct type
                return value
            # Convert other types to boolean
            return bool(value)

        elif param_type == "array":
            if isinstance(value, str):
                # Try to parse JSON array
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
            elif isinstance(value, list):
                # Already correct type
                return value

        elif param_type == "object":
            if isinstance(value, str):
                # Try to parse JSON object
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
            elif isinstance(value, dict):
                # Already correct type
                return value

    except (ValueError, TypeError, json.JSONDecodeError):
        # If conversion fails, return the original value
        pass

    # Default: return original value if no conversion needed or conversion failed
    return value


