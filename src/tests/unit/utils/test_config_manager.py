#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the config_manager module.

This module contains unit tests for the configuration management functionality:
- Loading configuration
- Saving configuration
- Getting configuration values
- Setting configuration values
"""

import os
import tempfile
import unittest
import yaml
from unittest.mock import patch, MagicMock

import pytest
from src.tests.base_test import BaseTest
from src.utils.config_manager import (
    ConfigManager, get_config, save_config,
    get_config_value, set_config_value, DEFAULT_CONFIG_PATH
)


class TestConfigManager(BaseTest):
    """Unit tests for the ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test config file
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.test_config = {
            "application": {
                "name": "TestApp",
                "version": "1.0.0"
            },
            "ui": {
                "theme": "dark",
                "font": {
                    "family": "Arial",
                    "size": 12
                }
            },
            "data": {
                "directory": "/path/to/data"
            }
        }
        
        # Write the test config to file
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.test_config, f, default_flow_style=False)
        
        # Create a ConfigManager instance
        self.config_manager = ConfigManager(self.config_path)
    
    def test_init_with_existing_config(self):
        """Test initializing with an existing config file."""
        # Verify the config was loaded
        self.assertEqual(self.config_manager.config_path, self.config_path)
        self.assertEqual(self.config_manager.config, self.test_config)
    
    def test_init_with_nonexistent_config(self):
        """Test initializing with a non-existent config file."""
        # Create a path to a non-existent config file
        nonexistent_path = os.path.join(self.test_dir, "nonexistent.yaml")
        
        # Create a ConfigManager instance
        with patch("logging.Logger.warning") as mock_warning:
            config_manager = ConfigManager(nonexistent_path)
        
        # Verify a warning was logged
        mock_warning.assert_called_once()
        
        # Verify a default config was created
        self.assertEqual(config_manager.config_path, nonexistent_path)
        self.assertIsInstance(config_manager.config, dict)
        self.assertIn("application", config_manager.config)
        self.assertIn("ui", config_manager.config)
        
        # Verify the config file was created
        self.assertTrue(os.path.exists(nonexistent_path))
    
    def test_get_value_with_existing_key(self):
        """Test getting a value with an existing key."""
        # Get a value
        value = self.config_manager.get_value("application.name")
        
        # Verify the value
        self.assertEqual(value, "TestApp")
    
    def test_get_value_with_nonexistent_key(self):
        """Test getting a value with a non-existent key."""
        # Get a value with a non-existent key
        value = self.config_manager.get_value("nonexistent.key", "default")
        
        # Verify the default value was returned
        self.assertEqual(value, "default")
    
    def test_get_value_with_nested_key(self):
        """Test getting a value with a nested key."""
        # Get a value with a nested key
        value = self.config_manager.get_value("ui.font.family")
        
        # Verify the value
        self.assertEqual(value, "Arial")
    
    def test_get_with_section_and_subkey(self):
        """Test getting a value with a section and subkey."""
        # Get a value with a section and subkey
        value = self.config_manager.get("ui", "theme")
        
        # Verify the value
        self.assertEqual(value, "dark")
    
    def test_get_with_nonexistent_section(self):
        """Test getting a value with a non-existent section."""
        # Get a value with a non-existent section
        value = self.config_manager.get("nonexistent", "key", "default")
        
        # Verify the default value was returned
        self.assertEqual(value, "default")
    
    def test_get_with_nonexistent_subkey(self):
        """Test getting a value with a non-existent subkey."""
        # Get a value with a non-existent subkey
        value = self.config_manager.get("ui", "nonexistent", "default")
        
        # Verify the default value was returned
        self.assertEqual(value, "default")
    
    def test_get_section(self):
        """Test getting an entire section."""
        # Get an entire section
        section = self.config_manager.get("ui")
        
        # Verify the section
        self.assertEqual(section, self.test_config["ui"])
    
    def test_set_value_with_existing_key(self):
        """Test setting a value with an existing key."""
        # Set a value
        result = self.config_manager.set_value("application.name", "NewApp")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the value was set
        self.assertEqual(self.config_manager.get_value("application.name"), "NewApp")
        
        # Verify the config file was updated
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["application"]["name"], "NewApp")
    
    def test_set_value_with_new_key(self):
        """Test setting a value with a new key."""
        # Set a value with a new key
        result = self.config_manager.set_value("new.section.key", "value")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the value was set
        self.assertEqual(self.config_manager.get_value("new.section.key"), "value")
        
        # Verify the config file was updated
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["new"]["section"]["key"], "value")
    
    def test_set_with_existing_section_and_key(self):
        """Test setting a value with an existing section and key."""
        # Set a value
        result = self.config_manager.set("ui", "theme", "light")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the value was set
        self.assertEqual(self.config_manager.get("ui", "theme"), "light")
        
        # Verify the config file was updated
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["ui"]["theme"], "light")
    
    def test_set_with_new_section(self):
        """Test setting a value with a new section."""
        # Set a value with a new section
        result = self.config_manager.set("new_section", "key", "value")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the value was set
        self.assertEqual(self.config_manager.get("new_section", "key"), "value")
        
        # Verify the config file was updated
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["new_section"]["key"], "value")
    
    def test_get_config(self):
        """Test getting the entire configuration."""
        # Get the entire configuration
        config = self.config_manager.get_config()
        
        # Verify the configuration
        self.assertEqual(config, self.test_config)
    
    def test_save_config(self):
        """Test saving the configuration."""
        # Modify the configuration
        self.config_manager.config["application"]["name"] = "ModifiedApp"
        
        # Save the configuration
        result = self.config_manager.save_config()
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the config file was updated
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["application"]["name"], "ModifiedApp")
    
    def test_save_config_with_error(self):
        """Test saving the configuration with an error."""
        # Modify the configuration
        self.config_manager.config["application"]["name"] = "ModifiedApp"
        
        # Mock open to raise an exception
        with patch("builtins.open", side_effect=Exception("Test error")):
            # Save the configuration
            result = self.config_manager.save_config()
        
        # Verify the result
        self.assertFalse(result)


