#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Tests for Base View Model

This module contains unit tests for the BaseViewModel class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
sys.path.insert(0, project_root)

from src.ui.base_view_model import BaseViewModel


class TestBaseViewModel(unittest.TestCase):
    """Test cases for the BaseViewModel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for dependencies
        self.event_bus_mock = MagicMock()
        self.state_manager_mock = MagicMock()
        self.error_handler_mock = MagicMock()
        
        # Create patches for get_* functions
        self.event_bus_patch = patch('src.ui.base_view_model.get_event_bus', return_value=self.event_bus_mock)
        self.state_manager_patch = patch('src.ui.base_view_model.get_state_manager', return_value=self.state_manager_mock)
        self.error_handler_patch = patch('src.ui.base_view_model.get_error_handler', return_value=self.error_handler_mock)
        
        # Start patches
        self.event_bus_patch.start()
        self.state_manager_patch.start()
        self.error_handler_patch.start()
        
        # Create test instance
        self.view_model = BaseViewModel()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.event_bus_patch.stop()
        self.state_manager_patch.stop()
        self.error_handler_patch.stop()
    
    def test_initialization(self):
        """Test that the view model is initialized correctly."""
        # Check that dependencies are set
        self.assertEqual(self.view_model.event_bus, self.event_bus_mock)
        self.assertEqual(self.view_model.state_manager, self.state_manager_mock)
        self.assertEqual(self.view_model.error_handler, self.error_handler_mock)
        
        # Check that property changed handlers are initialized
        self.assertEqual(self.view_model._property_changed_handlers, {})
        
        # Check that initialization flag is set
        self.assertFalse(self.view_model._is_initialized)
    
    def test_initialize(self):
        """Test the initialize method."""
        # Create a subclass that overrides the initialization methods
        class TestViewModel(BaseViewModel):
            def _register_event_handlers(self):
                self.register_called = True
            
            def _load_state(self):
                self.load_called = True
        
        # Create an instance of the subclass
        test_vm = TestViewModel()
        test_vm.register_called = False
        test_vm.load_called = False
        
        # Call initialize
        test_vm.initialize()
        
        # Check that the methods were called
        self.assertTrue(test_vm.register_called)
        self.assertTrue(test_vm.load_called)
        
        # Check that initialization flag is set
        self.assertTrue(test_vm._is_initialized)
        
        # Call initialize again
        test_vm.register_called = False
        test_vm.load_called = False
        test_vm.initialize()
        
        # Check that the methods were not called again
        self.assertFalse(test_vm.register_called)
        self.assertFalse(test_vm.load_called)
    
    def test_cleanup(self):
        """Test the cleanup method."""
        # Create a subclass that overrides the cleanup methods
        class TestViewModel(BaseViewModel):
            def _unregister_event_handlers(self):
                self.unregister_called = True
            
            def _save_state(self):
                self.save_called = True
        
        # Create an instance of the subclass
        test_vm = TestViewModel()
        test_vm.unregister_called = False
        test_vm.save_called = False
        
        # Call cleanup without initializing
        test_vm.cleanup()
        
        # Check that the methods were not called
        self.assertFalse(test_vm.unregister_called)
        self.assertFalse(test_vm.save_called)
        
        # Initialize and then cleanup
        test_vm.initialize()
        test_vm.unregister_called = False
        test_vm.save_called = False
        test_vm.cleanup()
        
        # Check that the methods were called
        self.assertTrue(test_vm.unregister_called)
        self.assertTrue(test_vm.save_called)
        
        # Check that initialization flag is cleared
        self.assertFalse(test_vm._is_initialized)
    
    def test_property_changed_handlers(self):
        """Test the property changed handler registration and notification."""
        # Create handlers
        handler1 = MagicMock()
        handler2 = MagicMock()
        
        # Register handlers
        self.view_model.register_property_changed_handler("test_property", handler1)
        self.view_model.register_property_changed_handler("test_property", handler2)
        
        # Check that handlers are registered
        self.assertEqual(len(self.view_model._property_changed_handlers["test_property"]), 2)
        self.assertIn(handler1, self.view_model._property_changed_handlers["test_property"])
        self.assertIn(handler2, self.view_model._property_changed_handlers["test_property"])
        
        # Notify property changed
        test_value = "test_value"
        self.view_model.notify_property_changed("test_property", test_value)
        
        # Check that handlers were called
        handler1.assert_called_once_with("test_property", test_value)
        handler2.assert_called_once_with("test_property", test_value)
        
        # Unregister handler1
        self.view_model.unregister_property_changed_handler("test_property", handler1)
        
        # Check that handler1 is unregistered
        self.assertEqual(len(self.view_model._property_changed_handlers["test_property"]), 1)
        self.assertNotIn(handler1, self.view_model._property_changed_handlers["test_property"])
        self.assertIn(handler2, self.view_model._property_changed_handlers["test_property"])
        
        # Reset mocks
        handler1.reset_mock()
        handler2.reset_mock()
        
        # Notify property changed again
        test_value2 = "test_value2"
        self.view_model.notify_property_changed("test_property", test_value2)
        
        # Check that only handler2 was called
        handler1.assert_not_called()
        handler2.assert_called_once_with("test_property", test_value2)
        
        # Unregister handler2
        self.view_model.unregister_property_changed_handler("test_property", handler2)
        
        # Check that property is removed from handlers dictionary
        self.assertNotIn("test_property", self.view_model._property_changed_handlers)
    
    def test_property_changed_handler_exception(self):
        """Test that exceptions in property changed handlers are handled."""
        # Create a handler that raises an exception
        handler = MagicMock(side_effect=Exception("Test exception"))
        
        # Register handler
        self.view_model.register_property_changed_handler("test_property", handler)
        
        # Notify property changed
        test_value = "test_value"
        self.view_model.notify_property_changed("test_property", test_value)
        
        # Check that handler was called
        handler.assert_called_once_with("test_property", test_value)
        
        # Check that error handler was called
        self.error_handler_mock.handle_exception.assert_called_once()
    
    def test_handle_error(self):
        """Test the handle_error method."""
        # Call handle_error
        error_type = "TestError"
        error_message = "Test error message"
        self.view_model.handle_error(error_type, error_message)
        
        # Check that error handler was called
        self.error_handler_mock.handle_error.assert_called_once_with(error_type, error_message)
    
    def test_handle_exception(self):
        """Test the handle_exception method."""
        # Call handle_exception
        exception = Exception("Test exception")
        context = "Test context"
        self.view_model.handle_exception(exception, context)
        
        # Check that error handler was called
        self.error_handler_mock.handle_exception.assert_called_once_with(exception, context)
        
        # Call handle_exception without context
        self.error_handler_mock.handle_exception.reset_mock()
        self.view_model.handle_exception(exception)
        
        # Check that error handler was called with class name as context
        self.error_handler_mock.handle_exception.assert_called_once_with(exception, self.view_model.__class__.__name__)


if __name__ == "__main__":
    unittest.main()
