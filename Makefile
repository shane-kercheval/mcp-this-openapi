.PHONY: tests build linting unittests coverage mcp_dev mcp_install mcp_test verify package package-build package-publish help

-include .env
export

####
# Project
####

help: ## Display this help
	@echo "MCP-This-OpenAPI Development Commands"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Install dependencies 
	uv sync

####
# Development
####

mcp_dev: ## Run the MCP server with config in development mode
	uv run mcp dev ./src/mcp_this_openapi/server.py

mcp_install: ## Install the MCP server in Claude Desktop
	uv run mcp install --name "MCP-This-OpenAPI" ./src/mcp_this_openapi/server.py

mcp_test: ## Run the sample test server
	uv run mcp dev ./src/mcp_this_openapi/server.py

####
# Testing
####

linting: ## Run linting checks
	uv run ruff check src --fix --unsafe-fixes
	uv run ruff check tests --fix --unsafe-fixes

unittests: ## Run unit tests
	uv run pytest tests -v --durations=10

tests: linting unittests

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
