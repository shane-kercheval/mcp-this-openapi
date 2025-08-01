"""Tests for schema fixing utilities."""

import pytest
from unittest.mock import Mock

from mcp_this_openapi.openapi.schema_fix import create_schema_fixing_component_fn


class TestSchemaFixing:
    """Test schema fixing functionality."""

    def test_create_schema_fixing_component_fn_with_validation_disabled(self):
        """Test that disabling validation sets output_schema to None."""
        # Create the component function
        component_fn = create_schema_fixing_component_fn(disable_validation=True)

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

    def test_create_schema_fixing_component_fn_with_validation_enabled(self):
        """Test that when validation is enabled, schemas are left untouched."""
        # Create the component function with validation enabled
        component_fn = create_schema_fixing_component_fn(disable_validation=False)

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

    def test_create_schema_fixing_component_fn_validation_disabled_overrides_schema(self):
        """Test that disabling validation works regardless of schema content."""
        component_fn = create_schema_fixing_component_fn(disable_validation=True)

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

    def test_create_schema_fixing_component_fn_with_healthy_schema(self):
        """Test that healthy schemas are left untouched."""
        component_fn = create_schema_fixing_component_fn(disable_validation=False)

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

    def test_create_schema_fixing_component_fn_handles_missing_output_schema(self):
        """Test that components without output_schema are handled gracefully."""
        component_fn = create_schema_fixing_component_fn(disable_validation=True)

        # Mock component without output_schema attribute
        mock_component = Mock(spec=[])  # Empty spec means no attributes
        mock_route = Mock()

        # Should not raise an exception
        component_fn(mock_route, mock_component)

    def test_create_schema_fixing_component_fn_no_side_effects_when_enabled(self):
        """Test that no changes occur when validation is enabled."""
        component_fn = create_schema_fixing_component_fn(disable_validation=False)

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
        component_fn = create_schema_fixing_component_fn(disable_validation=True)

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
