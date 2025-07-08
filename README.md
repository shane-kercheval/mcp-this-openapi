# mcp-this-openapi

[![Tests](https://github.com/shane-kercheval/mcp-this-openai/actions/workflows/tests.yaml/badge.svg)](https://github.com/shane-kercheval/mcp-this-openai/actions/workflows/tests.yaml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol (MCP) server that automatically generates tools from OpenAPI/Swagger specifications, allowing MCP Clients (e.g. Claude Desktop) to interact with any REST API.

## Features

- 🔄 **Automatic Tool Generation**: Converts OpenAPI specs into callable MCP tools
- 🔐 **Multiple Authentication Types**: Bearer tokens, API keys, Basic auth, or no auth
- 🎯 **Path Filtering**: Include/exclude specific API endpoints using regex patterns
- 🌐 **Flexible Spec Loading**: Supports both JSON and YAML OpenAPI specifications
- 🔒 **Environment Variables**: Secure credential management with `${VAR_NAME}` expansion

## Quick Start with Petstore API

The easiest way to get started is with the Swagger Petstore demo API:

### 1. Create Configuration File

Create `petstore-config.yaml`:

```yaml
server:
  name: "petstore-demo"

openapi:
  spec_url: "https://petstore3.swagger.io/api/v3/openapi.json"

authentication:
  type: "none"
```

### 2. Configure Claude Desktop

Add this to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "petstore": {
      "command": "uvx",
      "args": [
        "mcp-mcp_this_openapi",
        "--config-path",
        "/path/to/your/petstore-config.yaml"
      ]
    }
  }
}
```

### 3. Try it in Claude

Once configured, you can ask Claude things like:

- "What pet operations are available?"
- "Get information about pet with ID 1"
- "Show me the pet store inventory"

## Configuration Reference

### Basic Configuration

```yaml
server:
  name: "my-api-server"  # Name displayed in Claude

openapi:
  spec_url: "https://api.example.com/openapi.json"  # OpenAPI spec URL

authentication:
  type: "none"  # No authentication required
```

### Authentication Options

#### No Authentication
```yaml
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

### Path Filtering

Control which API endpoints are exposed as tools:

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

# Exclude dangerous operations
exclude_patterns:
  - "^/v1/.*delete"
  - "^/v1/charges"
```

## Claude Desktop Integration

### macOS Configuration Location
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Complete Claude Desktop Configuration Example

```json
{
  "mcpServers": {
    "petstore": {
      "command": "python",
      "args": [
        "-m", 
        "mcp_this_openapi", 
        "--config-path", 
        "/Users/yourusername/configs/petstore.yaml"
      ]
    },
    "github": {
      "command": "python",
      "args": [
        "-m", 
        "mcp_this_openapi", 
        "--config-path", 
        "/Users/yourusername/configs/github.yaml"
      ],
      "env": {
        "GITHUB_TOKEN": "your-github-token-here"
      }
    }
  }
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
