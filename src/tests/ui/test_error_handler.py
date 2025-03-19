#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the UIErrorHandler class.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

# Adjust the Python path to include the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
sys.path.insert(0, project_root)

from src.ui.error_handler import UIErrorHandler, get_error_handler


class TestUIErrorHandler(unittest.TestCase):
    """Tests for the UIErrorHandler class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        # Create a new error handler for each test
        self.error_handler = UIErrorHandler()
        
        # Mock the event bus
        self.error_handler.event_bus = MagicMock()
        
        # Mock the QMessageBox.critical method
        self.message_box_patch = patch('src.ui.error_handler.QMessageBox.critical')
        self.mock_message_box = self.message_box_patch.start()
    
    def tearDown(self):
        """Tear down the test case."""
        # Stop the QMessageBox.critical patch
        self.message_box_patch.stop()
    
    def test_singleton_pattern(self):
        """Test that get_error_handler returns the same instance each time."""
        error_handler1 = get_error_handler()
        error_handler2 = get_error_handler()
        
        # Check that both instances are the same object
        self.assertIs(error_handler1, error_handler2)
    
    def test_handle_error(self):
        """Test handle_error method."""
        # Set up a mock callback
        callback = MagicMock()
        self.error_handler.error_occurred.connect(callback)
        
        # Handle an error
        self.error_handler.handle_error("TestError", "Test error message")
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with("TestError", "Test error message")
        
        # Check that the event bus was called with the correct arguments
        self.error_handler.event_bus.emit_error_occurred.assert_called_once_with(
            "TestError", "Test error message"
        )
        
        # Check that the QMessageBox.critical method was called
        self.mock_message_box.assert_called_once()
    
    def test_handle_error_no_dialog(self):
        """Test handle_error method with show_dialog=False."""
        # Set up a mock callback
        callback = MagicMock()
        self.error_handler.error_occurred.connect(callback)
        
        # Handle an error without showing a dialog
        self.error_handler.handle_error("TestError", "Test error message", show_dialog=False)
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with("TestError", "Test error message")
        
        # Check that the event bus was called with the correct arguments
        self.error_handler.event_bus.emit_error_occurred.assert_called_once_with(
            "TestError", "Test error message"
        )
        
        # Check that the QMessageBox.critical method was not called
        self.mock_message_box.assert_not_called()
    
    def test_handle_exception(self):
        """Test handle_exception method."""
        # Set up a mock callback
        callback = MagicMock()
        self.error_handler.error_occurred.connect(callback)
        
        # Create an exception
        exception = ValueError("Test exception")
        
        # Handle the exception
        self.error_handler.handle_exception(exception)
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with("ValueError", "Test exception")
        
        # Check that the event bus was called with the correct arguments
        self.error_handler.event_bus.emit_error_occurred.assert_called_once_with(
            "ValueError", "Test exception"
        )
        
        # Check that the QMessageBox.critical method was called
        self.mock_message_box.assert_called_once()
    
    def test_handle_exception_with_context(self):
        """Test handle_exception method with context."""
        # Set up a mock callback
        callback = MagicMock()
        self.error_handler.error_occurred.connect(callback)
        
        # Create an exception
        exception = ValueError("Test exception")
        
        # Handle the exception with context
        self.error_handler.handle_exception(exception, context="Loading document")
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with("ValueError", "Loading document: Test exception")
        
        # Check that the event bus was called with the correct arguments
        self.error_handler.event_bus.emit_error_occurred.assert_called_once_with(
            "ValueError", "Loading document: Test exception"
        )
        
        # Check that the QMessageBox.critical method was called
        self.mock_message_box.assert_called_once()
    
    def test_handle_exception_no_dialog(self):
        """Test handle_exception method with show_dialog=False."""
        # Set up a mock callback
        callback = MagicMock()
        self.error_handler.error_occurred.connect(callback)
        
        # Create an exception
        exception = ValueError("Test exception")
        
        # Handle the exception without showing a dialog
        self.error_handler.handle_exception(exception, show_dialog=False)
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with("ValueError", "Test exception")
        
        # Check that the event bus was called with the correct arguments
        self.error_handler.event_bus.emit_error_occurred.assert_called_once_with(
            "ValueError", "Test exception"
        )
        
        # Check that the QMessageBox.critical method was not called
        self.mock_message_box.assert_not_called()


if __name__ == '__main__':
    unittest.main()
