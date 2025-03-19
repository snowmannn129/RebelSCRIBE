#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Tests for Enhanced UI Error Handler

This module contains tests for the enhanced UI error handler.
"""

import os
import json
import csv
import re
import uuid
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt

from src.ui.enhanced_error_handler import (
    EnhancedErrorHandler, ErrorSeverity, DialogType, NotificationPosition,
    ErrorRecord, ErrorFilter, ErrorCallback, ErrorPattern,
    NonBlockingNotification, NotificationManager,
    get_enhanced_error_handler
)
from src.ui.event_bus import ErrorOccurredEvent, EventCategory, EventPriority


# Create QApplication instance for tests
app = QApplication([])


class TestErrorSeverity(unittest.TestCase):
    """Tests for the ErrorSeverity enum."""
    
    def test_string_representation(self):
        """Test string representation of severity levels."""
        self.assertEqual(str(ErrorSeverity.INFO), "INFO")
        self.assertEqual(str(ErrorSeverity.WARNING), "WARNING")
        self.assertEqual(str(ErrorSeverity.ERROR), "ERROR")
        self.assertEqual(str(ErrorSeverity.CRITICAL), "CRITICAL")
    
    def test_from_string(self):
        """Test creating severity from string."""
        self.assertEqual(ErrorSeverity.from_string("INFO"), ErrorSeverity.INFO)
        self.assertEqual(ErrorSeverity.from_string("WARNING"), ErrorSeverity.WARNING)
        self.assertEqual(ErrorSeverity.from_string("ERROR"), ErrorSeverity.ERROR)
        self.assertEqual(ErrorSeverity.from_string("CRITICAL"), ErrorSeverity.CRITICAL)
        
        # Test case insensitivity
        self.assertEqual(ErrorSeverity.from_string("info"), ErrorSeverity.INFO)
        self.assertEqual(ErrorSeverity.from_string("Warning"), ErrorSeverity.WARNING)
        
        # Test invalid string
        self.assertEqual(ErrorSeverity.from_string("INVALID"), ErrorSeverity.ERROR)


class TestErrorRecord(unittest.TestCase):
    """Tests for the ErrorRecord class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
        self.error_record = ErrorRecord(
            id="test-id",
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="test-component",
            timestamp=self.timestamp,
            context={"test": "value"},
            handled=False
        )
    
    def test_to_dict(self):
        """Test converting error record to dictionary."""
        error_dict = self.error_record.to_dict()
        
        self.assertEqual(error_dict["id"], "test-id")
        self.assertEqual(error_dict["error_type"], "TestError")
        self.assertEqual(error_dict["error_message"], "Test error message")
        self.assertEqual(error_dict["severity"], "ERROR")
        self.assertEqual(error_dict["component"], "test-component")
        self.assertEqual(error_dict["timestamp"], self.timestamp.isoformat())
        self.assertEqual(error_dict["context"], {"test": "value"})
        self.assertEqual(error_dict["handled"], False)
    
    def test_from_dict(self):
        """Test creating error record from dictionary."""
        error_dict = {
            "id": "test-id",
            "error_type": "TestError",
            "error_message": "Test error message",
            "severity": "ERROR",
            "component": "test-component",
            "timestamp": self.timestamp.isoformat(),
            "context": {"test": "value"},
            "handled": False
        }
        
        error_record = ErrorRecord.from_dict(error_dict)
        
        self.assertEqual(error_record.id, "test-id")
        self.assertEqual(error_record.error_type, "TestError")
        self.assertEqual(error_record.error_message, "Test error message")
        self.assertEqual(error_record.severity, ErrorSeverity.ERROR)
        self.assertEqual(error_record.component, "test-component")
        self.assertEqual(error_record.timestamp, self.timestamp)
        self.assertEqual(error_record.context, {"test": "value"})
        self.assertEqual(error_record.handled, False)


