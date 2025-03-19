#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - UI State Manager

This module implements a central state manager for UI state.
It provides a way to manage UI state in a consistent way,
making state changes explicit and trackable.

Enhanced version includes:
- Support for nested state
- State history for undo/redo functionality
- State persistence for user preferences
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
import json
import os
from collections import deque
from datetime import datetime
import copy

from src.utils.logging_utils import get_logger
from src.ui.event_bus import get_event_bus

logger = get_logger(__name__)


class StateChange:
    """Represents a change to the state for history tracking."""
    
    def __init__(self, key: str, old_value: Any, new_value: Any, timestamp: datetime = None):
        """
        Initialize a state change.
        
        Args:
            key: The key of the state that changed.
            old_value: The previous value.
            new_value: The new value.
            timestamp: When the change occurred (defaults to now).
        """
        self.key = key
        self.old_value = copy.deepcopy(old_value)
        self.new_value = copy.deepcopy(new_value)
        self.timestamp = timestamp or datetime.now()
    
    def __repr__(self) -> str:
        """Return a string representation of the state change."""
        return f"StateChange(key={self.key}, old={self.old_value}, new={self.new_value}, time={self.timestamp})"


class UIStateManager(QObject):
    """
    Central state manager for UI state.
    
    This class provides a way to manage UI state in a consistent way,
    making state changes explicit and trackable.
    
    Enhanced version includes:
    - Support for nested state
    - State history for undo/redo functionality
    - State persistence for user preferences
    """
    
    # Define signals for state changes
    state_changed = pyqtSignal(str, object)  # key, value
    nested_state_changed = pyqtSignal(list, object)  # path, value
    
    def __init__(self, max_history_size: int = 100):
        """
        Initialize the state manager.
        
        Args:
            max_history_size: Maximum number of state changes to keep in history.
        """
        super().__init__()
        self._state: Dict[str, Any] = {}
        
        # Get event bus instance
        self.event_bus = get_event_bus()
        
        # State history for undo/redo
        self._history: deque = deque(maxlen=max_history_size)
        self._redo_stack: deque = deque(maxlen=max_history_size)
        self._history_enabled = True
        self._history_excluded_keys: Set[str] = set()
        
        # State persistence
        self._persistent_keys: Set[str] = set()
        self._persistence_path: Optional[str] = None
        
        logger.debug("Enhanced UI State Manager initialized")
    
    #
    # Basic state operations
    #
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a state value.
        
        Args:
            key: The key of the state value to get.
            default: The default value to return if the key is not found.
            
        Returns:
            The state value, or the default value if the key is not found.
        """
        return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any, track_history: bool = True) -> None:
        """
        Set a state value.
        
        Args:
            key: The key of the state value to set.
            value: The value to set.
            track_history: Whether to track this change in history.
        """
        # Check if the value has changed
        old_value = self._state.get(key)
        if key in self._state and self._state[key] == value:
            return
        
        # Track in history if enabled and not excluded
        if (track_history and self._history_enabled and 
            key not in self._history_excluded_keys):
            self._add_to_history(key, old_value, value)
        
        # Update state
        self._state[key] = value
        
        # Emit state changed signal
        self.state_changed.emit(key, value)
        
        # Emit UI state changed event
        self.event_bus.emit_ui_state_changed(key, value)
        
        # Persist state if needed
        if key in self._persistent_keys:
            self._persist_state()
        
        logger.debug(f"State changed: {key}={value}")
    
    def clear_state(self, key: str, track_history: bool = True) -> None:
        """
        Clear a state value.
        
        Args:
            key: The key of the state value to clear.
            track_history: Whether to track this change in history.
        """
        if key in self._state:
            old_value = self._state[key]
            
            # Track in history if enabled and not excluded
            if (track_history and self._history_enabled and 
                key not in self._history_excluded_keys):
                self._add_to_history(key, old_value, None)
            
            del self._state[key]
            
            # Emit state changed signal
            self.state_changed.emit(key, None)
            
            # Emit UI state changed event
            self.event_bus.emit_ui_state_changed(key, None)
            
            # Persist state if needed
            if key in self._persistent_keys:
                self._persist_state()
            
            logger.debug(f"State cleared: {key}")
    
    def clear_all_state(self, track_history: bool = True) -> None:
        """
        Clear all state values.
        
        Args:
            track_history: Whether to track this change in history.
        """
        # Get keys to clear
        keys = list(self._state.keys())
        
        if track_history and self._history_enabled:
            # Add all changes to history as a batch
            for key in keys:
                if key not in self._history_excluded_keys:
                    self._add_to_history(key, self._state[key], None)
        
        # Clear state
        self._state.clear()
        
        # Emit state changed signals
        for key in keys:
            # Emit state changed signal
            self.state_changed.emit(key, None)
            
            # Emit UI state changed event
            self.event_bus.emit_ui_state_changed(key, None)
        
        # Persist state if needed
        if any(key in self._persistent_keys for key in keys):
            self._persist_state()
        
        logger.debug("All state cleared")
    
    #
    # Nested state operations
    #
    
    def get_nested_state(self, path: List[str], default: Any = None) -> Any:
        """
        Get a nested state value using a path.
        
        Args:
            path: List of keys representing the path to the nested state.
            default: The default value to return if the path is not found.
            
        Returns:
            The nested state value, or the default value if the path is not found.
        """
        if not path:
            return default
        
        # Start with the top-level state
        current = self._state
        
        # Navigate through the path
        for i, key in enumerate(path):
            if not isinstance(current, dict) or key not in current:
                return default
            
            if i == len(path) - 1:
                # Last key in path, return the value
                return current[key]
            else:
                # Continue navigating
                current = current[key]
        
        return default
    
    def set_nested_state(self, path: List[str], value: Any, track_history: bool = True) -> None:
        """
        Set a nested state value using a path.
        
        Args:
            path: List of keys representing the path to the nested state.
            value: The value to set.
            track_history: Whether to track this change in history.
        """
        if not path:
            return
        
        # Get the old value for history tracking
        old_value = self.get_nested_state(path)
        
        # Check if the value has changed
        if old_value == value:
            return
        
        # Start with the top-level state
        current = self._state
        
        # Navigate through the path, creating dictionaries as needed
        for i, key in enumerate(path):
            if i == len(path) - 1:
                # Last key in path, set the value
                current[key] = value
            else:
                # Create nested dictionaries as needed
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
        
        # Track in history if enabled
        if track_history and self._history_enabled:
            # Use a special format for the key to represent the path
            history_key = ".".join(path)
            if history_key not in self._history_excluded_keys:
                self._add_to_history(history_key, old_value, value)
        
        # Emit nested state changed signal
        self.nested_state_changed.emit(path, value)
        
        # Emit UI state changed event with a special key format
        self.event_bus.emit_ui_state_changed(".".join(path), value)
        
        # Persist state if needed
        if any(key in self._persistent_keys for key in path):
            self._persist_state()
        
        logger.debug(f"Nested state changed: {'.'.join(path)}={value}")
    
    def clear_nested_state(self, path: List[str], track_history: bool = True) -> None:
        """
        Clear a nested state value using a path.
        
        Args:
            path: List of keys representing the path to the nested state.
            track_history: Whether to track this change in history.
        """
        if not path:
            return
        
        # Get the old value for history tracking
        old_value = self.get_nested_state(path)
        
        if old_value is None:
            return  # Nothing to clear
        
        # Start with the top-level state
        current = self._state
        
        # Navigate through the path
        for i, key in enumerate(path):
            if not isinstance(current, dict) or key not in current:
                return  # Path doesn't exist
            
            if i == len(path) - 1:
                # Last key in path, delete the value
                del current[key]
            else:
                # Continue navigating
                current = current[key]
        
        # Clean up empty parent dictionaries
        self._cleanup_empty_parents(path)
        
        # Track in history if enabled
        if track_history and self._history_enabled:
            # Use a special format for the key to represent the path
            history_key = ".".join(path)
            if history_key not in self._history_excluded_keys:
                self._add_to_history(history_key, old_value, None)
        
        # Emit nested state changed signal
        self.nested_state_changed.emit(path, None)
        
        # Emit UI state changed event with a special key format
        self.event_bus.emit_ui_state_changed(".".join(path), None)
        
        # Persist state if needed
        if any(key in self._persistent_keys for key in path):
            self._persist_state()
        
        logger.debug(f"Nested state cleared: {'.'.join(path)}")
    
    def _cleanup_empty_parents(self, path: List[str]) -> None:
        """
        Clean up empty parent dictionaries after clearing a nested state.
        
        Args:
            path: List of keys representing the path to the cleared state.
        """
        if len(path) <= 1:
            return  # No parents to clean up
        
        # Start from the immediate parent and work up
        for i in range(len(path) - 1, 0, -1):
            parent_path = path[:i]
            child_key = path[i]
            
            # Get the parent dictionary
            parent = self._state
            for key in parent_path[:-1]:
                if not isinstance(parent, dict) or key not in parent:
                    return  # Parent doesn't exist
                parent = parent[key]
            
            # Check if the parent's child is an empty dictionary
            last_parent_key = parent_path[-1]
            if (last_parent_key in parent and 
                isinstance(parent[last_parent_key], dict) and 
                len(parent[last_parent_key]) == 0):
                # Remove the empty dictionary
                del parent[last_parent_key]
            else:
                # If this parent is not empty, higher parents won't be empty either
                break
    
    #
    # History operations
    #
    
    def _add_to_history(self, key: str, old_value: Any, new_value: Any) -> None:
        """
        Add a state change to the history.
        
        Args:
            key: The key of the state that changed.
            old_value: The previous value.
            new_value: The new value.
        """
        change = StateChange(key, old_value, new_value)
        self._history.append(change)
        
        # Clear redo stack when a new change is made
        self._redo_stack.clear()
    
    def enable_history(self, enabled: bool = True) -> None:
        """
        Enable or disable history tracking.
        
        Args:
            enabled: Whether to enable history tracking.
        """
        self._history_enabled = enabled
        logger.debug(f"History tracking {'enabled' if enabled else 'disabled'}")
    
    def exclude_from_history(self, key: str) -> None:
        """
        Exclude a key from history tracking.
        
        Args:
            key: The key to exclude from history tracking.
        """
        self._history_excluded_keys.add(key)
        logger.debug(f"Key excluded from history: {key}")
    
    def include_in_history(self, key: str) -> None:
        """
        Include a key in history tracking.
        
        Args:
            key: The key to include in history tracking.
        """
        if key in self._history_excluded_keys:
            self._history_excluded_keys.remove(key)
            logger.debug(f"Key included in history: {key}")
    
    def clear_history(self) -> None:
        """Clear the history."""
        self._history.clear()
        self._redo_stack.clear()
        logger.debug("History cleared")
    
    def can_undo(self) -> bool:
        """
        Check if undo is available.
        
        Returns:
            True if undo is available, False otherwise.
        """
        return len(self._history) > 0
    
    def can_redo(self) -> bool:
        """
        Check if redo is available.
        
        Returns:
            True if redo is available, False otherwise.
        """
        return len(self._redo_stack) > 0
    
    def undo(self) -> bool:
        """
        Undo the last state change.
        
        Returns:
            True if a change was undone, False otherwise.
        """
        if not self._history:
            return False
        
        # Get the last change
        change = self._history.pop()
        
        # Add to redo stack
        self._redo_stack.append(change)
        
        # Revert the change
        if "." in change.key:
            # Nested state change
            path = change.key.split(".")
            if change.old_value is None:
                self.clear_nested_state(path, track_history=False)
            else:
                self.set_nested_state(path, change.old_value, track_history=False)
        else:
            # Regular state change
            if change.old_value is None:
                self.clear_state(change.key, track_history=False)
            else:
                self.set_state(change.key, change.old_value, track_history=False)
        
        logger.debug(f"Undid change: {change}")
        return True
    
    def redo(self) -> bool:
        """
        Redo the last undone state change.
        
        Returns:
            True if a change was redone, False otherwise.
        """
        if not self._redo_stack:
            return False
        
        # Get the last undone change
        change = self._redo_stack.pop()
        
        # Add back to history
        self._history.append(change)
        
        # Apply the change
        if "." in change.key:
            # Nested state change
            path = change.key.split(".")
            if change.new_value is None:
                self.clear_nested_state(path, track_history=False)
            else:
                self.set_nested_state(path, change.new_value, track_history=False)
        else:
            # Regular state change
            if change.new_value is None:
                self.clear_state(change.key, track_history=False)
            else:
                self.set_state(change.key, change.new_value, track_history=False)
        
        logger.debug(f"Redid change: {change}")
        return True
    
    def get_history(self) -> List[StateChange]:
        """
        Get the history of state changes.
        
        Returns:
            List of state changes, oldest first.
        """
        return list(self._history)
    
    #
    # Persistence operations
    #
    
    def set_persistence_path(self, path: str) -> None:
        """
        Set the path for state persistence.
        
        Args:
            path: The path to the file where state will be persisted.
        """
        self._persistence_path = path
        logger.debug(f"Persistence path set: {path}")
    
    def mark_as_persistent(self, key: str) -> None:
        """
        Mark a key as persistent.
        
        Args:
            key: The key to mark as persistent.
        """
        self._persistent_keys.add(key)
        logger.debug(f"Key marked as persistent: {key}")
    
    def unmark_as_persistent(self, key: str) -> None:
        """
        Unmark a key as persistent.
        
        Args:
            key: The key to unmark as persistent.
        """
        if key in self._persistent_keys:
            self._persistent_keys.remove(key)
            logger.debug(f"Key unmarked as persistent: {key}")
    
    def _persist_state(self) -> None:
        """Persist the state to disk."""
        if not self._persistence_path:
            logger.warning("Cannot persist state: No persistence path set")
            return
        
        try:
            # Create a dictionary with only the persistent keys
            persistent_state = {
                key: self._state[key]
                for key in self._persistent_keys
                if key in self._state
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self._persistence_path), exist_ok=True)
            
            # Write to file
            with open(self._persistence_path, 'w') as f:
                json.dump(persistent_state, f, indent=2)
            
            logger.debug(f"State persisted to {self._persistence_path}")
        except Exception as e:
            logger.error(f"Error persisting state: {str(e)}")
    
    def load_persistent_state(self) -> None:
        """Load persistent state from disk."""
        if not self._persistence_path:
            logger.warning("Cannot load persistent state: No persistence path set")
            return
        
        if not os.path.exists(self._persistence_path):
            logger.debug(f"Persistent state file not found: {self._persistence_path}")
            return
        
        try:
            # Read from file
            with open(self._persistence_path, 'r') as f:
                persistent_state = json.load(f)
            
            # Update state with persistent values
            for key, value in persistent_state.items():
                self.set_state(key, value, track_history=False)
            
            logger.debug(f"Persistent state loaded from {self._persistence_path}")
        except Exception as e:
            logger.error(f"Error loading persistent state: {str(e)}")


# Create a singleton instance of the state manager
_instance: Optional[UIStateManager] = None

def get_state_manager() -> UIStateManager:
    """
    Get the singleton instance of the state manager.
    
    Returns:
        The state manager instance.
    """
    global _instance
    if _instance is None:
        _instance = UIStateManager()
    return _instance
