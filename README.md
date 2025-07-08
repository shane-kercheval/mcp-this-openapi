# mcp-this-openapi

[![Tests](https://github.com/shane-kercheval/mcp-this-openapi/actions/workflows/tests.yaml/badge.svg)](https://github.com/shane-kercheval/mcp-this-openapi/actions/workflows/tests.yaml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol (MCP) server that automatically generates tools from OpenAPI/Swagger specifications, allowing MCP Clients (e.g. Claude Desktop) to interact with any REST API.

## Features

- 🔄 **Automatic Tool Generation**: Converts OpenAPI specs into callable MCP tools
- 🔐 **Multiple Authentication Types**: Bearer tokens, API keys, Basic auth, or no auth
- 🎯 **Path Filtering**: Include/exclude specific API endpoints using regex patterns
- 🌐 **Flexible Spec Loading**: Supports both JSON and YAML OpenAPI specifications
- 🔒 **Environment Variables**: Secure credential management with `${VAR_NAME}` expansion
- 🛡️ **Secure by Default**: Only GET (read-only) operations enabled by default

## Quick Start

### Minimal Usage

The easiest way to get started is with a simple command line argument:

**1. Configure Claude Desktop**

Add this to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "petstore": {
      "command": "uvx",
      "args": [
        "mcp-this-openapi",
        "--openapi-spec-url",
        "https://petstore3.swagger.io/api/v3/openapi.json"
      ]
    }
  }
}
```

**2. Try it in Claude**

Once configured, you can ask Claude things like:
- "What pet operations are available?"
- "Get information about pet with ID 1" 
- "Show me the pet store inventory"

**🔒 Security Note**: By default, only `GET` (read-only) operations are enabled for safety.

### Advanced Usage (Configuration File)

For authentication, filtering, or other advanced features, create a YAML configuration file:

**1. Create `petstore-config.yaml`:**

```yaml
server:
  name: "petstore-demo"
openapi:
  spec_url: "https://petstore3.swagger.io/api/v3/openapi.json"
authentication:
  type: "none"
include_methods:
  - GET
  - POST  # Explicitly enable creating resources
  - PUT   # Explicitly enable updating resources
```

**2. Configure Claude Desktop:**

```json
{
  "mcpServers": {
    "petstore": {
      "command": "uvx",
      "args": [
        "mcp-this-openapi",
        "--config-path",
        "/path/to/your/petstore-config.yaml"
      ]
    }
  }
}
```

## Configuration Reference

### CLI Arguments (Minimal Usage)

For simple use cases, you can use CLI arguments instead of a configuration file:

```bash
# Minimal usage (with default server name)
mcp-this-openapi --openapi-spec-url https://petstore3.swagger.io/api/v3/openapi.json

# With custom server name
mcp-this-openapi \
  --openapi-spec-url https://petstore3.swagger.io/api/v3/openapi.json \
  --server-name "my-petstore"
```

**Available CLI Arguments:**
- `--openapi-spec-url URL` - URL to OpenAPI/Swagger specification (required)
- `--server-name NAME` - Name for the MCP server (optional, defaults to "openapi-server")
- `--config-path PATH` - Path to YAML configuration file (mutually exclusive with --openapi-spec-url)

**Claude Desktop Example:**
```json
{
  "mcpServers": {
    "my-api": {
      "command": "uvx",
      "args": [
        "mcp-this-openapi",
        "--openapi-spec-url", "https://api.example.com/openapi.json",
        "--server-name", "my-api"
      ]
    }
  }
}
```

### YAML Configuration (Advanced Usage)

For authentication, method filtering, and other advanced features, use a YAML configuration file:

```yaml
server:
  name: "my-api-server"  # Name displayed in Claude

openapi:
  spec_url: "https://api.example.com/openapi.json"  # OpenAPI spec URL

# Authentication is optional - omit for no authentication
authentication:
  type: "none"  # Explicit no authentication (same as omitting this section)