class TestErrorFilter(unittest.TestCase):
    """Tests for the ErrorFilter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.now = datetime.now()
        self.error_record = ErrorRecord(
            id="test-id",
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            timestamp=self.now,
            context={"test": "value"},
            handled=False
        )
    
    def test_severity_filter(self):
        """Test filtering by severity."""
        # Matching severity
        filter_match = ErrorFilter(severity=ErrorSeverity.ERROR)
        self.assertTrue(filter_match.matches(self.error_record))
        
        # Non-matching severity
        filter_no_match = ErrorFilter(severity=ErrorSeverity.WARNING)
        self.assertFalse(filter_no_match.matches(self.error_record))
    
    def test_component_filter(self):
        """Test filtering by component."""
        # Matching component (exact)
        filter_match_exact = ErrorFilter(component="ui.test-component")
        self.assertTrue(filter_match_exact.matches(self.error_record))
        
        # Matching component (prefix)
        filter_match_prefix = ErrorFilter(component="ui")
        self.assertTrue(filter_match_prefix.matches(self.error_record))
        
        # Non-matching component
        filter_no_match = ErrorFilter(component="backend")
        self.assertFalse(filter_no_match.matches(self.error_record))
        
        # Component filter with None component
        error_record_no_component = ErrorRecord(
            id="test-id",
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component=None,
            timestamp=self.now,
            context={"test": "value"},
            handled=False
        )
        filter_component = ErrorFilter(component="ui")
        self.assertFalse(filter_component.matches(error_record_no_component))
    
    def test_error_type_filter(self):
        """Test filtering by error type."""
        # Matching error type
        filter_match = ErrorFilter(error_type="TestError")
        self.assertTrue(filter_match.matches(self.error_record))
        
        # Non-matching error type
        filter_no_match = ErrorFilter(error_type="OtherError")
        self.assertFalse(filter_no_match.matches(self.error_record))
    
    def test_time_range_filter(self):
        """Test filtering by time range."""
        # Time range that includes the error
        start = self.now - timedelta(minutes=5)
        end = self.now + timedelta(minutes=5)
        filter_match = ErrorFilter(time_range=(start, end))
        self.assertTrue(filter_match.matches(self.error_record))
        
        # Time range before the error
        start = self.now - timedelta(minutes=10)
        end = self.now - timedelta(minutes=5)
        filter_no_match_before = ErrorFilter(time_range=(start, end))
        self.assertFalse(filter_no_match_before.matches(self.error_record))
        
        # Time range after the error
        start = self.now + timedelta(minutes=5)
        end = self.now + timedelta(minutes=10)
        filter_no_match_after = ErrorFilter(time_range=(start, end))
        self.assertFalse(filter_no_match_after.matches(self.error_record))
    
    def test_message_pattern_filter(self):
        """Test filtering by message pattern."""
        # Matching pattern (string)
        filter_match_string = ErrorFilter(message_pattern="error message")
        self.assertTrue(filter_match_string.matches(self.error_record))
        
        # Matching pattern (regex)
        filter_match_regex = ErrorFilter(message_pattern=re.compile(r"Test \w+ message"))
        self.assertTrue(filter_match_regex.matches(self.error_record))
        
        # Non-matching pattern
        filter_no_match = ErrorFilter(message_pattern="other message")
        self.assertFalse(filter_no_match.matches(self.error_record))
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        # All filters match
        filter_all_match = ErrorFilter(
            severity=ErrorSeverity.ERROR,
            component="ui",
            error_type="TestError",
            time_range=(self.now - timedelta(minutes=5), self.now + timedelta(minutes=5)),
            message_pattern="error"
        )
        self.assertTrue(filter_all_match.matches(self.error_record))
        
        # One filter doesn't match
        filter_one_no_match = ErrorFilter(
            severity=ErrorSeverity.ERROR,
            component="ui",
            error_type="OtherError",  # This doesn't match
            time_range=(self.now - timedelta(minutes=5), self.now + timedelta(minutes=5)),
            message_pattern="error"
        )
        self.assertFalse(filter_one_no_match.matches(self.error_record))


class TestErrorCallback(unittest.TestCase):
    """Tests for the ErrorCallback class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.now = datetime.now()
        self.error_record = ErrorRecord(
            id="test-id",
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            timestamp=self.now,
            context={"test": "value"},
            handled=False
        )
        
        self.callback_fn = MagicMock()
        self.callback_id = "test-callback-id"
    
    def test_callback_with_no_filter(self):
        """Test callback with no filter."""
        callback = ErrorCallback(
            callback_id=self.callback_id,
            callback=self.callback_fn
        )
        
        # Should match any error
        self.assertTrue(callback.matches(self.error_record))
    
    def test_callback_with_matching_filter(self):
        """Test callback with matching filter."""
        error_filter = ErrorFilter(severity=ErrorSeverity.ERROR)
        callback = ErrorCallback(
            callback_id=self.callback_id,
            callback=self.callback_fn,
            filter=error_filter
        )
        
        # Should match the error
        self.assertTrue(callback.matches(self.error_record))
    
    def test_callback_with_non_matching_filter(self):
        """Test callback with non-matching filter."""
        error_filter = ErrorFilter(severity=ErrorSeverity.WARNING)
        callback = ErrorCallback(
            callback_id=self.callback_id,
            callback=self.callback_fn,
            filter=error_filter
        )
        
        # Should not match the error
        self.assertFalse(callback.matches(self.error_record))


