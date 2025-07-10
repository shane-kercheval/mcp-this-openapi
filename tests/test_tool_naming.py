"""Tests for tool naming utilities with clash detection."""


from mcp_this_openapi.openapi.tool_naming import (
    extract_version_from_path,
    generate_base_tool_name_from_path,
    generate_mcp_names_with_clash_detection,
    generate_mcp_names_from_spec,
)


class TestVersionExtraction:
    """Test version extraction from paths."""

    def test_extract_version_v1_pattern(self):
        """Test extraction of v1, v2, etc. patterns."""
        assert extract_version_from_path("/v1/users/") == ("v1", "/users/")
        assert extract_version_from_path("/v2/posts/") == ("v2", "/posts/")
        assert extract_version_from_path("/v10/items/") == ("v10", "/items/")

    def test_extract_version_api_pattern(self):
        """Test extraction of /api/v1/ patterns."""
        assert extract_version_from_path("/api/v1/users/") == ("v1", "/api/users/")
        assert extract_version_from_path("/api/v2/posts/") == ("v2", "/api/posts/")

    def test_extract_version_date_pattern(self):
        """Test extraction of date-based versions."""
        assert extract_version_from_path("/2023-01-01/users/") == ("2023-01-01", "/users/")
        assert extract_version_from_path("/api/2024-12-31/posts/") == ("2024-12-31", "/api/posts/")

    def test_extract_version_no_version(self):
        """Test paths without version patterns."""
        assert extract_version_from_path("/users/") == ("", "/users/")
        assert extract_version_from_path("/api/users/") == ("", "/api/users/")
        assert extract_version_from_path("/health/") == ("", "/health/")

    def test_extract_version_complex_paths(self):
        """Test version extraction from complex nested paths."""
        assert extract_version_from_path("/api/v1/users/{id}/posts/") == ("v1", "/api/users/{id}/posts/")  # noqa: E501
        assert extract_version_from_path("/v2/admin/settings/") == ("v2", "/admin/settings/")


class TestBaseNameGeneration:
    """Test base tool name generation."""

    def test_generate_base_name_simple(self):
        """Test simple path to name conversion."""
        assert generate_base_tool_name_from_path("GET", "/users/") == "get_users"
        assert generate_base_tool_name_from_path("POST", "/posts/") == "post_posts"
        assert generate_base_tool_name_from_path("DELETE", "/items/") == "delete_items"

    def test_generate_base_name_with_api_prefix(self):
        """Test paths with /api/ prefix."""
        assert generate_base_tool_name_from_path("GET", "/api/users/") == "get_users"
        assert generate_base_tool_name_from_path("POST", "/api/posts/") == "post_posts"

    def test_generate_base_name_nested_resources(self):
        """Test nested resource paths."""
        assert generate_base_tool_name_from_path("GET", "/users/posts/") == "get_users_posts"
        assert generate_base_tool_name_from_path("POST", "/customers/orders/") == "post_customers_orders"  # noqa: E501
        assert generate_base_tool_name_from_path("PUT", "/projects/tasks/") == "put_projects_tasks"

    def test_generate_base_name_with_path_parameters(self):
        """Test paths with parameters are filtered out."""
        assert generate_base_tool_name_from_path("GET", "/users/{id}/posts/") == "get_users_posts"
        assert generate_base_tool_name_from_path("PUT", "/users/{user_id}/settings/") == "put_users_settings"  # noqa: E501
        assert generate_base_tool_name_from_path("DELETE", "/projects/{project_id}/tasks/{task_id}/") == "delete_projects_tasks"  # noqa: E501

    def test_generate_base_name_with_hyphens(self):
        """Test paths with hyphens are converted to underscores."""
        assert generate_base_tool_name_from_path("POST", "/txt-2-sql/") == "post_txt_2_sql"
        assert generate_base_tool_name_from_path("GET", "/user-settings/") == "get_user_settings"

    def test_generate_base_name_edge_cases(self):
        """Test edge cases in path processing."""
        assert generate_base_tool_name_from_path("GET", "/") == "get"
        assert generate_base_tool_name_from_path("POST", "/api/") == "post"
        assert generate_base_tool_name_from_path("GET", "///users///") == "get_users"


