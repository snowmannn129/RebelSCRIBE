#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - UI Error Handler

This module implements a central error handler for UI errors.
It provides a way to handle UI errors in a consistent way,
showing appropriate error messages to users and logging errors for debugging.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

from src.utils.logging_utils import get_logger
from src.ui.event_bus import get_event_bus

logger = get_logger(__name__)


class UIErrorHandler(QObject):
    """
    Central error handler for UI errors.
    
    This class provides a way to handle UI errors in a consistent way,
    showing appropriate error messages to users and logging errors for debugging.
    """
    
    # Define signals for error events
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    
    def __init__(self, parent=None):
        """
        Initialize the error handler.
        
        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        
        # Get event bus instance
        self.event_bus = get_event_bus()
        
        logger.debug("UI Error Handler initialized")
    
    def handle_error(self, error_type: str, error_message: str, 
                    show_dialog: bool = True, parent=None) -> None:
        """
        Handle an error.
        
        Args:
            error_type: The type of error.
            error_message: The error message.
            show_dialog: Whether to show an error dialog.
            parent: The parent widget for the error dialog.
        """
        # Log the error
        logger.error(f"{error_type}: {error_message}")
        
        # Emit the error signal
        self.error_occurred.emit(error_type, error_message)
        
        # Emit the error event
        self.event_bus.emit_error_occurred(error_type, error_message)
        
        # Show error dialog if requested
        if show_dialog:
            QMessageBox.critical(
                parent,
                f"Error: {error_type}",
                error_message
            )
    
    def handle_exception(self, exception: Exception, context: str = "",
                        show_dialog: bool = True, parent=None) -> None:
        """
        Handle an exception.
        
        Args:
            exception: The exception to handle.
            context: The context in which the exception occurred.
            show_dialog: Whether to show an error dialog.
            parent: The parent widget for the error dialog.
        """
        error_type = type(exception).__name__
        error_message = f"{context}: {str(exception)}" if context else str(exception)
        self.handle_error(error_type, error_message, show_dialog, parent)


# Create a singleton instance of the error handler
_instance: Optional[UIErrorHandler] = None

def get_error_handler(parent=None) -> UIErrorHandler:
    """
    Get the singleton instance of the error handler.
    
    Args:
        parent: The parent QObject.
    
    Returns:
        The error handler instance.
    """
    global _instance
    if _instance is None:
        _instance = UIErrorHandler(parent)
    return _instance
