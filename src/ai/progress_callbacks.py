#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progress callback utilities for AI operations in RebelSCRIBE.

This module provides utilities for tracking progress of long-running AI operations
such as model downloading, fine-tuning, and text generation.
"""

import time
import threading
from typing import Callable, Dict, Any, Optional, List, Union, Tuple
from enum import Enum
import logging

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class OperationType(Enum):
    """Types of operations that can report progress."""
    DOWNLOAD = "download"
    FINE_TUNING = "fine_tuning"
    GENERATION = "generation"
    INFERENCE = "inference"
    QUANTIZATION = "quantization"
    OPTIMIZATION = "optimization"
    DISCOVERY = "discovery"
    UPDATE_CHECK = "update_check"
    BENCHMARK = "benchmark"
    EVALUATION = "evaluation"


class ProgressStatus(Enum):
    """Status of an operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ProgressInfo:
    """Information about the progress of an operation."""
    
    def __init__(self, operation_type: OperationType, operation_id: str = None):
        """
        Initialize progress information.
        
        Args:
            operation_type: The type of operation.
            operation_id: A unique identifier for the operation. If None, a unique ID will be generated.
        """
        self.operation_type = operation_type
        self.operation_id = operation_id or f"{operation_type.value}_{int(time.time() * 1000)}"
        self.status = ProgressStatus.PENDING
        self.progress = 0.0  # 0.0 to 1.0
        self.message = ""
        self.start_time = None
        self.end_time = None
        self.error = None
        self.result = None
        self.details = {}  # Additional operation-specific details
    
    def start(self, message: str = "") -> None:
        """
        Mark the operation as started.
        
        Args:
            message: An optional message describing the operation.
        """
        self.status = ProgressStatus.RUNNING
        self.start_time = time.time()
        self.message = message or f"Starting {self.operation_type.value} operation"
        logger.debug(f"Operation {self.operation_id} started: {self.message}")
    
    def update(self, progress: float, message: str = "") -> None:
        """
        Update the progress of the operation.
        
        Args:
            progress: The progress value between 0.0 and 1.0.
            message: An optional message describing the current step.
        """
        self.progress = max(0.0, min(1.0, progress))  # Clamp between 0.0 and 1.0
        if message:
            self.message = message
        logger.debug(f"Operation {self.operation_id} progress: {self.progress:.1%} - {self.message}")
    
    def complete(self, result: Any = None, message: str = "") -> None:
        """
        Mark the operation as completed.
        
        Args:
            result: The result of the operation.
            message: An optional message describing the completion.
        """
        self.status = ProgressStatus.COMPLETED
        self.progress = 1.0
        self.end_time = time.time()
        self.result = result
        self.message = message or f"Completed {self.operation_type.value} operation"
        logger.debug(f"Operation {self.operation_id} completed: {self.message}")
    
    def fail(self, error: Union[str, Exception], message: str = "") -> None:
        """
        Mark the operation as failed.
        
        Args:
            error: The error that caused the failure.
            message: An optional message describing the failure.
        """
        self.status = ProgressStatus.FAILED
        self.end_time = time.time()
        self.error = str(error) if isinstance(error, Exception) else error
        self.message = message or f"Failed {self.operation_type.value} operation: {self.error}"
        logger.error(f"Operation {self.operation_id} failed: {self.message}")
    
    def cancel(self, message: str = "") -> None:
        """
        Mark the operation as canceled.
        
        Args:
            message: An optional message describing the cancellation.
        """
        self.status = ProgressStatus.CANCELED
        self.end_time = time.time()
        self.message = message or f"Canceled {self.operation_type.value} operation"
        logger.warning(f"Operation {self.operation_id} canceled: {self.message}")
    
    def elapsed_time(self) -> float:
        """
        Get the elapsed time of the operation in seconds.
        
        Returns:
            float: The elapsed time in seconds, or 0 if the operation hasn't started.
        """
        if not self.start_time:
            return 0.0
        
        end = self.end_time or time.time()
        return end - self.start_time
    
    def estimated_time_remaining(self) -> Optional[float]:
        """
        Estimate the remaining time for the operation in seconds.
        
        Returns:
            Optional[float]: The estimated time remaining in seconds, or None if not applicable.
        """
        if not self.start_time or self.progress <= 0 or self.status != ProgressStatus.RUNNING:
            return None
        
        elapsed = self.elapsed_time()
        if self.progress >= 1.0:
            return 0.0
        
        return elapsed * (1.0 - self.progress) / self.progress
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the progress information to a dictionary.
        
        Returns:
            Dict[str, Any]: A dictionary representation of the progress information.
        """
        return {
            "operation_type": self.operation_type.value,
            "operation_id": self.operation_id,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_time": self.elapsed_time(),
            "estimated_time_remaining": self.estimated_time_remaining(),
            "error": self.error,
            "details": self.details
        }


# Type definition for progress callbacks
ProgressCallback = Callable[[ProgressInfo], None]


class ProgressTracker:
    """Tracks progress of multiple operations."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProgressTracker, cls).__new__(cls)
                cls._instance._operations = {}
                cls._instance._callbacks = {}
                cls._instance._global_callbacks = []
        return cls._instance
    
    def register_operation(self, progress_info: ProgressInfo) -> str:
        """
        Register a new operation to track.
        
        Args:
            progress_info: The progress information for the operation.
            
        Returns:
            str: The operation ID.
        """
        with self._lock:
            self._operations[progress_info.operation_id] = progress_info
        return progress_info.operation_id
    
    def update_operation(self, operation_id: str, progress: float, message: str = "") -> None:
        """
        Update the progress of an operation.
        
        Args:
            operation_id: The ID of the operation to update.
            progress: The new progress value between 0.0 and 1.0.
            message: An optional message describing the current step.
        """
        with self._lock:
            if operation_id in self._operations:
                progress_info = self._operations[operation_id]
                progress_info.update(progress, message)
                self._notify_callbacks(progress_info)
    
    def complete_operation(self, operation_id: str, result: Any = None, message: str = "") -> None:
        """
        Mark an operation as completed.
        
        Args:
            operation_id: The ID of the operation to complete.
            result: The result of the operation.
            message: An optional message describing the completion.
        """
        with self._lock:
            if operation_id in self._operations:
                progress_info = self._operations[operation_id]
                progress_info.complete(result, message)
                self._notify_callbacks(progress_info)
    
    def fail_operation(self, operation_id: str, error: Union[str, Exception], message: str = "") -> None:
        """
        Mark an operation as failed.
        
        Args:
            operation_id: The ID of the operation to fail.
            error: The error that caused the failure.
            message: An optional message describing the failure.
        """
        with self._lock:
            if operation_id in self._operations:
                progress_info = self._operations[operation_id]
                progress_info.fail(error, message)
                self._notify_callbacks(progress_info)
    
    def cancel_operation(self, operation_id: str, message: str = "") -> None:
        """
        Mark an operation as canceled.
        
        Args:
            operation_id: The ID of the operation to cancel.
            message: An optional message describing the cancellation.
        """
        with self._lock:
            if operation_id in self._operations:
                progress_info = self._operations[operation_id]
                progress_info.cancel(message)
                self._notify_callbacks(progress_info)
    
    def get_operation(self, operation_id: str) -> Optional[ProgressInfo]:
        """
        Get the progress information for an operation.
        
        Args:
            operation_id: The ID of the operation to get.
            
        Returns:
            Optional[ProgressInfo]: The progress information, or None if not found.
        """
        with self._lock:
            return self._operations.get(operation_id)
    
    def get_operations(self, operation_type: Optional[OperationType] = None,
                      status: Optional[ProgressStatus] = None) -> List[ProgressInfo]:
        """
        Get all operations matching the specified criteria.
        
        Args:
            operation_type: Filter by operation type, or None for all types.
            status: Filter by status, or None for all statuses.
            
        Returns:
            List[ProgressInfo]: A list of matching operations.
        """
        with self._lock:
            operations = list(self._operations.values())
        
        if operation_type:
            operations = [op for op in operations if op.operation_type == operation_type]
        
        if status:
            operations = [op for op in operations if op.status == status]
        
        return operations
    
    def register_callback(self, operation_id: str, callback: ProgressCallback) -> None:
        """
        Register a callback for a specific operation.
        
        Args:
            operation_id: The ID of the operation to register the callback for.
            callback: The callback function to register.
        """
        with self._lock:
            if operation_id not in self._callbacks:
                self._callbacks[operation_id] = []
            self._callbacks[operation_id].append(callback)
    
    def register_global_callback(self, callback: ProgressCallback) -> None:
        """
        Register a callback for all operations.
        
        Args:
            callback: The callback function to register.
        """
        with self._lock:
            self._global_callbacks.append(callback)
    
    def unregister_callback(self, operation_id: str, callback: ProgressCallback) -> bool:
        """
        Unregister a callback for a specific operation.
        
        Args:
            operation_id: The ID of the operation to unregister the callback for.
            callback: The callback function to unregister.
            
        Returns:
            bool: True if the callback was unregistered, False otherwise.
        """
        with self._lock:
            if operation_id in self._callbacks:
                try:
                    self._callbacks[operation_id].remove(callback)
                    return True
                except ValueError:
                    pass
        return False
    
    def unregister_global_callback(self, callback: ProgressCallback) -> bool:
        """
        Unregister a global callback.
        
        Args:
            callback: The callback function to unregister.
            
        Returns:
            bool: True if the callback was unregistered, False otherwise.
        """
        with self._lock:
            try:
                self._global_callbacks.remove(callback)
                return True
            except ValueError:
                pass
        return False
    
    def _notify_callbacks(self, progress_info: ProgressInfo) -> None:
        """
        Notify all registered callbacks for an operation.
        
        Args:
            progress_info: The progress information to notify about.
        """
        # Get callbacks to notify
        operation_callbacks = []
        global_callbacks = []
        
        with self._lock:
            operation_callbacks = self._callbacks.get(progress_info.operation_id, [])[:]
            global_callbacks = self._global_callbacks[:]
        
        # Notify operation-specific callbacks
        for callback in operation_callbacks:
            try:
                callback(progress_info)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}", exc_info=True)
        
        # Notify global callbacks
        for callback in global_callbacks:
            try:
                callback(progress_info)
            except Exception as e:
                logger.error(f"Error in global progress callback: {e}", exc_info=True)
    
    def clear_completed_operations(self, older_than: Optional[float] = None) -> int:
        """
        Clear completed, failed, or canceled operations from the tracker.
        
        Args:
            older_than: Clear only operations that ended more than this many seconds ago,
                      or None to clear all completed operations.
            
        Returns:
            int: The number of operations cleared.
        """
        to_clear = []
        
        with self._lock:
            for op_id, progress_info in self._operations.items():
                if progress_info.status in (ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELED):
                    if older_than is None or (progress_info.end_time and time.time() - progress_info.end_time > older_than):
                        to_clear.append(op_id)
            
            for op_id in to_clear:
                del self._operations[op_id]
                if op_id in self._callbacks:
                    del self._callbacks[op_id]
        
        return len(to_clear)