class TestErrorPattern(unittest.TestCase):
    """Tests for the ErrorPattern class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.now = datetime.now()
        self.error_record = ErrorRecord(
            id="test-id",
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            timestamp=self.now,
            context={"test": "value"},
            handled=False
        )
    
    def test_pattern_matching(self):
        """Test pattern matching."""
        # String pattern
        pattern_string = ErrorPattern("error message")
        self.assertTrue(pattern_string.matches(self.error_record))
        
        # Regex pattern
        pattern_regex = ErrorPattern(re.compile(r"Test \w+ message"))
        self.assertTrue(pattern_regex.matches(self.error_record))
        
        # Non-matching pattern
        pattern_no_match = ErrorPattern("other message")
        self.assertFalse(pattern_no_match.matches(self.error_record))
    
    def test_add_error(self):
        """Test adding errors to pattern."""
        pattern = ErrorPattern("error message")
        
        # Add first error
        pattern.add_error(self.error_record)
        self.assertEqual(pattern.count, 1)
        self.assertEqual(pattern.first_seen, self.now)
        self.assertEqual(pattern.last_seen, self.now)
        self.assertEqual(len(pattern.examples), 1)
        self.assertEqual(pattern.examples[0], self.error_record)
        
        # Add second error
        later = self.now + timedelta(minutes=5)
        error_record2 = ErrorRecord(
            id="test-id-2",
            error_type="TestError",
            error_message="Test error message 2",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            timestamp=later,
            context={"test": "value2"},
            handled=False
        )
        pattern.add_error(error_record2)
        self.assertEqual(pattern.count, 2)
        self.assertEqual(pattern.first_seen, self.now)  # Still the first error
        self.assertEqual(pattern.last_seen, later)  # Updated to the second error
        self.assertEqual(len(pattern.examples), 2)
        self.assertEqual(pattern.examples[1], error_record2)
        
        # Add more errors to test example limit
        for i in range(10):
            error_record = ErrorRecord(
                id=f"test-id-{i+3}",
                error_type="TestError",
                error_message=f"Test error message {i+3}",
                severity=ErrorSeverity.ERROR,
                component="ui.test-component",
                timestamp=later + timedelta(minutes=i),
                context={"test": f"value{i+3}"},
                handled=False
            )
            pattern.add_error(error_record)
        
        # Should only keep 5 examples
        self.assertEqual(pattern.count, 12)  # 2 + 10 = 12
        self.assertEqual(len(pattern.examples), 5)


@patch('src.ui.enhanced_error_handler.QMessageBox')
class TestEnhancedErrorHandler(unittest.TestCase):
    """Tests for the EnhancedErrorHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = EnhancedErrorHandler()
        
        # Mock event bus
        self.error_handler.event_bus = MagicMock()
        
        # Mock notification manager
        self.error_handler.notification_manager = MagicMock()
    
    def test_handle_error_basic(self, mock_message_box):
        """Test basic error handling."""
        error_id = self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component"
        )
        
        # Check that error was added to history
        self.assertEqual(len(self.error_handler.error_history), 1)
        error_record = self.error_handler.error_history[0]
        self.assertEqual(error_record.id, error_id)
        self.assertEqual(error_record.error_type, "TestError")
        self.assertEqual(error_record.error_message, "Test error message")
        self.assertEqual(error_record.severity, ErrorSeverity.ERROR)
        self.assertEqual(error_record.component, "ui.test-component")
        self.assertTrue(error_record.handled)
        
        # Check that error signal was emitted
        self.error_handler.event_bus.emit_event.assert_called_once()
        
        # Check that error dialog was shown
        mock_message_box.critical.assert_called_once()
    
    def test_handle_error_no_dialog(self, mock_message_box):
        """Test error handling without dialog."""
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Check that error dialog was not shown
        mock_message_box.critical.assert_not_called()
    
    def test_handle_error_with_notification(self, mock_message_box):
        """Test error handling with notification."""
        # Configure UI treatment for INFO severity to use notification
        self.error_handler.configure_ui_treatment(
            severity=ErrorSeverity.INFO,
            dialog_type=DialogType.NOTIFICATION,
            use_non_blocking=True,
            timeout=5000,
            position=NotificationPosition.TOP_RIGHT
        )
        
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test info message",
            severity=ErrorSeverity.INFO,
            component="ui.test-component"
        )
        
        # Check that notification was shown
        self.error_handler.notification_manager.show_notification.assert_called_once()
        
        # Check that error dialog was not shown
        mock_message_box.information.assert_not_called()
    
    def test_handle_exception(self, mock_message_box):
        """Test exception handling."""
        exception = ValueError("Test exception")
        
        self.error_handler.handle_exception(
            exception=exception,
            context="Test context",
            component="ui.test-component"
        )
        
        # Check that error was added to history
        self.assertEqual(len(self.error_handler.error_history), 1)
        error_record = self.error_handler.error_history[0]
        self.assertEqual(error_record.error_type, "ValueError")
        self.assertEqual(error_record.error_message, "Test context: Test exception")
        self.assertEqual(error_record.severity, ErrorSeverity.ERROR)
        self.assertEqual(error_record.component, "ui.test-component")
        self.assertTrue(error_record.handled)
        
        # Check that error dialog was shown
        mock_message_box.critical.assert_called_once()
    
    def test_log_error(self, mock_message_box):
        """Test logging error without dialog."""
        self.error_handler.log_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component"
        )
        
        # Check that error was added to history
        self.assertEqual(len(self.error_handler.error_history), 1)
        
        # Check that error dialog was not shown
        mock_message_box.critical.assert_not_called()
    
    def test_get_error_history(self, _):
        """Test getting error history."""
        # Add some errors
        self.error_handler.handle_error(
            error_type="TestError1",
            error_message="Test error message 1",
            severity=ErrorSeverity.INFO,
            component="ui.component1",
            show_dialog=False
        )
        
        self.error_handler.handle_error(
            error_type="TestError2",
            error_message="Test error message 2",
            severity=ErrorSeverity.WARNING,
            component="ui.component2",
            show_dialog=False
        )
        
        self.error_handler.handle_error(
            error_type="TestError3",
            error_message="Test error message 3",
            severity=ErrorSeverity.ERROR,
            component="backend.component1",
            show_dialog=False
        )
        
        # Get all errors
        all_errors = self.error_handler.get_error_history()
        self.assertEqual(len(all_errors), 3)
        
        # Filter by severity
        info_errors = self.error_handler.get_error_history(severity=ErrorSeverity.INFO)
        self.assertEqual(len(info_errors), 1)
        self.assertEqual(info_errors[0].error_type, "TestError1")
        
        # Filter by component
        ui_errors = self.error_handler.get_error_history(component="ui")
        self.assertEqual(len(ui_errors), 2)
        self.assertEqual(ui_errors[0].error_type, "TestError1")
        self.assertEqual(ui_errors[1].error_type, "TestError2")
        
        # Filter with limit
        limited_errors = self.error_handler.get_error_history(limit=2)
        self.assertEqual(len(limited_errors), 2)
        self.assertEqual(limited_errors[0].error_type, "TestError2")
        self.assertEqual(limited_errors[1].error_type, "TestError3")
    
    def test_clear_error_history(self, _):
        """Test clearing error history."""
        # Add some errors
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Check that error was added to history
        self.assertEqual(len(self.error_handler.error_history), 1)
        
        # Clear history
        self.error_handler.clear_error_history()
        
        # Check that history is empty
        self.assertEqual(len(self.error_handler.error_history), 0)
    
    def test_error_callbacks(self, _):
        """Test error callbacks."""
        # Create mock callback
        callback = MagicMock()
        
        # Register callback
        callback_id = self.error_handler.set_error_callback(
            error_type="TestError",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            callback=callback
        )
        
        # Handle matching error
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Check that callback was called
        callback.assert_called_once()
        
        # Handle non-matching error
        callback.reset_mock()
        self.error_handler.handle_error(
            error_type="OtherError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Check that callback was not called
        callback.assert_not_called()
        
        # Remove callback
        result = self.error_handler.remove_error_callback(callback_id)
        self.assertTrue(result)
        
        # Handle matching error again
        callback.reset_mock()
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Check that callback was not called
        callback.assert_not_called()
        
        # Try to remove non-existent callback
        result = self.error_handler.remove_error_callback("non-existent-id")
        self.assertFalse(result)
    
    def test_error_aggregation(self, _):
        """Test error aggregation."""
        # Enable error aggregation
        self.error_handler.enable_error_aggregation(
            enabled=True,
            timeout=5000,
            pattern_matching=False
        )
        
        # Handle first error
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Handle duplicate error
        self.error_handler.notification_manager.reset_mock()
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=True
        )
        
        # Check that notification was not shown for duplicate
        self.error_handler.notification_manager.show_notification.assert_not_called()
        
        # Check aggregated errors
        aggregated = self.error_handler.get_aggregated_errors()
        self.assertEqual(len(aggregated), 1)
        pattern, (example, count) = list(aggregated.items())[0]
        self.assertEqual(count, 2)
        
        # Disable error aggregation
        self.error_handler.enable_error_aggregation(enabled=False)
        
        # Handle duplicate error again
        self.error_handler.notification_manager.reset_mock()
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=True
        )
        
        # Check that notification was shown
        self.error_handler.notification_manager.show_notification.assert_not_called()  # Still not called because we're using modal dialogs for ERROR severity
    
    def test_rate_limiting(self, _):
        """Test rate limiting."""
        # Configure rate limiting
        self.error_handler.configure_rate_limiting(
            threshold=2,
            time_window=60000,
            use_exponential_backoff=False
        )
        
        # Handle first error
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message 1",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Handle second error
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message 2",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Handle third error (should be rate limited)
        self.error_handler.notification_manager.reset_mock()
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message 3",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=True
        )
        
        # Check that notification was not shown for rate-limited error
        self.error_handler.notification_manager.show_notification.assert_not_called()
    
    def test_component_registry(self, _):
        """Test component registry."""
        # Register component
        self.error_handler.register_component(
            component_name="ui.test-component",
            parent_component="ui",
            metadata={"description": "Test component"}
        )
        
        # Register child component
        self.error_handler.register_component(
            component_name="ui.test-component.child",
            parent_component="ui.test-component",
            metadata={"description": "Child component"}
        )
        
        # Get component hierarchy
        hierarchy = self.error_handler.get_component_hierarchy("ui.test-component.child")
        self.assertEqual(hierarchy, ["ui", "ui.test-component", "ui.test-component.child"])
        
        # Unregister component
        result = self.error_handler.unregister_component("ui.test-component")
        self.assertTrue(result)
        
        # Try to get hierarchy of unregistered component
        hierarchy = self.error_handler.get_component_hierarchy("ui.test-component")
        self.assertEqual(hierarchy, ["ui.test-component"])
        
        # Try to unregister non-existent component
        result = self.error_handler.unregister_component("non-existent-component")
        self.assertFalse(result)
    
    def test_export_error_history(self, _):
        """Test exporting error history."""
        # Add some errors
        self.error_handler.handle_error(
            error_type="TestError1",
            error_message="Test error message 1",
            severity=ErrorSeverity.INFO,
            component="ui.component1",
            show_dialog=False
        )
        
        self.error_handler.handle_error(
            error_type="TestError2",
            error_message="Test error message 2",
            severity=ErrorSeverity.WARNING,
            component="ui.component2",
            show_dialog=False
        )
        
        # Export to JSON
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_json:
            json_path = temp_json.name
        
        try:
            result = self.error_handler.export_error_history(
                file_path=json_path,
                format="json",
                include_system_info=True,
                anonymize=False
            )
            self.assertTrue(result)
            
            # Check that file exists and contains valid JSON
            with open(json_path, "r") as f:
                data = json.load(f)
                self.assertEqual(len(data), 2)
                self.assertEqual(data[0]["error_type"], "TestError1")
                self.assertEqual(data[1]["error_type"], "TestError2")
        finally:
            # Clean up
            if os.path.exists(json_path):
                os.unlink(json_path)
        
        # Export to CSV
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_csv:
            csv_path = temp_csv.name
        
        try:
            result = self.error_handler.export_error_history(
                file_path=csv_path,
                format="csv",
                include_system_info=False,
                anonymize=False
            )
            self.assertTrue(result)
            
            # Check that file exists and contains valid CSV
            with open(csv_path, "r", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 3)  # Header + 2 rows
                self.assertIn("error_type", rows[0])
                self.assertIn("TestError1", rows[1])
                self.assertIn("TestError2", rows[2])
        finally:
            # Clean up
            if os.path.exists(csv_path):
                os.unlink(csv_path)
        
        # Export to TXT
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_txt:
            txt_path = temp_txt.name
        
        try:
            result = self.error_handler.export_error_history(
                file_path=txt_path,
                format="txt",
                include_system_info=False,
                anonymize=False
            )
            self.assertTrue(result)
            
            # Check that file exists and contains text
            with open(txt_path, "r") as f:
                content = f.read()
                self.assertIn("RebelSCRIBE Error History", content)
        finally:
            # Clean up
            if os.path.exists(txt_path):
                os.unlink(txt_path)
    
    def test_enhanced_automatic_severity_detection(self, _):
        """Test enhanced automatic severity detection."""
        # Test critical exceptions
        critical_exceptions = [
            SystemError("Critical system error"),
            MemoryError("Out of memory"),
            RecursionError("Maximum recursion depth exceeded"),
            Exception("Fatal crash detected")  # Should be detected as critical from message
        ]
        
        for exception in critical_exceptions:
            severity = self.error_handler._determine_severity(exception)
            self.assertEqual(severity, ErrorSeverity.CRITICAL, f"Failed for {type(exception).__name__}")
        
        # Test error exceptions
        error_exceptions = [
            ValueError("Invalid value"),
            TypeError("Invalid type"),
            KeyError("Missing key"),
            FileNotFoundError("File not found"),
            ZeroDivisionError("Division by zero"),
            NotImplementedError("Not implemented")
        ]
        
        for exception in error_exceptions:
            severity = self.error_handler._determine_severity(exception)
            self.assertEqual(severity, ErrorSeverity.ERROR, f"Failed for {type(exception).__name__}")
        
        # Test warning exceptions
        warning_exceptions = [
            Warning("General warning"),
            DeprecationWarning("Feature is deprecated"),
            Exception("Warning: this is a warning")  # Should be detected as warning from message
        ]
        
        for exception in warning_exceptions:
            severity = self.error_handler._determine_severity(exception)
            self.assertEqual(severity, ErrorSeverity.WARNING, f"Failed for {type(exception).__name__}")
        
        # Test info exceptions
        info_exceptions = [
            Exception("Info: operation completed"),
            Exception("This is just an information message")
        ]
        
        for exception in info_exceptions:
            severity = self.error_handler._determine_severity(exception)
            self.assertEqual(severity, ErrorSeverity.INFO, f"Failed for {type(exception).__name__}")
        
        # Test custom exception with severity attribute
        class CustomException(Exception):
            def __init__(self, message, severity=None):
                super().__init__(message)
                self.severity = severity
        
        custom_exception = CustomException("Custom exception", "WARNING")
        severity = self.error_handler._determine_severity(custom_exception)
        self.assertEqual(severity, ErrorSeverity.WARNING)
        
        # Test custom exception with severity in class name
        class CustomCriticalError(Exception):
            pass
        
        critical_error = CustomCriticalError("This is a critical error")
        severity = self.error_handler._determine_severity(critical_error)
        self.assertEqual(severity, ErrorSeverity.CRITICAL)
    
    @patch('src.ui.enhanced_error_handler._send_error_report')
    def test_enhanced_error_reporting(self, mock_send_report, _):
        """Test enhanced error reporting capabilities."""
        # Mock the _send_error_report method
        self.error_handler._send_error_report = MagicMock(return_value=True)
        
        # Add an error
        error_id = self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Test basic error reporting
        result = self.error_handler.report_error(
            error_id=error_id,
            include_system_info=True,
            anonymize=True
        )
        
        self.assertTrue(result)
        self.error_handler._send_error_report.assert_called_once()
        
        # Check that the report contains the expected data
        report_data = self.error_handler._send_error_report.call_args[0][0]
        self.assertEqual(report_data["error_type"], "TestError")
        self.assertEqual(report_data["error_message"], "Test error message")
        self.assertEqual(report_data["severity"], "ERROR")
        self.assertEqual(report_data["component"], "ui.test-component")
        self.assertIn("system_info", report_data)
        
        # Test reporting with additional info
        self.error_handler._send_error_report.reset_mock()
        additional_info = {"user_action": "clicking save button", "document_id": "123"}
        
        result = self.error_handler.report_error(
            error_id=error_id,
            include_system_info=True,
            anonymize=True,
            additional_info=additional_info
        )
        
        self.assertTrue(result)
        self.error_handler._send_error_report.assert_called_once()
        
        # Check that the report contains the additional info
        report_data = self.error_handler._send_error_report.call_args[0][0]
        self.assertIn("additional_info", report_data)
        self.assertEqual(report_data["additional_info"], additional_info)
        
        # Test reporting with specific service
        self.error_handler._send_error_report.reset_mock()
        
        result = self.error_handler.report_error(
            error_id=error_id,
            include_system_info=True,
            anonymize=True,
            report_service="email"
        )
        
        self.assertTrue(result)
        self.error_handler._send_error_report.assert_called_once()
        
        # Check that the service was passed correctly
        service = self.error_handler._send_error_report.call_args[0][1]
        self.assertEqual(service, "email")
        
        # Test reporting non-existent error
        result = self.error_handler.report_error(
            error_id="non-existent-id",
            include_system_info=True,
            anonymize=True
        )
        
        self.assertFalse(result)
    
    def test_error_callbacks_with_priority(self, _):
        """Test error callbacks with priority."""
        # Create mock callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()
        
        # Register callbacks with different priorities
        self.error_handler.set_error_callback(
            error_type="TestError",
            callback=callback1,
            priority=1  # Low priority
        )
        
        self.error_handler.set_error_callback(
            error_type="TestError",
            callback=callback2,
            priority=3  # High priority
        )
        
        self.error_handler.set_error_callback(
            error_type="TestError",
            callback=callback3,
            priority=2  # Medium priority
        )
        
        # Handle error
        error_record = self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Check that callbacks were called in order of priority (high to low)
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()
        
        # Check call order using call_args
        callback2_call_time = callback2.call_args[0][0].timestamp
        callback3_call_time = callback3.call_args[0][0].timestamp
        callback1_call_time = callback1.call_args[0][0].timestamp
        
        # Higher priority should be called first
        self.assertLessEqual(callback2_call_time, callback3_call_time)
        self.assertLessEqual(callback3_call_time, callback1_call_time)
    
    def test_advanced_error_aggregation(self, _):
        """Test advanced error aggregation with pattern matching."""
        # Enable error aggregation with pattern matching
        self.error_handler.enable_error_aggregation(
            enabled=True,
            timeout=5000,
            pattern_matching=True
        )
        
        # Handle first error
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Failed to load file: test.txt",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Handle similar error with different filename
        self.error_handler.notification_manager.reset_mock()
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Failed to load file: data.csv",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=True
        )
        
        # Check that notification was not shown for similar error
        self.error_handler.notification_manager.show_notification.assert_not_called()
        
        # Check aggregated errors
        aggregated = self.error_handler.get_aggregated_errors()
        self.assertEqual(len(aggregated), 1)
        
        # The pattern should match both errors
        pattern, (example, count) = list(aggregated.items())[0]
        self.assertEqual(count, 2)
        
        # Handle completely different error
        self.error_handler.notification_manager.reset_mock()
        self.error_handler.handle_error(
            error_type="OtherError",
            error_message="Connection timeout",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=True
        )
        
        # Check that notification was shown for different error
        self.error_handler.notification_manager.show_notification.assert_not_called()  # Still not called because we're using modal dialogs for ERROR severity
        
        # Check aggregated errors again
        aggregated = self.error_handler.get_aggregated_errors()
        self.assertEqual(len(aggregated), 2)  # Now we have two patterns
    
    def test_exponential_backoff_rate_limiting(self, _):
        """Test rate limiting with exponential backoff."""
        # Configure rate limiting with exponential backoff
        self.error_handler.configure_rate_limiting(
            threshold=2,
            time_window=60000,
            use_exponential_backoff=True
        )
        
        # Set backoff parameters for testing
        self.error_handler.backoff_base = 2
        self.error_handler.backoff_max = 1000  # 1 second max
        
        # Handle first error
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=False
        )
        
        # Check error counts
        key = "TestError:ui.test-component"
        self.assertEqual(self.error_handler.error_counts[key], 1)
        
        # Handle second error immediately (should not be rate limited)
        self.error_handler.notification_manager.reset_mock()
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=True
        )
        
        # Check error counts
        self.assertEqual(self.error_handler.error_counts[key], 2)
        
        # Handle third error immediately (should be rate limited due to exponential backoff)
        self.error_handler.notification_manager.reset_mock()
        self.error_handler.handle_error(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.ERROR,
            component="ui.test-component",
            show_dialog=True
        )
        
        # Check that notification was not shown for rate-limited error
        self.error_handler.notification_manager.show_notification.assert_not_called()
        
        # Check that error count was not incremented
        self.assertEqual(self.error_handler.error_counts[key], 2)
    
    def test_component_error_statistics(self, _):
        """Test component error statistics."""
        # Add some errors
        self.error_handler.handle_error(
            error_type="TestError1",
            error_message="Test error message 1",
            severity=ErrorSeverity.INFO,
            component="ui.component1",
            show_dialog=False
        )
        
        self.error_handler.handle_error(
            error_type="TestError2",
            error_message="Test error message 2",
            severity=ErrorSeverity.WARNING,
            component="ui.component1",
            show_dialog=False
        )
        
        self.error_handler.handle_error(
            error_type="TestError3",
            error_message="Test error message 3",
            severity=ErrorSeverity.ERROR,
            component="backend.component1",
            show_dialog=False
        )
        
        self.error_handler.handle_error(
            error_type="TestError4",
            error_message="Test error message 4",
            severity=ErrorSeverity.CRITICAL,
            component="backend.component1",
            show_dialog=False
        )
        
        # Get statistics for all components
        stats = self.error_handler.get_component_error_statistics()
        self.assertEqual(len(stats), 2)  # Two components
        
        # Check ui.component1 statistics
        self.assertIn("ui.component1", stats)
        ui_stats = stats["ui.component1"]
        self.assertEqual(ui_stats[ErrorSeverity.INFO], 1)
        self.assertEqual(ui_stats[ErrorSeverity.WARNING], 1)
        self.assertEqual(ui_stats.get(ErrorSeverity.ERROR, 0), 0)
        self.assertEqual(ui_stats.get(ErrorSeverity.CRITICAL, 0), 0)
        
        # Check backend.component1 statistics
        self.assertIn("backend.component1", stats)
        backend_stats = stats["backend.component1"]
        self.assertEqual(backend_stats.get(ErrorSeverity.INFO, 0), 0)
        self.assertEqual(backend_stats.get(ErrorSeverity.WARNING, 0), 0)
        self.assertEqual(backend_stats[ErrorSeverity.ERROR], 1)
        self.assertEqual(backend_stats[ErrorSeverity.CRITICAL], 1)
        
        # Get statistics for specific component
        ui_stats = self.error_handler.get_component_error_statistics(component="ui")
        self.assertEqual(len(ui_stats), 1)
        self.assertIn("ui.component1", ui_stats)
        
        # Get statistics for specific time range
        now = datetime.now()
        time_range = (now - timedelta(minutes=5), now + timedelta(minutes=5))
        time_stats = self.error_handler.get_component_error_statistics(time_range=time_range)
        self.assertEqual(len(time_stats), 2)  # All errors are within this range


