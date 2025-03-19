#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the UIEventBus class.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication

# Adjust the Python path to include the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
sys.path.insert(0, project_root)

from src.ui.event_bus import UIEventBus, get_event_bus


class TestUIEventBus(unittest.TestCase):
    """Tests for the UIEventBus class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        self.event_bus = UIEventBus()
    
    def test_singleton_pattern(self):
        """Test that get_event_bus returns the same instance each time."""
        event_bus1 = get_event_bus()
        event_bus2 = get_event_bus()
        
        # Check that both instances are the same object
        self.assertIs(event_bus1, event_bus2)
    
    def test_document_selected_event(self):
        """Test document_selected event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.document_selected.connect(callback)
        
        # Emit the signal
        document_id = "test_doc_id"
        self.event_bus.emit_document_selected(document_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(document_id)
    
    def test_document_loaded_event(self):
        """Test document_loaded event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.document_loaded.connect(callback)
        
        # Emit the signal
        document_id = "test_doc_id"
        self.event_bus.emit_document_loaded(document_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(document_id)
    
    def test_document_saved_event(self):
        """Test document_saved event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.document_saved.connect(callback)
        
        # Emit the signal
        document_id = "test_doc_id"
        self.event_bus.emit_document_saved(document_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(document_id)
    
    def test_document_modified_event(self):
        """Test document_modified event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.document_modified.connect(callback)
        
        # Emit the signal
        document_id = "test_doc_id"
        self.event_bus.emit_document_modified(document_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(document_id)
    
    def test_document_created_event(self):
        """Test document_created event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.document_created.connect(callback)
        
        # Emit the signal
        document_id = "test_doc_id"
        self.event_bus.emit_document_created(document_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(document_id)
    
    def test_document_deleted_event(self):
        """Test document_deleted event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.document_deleted.connect(callback)
        
        # Emit the signal
        document_id = "test_doc_id"
        self.event_bus.emit_document_deleted(document_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(document_id)
    
    def test_project_loaded_event(self):
        """Test project_loaded event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.project_loaded.connect(callback)
        
        # Emit the signal
        project_id = "test_project_id"
        self.event_bus.emit_project_loaded(project_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(project_id)
    
    def test_project_saved_event(self):
        """Test project_saved event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.project_saved.connect(callback)
        
        # Emit the signal
        project_id = "test_project_id"
        self.event_bus.emit_project_saved(project_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(project_id)
    
    def test_project_closed_event(self):
        """Test project_closed event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.project_closed.connect(callback)
        
        # Emit the signal
        self.event_bus.emit_project_closed()
        
        # Check that the callback was called
        callback.assert_called_once()
    
    def test_project_created_event(self):
        """Test project_created event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.project_created.connect(callback)
        
        # Emit the signal
        project_id = "test_project_id"
        self.event_bus.emit_project_created(project_id)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(project_id)
    
    def test_ui_theme_changed_event(self):
        """Test ui_theme_changed event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.ui_theme_changed.connect(callback)
        
        # Emit the signal
        theme_name = "dark"
        self.event_bus.emit_ui_theme_changed(theme_name)
        
        # Check that the callback was called with the correct argument
        callback.assert_called_once_with(theme_name)
    
    def test_ui_state_changed_event(self):
        """Test ui_state_changed event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.ui_state_changed.connect(callback)
        
        # Emit the signal
        state_key = "current_document_id"
        state_value = "test_doc_id"
        self.event_bus.emit_ui_state_changed(state_key, state_value)
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with(state_key, state_value)
    
    def test_error_occurred_event(self):
        """Test error_occurred event."""
        # Create a mock callback
        callback = MagicMock()
        
        # Connect the callback to the signal
        self.event_bus.error_occurred.connect(callback)
        
        # Emit the signal
        error_type = "FileNotFound"
        error_message = "File not found: test.txt"
        self.event_bus.emit_error_occurred(error_type, error_message)
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with(error_type, error_message)


if __name__ == '__main__':
    unittest.main()