class TestClashDetection:
    """Test the clash detection algorithm."""

    def test_no_clashes_simple(self):
        """Test case with no name clashes."""
        spec = {
            "paths": {
                "/users/": {
                    "get": {"operationId": "getUsers"},
                },
                "/posts/": {
                    "get": {"operationId": "getPosts"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "getUsers": "get_users",
            "getPosts": "get_posts",
        }
        assert result == expected

    def test_version_clash_resolution(self):
        """Test clash resolution with versioned endpoints."""
        spec = {
            "paths": {
                "/v1/users/": {
                    "get": {"operationId": "getUsersV1"},
                },
                "/v2/users/": {
                    "get": {"operationId": "getUsersV2"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "getUsersV1": "v1_get_users",
            "getUsersV2": "v2_get_users",
        }
        assert result == expected

    def test_mixed_version_clash(self):
        """Test clash with one versioned and one non-versioned endpoint."""
        spec = {
            "paths": {
                "/users/": {
                    "get": {"operationId": "getUsers"},
                },
                "/v2/users/": {
                    "get": {"operationId": "getUsersV2"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "getUsers": "get_users",        # No version, keeps base name
            "getUsersV2": "v2_get_users",    # Has version, gets prefixed
        }
        assert result == expected

    def test_complex_api_clash_resolution(self):
        """Test clash resolution in complex API with multiple versions."""
        spec = {
            "paths": {
                "/api/v1/users/": {
                    "get": {"operationId": "getUsersV1"},
                },
                "/api/v2/users/": {
                    "get": {"operationId": "getUsersV2"},
                },
                "/api/v1/users/{id}/posts/": {
                    "get": {"operationId": "getUserPostsV1"},
                },
                "/api/v2/users/{id}/posts/": {
                    "get": {"operationId": "getUserPostsV2"},
                },
                "/health/": {
                    "get": {"operationId": "getHealth"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "getUsersV1": "v1_get_users",
            "getUsersV2": "v2_get_users",
            "getUserPostsV1": "v1_get_users_posts",
            "getUserPostsV2": "v2_get_users_posts",
            "getHealth": "get_health",  # No clash, no version needed
        }
        assert result == expected

    def test_no_version_clash_unresolvable(self):
        """Test case where clashes can't be resolved due to no versions."""
        spec = {
            "paths": {
                "/users/": {
                    "get": {"operationId": "getUsers1"},
                },
                "/api/users/": {
                    "get": {"operationId": "getUsers2"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        # Both should get the same name since no versions are available
        expected = {
            "getUsers1": "get_users",
            "getUsers2": "get_users",
        }
        assert result == expected

    def test_nested_resources_no_clash(self):
        """Test that different nested resources don't clash."""
        spec = {
            "paths": {
                "/users/{id}/posts/": {
                    "get": {"operationId": "getUserPosts"},
                },
                "/posts/": {
                    "get": {"operationId": "getPosts"},
                },
                "/users/{id}/settings/": {
                    "get": {"operationId": "getUserSettings"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "getUserPosts": "get_users_posts",
            "getPosts": "get_posts",
            "getUserSettings": "get_users_settings",
        }
        assert result == expected

    def test_multiple_methods_same_path(self):
        """Test multiple HTTP methods on the same path."""
        spec = {
            "paths": {
                "/users/": {
                    "get": {"operationId": "getUsers"},
                    "post": {"operationId": "createUser"},
                    "put": {"operationId": "updateUsers"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "getUsers": "get_users",
            "createUser": "post_users",
            "updateUsers": "put_users",
        }
        assert result == expected


class TestMcpNamesGeneration:
    """Test the main MCP names generation function."""

    def test_default_strategy_operationid(self):
        """Test default strategy uses operationId."""
        spec = {
            "paths": {
                "/users/": {
                    "get": {"operationId": "getUsersList__get"},
                },
                "/posts/": {
                    "post": {"operationId": "createNewPost__post"},
                },
            },
        }

        result = generate_mcp_names_from_spec(spec, use_operation_id=True)
        expected = {
            "getUsersList__get": "getUsersList",      # Double underscore suffix removed
            "createNewPost__post": "createNewPost",    # Double underscore suffix removed
        }
        assert result == expected

    def test_auto_strategy_with_clash_detection(self):
        """Test auto strategy uses smart generation."""
        spec = {
            "paths": {
                "/v1/users/": {
                    "get": {"operationId": "getUsersV1"},
                },
                "/v2/users/": {
                    "get": {"operationId": "getUsersV2"},
                },
                "/health/": {
                    "get": {"operationId": "getHealth"},
                },
            },
        }

        result = generate_mcp_names_from_spec(spec, use_operation_id=False)
        expected = {
            "getUsersV1": "v1_get_users",
            "getUsersV2": "v2_get_users",
            "getHealth": "get_health",
        }
        assert result == expected

    def test_missing_operation_id_skipped(self):
        """Test that operations without operationId are skipped."""
        spec = {
            "paths": {
                "/users/": {
                    "get": {"operationId": "getUsers"},
                    "post": {},  # Missing operationId
                },
            },
        }

        result = generate_mcp_names_from_spec(spec, use_operation_id=True)
        expected = {
            "getUsers": "getUsers",
        }
        assert result == expected

    def test_non_http_methods_skipped(self):
        """Test that non-HTTP methods are skipped."""
        spec = {
            "paths": {
                "/users/": {
                    "get": {"operationId": "getUsers"},
                    "parameters": [{"name": "test"}],  # Not an HTTP method
                    "summary": "Users endpoint",       # Not an HTTP method
                },
            },
        }

        result = generate_mcp_names_from_spec(spec, use_operation_id=True)
        expected = {
            "getUsers": "getUsers",
        }
        assert result == expected


class TestRealWorldScenarios:
    """Test scenarios based on real API patterns."""

    def test_your_api_scenario(self):
        """Test the specific scenario from your API."""
        spec = {
            "paths": {
                "/api/v1/schemas/": {
                    "get": {"operationId": "get_schemas_api_v1_schemas__get"},
                },
                "/api/v2/schemas/": {
                    "get": {"operationId": "get_schemas_api_v2_schemas__get"},
                },
                "/health/": {
                    "get": {"operationId": "get_status_health__get"},
                },
                "/api/v1/query/": {
                    "post": {"operationId": "post_query_api_v1_query__post"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "get_schemas_api_v1_schemas__get": "v1_get_schemas",
            "get_schemas_api_v2_schemas__get": "v2_get_schemas",
            "get_status_health__get": "get_health",
            "post_query_api_v1_query__post": "post_query",  # No clash, no version needed
        }
        assert result == expected

    def test_github_api_pattern(self):
        """Test GitHub-style API patterns."""
        spec = {
            "paths": {
                "/user": {
                    "get": {"operationId": "getAuthenticatedUser"},
                },
                "/users/{username}": {
                    "get": {"operationId": "getUser"},
                },
                "/user/repos": {
                    "get": {"operationId": "getUserRepos"},
                },
                "/repos/{owner}/{repo}": {
                    "get": {"operationId": "getRepo"},
                },
            },
        }

        result = generate_mcp_names_with_clash_detection(spec)
        expected = {
            "getAuthenticatedUser": "get_user",
            "getUser": "get_users",          # Different from get_user (singular vs plural)
            "getUserRepos": "get_user_repos",
            "getRepo": "get_repos",
        }
        assert result == expected
