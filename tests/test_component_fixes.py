"""Tests for component fixes including schema validation and parameter conversion."""

import pytest
from unittest.mock import Mock

from mcp_this_openapi.openapi.component_fixes import (
    create_component_fixes,
    convert_value_by_type,
    convert_parameters_by_schema,
)


class TestSchemaFixing:
    """Test schema fixing functionality."""

    def test_create_component_fixes_with_validation_disabled(self):
        """Test that disabling validation sets output_schema to None."""
        # Create the component function
        component_fn = create_component_fixes(disable_output_validation=True)

        # Mock a component with output_schema
        mock_component = Mock()
        mock_component.output_schema = {"type": "object", "properties": {}}
        mock_component.name = "test_tool"

        # Mock route (not used in this test but required by function signature)
        mock_route = Mock()

        # Call the function
        component_fn(mock_route, mock_component)

        # Verify output_schema was set to None
        assert mock_component.output_schema is None

    def test_create_component_fixes_with_validation_enabled(self):
        """Test that when validation is enabled, schemas are left untouched."""
        # Create the component function with validation enabled
        component_fn = create_component_fixes(disable_output_validation=False)

        # Mock a component with any schema
        original_schema = {
            "$ref": "#/components/schemas/test",
            "properties": {
                "field": {"$ref": "#/$defs/other"},
            },
        }
        mock_component = Mock()
        mock_component.output_schema = original_schema
        mock_component.name = "test_tool"

        # Mock route
        mock_route = Mock()

        # Call the function
        component_fn(mock_route, mock_component)

        # Schema should be left untouched when validation is enabled
        assert mock_component.output_schema == original_schema

    def test_create_component_fixes_validation_disabled_overrides_schema(self):
        """Test that disabling validation works regardless of schema content."""
        component_fn = create_component_fixes(disable_output_validation=True)

        # Mock component with any schema content
        mock_component = Mock()
        mock_component.output_schema = {
            "$ref": "#/components/schemas/src__api__routers__api__v1__schemas__models__TableItem",
        }
        mock_component.name = "test_tool"

        mock_route = Mock()

        # Call the function
        component_fn(mock_route, mock_component)

        # Should disable validation regardless of schema content
        assert mock_component.output_schema is None

    def test_create_component_fixes_with_healthy_schema(self):
        """Test that healthy schemas are left untouched."""
        component_fn = create_component_fixes(disable_output_validation=False)

        # Mock component with clean, simple schema
        original_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
            },
        }
        mock_component = Mock()
        mock_component.output_schema = original_schema
        mock_component.name = "test_tool"

        mock_route = Mock()

        # Call the function
        component_fn(mock_route, mock_component)

        # Should leave healthy schema untouched
        assert mock_component.output_schema == original_schema

    def test_create_component_fixes_handles_missing_output_schema(self):
        """Test that components without output_schema are handled gracefully."""
        component_fn = create_component_fixes(disable_output_validation=True)

        # Mock component without output_schema attribute
        mock_component = Mock(spec=[])  # Empty spec means no attributes
        mock_route = Mock()

        # Should not raise an exception
        component_fn(mock_route, mock_component)

    def test_create_component_fixes_no_side_effects_when_enabled(self):
        """Test that no changes occur when validation is enabled."""
        component_fn = create_component_fixes(disable_output_validation=False)

        # Mock component with schema
        original_schema = {"type": "object"}
        mock_component = Mock()
        mock_component.output_schema = original_schema
        mock_component.name = "test_tool"

        mock_route = Mock()

        # Call the function
        component_fn(mock_route, mock_component)

        # Should leave everything unchanged
        assert mock_component.output_schema == original_schema

    def test_component_function_signature_compatibility(self):
        """Test that our component function has the expected signature for FastMCP."""
        component_fn = create_component_fixes(disable_output_validation=True)

        # Verify it's callable with (route, component) parameters
        assert callable(component_fn)

        # Test with minimal mocks to ensure signature compatibility
        mock_route = Mock()
        mock_component = Mock()
        mock_component.output_schema = {}

        try:
            result = component_fn(mock_route, mock_component)
            # Function should return None (it modifies component in-place)
            assert result is None
        except TypeError as e:
            pytest.fail(f"Function signature incompatible with FastMCP expectations: {e}")


class TestParameterTypeConversion:
    """Test parameter type conversion functions."""

    def test_convert_integer_from_string(self):
        """Test converting string to integer."""
        schema = {"type": "integer"}

        assert convert_value_by_type("100", schema) == 100
        assert convert_value_by_type("0", schema) == 0
        assert convert_value_by_type("-5", schema) == -5

    def test_convert_integer_from_float(self):
        """Test converting float to integer."""
        schema = {"type": "integer"}

        assert convert_value_by_type(100.0, schema) == 100
        assert convert_value_by_type(99.9, schema) == 99

    def test_convert_integer_already_correct(self):
        """Test that integers are preserved."""
        schema = {"type": "integer"}

        assert convert_value_by_type(100, schema) == 100
        assert convert_value_by_type(0, schema) == 0

    def test_convert_number_from_string(self):
        """Test converting string to number."""
        schema = {"type": "number"}

        assert convert_value_by_type("100", schema) == 100
        assert convert_value_by_type("99.5", schema) == 99.5
        assert convert_value_by_type("0.1", schema) == 0.1

    def test_convert_boolean_from_string(self):
        """Test converting string to boolean."""
        schema = {"type": "boolean"}

        # True cases
        assert convert_value_by_type("true", schema) is True
        assert convert_value_by_type("True", schema) is True
        assert convert_value_by_type("1", schema) is True
        assert convert_value_by_type("yes", schema) is True
        assert convert_value_by_type("on", schema) is True

        # False cases
        assert convert_value_by_type("false", schema) is False
        assert convert_value_by_type("False", schema) is False
        assert convert_value_by_type("0", schema) is False
        assert convert_value_by_type("no", schema) is False
        assert convert_value_by_type("off", schema) is False

    def test_convert_parameters_by_schema(self):
        """Test converting multiple parameters based on schema."""
        params = {
            "limit": "100",
            "offset": "50",
            "include_deleted": "true",
            "name": "test",
        }

        schema_properties = {
            "limit": {"type": "integer"},
            "offset": {"type": "integer"},
            "include_deleted": {"type": "boolean"},
            "name": {"type": "string"},
        }

        result = convert_parameters_by_schema(params, schema_properties)

        assert result["limit"] == 100
        assert result["offset"] == 50
        assert result["include_deleted"] is True
        assert result["name"] == "test"

    def test_convert_parameters_missing_schema(self):
        """Test that parameters without schema are preserved."""
        params = {
            "limit": "100",
            "unknown_param": "value",
        }

        schema_properties = {
            "limit": {"type": "integer"},
        }

        result = convert_parameters_by_schema(params, schema_properties)

        assert result["limit"] == 100
        assert result["unknown_param"] == "value"  # Preserved as-is

    def test_convert_invalid_values(self):
        """Test that invalid conversions return original values."""
        schema = {"type": "integer"}

        # These should return original values since they can't be converted
        assert convert_value_by_type("not_a_number", schema) == "not_a_number"
        assert convert_value_by_type([], schema) == []
        assert convert_value_by_type({}, schema) == {}

    def test_convert_none_values(self):
        """Test that None values are preserved."""
        schema = {"type": "integer"}

        assert convert_value_by_type(None, schema) is None

    def test_convert_no_type_schema(self):
        """Test handling schemas without type information."""
        schema = {"description": "Some parameter"}

        assert convert_value_by_type("100", schema) == "100"  # Unchanged
