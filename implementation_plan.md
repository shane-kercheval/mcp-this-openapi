# Implementation Plan for mcp-this-openapi

## 📁 **Project Structure to Create**

```
mcp-this-openapi/
├── src/
│   └── mcp_this_openapi/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── loader.py
│       ├── openapi/
│       │   ├── __init__.py
│       │   ├── fetcher.py
│       │   ├── filter.py
│       │   └── auth.py
│       └── server.py
├── tests/
│   ├── fixtures/
│   │   ├── configs/
│   │   └── openapi_specs/
│   ├── test_config.py
│   ├── test_openapi.py
│   ├── test_auth.py
│   ├── test_server.py
│   └── test_integration.py
├── examples/
│   └── configs/
├── pyproject.toml
├── Makefile
└── README.md
```

## 🔧 **1. Project Setup Files**

### **pyproject.toml**
- Copy structure from mcp-this example
- Update name to "mcp-this-openapi"  
- Add dependencies: `fastmcp`, `httpx`, `pydantic`, `pyyaml`, `mcp`, `click`
- Add dev dependencies: `pytest`, `pytest-asyncio`, `respx`, `coverage`, `ruff`
- use `uv` package manager (see Makefile)
- Set entry point: `mcp-this-openapi = "mcp_this_openapi.__main__:main"`

### **Makefile**
- Copy from mcp-this example
- Update commands to use "mcp-this-openapi" instead of "mcp-this"
- Keep same structure for build, test, lint, coverage commands

## 📋 **2. Configuration Models (src/mcp_this_openapi/config/models.py)**

### **Pydantic Models to Create:**

**ServerConfig:**
- `name: str` - Server name for MCP

**OpenAPIConfig:**  
- `spec_url: str` - URL to fetch OpenAPI/Swagger spec

**AuthenticationConfig:**
- `type: Literal["bearer", "api_key", "basic", "none"]` - Auth type
- `token: Optional[str]` - For bearer auth, supports env var substitution
- `api_key: Optional[str]` - For api_key auth  
- `header_name: Optional[str]` - Header name for api_key (default "X-API-Key")
- `username: Optional[str]` - For basic auth
- `password: Optional[str]` - For basic auth

**Config (main model):**
- `server: ServerConfig`
- `openapi: OpenAPIConfig` 
- `authentication: Optional[AuthenticationConfig]`
- `include_patterns: Optional[List[str]]` - Regex patterns for path inclusion
- `exclude_patterns: Optional[List[str]]` - Regex patterns for path exclusion

## 📥 **3. Configuration Loader (src/mcp_this_openapi/config/loader.py)**

### **Functions to Implement:**

**`expand_env_vars(value: str) -> str`:**
- Check if value starts with "${" and ends with "}"
- If yes, extract env var name and get from `os.environ`
- Raise clear error if env var doesn't exist
- If no, return value as-is

**`load_config(config_path: str) -> Config`:**
- Load YAML file using `yaml.safe_load()`
- Recursively process all string values through `expand_env_vars()`
- Validate using Pydantic Config model
- Return validated Config object

## 🌐 **4. OpenAPI Spec Fetcher (src/mcp_this_openapi/openapi/fetcher.py)**

### **Functions to Implement:**

**`fetch_openapi_spec(url: str) -> dict`:**
- Use `httpx.AsyncClient()` to fetch spec from URL
- Handle both JSON and YAML responses
- Parse and return as Python dict
- Raise clear errors for network issues, invalid JSON/YAML, HTTP errors

## 🔍 **5. OpenAPI Spec Filter (src/mcp_this_openapi/openapi/filter.py)**

### **Functions to Implement:**

**`filter_openapi_paths(spec: dict, include_patterns: List[str], exclude_patterns: List[str]) -> dict`:**
- Take original OpenAPI spec dict
- Get all paths from `spec["paths"]`
- For each path, check against include patterns using `re.match()`
- If include_patterns specified, path must match at least one include pattern
- Then check against exclude patterns - if matches any exclude, remove it
- Return modified spec dict with filtered paths
- Preserve all other spec sections (info, components, etc.)

## 🔐 **6. Authentication Handler (src/mcp_this_openapi/openapi/auth.py)**

### **Functions to Implement:**

**`create_authenticated_client(auth_config: Optional[AuthenticationConfig], base_url: str) -> httpx.AsyncClient`:**
- Create `httpx.AsyncClient` with appropriate authentication
- For `bearer`: Add `Authorization: Bearer {token}` header
- For `api_key`: Add `{header_name}: {api_key}` header  
- For `basic`: Use `httpx.BasicAuth(username, password)`
- For `none` or None: No authentication
- Return configured client with base_url set from OpenAPI spec servers[0].url

## 🖥️ **7. Main Server (src/mcp_this_openapi/server.py)**

### **Functions to Implement:**

