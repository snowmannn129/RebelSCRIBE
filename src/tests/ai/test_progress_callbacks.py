#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the progress_callbacks module.

This module contains tests for the progress tracking functionality
used for long-running AI operations.
"""

import unittest
import time
import threading
from unittest.mock import MagicMock, patch

from src.tests.base_test import BaseTest
from src.ai.progress_callbacks import (
    OperationType, ProgressStatus, ProgressInfo, ProgressCallback,
    ProgressTracker, create_operation, start_operation, update_progress,
    complete_operation, fail_operation, cancel_operation,
    get_operation_progress, register_progress_callback,
    register_global_progress_callback
)


class TestProgressCallbacks(BaseTest):
    """Unit tests for the progress_callbacks module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Reset the ProgressTracker singleton for each test
        ProgressTracker._instance = None
        self.tracker = ProgressTracker()
    
    def test_progress_info_creation(self):
        """Test creating a ProgressInfo object."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        
        self.assertEqual(progress_info.operation_type, OperationType.DOWNLOAD)
        self.assertEqual(progress_info.operation_id, "test_operation")
        self.assertEqual(progress_info.status, ProgressStatus.PENDING)
        self.assertEqual(progress_info.progress, 0.0)
        self.assertEqual(progress_info.message, "")
        self.assertIsNone(progress_info.start_time)
        self.assertIsNone(progress_info.end_time)
        self.assertIsNone(progress_info.error)
        self.assertIsNone(progress_info.result)
        self.assertEqual(progress_info.details, {})
    
    def test_progress_info_lifecycle(self):
        """Test the lifecycle of a ProgressInfo object."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        
        # Start
        progress_info.start("Starting download")
        self.assertEqual(progress_info.status, ProgressStatus.RUNNING)
        self.assertIsNotNone(progress_info.start_time)
        self.assertEqual(progress_info.message, "Starting download")
        
        # Update
        progress_info.update(0.5, "Downloading 50%")
        self.assertEqual(progress_info.progress, 0.5)
        self.assertEqual(progress_info.message, "Downloading 50%")
        
        # Complete
        result = "Download result"
        progress_info.complete(result, "Download completed")
        self.assertEqual(progress_info.status, ProgressStatus.COMPLETED)
        self.assertEqual(progress_info.progress, 1.0)
        self.assertIsNotNone(progress_info.end_time)
        self.assertEqual(progress_info.result, result)
        self.assertEqual(progress_info.message, "Download completed")
    
    def test_progress_info_failure(self):
        """Test failing a ProgressInfo object."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        progress_info.start("Starting download")
        
        # Fail
        error = "Download failed"
        progress_info.fail(error, "Error occurred")
        self.assertEqual(progress_info.status, ProgressStatus.FAILED)
        self.assertIsNotNone(progress_info.end_time)
        self.assertEqual(progress_info.error, error)
        self.assertEqual(progress_info.message, "Error occurred")
    
    def test_progress_info_cancellation(self):
        """Test canceling a ProgressInfo object."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        progress_info.start("Starting download")
        
        # Cancel
        progress_info.cancel("Download canceled")
        self.assertEqual(progress_info.status, ProgressStatus.CANCELED)
        self.assertIsNotNone(progress_info.end_time)
        self.assertEqual(progress_info.message, "Download canceled")
    
    def test_progress_info_elapsed_time(self):
        """Test calculating elapsed time."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        
        # No start time
        self.assertEqual(progress_info.elapsed_time(), 0.0)
        
        # With start time
        progress_info.start("Starting download")
        time.sleep(0.1)  # Sleep for a short time
        elapsed = progress_info.elapsed_time()
        self.assertGreater(elapsed, 0.0)
        
        # With end time
        progress_info.complete("Result", "Completed")
        elapsed_final = progress_info.elapsed_time()
        self.assertGreaterEqual(elapsed_final, elapsed)
    
    def test_progress_info_estimated_time_remaining(self):
        """Test estimating remaining time."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        
        # No start time
        self.assertIsNone(progress_info.estimated_time_remaining())
        
        # With start time but zero progress
        progress_info.start("Starting download")
        self.assertIsNone(progress_info.estimated_time_remaining())
        
        # With progress
        time.sleep(0.1)  # Sleep for a short time
        progress_info.update(0.5, "Downloading 50%")
        remaining = progress_info.estimated_time_remaining()
        self.assertIsNotNone(remaining)
        self.assertGreaterEqual(remaining, 0.0)
        
        # Completed
        progress_info.complete("Result", "Completed")
        self.assertEqual(progress_info.estimated_time_remaining(), 0.0)
    
    def test_progress_info_to_dict(self):
        """Test converting ProgressInfo to a dictionary."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        progress_info.start("Starting download")
        progress_info.update(0.5, "Downloading 50%")
        
        info_dict = progress_info.to_dict()
        self.assertEqual(info_dict["operation_type"], "download")
        self.assertEqual(info_dict["operation_id"], "test_operation")
        self.assertEqual(info_dict["status"], "running")
        self.assertEqual(info_dict["progress"], 0.5)
        self.assertEqual(info_dict["message"], "Downloading 50%")
        self.assertIsNotNone(info_dict["start_time"])
        self.assertIsNone(info_dict["end_time"])
        self.assertGreater(info_dict["elapsed_time"], 0.0)
        self.assertIsNotNone(info_dict["estimated_time_remaining"])
        self.assertIsNone(info_dict["error"])
        self.assertEqual(info_dict["details"], {})
    
    def test_progress_tracker_singleton(self):
        """Test that ProgressTracker is a singleton."""
        tracker1 = ProgressTracker()
        tracker2 = ProgressTracker()
        self.assertIs(tracker1, tracker2)
    
    def test_register_operation(self):
        """Test registering an operation with the tracker."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        operation_id = self.tracker.register_operation(progress_info)
        
        self.assertEqual(operation_id, "test_operation")
        self.assertIs(self.tracker.get_operation(operation_id), progress_info)
    
    def test_update_operation(self):
        """Test updating an operation in the tracker."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        self.tracker.register_operation(progress_info)
        
        self.tracker.update_operation("test_operation", 0.5, "Downloading 50%")
        
        updated_info = self.tracker.get_operation("test_operation")
        self.assertEqual(updated_info.progress, 0.5)
        self.assertEqual(updated_info.message, "Downloading 50%")
    
    def test_complete_operation(self):
        """Test completing an operation in the tracker."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        progress_info.start("Starting download")
        self.tracker.register_operation(progress_info)
        
        result = "Download result"
        self.tracker.complete_operation("test_operation", result, "Download completed")
        
        completed_info = self.tracker.get_operation("test_operation")
        self.assertEqual(completed_info.status, ProgressStatus.COMPLETED)
        self.assertEqual(completed_info.progress, 1.0)
        self.assertEqual(completed_info.result, result)
        self.assertEqual(completed_info.message, "Download completed")
    
    def test_fail_operation(self):
        """Test failing an operation in the tracker."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        progress_info.start("Starting download")
        self.tracker.register_operation(progress_info)
        
        error = "Download failed"
        self.tracker.fail_operation("test_operation", error, "Error occurred")
        
        failed_info = self.tracker.get_operation("test_operation")
        self.assertEqual(failed_info.status, ProgressStatus.FAILED)
        self.assertEqual(failed_info.error, error)
        self.assertEqual(failed_info.message, "Error occurred")
    
    def test_cancel_operation(self):
        """Test canceling an operation in the tracker."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        progress_info.start("Starting download")
        self.tracker.register_operation(progress_info)
        
        self.tracker.cancel_operation("test_operation", "Download canceled")
        
        canceled_info = self.tracker.get_operation("test_operation")
        self.assertEqual(canceled_info.status, ProgressStatus.CANCELED)
        self.assertEqual(canceled_info.message, "Download canceled")
    
    def test_get_operations(self):
        """Test getting operations from the tracker."""
        # Create and register operations
        download_info = ProgressInfo(OperationType.DOWNLOAD, "download_op")
        download_info.start("Starting download")
        self.tracker.register_operation(download_info)
        
        finetune_info = ProgressInfo(OperationType.FINE_TUNING, "finetune_op")
        finetune_info.start("Starting fine-tuning")
        self.tracker.register_operation(finetune_info)
        
        # Get all operations
        all_ops = self.tracker.get_operations()
        self.assertEqual(len(all_ops), 2)
        
        # Filter by operation type
        download_ops = self.tracker.get_operations(operation_type=OperationType.DOWNLOAD)
        self.assertEqual(len(download_ops), 1)
        self.assertEqual(download_ops[0].operation_id, "download_op")
        
        # Filter by status
        running_ops = self.tracker.get_operations(status=ProgressStatus.RUNNING)
        self.assertEqual(len(running_ops), 2)
        
        # Complete one operation
        self.tracker.complete_operation("download_op", "Result", "Completed")
        
        # Filter by status again
        running_ops = self.tracker.get_operations(status=ProgressStatus.RUNNING)
        self.assertEqual(len(running_ops), 1)
        self.assertEqual(running_ops[0].operation_id, "finetune_op")
        
        completed_ops = self.tracker.get_operations(status=ProgressStatus.COMPLETED)
        self.assertEqual(len(completed_ops), 1)
        self.assertEqual(completed_ops[0].operation_id, "download_op")
    
    def test_register_callback(self):
        """Test registering a callback for an operation."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        self.tracker.register_operation(progress_info)
        
        callback = MagicMock()
        self.tracker.register_callback("test_operation", callback)
        
        # Update the operation to trigger the callback
        self.tracker.update_operation("test_operation", 0.5, "Downloading 50%")
        
        # Verify callback was called
        callback.assert_called_once()
        args = callback.call_args[0]
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0].operation_id, "test_operation")
        self.assertEqual(args[0].progress, 0.5)
    
    def test_register_global_callback(self):
        """Test registering a global callback."""
        callback = MagicMock()
        self.tracker.register_global_callback(callback)
        
        # Create and update an operation
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        self.tracker.register_operation(progress_info)
        self.tracker.update_operation("test_operation", 0.5, "Downloading 50%")
        
        # Verify callback was called
        callback.assert_called_once()
        args = callback.call_args[0]
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0].operation_id, "test_operation")
        self.assertEqual(args[0].progress, 0.5)
    
    def test_unregister_callback(self):
        """Test unregistering a callback."""
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        self.tracker.register_operation(progress_info)
        
        callback = MagicMock()
        self.tracker.register_callback("test_operation", callback)
        
        # Unregister the callback
        result = self.tracker.unregister_callback("test_operation", callback)
        self.assertTrue(result)
        
        # Update the operation
        self.tracker.update_operation("test_operation", 0.5, "Downloading 50%")
        
        # Verify callback was not called
        callback.assert_not_called()
    
    def test_unregister_global_callback(self):
        """Test unregistering a global callback."""
        callback = MagicMock()
        self.tracker.register_global_callback(callback)
        
        # Unregister the callback
        result = self.tracker.unregister_global_callback(callback)
        self.assertTrue(result)
        
        # Create and update an operation
        progress_info = ProgressInfo(OperationType.DOWNLOAD, "test_operation")
        self.tracker.register_operation(progress_info)
        self.tracker.update_operation("test_operation", 0.5, "Downloading 50%")
        
        # Verify callback was not called
        callback.assert_not_called()
    
    def test_clear_completed_operations(self):
        """Test clearing completed operations."""
        # Create and register operations
        download_info = ProgressInfo(OperationType.DOWNLOAD, "download_op")
        download_info.start("Starting download")
        self.tracker.register_operation(download_info)
        
        finetune_info = ProgressInfo(OperationType.FINE_TUNING, "finetune_op")
        finetune_info.start("Starting fine-tuning")
        self.tracker.register_operation(finetune_info)
        
        # Complete one operation
        self.tracker.complete_operation("download_op", "Result", "Completed")
        
        # Clear completed operations
        cleared = self.tracker.clear_completed_operations()
        self.assertEqual(cleared, 1)
        
        # Verify the completed operation was cleared
        self.assertIsNone(self.tracker.get_operation("download_op"))
        self.assertIsNotNone(self.tracker.get_operation("finetune_op"))
    
    def test_convenience_functions(self):
        """Test the convenience functions for operation management."""
        # Create operation
        operation_id, progress_info = create_operation(OperationType.DOWNLOAD)
        self.assertEqual(progress_info.operation_type, OperationType.DOWNLOAD)
        self.assertEqual(progress_info.status, ProgressStatus.PENDING)
        
        # Start operation
        start_operation(operation_id, "Starting download")
        progress_info = get_operation_progress(operation_id)
        self.assertEqual(progress_info.status, ProgressStatus.RUNNING)
        self.assertEqual(progress_info.message, "Starting download")
        
        # Update progress
        update_progress(operation_id, 0.5, "Downloading 50%")
        progress_info = get_operation_progress(operation_id)
        self.assertEqual(progress_info.progress, 0.5)
        self.assertEqual(progress_info.message, "Downloading 50%")
        
        # Complete operation
        result = "Download result"
        complete_operation(operation_id, result, "Download completed")
        progress_info = get_operation_progress(operation_id)
        self.assertEqual(progress_info.status, ProgressStatus.COMPLETED)
        self.assertEqual(progress_info.result, result)
        
        # Create and fail operation
        fail_id, _ = create_operation(OperationType.DOWNLOAD, "fail_op")
        start_operation(fail_id, "Starting download")
        fail_operation(fail_id, "Download failed", "Error occurred")
        progress_info = get_operation_progress(fail_id)
        self.assertEqual(progress_info.status, ProgressStatus.FAILED)
        self.assertEqual(progress_info.error, "Download failed")
        
        # Create and cancel operation
        cancel_id, _ = create_operation(OperationType.DOWNLOAD, "cancel_op")
        start_operation(cancel_id, "Starting download")
        cancel_operation(cancel_id, "Download canceled")
        progress_info = get_operation_progress(cancel_id)
        self.assertEqual(progress_info.status, ProgressStatus.CANCELED)
        self.assertEqual(progress_info.message, "Download canceled")
    
    def test_callback_registration_convenience_functions(self):
        """Test the convenience functions for callback registration."""
        # Create operation
        operation_id, _ = create_operation(OperationType.DOWNLOAD)
        
        # Register callback
        callback = MagicMock()
        register_progress_callback(operation_id, callback)
        
        # Update progress to trigger callback
        update_progress(operation_id, 0.5, "Downloading 50%")
        
        # Verify callback was called
        callback.assert_called_once()
        
        # Register global callback
        global_callback = MagicMock()
        register_global_progress_callback(global_callback)
        
        # Update progress again to trigger both callbacks
        update_progress(operation_id, 0.7, "Downloading 70%")
        
        # Verify callbacks were called
        self.assertEqual(callback.call_count, 2)
        global_callback.assert_called_once()
    
    def test_callback_error_handling(self):
        """Test error handling in callbacks."""
        # Create operation
        operation_id, _ = create_operation(OperationType.DOWNLOAD)
        
        # Register a callback that raises an exception
        def error_callback(progress_info):
            raise ValueError("Callback error")
        
        register_progress_callback(operation_id, error_callback)
        
        # Update progress to trigger callback
        # This should not raise an exception
        try:
            update_progress(operation_id, 0.5, "Downloading 50%")
            # If we get here, no exception was raised
            self.assertTrue(True)
        except Exception:
            self.fail("Exception should not be raised from callback")
    
    def test_thread_safety(self):
        """Test thread safety of the ProgressTracker."""
        # Create operation
        operation_id, _ = create_operation(OperationType.DOWNLOAD)
        start_operation(operation_id, "Starting download")
        
        # Create a callback that records the progress values
        progress_values = []
        
        def record_progress(progress_info):
            progress_values.append(progress_info.progress)
        
        register_progress_callback(operation_id, record_progress)
        
        # Create threads that update progress
        def update_thread(progress):
            update_progress(operation_id, progress, f"Progress {progress}")
        
        threads = []
        for i in range(10):
            progress = i / 10.0
            thread = threading.Thread(target=update_thread, args=(progress,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify that we have 10 progress values
        self.assertEqual(len(progress_values), 10)
        
        # Verify that the final progress value is correct
        final_progress = get_operation_progress(operation_id).progress
        self.assertIn(final_progress, progress_values)


if __name__ == "__main__":
    unittest.main()