class TestConfigManagerFunctions(BaseTest):
    """Unit tests for the config_manager module functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test config file
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.test_config = {
            "application": {
                "name": "TestApp",
                "version": "1.0.0"
            },
            "ui": {
                "theme": "dark"
            }
        }
        
        # Write the test config to file
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.test_config, f, default_flow_style=False)
        
        # Reset the singleton instance
        from src.utils.config_manager import _config_manager_instance
        import src.utils.config_manager
        src.utils.config_manager._config_manager_instance = None
    
    def test_get_config_function(self):
        """Test the get_config function."""
        # Get the config manager
        config_manager = get_config(self.config_path)
        
        # Verify the config manager
        self.assertIsInstance(config_manager, ConfigManager)
        self.assertEqual(config_manager.config_path, self.config_path)
        self.assertEqual(config_manager.config, self.test_config)
        
        # Get the config manager again
        config_manager2 = get_config(self.config_path)
        
        # Verify it's the same instance
        self.assertIs(config_manager2, config_manager)
        
        # Get the config manager with a different path
        different_path = os.path.join(self.test_dir, "different.yaml")
        config_manager3 = get_config(different_path)
        
        # Verify it's a different instance
        self.assertIsNot(config_manager3, config_manager)
        self.assertEqual(config_manager3.config_path, different_path)
    
    def test_save_config_function(self):
        """Test the save_config function."""
        # Modify the configuration
        self.test_config["application"]["name"] = "ModifiedApp"
        
        # Save the configuration
        result = save_config(self.test_config, self.config_path)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the config file was updated
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["application"]["name"], "ModifiedApp")
    
    def test_save_config_function_with_default_path(self):
        """Test the save_config function with the default path."""
        # Create a backup of the default config file if it exists
        default_config_backup = None
        if os.path.exists(DEFAULT_CONFIG_PATH):
            with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
                default_config_backup = f.read()
        
        try:
            # Modify the configuration
            self.test_config["application"]["name"] = "ModifiedApp"
            
            # Save the configuration with the default path
            with patch("src.utils.config_manager.DEFAULT_CONFIG_PATH", self.config_path):
                result = save_config(self.test_config)
            
            # Verify the result
            self.assertTrue(result)
            
            # Verify the config file was updated
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self.assertEqual(config["application"]["name"], "ModifiedApp")
        
        finally:
            # Restore the default config file if it existed
            if default_config_backup is not None:
                with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
                    f.write(default_config_backup)
    
    def test_get_config_value_function(self):
        """Test the get_config_value function."""
        # Get a value
        value = get_config_value("application.name", config_path=self.config_path)
        
        # Verify the value
        self.assertEqual(value, "TestApp")
        
        # Get a value with a non-existent key
        value = get_config_value("nonexistent.key", "default", config_path=self.config_path)
        
        # Verify the default value was returned
        self.assertEqual(value, "default")
    
    def test_set_config_value_function(self):
        """Test the set_config_value function."""
        # Set a value
        result = set_config_value("application.name", "NewApp", config_path=self.config_path)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the value was set
        value = get_config_value("application.name", config_path=self.config_path)
        self.assertEqual(value, "NewApp")
        
        # Verify the config file was updated
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["application"]["name"], "NewApp")


# Pytest-style tests
class TestConfigManagerPytest:
    """Pytest-style tests for the config_manager module."""
    
    @pytest.fixture
    def setup(self, base_test_fixture):
        """Set up test fixtures."""
        # Create a test config file
        config_path = os.path.join(base_test_fixture["test_dir"], "test_config.yaml")
        test_config = {
            "application": {
                "name": "TestApp",
                "version": "1.0.0"
            },
            "ui": {
                "theme": "dark",
                "font": {
                    "family": "Arial",
                    "size": 12
                }
            }
        }
        
        # Write the test config to file
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        # Create a ConfigManager instance
        config_manager = ConfigManager(config_path)
        
        # Reset the singleton instance
        from src.utils.config_manager import _config_manager_instance
        import src.utils.config_manager
        src.utils.config_manager._config_manager_instance = None
        
        return {
            **base_test_fixture,
            "config_path": config_path,
            "test_config": test_config,
            "config_manager": config_manager
        }
    
    def test_get_value_pytest(self, setup):
        """Test getting a value using pytest style."""
        # Get a value
        value = setup["config_manager"].get_value("application.name")
        
        # Verify the value
        assert value == "TestApp"
        
        # Get a value with a non-existent key
        value = setup["config_manager"].get_value("nonexistent.key", "default")
        
        # Verify the default value was returned
        assert value == "default"
        
        # Get a value with a nested key
        value = setup["config_manager"].get_value("ui.font.family")
        
        # Verify the value
        assert value == "Arial"
    
    def test_set_value_pytest(self, setup):
        """Test setting a value using pytest style."""
        # Set a value
        result = setup["config_manager"].set_value("application.name", "NewApp")
        
        # Verify the result
        assert result is True
        
        # Verify the value was set
        assert setup["config_manager"].get_value("application.name") == "NewApp"
        
        # Verify the config file was updated
        with open(setup["config_path"], "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert config["application"]["name"] == "NewApp"


if __name__ == '__main__':
    unittest.main()
