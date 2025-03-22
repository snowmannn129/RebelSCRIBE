#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Error Handler Initialization

This module initializes the error handler for RebelSCRIBE.
"""

import os
import sys
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ErrorHandler:
    """
    Error handler for RebelSCRIBE.
    
    This class handles errors and exceptions in the application.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.main_window = None
        
        logger.debug("Error handler initialized")
    
    def set_main_window(self, main_window):
        """
        Set the main window.
        
        Args:
            main_window: The main window.
        """
        self.main_window = main_window
    
    def show_error(self, message, title="Error", details=None):
        """
        Show an error message.
        
        Args:
            message: The error message.
            title: The error title.
            details: The error details.
        """
        logger.error(f"Error: {message}")
        
        # Create message box
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if details:
            msg_box.setDetailedText(details)
        
        # Show message box
        msg_box.exec()
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Handle an exception.
        
        Args:
            exc_type: The exception type.
            exc_value: The exception value.
            exc_traceback: The exception traceback.
        """
        # Log exception
        logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Format traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)
        
        # Show error message
        self.show_error(
            f"An unhandled exception occurred: {str(exc_value)}",
            "Unhandled Exception",
            tb_text
        )

# Global error handler
error_handler = ErrorHandler()

def initialize_error_handler():
    """Initialize the error handler."""
    logger.debug("Initializing error handler")
    
    # Set up exception hook
    sys.excepthook = error_handler.handle_exception
    
    logger.debug("Error handler initialized")
    
    return error_handler