# Convenience functions for creating and tracking operations

def create_operation(operation_type: OperationType, operation_id: str = None,
                    callback: ProgressCallback = None) -> Tuple[str, ProgressInfo]:
    """
    Create and register a new operation.
    
    Args:
        operation_type: The type of operation.
        operation_id: A unique identifier for the operation, or None to generate one.
        callback: An optional callback function to register for this operation.
        
    Returns:
        Tuple[str, ProgressInfo]: The operation ID and progress information.
    """
    progress_info = ProgressInfo(operation_type, operation_id)
    tracker = ProgressTracker()
    tracker.register_operation(progress_info)
    
    if callback:
        tracker.register_callback(progress_info.operation_id, callback)
    
    return progress_info.operation_id, progress_info


def start_operation(operation_id: str, message: str = "") -> None:
    """
    Start an operation.
    
    Args:
        operation_id: The ID of the operation to start.
        message: An optional message describing the operation.
    """
    tracker = ProgressTracker()
    progress_info = tracker.get_operation(operation_id)
    
    if progress_info:
        progress_info.start(message)
        tracker._notify_callbacks(progress_info)


def update_progress(operation_id: str, progress: float, message: str = "") -> None:
    """
    Update the progress of an operation.
    
    Args:
        operation_id: The ID of the operation to update.
        progress: The new progress value between 0.0 and 1.0.
        message: An optional message describing the current step.
    """
    ProgressTracker().update_operation(operation_id, progress, message)


