"""Test with a real FastAPI server to validate parameter handling."""

import pytest
import asyncio
import threading
import time
import uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel
import httpx
import json

from mcp_this_openapi.server import create_mcp_server
from mcp_this_openapi.config.models import (
    Config,
    OpenAPIConfig,
    AuthenticationConfig,
    ServerConfig,
)
from mcp_this_openapi.openapi.fetcher import fetch_openapi_spec
from mcp_this_openapi.openapi.filter import filter_openapi_paths
from mcp_this_openapi.openapi.auth import create_authenticated_client
from mcp_this_openapi.openapi.url_utils import extract_base_url
from mcp_this_openapi.openapi.tool_naming import generate_mcp_names_from_spec
from mcp_this_openapi.openapi.schema_fix import create_schema_fixing_component_fn
from fastmcp import FastMCP

# Create a real FastAPI app that's strict about types
app = FastAPI(title="Strict API", version="1.0.0")

class ItemsResponse(BaseModel):  # noqa: D101
    items: list[dict]
    total: int
    limit_received: int
    limit_type: str

@app.get("/items", response_model=ItemsResponse)
async def get_items(
    limit: int = Query(default=10, ge=1, le=100, description="Number of items to return"),
):
    """Endpoint that strictly validates integer types."""
    return ItemsResponse(
        items=[{"id": i, "name": f"item_{i}"} for i in range(limit)],
        total=1000,
        limit_received=limit,
        limit_type=type(limit).__name__,
    )

@app.get("/openapi.json")
async def get_openapi():
    """Return the OpenAPI spec."""
    return app.openapi()


class FastAPITestServer:
    """Helper to run FastAPI server in background thread for testing."""

    def __init__(self, port: int = 8899):
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the server in a background thread."""
        def run_server() -> None:
            config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="error")
            self.server = uvicorn.Server(config)
            asyncio.run(self.server.serve())

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

        # Wait for server to start
        for _ in range(50):  # 5 second timeout
            try:
                response = httpx.get(f"http://127.0.0.1:{self.port}/openapi.json", timeout=1.0)
                if response.status_code == 200:
                    break
            except:  # noqa: E722
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("FastAPI test server failed to start")

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.should_exit = True


@pytest.fixture(scope="module")
def fastapi_server():
    """Start a real FastAPI server for testing."""
    server = FastAPITestServer()
    server.start()
    yield server
    server.stop()


@pytest.mark.asyncio
class TestRealFastAPIValidation:
    """Test against a real FastAPI server to see how it handles string vs integer parameters."""

    async def test_direct_api_calls_with_different_types(self, fastapi_server):  # noqa: ANN001
        """Test calling the FastAPI server directly with different parameter types."""
        base_url = f"http://127.0.0.1:{fastapi_server.port}"

        async with httpx.AsyncClient() as client:
            # Test: Integer parameter
            response = await client.get(f"{base_url}/items", params={"limit": 5})
            assert response.status_code == 200
            data = response.json()
            assert data["limit_received"] == 5
            assert data["limit_type"] == "int"

            # Test: String parameter (FastAPI converts automatically)
            response = await client.get(f"{base_url}/items", params={"limit": "10"})
            assert response.status_code == 200
            data = response.json()
            assert data["limit_received"] == 10
            assert data["limit_type"] == "int"

            # Test: Invalid string (should fail)
            response = await client.get(f"{base_url}/items", params={"limit": "invalid"})
            assert response.status_code == 422
            error = response.json()
            assert "valid integer" in error["detail"][0]["msg"].lower()

            # Test: Float string (should fail)
            response = await client.get(f"{base_url}/items", params={"limit": "10.5"})
            assert response.status_code == 422
            error = response.json()
            assert "int_parsing" in error["detail"][0]["type"]

    async def test_mcp_server_with_real_fastapi_backend(self, fastapi_server):  # noqa: ANN001
        """Test our MCP server against the real FastAPI server."""
        base_url = f"http://127.0.0.1:{fastapi_server.port}"

        config = Config(
            server=ServerConfig(name="test-server"),
            openapi=OpenAPIConfig(spec_url=f"{base_url}/openapi.json"),
            authentication=AuthenticationConfig(type="none"),
            disable_schema_validation=False,
        )

        mcp_server = await create_mcp_server(config)
        tools = await mcp_server.get_tools()

        # Find the get_items tool
        get_items_tool = None
        for tool_name, tool in tools.items():
            if "items" in tool_name.lower():
                get_items_tool = tool
                break

        assert get_items_tool is not None, f"No items tool found in {list(tools.keys())}"

        # Test: MCP with string parameters
        result = await get_items_tool.run({"limit": "7"})
        assert result is not None

        response_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])  # noqa: E501
        response_data = json.loads(response_text)
        assert response_data['limit_received'] == 7
        assert response_data['limit_type'] == "int"

        # Test: MCP with integer parameters
        result = await get_items_tool.run({"limit": 8})
        assert result is not None

        response_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])  # noqa: E501
        response_data = json.loads(response_text)
        assert response_data['limit_received'] == 8
        assert response_data['limit_type'] == "int"

        # Test: MCP with invalid string (should fail)
        with pytest.raises(Exception) as exc_info:  # noqa: PT011
            await get_items_tool.run({"limit": "invalid"})

        assert "422" in str(exc_info.value) or "Unprocessable" in str(exc_info.value)

    async def test_comparison_with_parameter_conversion_enabled(self, fastapi_server):  # noqa: ANN001
        """Test that schema fixing component produces same results as no conversion."""
        base_url = f"http://127.0.0.1:{fastapi_server.port}"
        config = Config(
            server=ServerConfig(name="test-server-with-schema-fix"),
            openapi=OpenAPIConfig(spec_url=f"{base_url}/openapi.json"),
            authentication=AuthenticationConfig(type="none"),
            disable_schema_validation=False,
        )

        # Create server with schema fixing component
        spec = await fetch_openapi_spec(config.openapi.spec_url)
        spec = filter_openapi_paths(spec, config.include_patterns, config.exclude_patterns,
                                  config.include_methods, config.exclude_methods, config.include_deprecated)  # noqa: E501
        base_url_extracted = extract_base_url(spec, config.openapi.spec_url)
        client = create_authenticated_client(config.authentication, base_url_extracted)

        mcp_names = None
        if config.tool_naming == "auto":
            mcp_names = generate_mcp_names_from_spec(spec, use_operation_id=False)

        mcp_component_fn = create_schema_fixing_component_fn(disable_validation=config.disable_schema_validation)  # noqa: E501

        mcp_server = FastMCP.from_openapi(
            openapi_spec=spec,
            client=client,
            name=config.server.name,
            mcp_names=mcp_names,
            mcp_component_fn=mcp_component_fn,
        )

        tools = await mcp_server.get_tools()

        # Find the get_items tool
        get_items_tool = None
        for tool_name, tool in tools.items():
            if "items" in tool_name.lower():
                get_items_tool = tool
                break

        assert get_items_tool is not None

        # Test with string parameter - should work the same as without conversion
        result = await get_items_tool.run({"limit": "9"})
        assert result is not None

        response_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])  # noqa: E501
        response_data = json.loads(response_text)
        assert response_data['limit_received'] == 9
        assert response_data['limit_type'] == "int"