class TestNotificationManager(unittest.TestCase):
    """Tests for the NotificationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.notification_manager = NotificationManager()
    
    def test_configure(self):
        """Test configuring the notification manager."""
        # Configure notification manager
        self.notification_manager.configure(
            max_notifications=10,
            spacing=20,
            animation_duration=500,
            fade_effect=False,
            slide_effect=True,
            stacking_order="oldest_on_top"
        )
        
        # Check configuration
        self.assertEqual(self.notification_manager.max_notifications, 10)
        self.assertEqual(self.notification_manager.spacing, 20)
        self.assertEqual(self.notification_manager.animation_duration, 500)
        self.assertEqual(self.notification_manager.fade_effect, False)
        self.assertEqual(self.notification_manager.slide_effect, True)
        self.assertEqual(self.notification_manager.stacking_order, "oldest_on_top")
    
    def test_set_default_timeout(self):
        """Test setting default timeouts."""
        # Set default timeouts
        self.notification_manager.set_default_timeout(ErrorSeverity.INFO, 3000)
        self.notification_manager.set_default_timeout(ErrorSeverity.WARNING, 6000)
        self.notification_manager.set_default_timeout(ErrorSeverity.ERROR, 9000)
        self.notification_manager.set_default_timeout(ErrorSeverity.CRITICAL, None)
        
        # Check default timeouts
        self.assertEqual(self.notification_manager.default_timeouts[ErrorSeverity.INFO], 3000)
        self.assertEqual(self.notification_manager.default_timeouts[ErrorSeverity.WARNING], 6000)
        self.assertEqual(self.notification_manager.default_timeouts[ErrorSeverity.ERROR], 9000)
        self.assertIsNone(self.notification_manager.default_timeouts[ErrorSeverity.CRITICAL])
    
    @patch('src.ui.enhanced_error_handler.NonBlockingNotification')
    def test_show_notification(self, mock_notification):
        """Test showing a notification."""
        # Create mock notification
        mock_instance = MagicMock()
        mock_notification.return_value = mock_instance
        
        # Show notification
        self.notification_manager.show_notification(
            title="Test Title",
            message="Test Message",
            severity=ErrorSeverity.INFO,
            timeout=5000
        )
        
        # Check that notification was created
        mock_notification.assert_called_once()
        self.assertEqual(len(self.notification_manager.notifications), 1)
        
        # Check notification parameters
        args, kwargs = mock_notification.call_args
        self.assertEqual(kwargs["title"], "Test Title")
        self.assertEqual(kwargs["message"], "Test Message")
        self.assertEqual(kwargs["severity"], ErrorSeverity.INFO)
        self.assertEqual(kwargs["timeout"], 5000)
        
        # Show another notification
        mock_notification.reset_mock()
        mock_instance2 = MagicMock()
        mock_notification.return_value = mock_instance2
        
        self.notification_manager.show_notification(
            title="Test Title 2",
            message="Test Message 2",
            severity=ErrorSeverity.WARNING
        )
        
        # Check that notification was created
        mock_notification.assert_called_once()
        self.assertEqual(len(self.notification_manager.notifications), 2)
        
        # Check that default timeout was used
        args, kwargs = mock_notification.call_args
        self.assertEqual(kwargs["timeout"], self.notification_manager.default_timeouts[ErrorSeverity.WARNING])
    
    @patch('src.ui.enhanced_error_handler.NonBlockingNotification')
    def test_max_notifications(self, mock_notification):
        """Test maximum number of notifications."""
        # Set max notifications to 2
        self.notification_manager.max_notifications = 2
        
        # Create mock notifications
        mock_instances = [MagicMock() for _ in range(3)]
        mock_notification.side_effect = mock_instances
        
        # Show 3 notifications (exceeding the limit)
        for i in range(3):
            self.notification_manager.show_notification(
                title=f"Test Title {i+1}",
                message=f"Test Message {i+1}",
                severity=ErrorSeverity.INFO
            )
        
        # Check that only 2 notifications are kept
        self.assertEqual(len(self.notification_manager.notifications), 2)
        
        # Check that the oldest notification was closed
        mock_instances[0].close.assert_called_once()
    
    @patch('src.ui.enhanced_error_handler.NonBlockingNotification')
    def test_clear_all(self, mock_notification):
        """Test clearing all notifications."""
        # Create mock notifications
        mock_instances = [MagicMock() for _ in range(3)]
        mock_notification.side_effect = mock_instances
        
        # Show 3 notifications
        for i in range(3):
            self.notification_manager.show_notification(
                title=f"Test Title {i+1}",
                message=f"Test Message {i+1}",
                severity=ErrorSeverity.INFO
            )
        
        # Clear all notifications
        self.notification_manager.clear_all()
        
        # Check that all notifications were closed
        for mock_instance in mock_instances:
            mock_instance.close.assert_called_once()


class TestNonBlockingNotification(unittest.TestCase):
    """Tests for the NonBlockingNotification class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a parent widget
        self.parent = QWidget()
    
    def tearDown(self):
        """Clean up after tests."""
        self.parent.deleteLater()
    
    def test_create_notification(self):
        """Test creating a notification."""
        # Create notification
        notification = NonBlockingNotification(
            title="Test Title",
            message="Test Message",
            severity=ErrorSeverity.INFO,
            timeout=5000,
            parent=self.parent
        )
        
        # Check basic properties
        self.assertEqual(notification.severity, ErrorSeverity.INFO)
        self.assertEqual(notification.timeout, 5000)
        self.assertEqual(notification.remaining_time, 5000)
        self.assertFalse(notification.show_details)
        
        # Clean up
        notification.deleteLater()
    
    def test_notification_with_details(self):
        """Test notification with details."""
        # Create notification with details
        notification = NonBlockingNotification(
            title="Test Title",
            message="Test Message",
            severity=ErrorSeverity.INFO,
            timeout=5000,
            parent=self.parent,
            details="Detailed error information"
        )
        
        # Check that details are set
        self.assertEqual(notification.details, "Detailed error information")
        self.assertFalse(notification.show_details)
        
        # Toggle details
        notification.toggle_details()
        self.assertTrue(notification.show_details)
        
        # Toggle details again
        notification.toggle_details()
        self.assertFalse(notification.show_details)
        
        # Clean up
        notification.deleteLater()
    
    def test_notification_with_actions(self):
        """Test notification with action buttons."""
        # Create mock action callback
        action_callback = MagicMock()
        
        # Create notification with actions
        notification = NonBlockingNotification(
            title="Test Title",
            message="Test Message",
            severity=ErrorSeverity.INFO,
            timeout=5000,
            parent=self.parent,
            actions=[("Test Action", action_callback)]
        )
        
        # Check that actions are set
        self.assertEqual(len(notification.actions), 1)
        self.assertEqual(notification.actions[0][0], "Test Action")
        self.assertEqual(notification.actions[0][1], action_callback)
        
        # Test handling action
        notification.handle_action(action_callback)
        action_callback.assert_called_once()
        
        # Clean up
        notification.deleteLater()
    
    def test_notification_timeout(self):
        """Test notification timeout."""
        # Create notification with timeout
        notification = NonBlockingNotification(
            title="Test Title",
            message="Test Message",
            severity=ErrorSeverity.INFO,
            timeout=5000,
            parent=self.parent
        )
        
        # Mock the close method
        notification.close = MagicMock()
        
        # Simulate timeout
        notification.update_progress()
        notification.remaining_time = 0
        notification.update_progress()
        
        # Check that timer was stopped
        self.assertFalse(notification.timer.isActive())
        
        # Clean up
        notification.deleteLater()
    
    def test_notification_pause_resume(self):
        """Test pausing and resuming notification timeout."""
        # Create notification with timeout
        notification = NonBlockingNotification(
            title="Test Title",
            message="Test Message",
            severity=ErrorSeverity.INFO,
            timeout=5000,
            parent=self.parent
        )
        
        # Mock the timer
        notification.timer = MagicMock()
        notification.timer.isActive = MagicMock(return_value=True)
        
        # Pause timeout
        notification.pause_timeout()
        notification.timer.stop.assert_called_once()
        
        # Resume timeout
        notification.timer.reset_mock()
        notification.resume_timeout()
        notification.timer.start.assert_called_once()
        
        # Clean up
        notification.deleteLater()
