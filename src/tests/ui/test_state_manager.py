#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the UIStateManager class.
"""

import unittest
import sys
import os
import tempfile
import json
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

# Adjust the Python path to include the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
sys.path.insert(0, project_root)

from src.ui.state_manager import UIStateManager, get_state_manager, StateChange


class TestUIStateManager(unittest.TestCase):
    """Tests for the UIStateManager class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        # Create a new state manager for each test
        self.state_manager = UIStateManager()
        
        # Mock the event bus
        self.state_manager.event_bus = MagicMock()
    
    def test_singleton_pattern(self):
        """Test that get_state_manager returns the same instance each time."""
        state_manager1 = get_state_manager()
        state_manager2 = get_state_manager()
        
        # Check that both instances are the same object
        self.assertIs(state_manager1, state_manager2)
    
    def test_get_state(self):
        """Test get_state method."""
        # Set a state value
        self.state_manager._state["test_key"] = "test_value"
        
        # Get the state value
        value = self.state_manager.get_state("test_key")
        
        # Check that the value is correct
        self.assertEqual(value, "test_value")
    
    def test_get_state_default(self):
        """Test get_state method with default value."""
        # Get a non-existent state value with a default
        value = self.state_manager.get_state("non_existent_key", "default_value")
        
        # Check that the default value is returned
        self.assertEqual(value, "default_value")
    
    def test_set_state(self):
        """Test set_state method."""
        # Set up a mock callback
        callback = MagicMock()
        self.state_manager.state_changed.connect(callback)
        
        # Set a state value
        self.state_manager.set_state("test_key", "test_value")
        
        # Check that the state was updated
        self.assertEqual(self.state_manager._state["test_key"], "test_value")
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with("test_key", "test_value")
        
        # Check that the event bus was called with the correct arguments
        self.state_manager.event_bus.emit_ui_state_changed.assert_called_once_with("test_key", "test_value")
    
    def test_set_state_no_change(self):
        """Test set_state method with no change."""
        # Set a state value
        self.state_manager._state["test_key"] = "test_value"
        
        # Set up a mock callback
        callback = MagicMock()
        self.state_manager.state_changed.connect(callback)
        
        # Set the same state value
        self.state_manager.set_state("test_key", "test_value")
        
        # Check that the callback was not called
        callback.assert_not_called()
        
        # Check that the event bus was not called
        self.state_manager.event_bus.emit_ui_state_changed.assert_not_called()
    
    def test_clear_state(self):
        """Test clear_state method."""
        # Set a state value
        self.state_manager._state["test_key"] = "test_value"
        
        # Set up a mock callback
        callback = MagicMock()
        self.state_manager.state_changed.connect(callback)
        
        # Clear the state value
        self.state_manager.clear_state("test_key")
        
        # Check that the state was cleared
        self.assertNotIn("test_key", self.state_manager._state)
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with("test_key", None)
        
        # Check that the event bus was called with the correct arguments
        self.state_manager.event_bus.emit_ui_state_changed.assert_called_once_with("test_key", None)
    
    def test_clear_state_non_existent(self):
        """Test clear_state method with non-existent key."""
        # Set up a mock callback
        callback = MagicMock()
        self.state_manager.state_changed.connect(callback)
        
        # Clear a non-existent state value
        self.state_manager.clear_state("non_existent_key")
        
        # Check that the callback was not called
        callback.assert_not_called()
        
        # Check that the event bus was not called
        self.state_manager.event_bus.emit_ui_state_changed.assert_not_called()
    
    def test_clear_all_state(self):
        """Test clear_all_state method."""
        # Set some state values
        self.state_manager._state["key1"] = "value1"
        self.state_manager._state["key2"] = "value2"
        
        # Set up a mock callback
        callback = MagicMock()
        self.state_manager.state_changed.connect(callback)
        
        # Clear all state values
        self.state_manager.clear_all_state()
        
        # Check that the state was cleared
        self.assertEqual(len(self.state_manager._state), 0)
        
        # Check that the callback was called for each key
        self.assertEqual(callback.call_count, 2)
        
        # Check that the event bus was called for each key
        self.assertEqual(self.state_manager.event_bus.emit_ui_state_changed.call_count, 2)
    
    # Tests for nested state
    
    def test_get_nested_state(self):
        """Test get_nested_state method."""
        # Set a nested state value
        self.state_manager._state = {
            "parent": {
                "child": {
                    "grandchild": "value"
                }
            }
        }
        
        # Get the nested state value
        value = self.state_manager.get_nested_state(["parent", "child", "grandchild"])
        
        # Check that the value is correct
        self.assertEqual(value, "value")
    
    def test_get_nested_state_default(self):
        """Test get_nested_state method with default value."""
        # Get a non-existent nested state value with a default
        value = self.state_manager.get_nested_state(["parent", "child", "grandchild"], "default_value")
        
        # Check that the default value is returned
        self.assertEqual(value, "default_value")
    
    def test_set_nested_state(self):
        """Test set_nested_state method."""
        # Set up a mock callback
        callback = MagicMock()
        self.state_manager.nested_state_changed.connect(callback)
        
        # Set a nested state value
        self.state_manager.set_nested_state(["parent", "child", "grandchild"], "value")
        
        # Check that the state was updated
        self.assertEqual(
            self.state_manager._state["parent"]["child"]["grandchild"],
            "value"
        )
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with(["parent", "child", "grandchild"], "value")
        
        # Check that the event bus was called with the correct arguments
        self.state_manager.event_bus.emit_ui_state_changed.assert_called_once_with(
            "parent.child.grandchild", "value"
        )
    
    def test_clear_nested_state(self):
        """Test clear_nested_state method."""
        # Set a nested state value
        self.state_manager._state = {
            "parent": {
                "child": {
                    "grandchild": "value"
                }
            }
        }
        
        # Set up a mock callback
        callback = MagicMock()
        self.state_manager.nested_state_changed.connect(callback)
        
        # Clear the nested state value
        self.state_manager.clear_nested_state(["parent", "child", "grandchild"])
        
        # Check that the entire parent structure was cleaned up
        self.assertNotIn("parent", self.state_manager._state)
        
        # Check that the callback was called with the correct arguments
        callback.assert_called_once_with(["parent", "child", "grandchild"], None)
        
        # Check that the event bus was called with the correct arguments
        self.state_manager.event_bus.emit_ui_state_changed.assert_called_once_with(
            "parent.child.grandchild", None
        )
        
        # Test with siblings to ensure partial cleanup
        self.state_manager._state = {
            "parent": {
                "child1": {
                    "grandchild": "value"
                },
                "child2": {
                    "other": "value"
                }
            }
        }
        
        # Reset mocks
        callback.reset_mock()
        self.state_manager.event_bus.emit_ui_state_changed.reset_mock()
        
        # Clear one nested state value
        self.state_manager.clear_nested_state(["parent", "child1", "grandchild"])
        
        # Check that only the empty branch was cleaned up
        self.assertIn("parent", self.state_manager._state)
        self.assertNotIn("child1", self.state_manager._state["parent"])
        self.assertIn("child2", self.state_manager._state["parent"])
    
    # Tests for history
    
    def test_history_tracking(self):
        """Test that history is tracked correctly."""
        # Set a state value
        self.state_manager.set_state("test_key", "test_value")
        
        # Check that the history contains the change
        history = self.state_manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].key, "test_key")
        self.assertEqual(history[0].old_value, None)
        self.assertEqual(history[0].new_value, "test_value")
    
    def test_history_disabled(self):
        """Test that history tracking can be disabled."""
        # Disable history tracking
        self.state_manager.enable_history(False)
        
        # Set a state value
        self.state_manager.set_state("test_key", "test_value")
        
        # Check that the history is empty
        history = self.state_manager.get_history()
        self.assertEqual(len(history), 0)
    
    def test_exclude_from_history(self):
        """Test that keys can be excluded from history tracking."""
        # Exclude a key from history tracking
        self.state_manager.exclude_from_history("excluded_key")
        
        # Set state values
        self.state_manager.set_state("excluded_key", "excluded_value")
        self.state_manager.set_state("included_key", "included_value")
        
        # Check that only the included key is in the history
        history = self.state_manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].key, "included_key")
    
    def test_undo(self):
        """Test undo functionality."""
        # Set a state value
        self.state_manager.set_state("test_key", "test_value")
        
        # Undo the change
        result = self.state_manager.undo()
        
        # Check that undo was successful
        self.assertTrue(result)
        
        # Check that the state was reverted
        self.assertNotIn("test_key", self.state_manager._state)
        
        # Check that the history is empty
        self.assertEqual(len(self.state_manager.get_history()), 0)
        
        # Check that the redo stack contains the change
        self.assertTrue(self.state_manager.can_redo())
    
    def test_redo(self):
        """Test redo functionality."""
        # Set a state value
        self.state_manager.set_state("test_key", "test_value")
        
        # Undo the change
        self.state_manager.undo()
        
        # Redo the change
        result = self.state_manager.redo()
        
        # Check that redo was successful
        self.assertTrue(result)
        
        # Check that the state was restored
        self.assertEqual(self.state_manager._state["test_key"], "test_value")
        
        # Check that the history contains the change
        self.assertEqual(len(self.state_manager.get_history()), 1)
        
        # Check that the redo stack is empty
        self.assertFalse(self.state_manager.can_redo())
    
    def test_undo_nested_state(self):
        """Test undo functionality with nested state."""
        # Set a nested state value
        self.state_manager.set_nested_state(["parent", "child", "grandchild"], "value")
        
        # Undo the change
        result = self.state_manager.undo()
        
        # Check that undo was successful
        self.assertTrue(result)
        
        # Check that the state was reverted
        self.assertNotIn("parent", self.state_manager._state)
    
    # Tests for persistence
    
    def test_persistence(self):
        """Test state persistence."""
        # Create a temporary file for persistence
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Set persistence path
            self.state_manager.set_persistence_path(temp_path)
            
            # Mark a key as persistent
            self.state_manager.mark_as_persistent("persistent_key")
            
            # Set state values
            self.state_manager.set_state("persistent_key", "persistent_value")
            self.state_manager.set_state("non_persistent_key", "non_persistent_value")
            
            # Check that the file contains only the persistent key
            with open(temp_path, 'r') as f:
                persistent_state = json.load(f)
                self.assertEqual(len(persistent_state), 1)
                self.assertEqual(persistent_state["persistent_key"], "persistent_value")
            
            # Create a new state manager
            new_state_manager = UIStateManager()
            new_state_manager.event_bus = MagicMock()
            
            # Set persistence path
            new_state_manager.set_persistence_path(temp_path)
            
            # Load persistent state
            new_state_manager.load_persistent_state()
            
            # Check that the persistent key was loaded
            self.assertEqual(new_state_manager.get_state("persistent_key"), "persistent_value")
            
            # Check that the non-persistent key was not loaded
            self.assertIsNone(new_state_manager.get_state("non_persistent_key"))
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_unmark_as_persistent(self):
        """Test unmarking a key as persistent."""
        # Create a temporary file for persistence
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Set persistence path
            self.state_manager.set_persistence_path(temp_path)
            
            # Mark a key as persistent
            self.state_manager.mark_as_persistent("persistent_key")
            
            # Set state value
            self.state_manager.set_state("persistent_key", "persistent_value")
            
            # Unmark the key as persistent
            self.state_manager.unmark_as_persistent("persistent_key")
            
            # Change the value
            self.state_manager.set_state("persistent_key", "new_value")
            
            # Check that the file still contains the old value
            with open(temp_path, 'r') as f:
                persistent_state = json.load(f)
                self.assertEqual(persistent_state["persistent_key"], "persistent_value")
        finally:
            # Clean up
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
