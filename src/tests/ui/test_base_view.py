#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Tests for Base View

This module contains unit tests for the BaseView class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QEvent

from src.ui.base_view import BaseView
from src.ui.base_view_model import BaseViewModel


# Create a QApplication instance for the tests
app = QApplication([])


class TestBaseView(unittest.TestCase):
    """Test cases for the BaseView class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for dependencies
        self.event_bus_mock = MagicMock()
        self.state_manager_mock = MagicMock()
        self.error_handler_mock = MagicMock()
        
        # Create patches for get_* functions
        self.event_bus_patch = patch('src.ui.base_view.get_event_bus', return_value=self.event_bus_mock)
        self.state_manager_patch = patch('src.ui.base_view.get_state_manager', return_value=self.state_manager_mock)
        self.error_handler_patch = patch('src.ui.base_view.get_error_handler', return_value=self.error_handler_mock)
        
        # Start patches
        self.event_bus_patch.start()
        self.state_manager_patch.start()
        self.error_handler_patch.start()
        
        # Create a mock view model class
        self.view_model_mock = MagicMock(spec=BaseViewModel)
        self.view_model_class_mock = MagicMock(return_value=self.view_model_mock)
        
        # Create test instance
        self.view = BaseView(view_model_class=self.view_model_class_mock)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.event_bus_patch.stop()
        self.state_manager_patch.stop()
        self.error_handler_patch.stop()
        
        # Clean up view
        self.view.close()
    
    def test_initialization(self):
        """Test that the view is initialized correctly."""
        # Check that dependencies are set
        self.assertEqual(self.view.event_bus, self.event_bus_mock)
        self.assertEqual(self.view.state_manager, self.state_manager_mock)
        self.assertEqual(self.view.error_handler, self.error_handler_mock)
        
        # Check that view model is created and initialized
        self.view_model_class_mock.assert_called_once()
        self.assertEqual(self.view.view_model, self.view_model_mock)
        self.view_model_mock.initialize.assert_called_once()
        
        # Check that layout is created
        self.assertIsInstance(self.view.layout, QVBoxLayout)
    
    def test_initialization_without_view_model(self):
        """Test that the view can be initialized without a view model."""
        # Create a view without a view model
        view = BaseView()
        
        # Check that view model is None
        self.assertIsNone(view.view_model)
        
        # Clean up
        view.close()
    
    def test_connect_view_model(self):
        """Test the connect_view_model method."""
        # Create a subclass that overrides the connect_view_model method
        class TestView(BaseView):
            def _connect_property_changed_handlers(self):
                self.connect_called = True
        
        # Create a view with a view model
        view = TestView(view_model_class=self.view_model_class_mock)
        view.connect_called = False
        
        # Call connect_view_model
        view.connect_view_model()
        
        # Check that the method was called
        self.assertTrue(view.connect_called)
        
        # Create a view without a view model
        view = TestView()
        view.connect_called = False
        
        # Call connect_view_model
        view.connect_view_model()
        
        # Check that the method was not called
        self.assertFalse(view.connect_called)
        
        # Clean up
        view.close()
    
    def test_show_error(self):
        """Test the show_error method."""
        # Patch QMessageBox.critical
        with patch('PyQt6.QtWidgets.QMessageBox.critical') as critical_mock:
            # Call show_error
            error_type = "TestError"
            error_message = "Test error message"
            self.view.show_error(error_type, error_message)
            
            # Check that QMessageBox.critical was called
            critical_mock.assert_called_once_with(
                self.view,
                f"Error: {error_type}",
                error_message
            )
    
    def test_show_warning(self):
        """Test the show_warning method."""
        # Patch QMessageBox.warning
        with patch('PyQt6.QtWidgets.QMessageBox.warning') as warning_mock:
            # Call show_warning
            warning_title = "Test Warning"
            warning_message = "Test warning message"
            self.view.show_warning(warning_title, warning_message)
            
            # Check that QMessageBox.warning was called
            warning_mock.assert_called_once_with(
                self.view,
                warning_title,
                warning_message
            )
    
    def test_show_info(self):
        """Test the show_info method."""
        # Patch QMessageBox.information
        with patch('PyQt6.QtWidgets.QMessageBox.information') as info_mock:
            # Call show_info
            info_title = "Test Info"
            info_message = "Test info message"
            self.view.show_info(info_title, info_message)
            
            # Check that QMessageBox.information was called
            info_mock.assert_called_once_with(
                self.view,
                info_title,
                info_message
            )
    
    def test_show_confirmation(self):
        """Test the show_confirmation method."""
        # Patch QMessageBox.question
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes) as question_mock:
            # Call show_confirmation
            confirm_title = "Test Confirmation"
            confirm_message = "Test confirmation message"
            result = self.view.show_confirmation(confirm_title, confirm_message)
            
            # Check that QMessageBox.question was called
            question_mock.assert_called_once_with(
                self.view,
                confirm_title,
                confirm_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            # Check that result is True
            self.assertTrue(result)
        
        # Patch QMessageBox.question to return No
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.No) as question_mock:
            # Call show_confirmation
            confirm_title = "Test Confirmation"
            confirm_message = "Test confirmation message"
            result = self.view.show_confirmation(confirm_title, confirm_message)
            
            # Check that QMessageBox.question was called
            question_mock.assert_called_once_with(
                self.view,
                confirm_title,
                confirm_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            # Check that result is False
            self.assertFalse(result)
    
    def test_close_event(self):
        """Test the closeEvent method."""
        # Create a mock for the closing signal
        self.view.closing = MagicMock()
        
        # Create a mock event
        event = MagicMock(spec=QEvent)
        
        # Call closeEvent
        self.view.closeEvent(event)
        
        # Check that closing signal was emitted
        self.view.closing.emit.assert_called_once()
        
        # Check that view model was cleaned up
        self.view_model_mock.cleanup.assert_called_once()
        
        # Check that event was accepted
        event.accept.assert_called_once()
    
    def test_size_hint(self):
        """Test the sizeHint method."""
        # Call sizeHint
        size = self.view.sizeHint()
        
        # Check that size is correct
        self.assertEqual(size.width(), 400)
        self.assertEqual(size.height(), 300)


if __name__ == "__main__":
    unittest.main()
