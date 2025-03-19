#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the enhanced UIEventBus class.
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

from src.ui.event_bus import (
    UIEventBus, get_event_bus, BaseEvent, EventMetadata, EventPriority, EventCategory,
    DocumentSelectedEvent, DocumentLoadedEvent, ErrorOccurredEvent, EventFilter
)


class TestEnhancedUIEventBus(unittest.TestCase):
    """Tests for the enhanced UIEventBus class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up the test case."""
        self.event_bus = UIEventBus()
    
    def test_typed_event_emission(self):
        """Test emitting and handling typed events."""
        # Create a mock handler
        handler = MagicMock()
        
        # Register the handler for DocumentSelectedEvent
        self.event_bus.register_handler(DocumentSelectedEvent, handler)
        
        # Create and emit an event
        event = DocumentSelectedEvent(document_id="test_doc_id")
        self.event_bus.emit_event(event)
        
        # Check that the handler was called with the event
        handler.assert_called_once_with(event)
    
    def test_event_metadata(self):
        """Test event metadata."""
        # Create an event with custom metadata
        metadata = EventMetadata(
            priority=EventPriority.HIGH,
            category=EventCategory.ERROR
        )
        event = BaseEvent(metadata=metadata)
        
        # Check that the metadata was set correctly
        self.assertEqual(event.metadata.priority, EventPriority.HIGH)
        self.assertEqual(event.metadata.category, EventCategory.ERROR)
    
    def test_event_filtering(self):
        """Test event filtering."""
        # Create mock handlers
        error_handler = MagicMock()
        high_priority_handler = MagicMock()
        
        # Create filters
        error_filter = EventFilter(categories={EventCategory.ERROR})
        high_priority_filter = EventFilter(priorities={EventPriority.HIGH, EventPriority.CRITICAL})
        
        # Register filtered handlers
        self.event_bus.register_filtered_handler(BaseEvent, error_handler, error_filter)
        self.event_bus.register_filtered_handler(BaseEvent, high_priority_handler, high_priority_filter)
        
        # Create and emit a normal event
        normal_event = BaseEvent()
        normal_event.metadata.category = EventCategory.UI
        normal_event.metadata.priority = EventPriority.NORMAL
        self.event_bus.emit_event(normal_event)
        
        # Check that neither handler was called
        error_handler.assert_not_called()
        high_priority_handler.assert_not_called()
        
        # Create and emit an error event
        error_event = BaseEvent()
        error_event.metadata.category = EventCategory.ERROR
        error_event.metadata.priority = EventPriority.NORMAL
        self.event_bus.emit_event(error_event)
        
        # Check that only the error handler was called
        error_handler.assert_called_once_with(error_event)
        high_priority_handler.assert_not_called()
        
        # Reset mocks
        error_handler.reset_mock()
        high_priority_handler.reset_mock()
        
        # Create and emit a high priority event
        high_priority_event = BaseEvent()
        high_priority_event.metadata.category = EventCategory.UI
        high_priority_event.metadata.priority = EventPriority.HIGH
        self.event_bus.emit_event(high_priority_event)
        
        # Check that only the high priority handler was called
        error_handler.assert_not_called()
        high_priority_handler.assert_called_once_with(high_priority_event)
        
        # Reset mocks
        error_handler.reset_mock()
        high_priority_handler.reset_mock()
        
        # Create and emit a high priority error event
        high_priority_error_event = BaseEvent()
        high_priority_error_event.metadata.category = EventCategory.ERROR
        high_priority_error_event.metadata.priority = EventPriority.HIGH
        self.event_bus.emit_event(high_priority_error_event)
        
        # Check that both handlers were called
        error_handler.assert_called_once_with(high_priority_error_event)
        high_priority_handler.assert_called_once_with(high_priority_error_event)
    
    def test_event_history(self):
        """Test event history."""
        # Clear history
        self.event_bus.clear_history()
        
        # Create and emit some events
        event1 = DocumentSelectedEvent(document_id="doc1")
        event2 = DocumentLoadedEvent(document_id="doc1")
        event3 = ErrorOccurredEvent(error_type="TestError", error_message="Test error")
        
        self.event_bus.emit_event(event1)
        self.event_bus.emit_event(event2)
        self.event_bus.emit_event(event3)
        
        # Get history
        history = self.event_bus.get_history()
        
        # Check that all events are in the history
        self.assertEqual(len(history), 3)
        self.assertIs(history[0], event1)
        self.assertIs(history[1], event2)
        self.assertIs(history[2], event3)
        
        # Get filtered history
        error_filter = EventFilter(categories={EventCategory.ERROR})
        error_history = self.event_bus.get_history(filter=error_filter)
        
        # Check that only error events are in the filtered history
        self.assertEqual(len(error_history), 1)
        self.assertIs(error_history[0], event3)
        
        # Get limited history
        limited_history = self.event_bus.get_history(max_events=2)
        
        # Check that only the most recent events are in the limited history
        self.assertEqual(len(limited_history), 2)
        self.assertIs(limited_history[0], event2)
        self.assertIs(limited_history[1], event3)
        
        # Clear history
        self.event_bus.clear_history()
        
        # Check that history is empty
        self.assertEqual(len(self.event_bus.get_history()), 0)
    
    def test_legacy_compatibility(self):
        """Test backward compatibility with legacy signals."""
        # Create mock handlers
        legacy_handler = MagicMock()
        typed_handler = MagicMock()
        
        # Connect to legacy signal
        self.event_bus.document_selected.connect(legacy_handler)
        
        # Register handler for typed event
        self.event_bus.register_handler(DocumentSelectedEvent, typed_handler)
        
        # Emit event using legacy method
        document_id = "test_doc_id"
        self.event_bus.emit_document_selected(document_id)
        
        # Check that both handlers were called
        legacy_handler.assert_called_once_with(document_id)
        typed_handler.assert_called_once()
        self.assertEqual(typed_handler.call_args[0][0].document_id, document_id)
        
        # Reset mocks
        legacy_handler.reset_mock()
        typed_handler.reset_mock()
        
        # Emit event using typed method
        event = DocumentSelectedEvent(document_id=document_id)
        self.event_bus.emit_event(event)
        
        # Check that both handlers were called
        legacy_handler.assert_called_once_with(document_id)
        typed_handler.assert_called_once_with(event)
    
    def test_debug_mode(self):
        """Test debug mode."""
        # Enable debug mode
        self.event_bus.set_debug_mode(True)
        
        # Create and emit an event
        event = DocumentSelectedEvent(document_id="test_doc_id")
        self.event_bus.emit_event(event)
        
        # Disable debug mode
        self.event_bus.set_debug_mode(False)
        
        # Create and emit another event
        event = DocumentLoadedEvent(document_id="test_doc_id")
        self.event_bus.emit_event(event)
        
        # Note: We can't easily test the logging output, but at least we've
        # exercised the code paths to ensure they don't raise exceptions.
    
    def test_unregister_handler(self):
        """Test unregistering handlers."""
        # Create mock handlers
        handler1 = MagicMock()
        handler2 = MagicMock()
        
        # Register handlers
        self.event_bus.register_handler(DocumentSelectedEvent, handler1)
        self.event_bus.register_handler(DocumentSelectedEvent, handler2)
        
        # Create and emit an event
        event = DocumentSelectedEvent(document_id="test_doc_id")
        self.event_bus.emit_event(event)
        
        # Check that both handlers were called
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
        
        # Reset mocks
        handler1.reset_mock()
        handler2.reset_mock()
        
        # Unregister one handler
        self.event_bus.unregister_handler(DocumentSelectedEvent, handler1)
        
        # Emit another event
        event = DocumentSelectedEvent(document_id="test_doc_id")
        self.event_bus.emit_event(event)
        
        # Check that only the second handler was called
        handler1.assert_not_called()
        handler2.assert_called_once_with(event)
    
    def test_unregister_filtered_handler(self):
        """Test unregistering filtered handlers."""
        # Create mock handlers
        handler1 = MagicMock()
        handler2 = MagicMock()
        
        # Create filters
        filter1 = EventFilter(categories={EventCategory.DOCUMENT})
        filter2 = EventFilter(categories={EventCategory.DOCUMENT})
        
        # Register filtered handlers
        self.event_bus.register_filtered_handler(BaseEvent, handler1, filter1)
        self.event_bus.register_filtered_handler(BaseEvent, handler2, filter2)
        
        # Create and emit an event
        event = DocumentSelectedEvent(document_id="test_doc_id")
        self.event_bus.emit_event(event)
        
        # Check that both handlers were called
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
        
        # Reset mocks
        handler1.reset_mock()
        handler2.reset_mock()
        
        # Unregister one handler
        self.event_bus.unregister_filtered_handler(BaseEvent, handler1)
        
        # Emit another event
        event = DocumentSelectedEvent(document_id="test_doc_id")
        self.event_bus.emit_event(event)
        
        # Check that only the second handler was called
        handler1.assert_not_called()
        handler2.assert_called_once_with(event)


if __name__ == '__main__':
    unittest.main()
