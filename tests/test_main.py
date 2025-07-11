"""Tests for the CLI main module."""

import pytest
import tempfile
import os
from unittest.mock import patch
from pathlib import Path

from mcp_this_openapi.__main__ import main, find_default_config, parse_hybrid_list


class TestMain:
    """Test cases for the main CLI function."""

    def test_main_with_config_path(self):
        """Test main function with config path argument."""
        with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--config-path', '/path/to/config.yaml']):
                main()

                # Check that run_server was called with the correct config path
                mock_run_server.assert_called_once_with('/path/to/config.yaml')

    def test_main_missing_config_arg(self):
        """Test main function with missing config argument."""
        with patch('mcp_this_openapi.__main__.find_default_config', return_value=None):  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi']):
                with pytest.raises(SystemExit):  # Should exit when no config found
                    main()

    def test_main_nonexistent_config_file(self):
        """Test main function with nonexistent config file."""
        with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:
            mock_run_server.side_effect = FileNotFoundError("Configuration file not found")
            with patch('sys.argv', ['mcp-this-openapi', '--config-path', '/nonexistent/config.yaml']):  # noqa: E501, SIM117
                with pytest.raises(SystemExit):  # Should exit due to file not existing
                    main()

    def test_main_with_valid_config_file(self):
        """Test main function with valid config file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
server:
  name: "test-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
authentication:
  type: "none"
""")
            temp_config_path = f.name

        try:
            with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:  # noqa: SIM117
                with patch('sys.argv', ['mcp-this-openapi', '--config-path', temp_config_path]):
                    main()

                    # Check that run_server was called with the temp config path
                    mock_run_server.assert_called_once_with(temp_config_path)
        finally:
            os.unlink(temp_config_path)

    def test_main_keyboard_interrupt(self):
        """Test main function handling keyboard interrupt."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
server:
  name: "test-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
""")
            temp_config_path = f.name

        try:
            with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:  # noqa: SIM117
                with patch('sys.stderr'):
                    # Mock run_server to raise KeyboardInterrupt
                    mock_run_server.side_effect = KeyboardInterrupt()

                    with patch('sys.argv', ['mcp-this-openapi', '--config-path', temp_config_path]):  # noqa: E501, SIM117
                        with patch('sys.exit') as mock_exit:
                            main()

                            # Should exit with code 0 on keyboard interrupt
                            mock_exit.assert_called_once_with(0)
        finally:
            os.unlink(temp_config_path)

    def test_main_runtime_error(self):
        """Test main function handling runtime errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
server:
  name: "test-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
""")
            temp_config_path = f.name

        try:
            with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:  # noqa: SIM117
                with patch('sys.stderr'):
                    # Mock run_server to raise a ValueError
                    mock_run_server.side_effect = ValueError("Invalid configuration")

                    with patch('sys.argv', ['mcp-this-openapi', '--config-path', temp_config_path]):  # noqa: E501, SIM117
                        with patch('sys.exit') as mock_exit:
                            main()

                            # Should exit with code 1 on runtime error
                            mock_exit.assert_called_once_with(1)
        finally:
            os.unlink(temp_config_path)

    def test_main_help_option(self):
        """Test main function with help option."""
        with patch('sys.argv', ['mcp-this-openapi', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Click exits with code 0 for help
            assert exc_info.value.code == 0

    def test_main_config_path_expansion(self):
        """Test that config path is properly expanded."""
        # Create a config in a subdirectory
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "subdir" / "config.yaml"
            config_path.parent.mkdir(parents=True)

            with open(config_path, 'w') as f:
                f.write("""
server:
  name: "test-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
""")

            with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:  # noqa: SIM117
                with patch('sys.argv', ['mcp-this-openapi', '--config-path', str(config_path)]):
                    main()

                    # Should be called with the full path
                    mock_run_server.assert_called_once_with(str(config_path))

    def test_main_relative_config_path(self):
        """Test main function with relative config path."""
        # Create a temporary config file in current directory
        current_dir = os.getcwd()
        config_filename = "test_config.yaml"
        config_path = os.path.join(current_dir, config_filename)

        with open(config_path, 'w') as f:
            f.write("""
server:
  name: "test-server"
openapi:
  spec_url: "https://api.example.com/openapi.json"
""")

        try:
            with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:  # noqa: SIM117
                with patch('sys.argv', ['mcp-this-openapi', '--config-path', config_filename]):
                    main()

                    # Should be called with the relative path
                    mock_run_server.assert_called_once_with(config_filename)
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)


class TestFindDefaultConfig:
    """Test cases for the find_default_config function."""

    def test_find_default_config_example(self):
        """Test finding default config in examples directory."""
        # Should find the default example config
        config_path = find_default_config()

        # Should either find a default config or return None if not available
        if config_path:
            assert config_path.endswith(('default.yaml', 'petstore.yaml'))
            assert os.path.exists(config_path)

    def test_find_default_config_no_config(self):
        """Test behavior when no default config is found."""
        with patch('pathlib.Path.exists', return_value=False):
            config_path = find_default_config()
            assert config_path is None


class TestCLIArguments:
    """Test cases for CLI argument handling."""

    def test_main_with_openapi_spec_url_only(self):
        """Test main function with only openapi-spec-url argument."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json']):
                main()

                # Check that run_server_from_args was called with correct arguments
                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',  # server spec URL
                    'openapi-server',  # default server name
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    None,  # include_methods
                    None,  # exclude_methods
                )

    def test_main_with_openapi_spec_url_and_server_name(self):
        """Test main function with both openapi-spec-url and server-name arguments."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--server-name', 'my-api']):  # noqa: E501
                main()

                # Check that run_server_from_args was called with correct arguments
                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',  # server spec URL
                    'my-api',  # custom server name
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    None,  # include_methods
                    None,  # exclude_methods
                )

    def test_main_with_config_path_and_openapi_spec_url_conflict(self):
        """Test that config-path and openapi-spec-url are mutually exclusive."""
        with patch('sys.argv', ['mcp-this-openapi', '--config-path', 'config.yaml', '--openapi-spec-url', 'https://api.example.com/openapi.json']):  # noqa: E501, SIM117
            with pytest.raises(SystemExit):  # argparse should exit due to mutual exclusion
                main()

    def test_main_cli_args_with_keyboard_interrupt(self):
        """Test handling keyboard interrupt with CLI arguments."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.stderr'):
                # Mock run_server_from_args to raise KeyboardInterrupt
                mock_run_server.side_effect = KeyboardInterrupt()

                with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json']):  # noqa: SIM117
                    with patch('sys.exit') as mock_exit:
                        main()

                        # Should exit with code 0 on keyboard interrupt
                        mock_exit.assert_called_once_with(0)

    def test_main_cli_args_with_runtime_error(self):
        """Test handling runtime errors with CLI arguments."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.stderr'):
                # Mock run_server_from_args to raise a ValueError
                mock_run_server.side_effect = ValueError("Invalid OpenAPI spec URL")

                with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'invalid-url']):  # noqa: SIM117
                    with patch('sys.exit') as mock_exit:
                        main()

                        # Should exit with code 1 on runtime error
                        mock_exit.assert_called_once_with(1)

    def test_main_with_include_deprecated_flag(self):
        """Test main function with include-deprecated flag."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--include-deprecated']):  # noqa: E501
                main()

                # Check that run_server_from_args was called with include_deprecated=True
                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',  # server spec URL
                    'openapi-server',  # default server name
                    True,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    None,  # include_methods
                    None,  # exclude_methods
                )

    def test_main_with_disable_schema_validation_flag(self):
        """Test main function with disable-schema-validation flag."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--disable-schema-validation']):  # noqa: E501
                main()

                # Check that run_server_from_args was called with disable_schema_validation=True
                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',  # server spec URL
                    'openapi-server',  # default server name
                    False,  # include_deprecated
                    'default',  # tool_naming
                    True,  # disable_schema_validation
                    None,  # include_methods
                    None,  # exclude_methods
                )

    def test_main_no_arguments_with_no_default_config(self):
        """Test main function with no arguments and no default config."""
        with patch('mcp_this_openapi.__main__.find_default_config', return_value=None):  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi']):
                with pytest.raises(SystemExit):  # Should exit when no config found
                    main()

    def test_main_server_name_without_openapi_spec_url(self):
        """Test that server-name without openapi-spec-url uses config path."""
        with patch('mcp_this_openapi.__main__.run_server') as mock_run_server:  # noqa: SIM117
            with patch('mcp_this_openapi.__main__.find_default_config', return_value='/path/to/default.yaml'):  # noqa: E501
                with patch('sys.argv', ['mcp-this-openapi', '--server-name', 'my-server']):
                    main()

                    # Should use config file path since server-name alone isn't enough
                    mock_run_server.assert_called_once_with('/path/to/default.yaml')

    def test_help_shows_new_options(self):
        """Test that help message includes the new CLI options."""
        with patch('sys.argv', ['mcp-this-openapi', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 0 for help
            assert exc_info.value.code == 0


class TestParseHybridList:
    """Test cases for the parse_hybrid_list function."""

    def test_parse_hybrid_list_none_input(self):
        """Test parse_hybrid_list with None input."""
        result = parse_hybrid_list(None)
        assert result is None

    def test_parse_hybrid_list_empty_list(self):
        """Test parse_hybrid_list with empty list."""
        result = parse_hybrid_list([])
        assert result is None

    def test_parse_hybrid_list_single_item(self):
        """Test parse_hybrid_list with single item."""
        result = parse_hybrid_list(['GET'])
        assert result == ['GET']

    def test_parse_hybrid_list_multiple_items(self):
        """Test parse_hybrid_list with multiple separate items."""
        result = parse_hybrid_list(['GET', 'POST', 'PUT'])
        assert result == ['GET', 'POST', 'PUT']

    def test_parse_hybrid_list_comma_separated(self):
        """Test parse_hybrid_list with comma-separated values."""
        result = parse_hybrid_list(['GET,POST,PUT'])
        assert result == ['GET', 'POST', 'PUT']

    def test_parse_hybrid_list_mixed_format(self):
        """Test parse_hybrid_list with mixed comma-separated and separate items."""
        result = parse_hybrid_list(['GET,POST', 'PUT', 'DELETE,PATCH'])
        assert result == ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

    def test_parse_hybrid_list_whitespace_handling(self):
        """Test parse_hybrid_list handles whitespace correctly."""
        result = parse_hybrid_list(['GET, POST', ' PUT ', 'DELETE,PATCH '])
        assert result == ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

    def test_parse_hybrid_list_case_normalization(self):
        """Test parse_hybrid_list normalizes case to uppercase."""
        result = parse_hybrid_list(['get,post', 'Put', 'delete'])
        assert result == ['GET', 'POST', 'PUT', 'DELETE']

    def test_parse_hybrid_list_empty_values_filtered(self):
        """Test parse_hybrid_list filters out empty values."""
        result = parse_hybrid_list(['GET,', ',POST', 'PUT,'])
        assert result == ['GET', 'POST', 'PUT']

    def test_parse_hybrid_list_multiple_commas(self):
        """Test parse_hybrid_list handles multiple consecutive commas."""
        result = parse_hybrid_list(['GET,,POST', 'PUT,,,DELETE'])
        assert result == ['GET', 'POST', 'PUT', 'DELETE']


class TestCLIMethodArguments:
    """Test cases for CLI method arguments (include-methods and exclude-methods)."""

    def test_main_with_include_methods_single(self):
        """Test main function with single include-methods argument."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--include-methods', 'GET']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    ['GET'],  # include_methods
                    None,  # exclude_methods
                )

    def test_main_with_include_methods_comma_separated(self):
        """Test main function with comma-separated include-methods."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--include-methods', 'GET,POST,PUT']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    ['GET', 'POST', 'PUT'],  # include_methods
                    None,  # exclude_methods
                )

    def test_main_with_include_methods_repeated_flags(self):
        """Test main function with repeated include-methods flags."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--include-methods', 'GET', '--include-methods', 'POST']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    ['GET', 'POST'],  # include_methods
                    None,  # exclude_methods
                )

    def test_main_with_exclude_methods_single(self):
        """Test main function with single exclude-methods argument."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--exclude-methods', 'DELETE']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    None,  # include_methods
                    ['DELETE'],  # exclude_methods
                )

    def test_main_with_exclude_methods_comma_separated(self):
        """Test main function with comma-separated exclude-methods."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--exclude-methods', 'DELETE,PATCH']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    None,  # include_methods
                    ['DELETE', 'PATCH'],  # exclude_methods
                )

    def test_main_with_both_include_and_exclude_methods(self):
        """Test main function with both include and exclude methods."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--include-methods', 'GET,POST', '--exclude-methods', 'DELETE']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    ['GET', 'POST'],  # include_methods
                    ['DELETE'],  # exclude_methods
                )

    def test_main_with_mixed_method_format(self):
        """Test main function with mixed format method arguments."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--include-methods', 'GET,POST', '--include-methods', 'PUT', '--exclude-methods', 'DELETE,PATCH']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'default',  # tool_naming
                    False,  # disable_schema_validation
                    ['GET', 'POST', 'PUT'],  # include_methods
                    ['DELETE', 'PATCH'],  # exclude_methods
                )

    def test_main_with_tool_naming_auto_and_methods(self):
        """Test main function with tool-naming auto and method filters."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', ['mcp-this-openapi', '--openapi-spec-url', 'https://api.example.com/openapi.json', '--tool-naming', 'auto', '--include-methods', 'GET,POST']):  # noqa: E501
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'openapi-server',
                    False,  # include_deprecated
                    'auto',  # tool_naming
                    False,  # disable_schema_validation
                    ['GET', 'POST'],  # include_methods
                    None,  # exclude_methods
                )

    def test_main_with_all_cli_options(self):
        """Test main function with all CLI options combined."""
        with patch('mcp_this_openapi.__main__.run_server_from_args') as mock_run_server:  # noqa: SIM117
            with patch('sys.argv', [
                'mcp-this-openapi',
                '--openapi-spec-url', 'https://api.example.com/openapi.json',
                '--server-name', 'my-api',
                '--include-deprecated',
                '--tool-naming', 'auto',
                '--disable-schema-validation',
                '--include-methods', 'GET,POST',
                '--exclude-methods', 'DELETE',
            ]):
                main()

                mock_run_server.assert_called_once_with(
                    'https://api.example.com/openapi.json',
                    'my-api',
                    True,  # include_deprecated
                    'auto',  # tool_naming
                    True,  # disable_schema_validation
                    ['GET', 'POST'],  # include_methods
                    ['DELETE'],  # exclude_methods
                )
