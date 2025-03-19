#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base test class for RebelSCRIBE tests.

This module provides a base test class with common setup and teardown
functionality to reduce code duplication across test files.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pytest

from src.utils.config_manager import ConfigManager


class BaseTest(unittest.TestCase):
    """Base class for RebelSCRIBE tests with common setup and teardown."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test configuration
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.config = self._create_mock_config()
        
        # Set up common paths
        self.test_project_path = os.path.join(self.test_dir, "test_project.rebelscribe")
        self.test_document_path = os.path.join(self.test_dir, "test_document.json")
        self.test_export_path = os.path.join(self.test_dir, "test_export.pdf")
        
        # Set up logging
        self._setup_logging()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.test_dir)
    
    def _create_mock_config(self):
        """Create a standard mock configuration."""
        mock_config = MagicMock(spec=ConfigManager)
        
        # Set up specific returns for different get calls
        mock_config.get.side_effect = lambda section, key=None, default=None: {
            "application": {
                "data_directory": self.test_dir,
                "autosave_interval": 5
            },
            "editor": {
                "font_family": "Arial",
                "font_size": 12,
                "theme": "light"
            },
            "ai": {
                "api_key": "mock_key",
                "model": "gpt-4"
            },
            "export": {
                "default_format": "PDF",
                "include_metadata": True
            },
            "backup": {
                "auto_backup": True,
                "backup_interval": 30,
                "max_backups": 5
            }
        }.get(section, {}).get(key, default) if key else {}
        
        return mock_config
    
    def _setup_logging(self):
        """Set up logging for tests."""
        # Mock the logging to avoid actual log file creation
        patcher = patch('src.utils.logging_utils.setup_logging')
        self.mock_setup_logging = patcher.start()
        self.addCleanup(patcher.stop)
    
    def create_test_file(self, path, content):
        """Create a test file with the given content."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return path
    
    def assert_file_exists(self, path):
        """Assert that a file exists."""
        self.assertTrue(os.path.exists(path), f"File does not exist: {path}")
    
    def assert_file_contains(self, path, expected_content):
        """Assert that a file contains the expected content."""
        self.assert_file_exists(path)
        with open(path, 'r') as f:
            content = f.read()
        self.assertIn(expected_content, content, 
                     f"File does not contain expected content: {path}")
    
    def assert_json_file_valid(self, path):
        """Assert that a file is a valid JSON file."""
        self.assert_file_exists(path)
        import json
        try:
            with open(path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            self.fail(f"File is not valid JSON: {path}, Error: {e}")
    
    def mock_service(self, service_class, **kwargs):
        """Create a mock service with the given attributes."""
        mock_service = MagicMock(spec=service_class)
        for key, value in kwargs.items():
            setattr(mock_service, key, value)
        return mock_service


# Pytest fixture version of the base test
@pytest.fixture
def base_test_fixture():
    """Fixture that provides the same functionality as BaseTest."""
    # Create a temporary directory for test files
    test_dir = tempfile.mkdtemp()
    
    # Create common paths
    test_project_path = os.path.join(test_dir, "test_project.rebelscribe")
    test_document_path = os.path.join(test_dir, "test_document.json")
    test_export_path = os.path.join(test_dir, "test_export.pdf")
    
    # Create a mock config
    mock_config = MagicMock(spec=ConfigManager)
    mock_config.get.side_effect = lambda section, key=None, default=None: {
        "application": {
            "data_directory": test_dir,
            "autosave_interval": 5
        },
        "editor": {
            "font_family": "Arial",
            "font_size": 12,
            "theme": "light"
        },
        "ai": {
            "api_key": "mock_key",
            "model": "gpt-4"
        },
        "export": {
            "default_format": "PDF",
            "include_metadata": True
        },
        "backup": {
            "auto_backup": True,
            "backup_interval": 30,
            "max_backups": 5
        }
    }.get(section, {}).get(key, default) if key else {}
    
    # Mock logging
    with patch('src.utils.logging_utils.setup_logging'):
        yield {
            "test_dir": test_dir,
            "config": mock_config,
            "test_project_path": test_project_path,
            "test_document_path": test_document_path,
            "test_export_path": test_export_path,
            "create_test_file": lambda path, content: _create_test_file(path, content),
            "assert_file_exists": lambda path: os.path.exists(path),
            "assert_file_contains": lambda path, expected_content: _assert_file_contains(path, expected_content),
            "assert_json_file_valid": lambda path: _assert_json_file_valid(path),
            "mock_service": lambda service_class, **kwargs: _mock_service(service_class, **kwargs)
        }
    
    # Clean up
    import shutil
    shutil.rmtree(test_dir)


def _create_test_file(path, content):
    """Create a test file with the given content."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _assert_file_contains(path, expected_content):
    """Assert that a file contains the expected content."""
    assert os.path.exists(path), f"File does not exist: {path}"
    with open(path, 'r') as f:
        content = f.read()
    assert expected_content in content, f"File does not contain expected content: {path}"


def _assert_json_file_valid(path):
    """Assert that a file is a valid JSON file."""
    assert os.path.exists(path), f"File does not exist: {path}"
    import json
    try:
        with open(path, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"File is not valid JSON: {path}, Error: {e}")


def _mock_service(service_class, **kwargs):
    """Create a mock service with the given attributes."""
    mock_service = MagicMock(spec=service_class)
    for key, value in kwargs.items():
        setattr(mock_service, key, value)
    return mock_service
