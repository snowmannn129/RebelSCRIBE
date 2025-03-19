#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Test Error Handler Integration

This module contains tests for the error handler integration.
"""

import unittest
import os
import tempfile
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt

from src.ui.error_handler import get_error_handler
from src.ui.enhanced_error_handler import ErrorSeverity, get_enhanced_error_handler
from src.ui.error_handler_integration import (
    ErrorHandlerIntegration, get_integrated_error_handler, replace_error_handler
)


class TestErrorHandlerIntegration(unittest.TestCase):
    """Test case for the error handler integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test case."""
        # Create QApplication instance if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up each test."""
        # Create a parent widget
        self.parent = QWidget()
        
        # Create integration instance
        self.integration = ErrorHandlerIntegration(self.parent)
        
        # Mock the original and enhanced handlers
        self.integration.original_handler = MagicMock()
        self.integration.enhanced_handler = MagicMock()
        
        # Set up return values
        self.integration.enhanced_handler.handle_error.return_value = "error_id_1"
        self.integration.enhanced_handler.handle_exception.return_value = "error_id_2"
    
    def tearDown(self):
        """Clean up after each test."""
        self.parent.deleteLater()
    
    def test_handle_error(self):
        """Test handle_error method."""
        # Call handle_error
        error_id = self.integration.handle_error(
            error_type="TestError",
            error_message="Test error message",
            show_dialog=True,
            parent=self.parent
        )
        
        # Check that enhanced handler was called
        self.integration.enhanced_handler.handle_error.assert_called_once()
        
        # Check that the error ID was returned
        self.assertEqual(error_id, "error_id_1")
    
    def test_handle_exception(self):
        """Test handle_exception method."""
        # Create an exception
        exception = ValueError("Test exception")
        
        # Call handle_exception
        error_id = self.integration.handle_exception(
            exception=exception,
            context="Test context",
            show_dialog=True,
            parent=self.parent
        )
        
        # Check that enhanced handler was called
        self.integration.enhanced_handler.handle_exception.assert_called_once()
        
        # Check that the error ID was returned
        self.assertEqual(error_id, "error_id_2")
    
    def test_determine_severity_from_type(self):
        """Test _determine_severity_from_type method."""
        # Create a real integration instance for this test
        real_integration = ErrorHandlerIntegration()
        
        # Test critical errors
        self.assertEqual(
            real_integration._determine_severity_from_type("CriticalError"),
            ErrorSeverity.CRITICAL
        )
        self.assertEqual(
            real_integration._determine_severity_from_type("FatalException"),
            ErrorSeverity.CRITICAL
        )
        
        # Test warning errors
        self.assertEqual(
            real_integration._determine_severity_from_type("WarningMessage"),
            ErrorSeverity.WARNING
        )
        self.assertEqual(
            real_integration._determine_severity_from_type("CautionRequired"),
            ErrorSeverity.WARNING
        )
        
        # Test info errors
        self.assertEqual(
            real_integration._determine_severity_from_type("InfoNotification"),
            ErrorSeverity.INFO
        )
        self.assertEqual(
            real_integration._determine_severity_from_type("InformationMessage"),
            ErrorSeverity.INFO
        )
        
        # Test default (ERROR)
        self.assertEqual(
            real_integration._determine_severity_from_type("SomeError"),
            ErrorSeverity.ERROR
        )
        self.assertEqual(
            real_integration._determine_severity_from_type("UnknownException"),
            ErrorSeverity.ERROR
        )
    
    def test_enhanced_methods(self):
        """Test enhanced methods."""
        # Test log_error
        self.integration.log_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.WARNING,
            component="TestComponent"
        )
        self.integration.enhanced_handler.log_error.assert_called_once()
        
        # Test get_error_history
        self.integration.get_error_history(
            severity=ErrorSeverity.ERROR,
            component="TestComponent",
            limit=10
        )
        self.integration.enhanced_handler.get_error_history.assert_called_once()
        
        # Test clear_error_history
        self.integration.clear_error_history()
        self.integration.enhanced_handler.clear_error_history.assert_called_once()
        
        # Test export_error_history
        self.integration.export_error_history(
            file_path="test.json",
            format="json",
            include_system_info=True,
            anonymize=False
        )
        self.integration.enhanced_handler.export_error_history.assert_called_once()
    
    def test_get_integrated_error_handler(self):
        """Test get_integrated_error_handler function."""
        # Get integrated error handler
        handler1 = get_integrated_error_handler()
        handler2 = get_integrated_error_handler()
        
        # Check that the same instance is returned
        self.assertIs(handler1, handler2)
    
    @patch('src.ui.error_handler.get_error_handler')
    def test_replace_error_handler(self, mock_get_error_handler):
        """Test replace_error_handler function."""
        # Call replace_error_handler
        replace_error_handler()
        
        # Check that get_error_handler was replaced
        import src.ui.error_handler
        self.assertEqual(
            src.ui.error_handler.get_error_handler,
            get_integrated_error_handler
        )


if __name__ == '__main__':
    unittest.main()
