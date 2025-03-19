#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the configuration migration module.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import yaml

from src.tests.base_test import BaseTest
from src.utils.config_migration import (
    get_config_version,
    compare_versions,
    get_migration_steps,
    migrate_config_0_0_0_to_0_1_0,
    migrate_config_0_1_0_to_0_2_0,
    migrate_config_0_2_0_to_0_3_0,
    migrate_config,
    backup_config,
    migrate_config_file
)


class TestConfigMigration(BaseTest):
    """Test case for the configuration migration module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configurations
        self.config_v0 = {}
        
        self.config_v1 = {
            "application": {
                "name": "RebelSCRIBE",
                "version": "0.1.0"
            },
            "ui": {
                "theme": "light"
            }
        }
        
        self.config_v2 = {
            "application": {
                "name": "RebelSCRIBE",
                "version": "0.2.0"
            },
            "ui": {
                "color_theme": "light",
                "show_toolbar": True,
                "show_statusbar": True
            },
            "editor": {
                "font_family": "Courier New",
                "font_size": 12,
                "line_spacing": 1.5,
                "show_line_numbers": True,
                "auto_save": True,
                "auto_save_interval": 60
            }
        }
        
        self.config_v3 = {
            "application": {
                "name": "RebelSCRIBE",
                "version": "0.3.0"
            },
            "ui": {
                "color_theme": "light",
                "show_toolbar": True,
                "show_statusbar": True
            },
            "editor": {
                "font_family": "Courier New",
                "font_size": 12,
                "line_spacing": 1.5,
                "show_line_numbers": True,
                "auto_save": True,
                "auto_save_interval": 60
            },
            "ai": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000,
                "use_local_models": False,
                "local_model_path": ""
            },
            "export": {
                "default_format": "docx",
                "include_metadata": True,
                "include_notes": False,
                "include_comments": False,
                "page_size": "A4",
                "margin": 2.54
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        super().tearDown()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_config_version(self):
        """Test getting the configuration version."""
        # Test with empty config
        self.assertEqual(get_config_version({}), "0.0.0")
        
        # Test with config v1
        self.assertEqual(get_config_version(self.config_v1), "0.1.0")
        
        # Test with config v2
        self.assertEqual(get_config_version(self.config_v2), "0.2.0")
        
        # Test with config v3
        self.assertEqual(get_config_version(self.config_v3), "0.3.0")
        
        # Test with invalid config
        with patch("logging.Logger.error") as mock_error:
            self.assertEqual(get_config_version(None), "0.0.0")
            mock_error.assert_called_once()
    
    def test_compare_versions(self):
        """Test comparing version strings."""
        # Test equal versions
        self.assertEqual(compare_versions("0.1.0", "0.1.0"), 0)
        
        # Test v1 < v2
        self.assertEqual(compare_versions("0.1.0", "0.2.0"), -1)
        
        # Test v1 > v2
        self.assertEqual(compare_versions("0.2.0", "0.1.0"), 1)
        
        # Test with different length versions
        self.assertEqual(compare_versions("0.1", "0.1.0"), 0)
        self.assertEqual(compare_versions("0.1.0", "0.1"), 0)
        
        # Test with major version difference
        self.assertEqual(compare_versions("1.0.0", "0.9.9"), 1)
        
        # Test with minor version difference
        self.assertEqual(compare_versions("0.2.0", "0.1.9"), 1)
        
        # Test with patch version difference
        self.assertEqual(compare_versions("0.1.1", "0.1.0"), 1)
        
        # Test with invalid versions
        with patch("logging.Logger.error") as mock_error:
            self.assertEqual(compare_versions("invalid", "0.1.0"), 0)
            mock_error.assert_called_once()
    
    def test_get_migration_steps(self):
        """Test getting migration steps."""
        # Test with same versions
        self.assertEqual(get_migration_steps("0.1.0", "0.1.0"), [])
        
        # Test with v1 < v2
        self.assertEqual(get_migration_steps("0.1.0", "0.2.0"), [("0.1.0", "0.2.0")])
        
        # Test with v1 > v2
        with patch("logging.Logger.error") as mock_error:
            self.assertEqual(get_migration_steps("0.2.0", "0.1.0"), [])
            mock_error.assert_called_once()
        
        # Test with multiple steps
        self.assertEqual(
            get_migration_steps("0.0.0", "0.3.0"),
            [("0.0.0", "0.1.0"), ("0.1.0", "0.2.0"), ("0.2.0", "0.3.0")]
        )
        
        # Test with no migration path
        with patch("logging.Logger.error") as mock_error:
            self.assertEqual(get_migration_steps("0.0.0", "0.4.0"), [])
            mock_error.assert_called()
    
    def test_migrate_config_0_0_0_to_0_1_0(self):
        """Test migrating from version 0.0.0 to 0.1.0."""
        # Test with empty config
        migrated = migrate_config_0_0_0_to_0_1_0({})
        self.assertEqual(migrated["application"]["version"], "0.1.0")
        self.assertEqual(migrated["ui"]["theme"], "light")
        
        # Test with existing config
        config = {"existing": "value"}
        migrated = migrate_config_0_0_0_to_0_1_0(config)
        self.assertEqual(migrated["application"]["version"], "0.1.0")
        self.assertEqual(migrated["ui"]["theme"], "light")
        self.assertEqual(migrated["existing"], "value")
    
    def test_migrate_config_0_1_0_to_0_2_0(self):
        """Test migrating from version 0.1.0 to 0.2.0."""
        # Test with v1 config
        migrated = migrate_config_0_1_0_to_0_2_0(self.config_v1)
        self.assertEqual(migrated["application"]["version"], "0.2.0")
        self.assertEqual(migrated["ui"]["color_theme"], "light")
        self.assertTrue(migrated["ui"]["show_toolbar"])
        self.assertTrue(migrated["ui"]["show_statusbar"])
        self.assertEqual(migrated["editor"]["font_family"], "Courier New")
        self.assertEqual(migrated["editor"]["font_size"], 12)
        self.assertEqual(migrated["editor"]["line_spacing"], 1.5)
        self.assertTrue(migrated["editor"]["show_line_numbers"])
        self.assertTrue(migrated["editor"]["auto_save"])
        self.assertEqual(migrated["editor"]["auto_save_interval"], 60)
    
    def test_migrate_config_0_2_0_to_0_3_0(self):
        """Test migrating from version 0.2.0 to 0.3.0."""
        # Test with v2 config
        migrated = migrate_config_0_2_0_to_0_3_0(self.config_v2)
        self.assertEqual(migrated["application"]["version"], "0.3.0")
        self.assertEqual(migrated["ai"]["provider"], "openai")
        self.assertEqual(migrated["ai"]["model"], "gpt-3.5-turbo")
        self.assertEqual(migrated["ai"]["temperature"], 0.7)
        self.assertEqual(migrated["ai"]["max_tokens"], 1000)
        self.assertFalse(migrated["ai"]["use_local_models"])
        self.assertEqual(migrated["ai"]["local_model_path"], "")
        self.assertEqual(migrated["export"]["default_format"], "docx")
        self.assertTrue(migrated["export"]["include_metadata"])
        self.assertFalse(migrated["export"]["include_notes"])
        self.assertFalse(migrated["export"]["include_comments"])
        self.assertEqual(migrated["export"]["page_size"], "A4")
        self.assertEqual(migrated["export"]["margin"], 2.54)
    
    def test_migrate_config(self):
        """Test migrating a configuration."""
        # Test with same versions
        self.assertEqual(migrate_config(self.config_v1, "0.1.0"), self.config_v1)
        
        # Test with v1 < v2
        migrated = migrate_config(self.config_v1, "0.2.0")
        self.assertEqual(migrated["application"]["version"], "0.2.0")
        
        # Test with v1 > v2
        with patch("logging.Logger.error") as mock_error:
            self.assertEqual(migrate_config(self.config_v2, "0.1.0"), self.config_v2)
            mock_error.assert_called_once()
        
        # Test with multiple steps
        migrated = migrate_config(self.config_v0, "0.3.0")
        self.assertEqual(migrated["application"]["version"], "0.3.0")
        
        # Test with no migration path
        with patch("logging.Logger.error") as mock_error:
            self.assertEqual(migrate_config(self.config_v0, "0.4.0"), self.config_v0)
            mock_error.assert_called()
        
        # Test with missing migration function
        with patch("logging.Logger.error") as mock_error:
            with patch("src.utils.config_migration.get_migration_steps", return_value=[("0.3.0", "0.4.0")]):
                self.assertEqual(migrate_config(self.config_v3, "0.4.0"), self.config_v3)
                mock_error.assert_called_once()
        
        # Test with exception
        with patch("logging.Logger.error") as mock_error:
            with patch("src.utils.config_migration.get_migration_steps", side_effect=Exception("Test exception")):
                self.assertEqual(migrate_config(self.config_v1, "0.2.0"), self.config_v1)
                mock_error.assert_called_once()
    
    def test_backup_config(self):
        """Test backing up a configuration file."""
        # Create a test config file
        config_path = os.path.join(self.temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config_v1, f)
        
        # Test backup
        backup_path = backup_config(config_path)
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        # Test backup content
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_config = yaml.safe_load(f)
        self.assertEqual(backup_config, self.config_v1)
        
        # Test with non-existent file
        with patch("logging.Logger.error") as mock_error:
            self.assertIsNone(backup_config("non_existent_file.yaml"))
            mock_error.assert_called_once()
    
    def test_migrate_config_file(self):
        """Test migrating a configuration file."""
        # Create a test config file
        config_path = os.path.join(self.temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config_v1, f)
        
        # Test migration
        self.assertTrue(migrate_config_file(config_path, "0.3.0"))
        
        # Test migrated content
        with open(config_path, "r", encoding="utf-8") as f:
            migrated_config = yaml.safe_load(f)
        self.assertEqual(migrated_config["application"]["version"], "0.3.0")
        
        # Test with non-existent file
        with patch("logging.Logger.error") as mock_error:
            self.assertFalse(migrate_config_file("non_existent_file.yaml", "0.3.0"))
            mock_error.assert_called_once()
        
        # Test with same versions
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config_v3, f)
        with patch("logging.Logger.info") as mock_info:
            self.assertTrue(migrate_config_file(config_path, "0.3.0"))
            mock_info.assert_called_once()
        
        # Test with backup failure
        with patch("src.utils.config_migration.backup_config", return_value=None):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(migrate_config_file(config_path, "0.4.0"))
                mock_error.assert_called_once()
        
        # Test with exception
        with patch("logging.Logger.error") as mock_error:
            with patch("builtins.open", side_effect=Exception("Test exception")):
                self.assertFalse(migrate_config_file(config_path, "0.3.0"))
                mock_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