**`create_mcp_server(config: Config) -> FastMCP`:**
- Fetch OpenAPI spec using `fetch_openapi_spec()`
- Filter spec paths using `filter_openapi_paths()` if patterns provided
- Extract base_url from spec's `servers[0].url`
- Create authenticated client using `create_authenticated_client()`
- Create FastMCP server using `FastMCP.from_openapi(openapi_spec=filtered_spec, client=auth_client, name=config.server.name)`
- Return the FastMCP server

**`run_server(config_path: str):`**
- Load config using `load_config()`
- Create server using `create_mcp_server()`
- Call `server.run()` to start MCP server

## 🖱️ **8. CLI Entry Point (src/mcp_this_openapi/__main__.py)**

### **Functions to Implement:**

**`main():`**
- Use Click to define CLI with `--config` option
- Call `run_server(config_path)` with provided config path
- Handle errors gracefully with proper error messages

## 🧪 **9. Test Fixtures (tests/fixtures/)**

### **Files to Create:**

**tests/fixtures/configs/petstore.yaml:**
```yaml
server:
  name: "petstore-test"
openapi:
  spec_url: "https://petstore3.swagger.io/api/v3/openapi.json"
authentication:
  type: "none"
```

**tests/fixtures/configs/github.yaml:**
```yaml  
server:
  name: "github-test"
openapi:
  spec_url: "https://api.github.com/openapi.json"
authentication:
  type: "bearer"
  token: "${GITHUB_TOKEN}"
include_patterns: ["^/repos", "^/user"]
exclude_patterns: ["^/admin"]
```

**tests/fixtures/openapi_specs/simple.json:**
- Small valid OpenAPI 3.0 spec with 2-3 operations for testing

## 🧪 **10. Unit Tests**

### **test_config.py:**
- Test YAML loading with valid configs
- Test environment variable expansion
- Test validation errors for invalid configs
- Test missing environment variables

### **test_openapi.py:**
- Test spec fetching with mocked HTTP responses using `respx`
- Test path filtering with various include/exclude patterns
- Test authentication client creation for each auth type

### **test_server.py:**
- Test MCP server creation end-to-end using test fixtures
- Follow pattern from mcp-this: use `stdio_client()` and `ClientSession`
- Test tool registration, tool calling, parameter handling

### **test_integration.py:**
- Full end-to-end tests with real OpenAPI specs (if reliable)
- Test error scenarios (network failures, invalid specs, etc.)

## 📝 **11. Examples (examples/configs/)**

### **Config Files to Create:**
- `petstore.yaml` - Working Swagger Petstore example
- `github.yaml` - GitHub API with auth example
- `jsonplaceholder.yaml` - Simple test API

## 🎯 **Implementation Priority**

1. **Setup** - pyproject.toml, Makefile, basic structure
2. **Config** - Pydantic models and YAML loader with env var support
3. **OpenAPI** - Spec fetcher and path filtering  
4. **Auth** - httpx client creation with different auth types
5. **Server** - FastMCP integration and main server logic
6. **CLI** - Click interface
7. **Tests** - Unit tests for each component
8. **Integration** - End-to-end MCP server tests
9. **Examples** - Working example configs

Each component should be implemented and tested independently before moving to the next.

---

Here is an mock implementation we got working for a proof of concept:

```python
#!/usr/bin/env python3
"""
FastMCP server using the real Petstore API (Swagger/OpenAPI compatible).
"""
import sys
import httpx
from fastmcp import FastMCP


def create_server():
    """Create and configure the FastMCP server."""
    # Use stderr for logging so it doesn't interfere with MCP protocol
    print("Creating Petstore MCP server...", file=sys.stderr)
    
    # Use the OpenAPI 3.0 Petstore API (not Swagger 2.0)
    spec_url = "https://petstore3.swagger.io/api/v3/openapi.json"
    
    try:
        # Try to fetch the OpenAPI spec (this will likely fail)
        import asyncio
        async def fetch_spec():
            async with httpx.AsyncClient() as client:
                print(f"Fetching OpenAPI spec from {spec_url}...", file=sys.stderr)
                response = await client.get(spec_url)
                response.raise_for_status()
                return response.json()
        
        # This should now work with OpenAPI 3.0!
        spec = asyncio.run(fetch_spec())
        print(f"✅ Loaded spec with {len(spec.get('paths', {}))} endpoints", file=sys.stderr)
    except Exception as e:
        print(f"❌ Failed to fetch spec: {e}", file=sys.stderr)
        raise  # Exit if we can't get the real spec

    
    # Create HTTP client for API calls
    api_client = httpx.AsyncClient(
        base_url="https://petstore3.swagger.io/api/v3",
        timeout=30.0
    )
    
    # Create FastMCP server
    print("Creating FastMCP server...", file=sys.stderr)
    server = FastMCP.from_openapi(
        openapi_spec=spec,
        client=api_client,
        name="petstore"
    )
    
    print("🚀 Starting MCP server (connect with Claude Desktop)...", file=sys.stderr)
    print("💡 Available tools will be generated from the Petstore API spec", file=sys.stderr)
    
    return server


if __name__ == "__main__":
    server = create_server()
    server.run()
```

