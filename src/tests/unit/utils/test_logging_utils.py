#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the logging_utils module.

This module contains unit tests for the logging utility functions:
- Logging configuration
- Log level management
- Handler management
- Logger retrieval
"""

import os
import logging
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from src.tests.base_test import BaseTest
from src.utils.logging_utils import (
    setup_logging, get_logger, set_log_level, add_file_handler,
    add_console_handler, get_log_levels, get_all_loggers,
    disable_logging, enable_logging, DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL, DEFAULT_MAX_BYTES, DEFAULT_BACKUP_COUNT
)


class TestLoggingUtils(BaseTest):
    """Unit tests for the logging_utils module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test log file path
        self.log_file = os.path.join(self.test_dir, "test.log")
        
        # Save the original logging configuration
        self.original_handlers = logging.root.handlers.copy()
        self.original_level = logging.root.level
        
        # Clear all handlers
        logging.root.handlers.clear()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Restore the original logging configuration
        logging.root.handlers.clear()
        for handler in self.original_handlers:
            logging.root.addHandler(handler)
        logging.root.setLevel(self.original_level)
        
        # Call the parent tearDown
        super().tearDown()
    
    def test_setup_logging_with_defaults(self):
        """Test setting up logging with default values."""
        # Set up logging with defaults
        logger = setup_logging()
        
        # Verify the logger
        self.assertEqual(logger, logging.root)
        self.assertEqual(logger.level, DEFAULT_LOG_LEVEL)
        
        # Verify handlers
        self.assertEqual(len(logger.handlers), 2)  # Console and file
        
        # Verify console handler
        console_handler = next((h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)), None)
        self.assertIsNotNone(console_handler)
        self.assertEqual(console_handler.formatter._fmt, DEFAULT_LOG_FORMAT)
        
        # Verify file handler
        file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.formatter._fmt, DEFAULT_LOG_FORMAT)
        self.assertEqual(file_handler.baseFilename, os.path.abspath("rebelscribe.log"))
        
        # Close the file handler to avoid file access issues during tearDown
        if file_handler:
            file_handler.close()
    
    def test_setup_logging_with_custom_values(self):
        """Test setting up logging with custom values."""
        # Custom values
        log_level = logging.DEBUG
        log_format = "%(levelname)s - %(message)s"
        max_bytes = 1024
        backup_count = 3
        
        # Set up logging with custom values
        logger = setup_logging(
            log_file=self.log_file,
            log_level=log_level,
            log_format=log_format,
            max_bytes=max_bytes,
            backup_count=backup_count
        )
        
        # Verify the logger
        self.assertEqual(logger, logging.root)
        self.assertEqual(logger.level, log_level)
        
        # Verify handlers
        self.assertEqual(len(logger.handlers), 2)  # Console and file
        
        # Verify console handler
        console_handler = next((h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)), None)
        self.assertIsNotNone(console_handler)
        self.assertEqual(console_handler.formatter._fmt, log_format)
        
        # Verify file handler
        file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.formatter._fmt, log_format)
        self.assertEqual(file_handler.baseFilename, os.path.abspath(self.log_file))
        self.assertEqual(file_handler.maxBytes, max_bytes)
        self.assertEqual(file_handler.backupCount, backup_count)
        
        # Close the file handler to avoid file access issues during tearDown
        if file_handler:
            file_handler.close()
    
    def test_setup_logging_console_only(self):
        """Test setting up logging with console output only."""
        # Set up logging with console output only
        logger = setup_logging(file_output=False)
        
        # Verify the logger
        self.assertEqual(logger, logging.root)
        
        # Verify handlers
        self.assertEqual(len(logger.handlers), 1)  # Console only
        
        # Verify console handler
        console_handler = next((h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)), None)
        self.assertIsNotNone(console_handler)
    
    def test_setup_logging_file_only(self):
        """Test setting up logging with file output only."""
        # Set up logging with file output only
        logger = setup_logging(log_file=self.log_file, console_output=False)
        
        # Verify the logger
        self.assertEqual(logger, logging.root)
        
        # Verify handlers
        self.assertEqual(len(logger.handlers), 1)  # File only
        
        # Verify file handler
        file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.baseFilename, os.path.abspath(self.log_file))
        
        # Close the file handler to avoid file access issues during tearDown
        if file_handler:
            file_handler.close()
    
    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        # Create a path with a non-existent directory
        log_dir = os.path.join(self.test_dir, "logs")
        log_file = os.path.join(log_dir, "test.log")
        
        # Verify the directory doesn't exist
        self.assertFalse(os.path.exists(log_dir))
        
        # Set up logging
        logger = setup_logging(log_file=log_file)
        
        # Verify the directory was created
        self.assertTrue(os.path.exists(log_dir))
        
        # Close the file handler to avoid file access issues during tearDown
        file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
        if file_handler:
            file_handler.close()
    
    def test_get_logger(self):
        """Test getting a logger."""
        # Get a logger
        logger_name = "test_logger"
        logger = get_logger(logger_name)
        
        # Verify the logger
        self.assertEqual(logger.name, logger_name)
        self.assertIsInstance(logger, logging.Logger)
    
    def test_set_log_level_with_int(self):
        """Test setting the log level with an integer level."""
        # Set up a logger
        logger_name = "test_logger"
        logger = logging.getLogger(logger_name)
        
        # Set the log level
        set_log_level(logging.DEBUG, logger_name)
        
        # Verify the log level
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_set_log_level_with_string(self):
        """Test setting the log level with a string level."""
        # Set up a logger
        logger_name = "test_logger"
        logger = logging.getLogger(logger_name)
        
        # Set the log level
        set_log_level("DEBUG", logger_name)
        
        # Verify the log level
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_set_log_level_root_logger(self):
        """Test setting the log level for the root logger."""
        # Set the log level
        set_log_level(logging.DEBUG)
        
        # Verify the log level
        self.assertEqual(logging.root.level, logging.DEBUG)
    
    def test_add_file_handler(self):
        """Test adding a file handler to a logger."""
        # Set up a logger
        logger_name = "test_logger"
        logger = logging.getLogger(logger_name)
        
        # Add a file handler
        handler = add_file_handler(self.log_file, logger_name=logger_name)
        
        # Verify the handler
        self.assertIn(handler, logger.handlers)
        self.assertIsInstance(handler, logging.FileHandler)
        self.assertEqual(handler.baseFilename, os.path.abspath(self.log_file))
        
        # Close the handler to avoid file access issues during tearDown
        handler.close()
        logger.removeHandler(handler)
    
    def test_add_file_handler_creates_directory(self):
        """Test that add_file_handler creates the log directory if it doesn't exist."""
        # Create a path with a non-existent directory
        log_dir = os.path.join(self.test_dir, "logs")
        log_file = os.path.join(log_dir, "test.log")
        
        # Verify the directory doesn't exist
        self.assertFalse(os.path.exists(log_dir))
        
        # Add a file handler
        handler = add_file_handler(log_file)
        
        # Verify the directory was created
        self.assertTrue(os.path.exists(log_dir))
        
        # Close the handler to avoid file access issues during tearDown
        handler.close()
        logging.root.removeHandler(handler)
    
    def test_add_console_handler(self):
        """Test adding a console handler to a logger."""
        # Set up a logger
        logger_name = "test_logger"
        logger = logging.getLogger(logger_name)
        
        # Add a console handler
        handler = add_console_handler(logger_name=logger_name)
        
        # Verify the handler
        self.assertIn(handler, logger.handlers)
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertNotIsInstance(handler, logging.FileHandler)
    
    def test_get_log_levels(self):
        """Test getting a dictionary of log levels."""
        # Get log levels
        levels = get_log_levels()
        
        # Verify the levels
        self.assertIsInstance(levels, dict)
        self.assertEqual(levels["DEBUG"], logging.DEBUG)
        self.assertEqual(levels["INFO"], logging.INFO)
        self.assertEqual(levels["WARNING"], logging.WARNING)
        self.assertEqual(levels["ERROR"], logging.ERROR)
        self.assertEqual(levels["CRITICAL"], logging.CRITICAL)
    
    def test_get_all_loggers(self):
        """Test getting a list of all logger names."""
        # Create some loggers
        logging.getLogger("test_logger1")
        logging.getLogger("test_logger2")
        
        # Get all loggers
        loggers = get_all_loggers()
        
        # Verify the loggers
        self.assertIsInstance(loggers, list)
        self.assertIn("test_logger1", loggers)
        self.assertIn("test_logger2", loggers)
    
    def test_disable_enable_logging(self):
        """Test disabling and enabling logging."""
        # Set up a logger
        logger = logging.getLogger("test_logger")
        
        # Create a mock handler
        mock_handler = MagicMock()
        mock_handler.level = logging.NOTSET  # Set a proper level value
        logger.addHandler(mock_handler)
        
        # Log a message
        logger.warning("Test message")
        
        # Verify the handler was called
        mock_handler.handle.assert_called()
        
        # Reset the mock
        mock_handler.reset_mock()
        
        # Disable logging
        disable_logging()
        
        # Log a message
        logger.warning("Test message")
        
        # Verify the handler was not called
        mock_handler.handle.assert_not_called()
        
        # Enable logging
        enable_logging()
        
        # Log a message
        logger.warning("Test message")
        
        # Verify the handler was called
        mock_handler.handle.assert_called()


