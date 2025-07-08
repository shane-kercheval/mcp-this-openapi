"""Tests for the CLI main module."""

import pytest
import tempfile
import os
from unittest.mock import patch
from pathlib import Path

from mcp_this_openapi.__main__ import main, find_default_config


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