```

**When to use YAML configuration:**
- ✅ API requires authentication
- ✅ Need to filter specific endpoints or methods
- ✅ Want to use environment variables for credentials
- ✅ Complex API setup

**When to use CLI arguments:**
- ✅ Public API with no authentication
- ✅ Quick testing or prototyping
- ✅ Simple setup
- ✅ Default GET-only access is sufficient

### Authentication Options

#### No Authentication
```yaml
# Option 1: Omit authentication section entirely (recommended)
# No authentication section needed

# Option 2: Explicit none type
authentication:
  type: "none"
```

#### Bearer Token
```yaml
authentication:
  type: "bearer"
  token: "your-bearer-token"
  # Or use environment variable:
  # token: "${API_TOKEN}"
```

#### API Key
```yaml
authentication:
  type: "api_key"
  api_key: "your-api-key"
  header_name: "X-API-Key"  # Optional, defaults to "X-API-Key"
  # Or use environment variable:
  # api_key: "${API_KEY}"
```

#### Basic Authentication
```yaml
authentication:
  type: "basic"
  username: "your-username"
  password: "your-password"
  # Or use environment variables:
  # username: "${API_USER}"
  # password: "${API_PASS}"
```

### Path and Method Filtering

Control which API endpoints and HTTP methods are exposed as tools:

```yaml
server:
  name: "filtered-api"

openapi:
  spec_url: "https://api.example.com/openapi.json"

authentication:
  type: "none"

# Include only user and repo related endpoints
include_patterns:
  - "^/users"
  - "^/repos"

# Exclude admin endpoints
exclude_patterns:
  - "^/admin"
  - "^/internal"

# Only allow safe read operations
include_methods:
  - GET
  - HEAD

# Or exclude dangerous operations
exclude_methods:
  - DELETE
  - PUT
  - PATCH
```

#### Method Filtering Examples

**🛡️ Default Behavior** (automatic, no configuration needed):
```yaml
# GET-only operations are enabled by default for security
# No method filtering configuration needed for read-only access
server:
  name: "safe-api"
openapi:
  spec_url: "https://api.example.com/openapi.json"
```

**Enable Write Operations** (explicit opt-in required):
```yaml
include_methods:
  - GET
  - POST   # Allow creating resources
  - PUT    # Allow updating resources
```

**All Operations** (for full API access):
```yaml
include_methods:
  - GET
  - POST
  - PUT
  - DELETE
  - PATCH
```

**Exclude Specific Operations**:
```yaml
exclude_methods:
  - DELETE  # Allow all except delete
```

**Combined Path and Method Filtering**:
```yaml
# Only allow GET operations on user endpoints
include_patterns:
  - "^/users"
include_methods:
  - GET
```

### Environment Variables

Keep sensitive credentials out of your config files:

```yaml
server:
  name: "secure-api"

openapi:
  spec_url: "https://api.example.com/openapi.json"

authentication:
  type: "bearer"
  token: "${API_TOKEN}"  # Will read from environment variable
```

Set the environment variable:
```bash
export API_TOKEN="your-secret-token"
```

## Real-World Examples

### GitHub API Example

```yaml
server:
  name: "github-api"

openapi:
  spec_url: "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json"

authentication:
  type: "bearer"
  token: "${GITHUB_TOKEN}"

# Only expose user and repository operations
include_patterns:
  - "^/user"
  - "^/repos"

# Exclude admin operations
exclude_patterns:
  - "^/admin"
```

### Stripe API Example

```yaml
server:
  name: "stripe-api"

openapi:
  spec_url: "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"

authentication:
  type: "bearer"
  token: "${STRIPE_SECRET_KEY}"

# Only expose safe read operations
include_patterns:
  - "^/v1/customers"
  - "^/v1/products"
  - "^/v1/prices"

# Only allow read operations for safety
include_methods:
  - GET
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