def complete_operation(operation_id: str, result: Any = None, message: str = "") -> None:
    """
    Mark an operation as completed.
    
    Args:
        operation_id: The ID of the operation to complete.
        result: The result of the operation.
        message: An optional message describing the completion.
    """
    ProgressTracker().complete_operation(operation_id, result, message)


def fail_operation(operation_id: str, error: Union[str, Exception], message: str = "") -> None:
    """
    Mark an operation as failed.
    
    Args:
        operation_id: The ID of the operation to fail.
        error: The error that caused the failure.
        message: An optional message describing the failure.
    """
    ProgressTracker().fail_operation(operation_id, error, message)


def cancel_operation(operation_id: str, message: str = "") -> None:
    """
    Mark an operation as canceled.
    
    Args:
        operation_id: The ID of the operation to cancel.
        message: An optional message describing the cancellation.
    """
    ProgressTracker().cancel_operation(operation_id, message)


def get_operation_progress(operation_id: str) -> Optional[ProgressInfo]:
    """
    Get the progress information for an operation.
    
    Args:
        operation_id: The ID of the operation to get.
        
    Returns:
        Optional[ProgressInfo]: The progress information, or None if not found.
    """
    return ProgressTracker().get_operation(operation_id)


def register_progress_callback(operation_id: str, callback: ProgressCallback) -> None:
    """
    Register a callback for a specific operation.
    
    Args:
        operation_id: The ID of the operation to register the callback for.
        callback: The callback function to register.
    """
    ProgressTracker().register_callback(operation_id, callback)


def register_global_progress_callback(callback: ProgressCallback) -> None:
    """
    Register a callback for all operations.
    
    Args:
        callback: The callback function to register.
    """
    ProgressTracker().register_global_callback(callback)