# Pytest-style tests
class TestLoggingUtilsPytest:
    """Pytest-style tests for the logging_utils module."""
    
    @pytest.fixture
    def setup(self, base_test_fixture):
        """Set up test fixtures."""
        # Create a test log file path
        log_file = os.path.join(base_test_fixture["test_dir"], "test.log")
        
        # Save the original logging configuration
        original_handlers = logging.root.handlers.copy()
        original_level = logging.root.level
        
        # Clear all handlers
        logging.root.handlers.clear()
        
        yield {
            **base_test_fixture,
            "log_file": log_file
        }
        
        # Restore the original logging configuration
        logging.root.handlers.clear()
        for handler in original_handlers:
            logging.root.addHandler(handler)
        logging.root.setLevel(original_level)
    
    def test_setup_logging_pytest(self, setup):
        """Test setting up logging using pytest style."""
        # Set up logging
        logger = setup_logging(log_file=setup["log_file"])
        
        # Verify the logger
        assert logger == logging.root
        assert logger.level == DEFAULT_LOG_LEVEL
        
        # Verify handlers
        assert len(logger.handlers) == 2  # Console and file
        
        # Verify file handler
        file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
        assert file_handler is not None
        assert file_handler.baseFilename == os.path.abspath(setup["log_file"])
        
        # Close the file handler to avoid file access issues during tearDown
        if file_handler:
            file_handler.close()
    
    def test_get_logger_pytest(self, setup):
        """Test getting a logger using pytest style."""
        # Get a logger
        logger_name = "test_logger"
        logger = get_logger(logger_name)
        
        # Verify the logger
        assert logger.name == logger_name
        assert isinstance(logger, logging.Logger)


if __name__ == '__main__':
    unittest.main()