This is the pyproject.toml and Makefile we used for a similar project, but don't blindly copy them, as they may need adjustments for this project:

```toml
[project]
name = "mcp-this"
version = "0.0.21"
description = "MCP Server that exposes CLI commands as tools for Claude using YAML configuration files"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "Shane Kercheval", email = "shane.kercheval@gmail.com"},
]
keywords = ["MCP", "Claude", "AI", "CLI", "tools"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities",
]
dependencies = [
    "click>=8.1.8",
    "python-dotenv>=1.0.1",
    "pyyaml",
    "mcp",
    "fastmcp>=2.2.0",
    "httpx>=0.24.0",
    "pydantic>=2.0.0",
    "aiofiles>=24.1.0",
]

[dependency-groups]
dev = [
    "coverage>=7.7.1",
    "pytest>=8.3.5",
    "pytest-asyncio>=0.25.3",
    "pytest-timeout>=2.3.1",
    "ruff>=0.11.0",
    "pip>=25.0.1",
    "ipykernel>=6.29.5",
    "sik-llms",
    "mcp[cli]",
    "aiofiles>=24.1.0",
    "respx>=0.20.0",
]

[project.scripts]
mcp-this = "mcp_this.__main__:main"

[tool.hatch.metadata]
allow-direct-references = true

[tool.hatch.build.targets.wheel]
packages = ["src/mcp_this"]
include = ["src/mcp_this/configs/*.yaml"]

[build-system]
requires = ["hatchling>=1.17.1"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
timeout = 60
timeout_method = "signal"  # note this only works on unix; "thread" method (default) is safer but might not catch hanging subprocesses
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

```makefile
.PHONY: tests build linting unittests coverage mcp_dev mcp_install mcp_test verify package package-build package-publish help

-include .env
export

####
# Project
####

help: ## Display this help
	@echo "MCP-This Development Commands"
	@echo "============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Install dependencies 
	uv sync

####
# Development
####

mcp_dev: ## Run the MCP server with default config in development mode
	MCP_THIS_CONFIG_PATH=./src/mcp_this/configs/default.yaml uv run mcp dev ./src/mcp_this/mcp_server.py

mcp_custom: ## Run the MCP server with a custom config (path in CONFIG var)
	MCP_THIS_CONFIG_PATH=$(CONFIG) uv run mcp dev ./src/mcp_this/mcp_server.py

mcp_install: ## Install the MCP server in Claude Desktop with the default config
	uv run mcp install --name "MCP-This" ./src/mcp_this/mcp_server.py

mcp_install_custom: ## Install the MCP server with a custom config (path in CONFIG var)
	uv run mcp install --name "MCP-This" ./src/mcp_this/mcp_server.py -- --config $(CONFIG)

mcp_test: ## Run the sample test server
	uv run mcp dev ./src/mcp_this/test_server.py


mcp_inspector_github:
	npx @modelcontextprotocol/inspector \
		uv run -m mcp_this \
		--config_path /Users/shanekercheval/repos/mcp-this/src/mcp_this/configs/github.yaml

####
# Testing
####

linting: ## Run linting checks
	uv run ruff check src --fix --unsafe-fixes
	uv run ruff check tests --fix --unsafe-fixes

unittests: ## Run unit tests
	uv run pytest tests -v --durations=10

tests: linting coverage

coverage: ## Run tests with coverage
	uv run coverage run -m pytest --durations=0 tests
	uv run coverage html

open_coverage: ## Open coverage report in browser
	open 'htmlcov/index.html'

verify: linting unittests coverage ## Run all verification checks

chat:
	uv run python examples/cli.py \
		-chat \
		--mcp_config examples/mcp_config_cli.json \
		--model 'gpt-4o'

chat_tools:
	uv run python examples/cli.py \
		-tools \
		--mcp_config examples/mcp_config_cli.json

####
# Packaging and Distribution
####

package-build: ## Build the package
	rm -rf dist/*
	uv build --no-sources

package-publish: ## Publish the package to PyPI (requires UV_PUBLISH_TOKEN)
	uv publish --token ${UV_PUBLISH_TOKEN}

package: package-build package-publish ## Build and publish the package

####
# Development Tools
####

add-dep: ## Add a dependency (PKG=package_name)
	uv add $(PKG)

add-dev-dep: ## Add a development dependency (PKG=package_name)
	uv add $(PKG) --group dev

## Run MCP-This with uvx directly (for Claude Desktop testing)
test-uvx: 
	npx -y uvx mcp-this --config ./src/mcp_this/configs/default.yaml --verbose
```

Only copy useful commands and sections from the Makefile.
