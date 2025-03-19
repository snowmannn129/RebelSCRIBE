#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Error Handler Integration

This module provides integration between the original error handler and the enhanced error handler.
It ensures backward compatibility while providing access to the enhanced features.
"""

from typing import Optional, Dict, Any, Callable
from PyQt6.QtWidgets import QWidget

from src.utils.logging_utils import get_logger
from src.ui.error_handler import UIErrorHandler, get_error_handler
from src.ui.enhanced_error_handler import (
    EnhancedErrorHandler, get_enhanced_error_handler, 
    ErrorSeverity, ErrorRecord, ErrorFilter, ErrorCallback
)

logger = get_logger(__name__)


class ErrorHandlerIntegration:
    """
    Integration class for transitioning from the original error handler to the enhanced one.
    
    This class wraps the enhanced error handler and provides the same interface as the
    original error handler, ensuring backward compatibility while providing access to
    the enhanced features.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the error handler integration.
        
        Args:
            parent: The parent QObject.
        """
        # Get instances of both error handlers
        self.original_handler = get_error_handler(parent)
        self.enhanced_handler = get_enhanced_error_handler(parent)
        
        # Connect signals
        self._connect_signals()
        
        logger.debug("Error Handler Integration initialized")
    
    def _connect_signals(self):
        """Connect signals between the original and enhanced error handlers."""
        # Connect enhanced handler's error_occurred signal to original handler's error_occurred signal
        self.enhanced_handler.error_occurred.connect(self._on_enhanced_error_occurred)
    
    def _on_enhanced_error_occurred(self, error_record: ErrorRecord):
        """
        Handle error occurred event from enhanced handler.
        
        Args:
            error_record: The error record.
        """
        # Emit the original handler's error_occurred signal
        self.original_handler.error_occurred.emit(error_record.error_type, error_record.error_message)
    
    def handle_error(self, error_type: str, error_message: str, 
                    show_dialog: bool = True, parent=None) -> str:
        """
        Handle an error using the enhanced error handler.
        
        Args:
            error_type: The type of error.
            error_message: The error message.
            show_dialog: Whether to show an error dialog.
            parent: The parent widget for the error dialog.
            
        Returns:
            The ID of the error record.
        """
        # Determine severity based on error type
        severity = self._determine_severity_from_type(error_type)
        
        # Call enhanced handler
        return self.enhanced_handler.handle_error(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            parent=parent,
            show_dialog=show_dialog
        )
    
    def handle_exception(self, exception: Exception, context: str = "",
                        show_dialog: bool = True, parent=None) -> str:
        """
        Handle an exception using the enhanced error handler.
        
        Args:
            exception: The exception to handle.
            context: The context in which the exception occurred.
            show_dialog: Whether to show an error dialog.
            parent: The parent widget for the error dialog.
            
        Returns:
            The ID of the error record.
        """
        # Call enhanced handler
        return self.enhanced_handler.handle_exception(
            exception=exception,
            context=context,
            parent=parent,
            show_dialog=show_dialog
        )
    
    def _determine_severity_from_type(self, error_type: str) -> ErrorSeverity:
        """
        Determine the severity of an error based on its type.
        
        Args:
            error_type: The type of error.
            
        Returns:
            The error severity.
        """
        # Critical errors
        if any(critical in error_type.lower() for critical in [
            'critical', 'fatal', 'crash', 'corrupt', 'emergency', 'system'
        ]):
            return ErrorSeverity.CRITICAL
        
        # Warning errors
        if any(warning in error_type.lower() for warning in [
            'warning', 'caution', 'attention', 'notice'
        ]):
            return ErrorSeverity.WARNING
        
        # Info errors
        if any(info in error_type.lower() for info in [
            'info', 'information', 'notification', 'note'
        ]):
            return ErrorSeverity.INFO
        
        # Default to ERROR
        return ErrorSeverity.ERROR
    
    # Enhanced methods (not in the original interface)
    
    def log_error(self, error_type: str, error_message: str, 
                 severity: ErrorSeverity = ErrorSeverity.ERROR, 
                 component: Optional[str] = None) -> str:
        """
        Log an error without displaying a UI message.
        
        Args:
            error_type: The type of error.
            error_message: The error message.
            severity: The error severity.
            component: The component that generated the error.
            
        Returns:
            The ID of the error record.
        """
        return self.enhanced_handler.log_error(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            component=component
        )
    
    def get_error_history(self, 
                         severity: Optional[ErrorSeverity] = None, 
                         component: Optional[str] = None, 
                         limit: Optional[int] = None) -> list:
        """
        Get the history of errors, optionally filtered by severity and component.
        
        Args:
            severity: Filter by severity level.
            component: Filter by component.
            limit: Maximum number of errors to return.
            
        Returns:
            List of error records.
        """
        return self.enhanced_handler.get_error_history(
            severity=severity,
            component=component,
            limit=limit
        )
    
    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.enhanced_handler.clear_error_history()
    
    def export_error_history(self, 
                            file_path: str, 
                            format: str = "json", 
                            include_system_info: bool = True, 
                            anonymize: bool = False) -> bool:
        """
        Export the error history to a file.
        
        Args:
            file_path: The path to export to.
            format: The format to export in ("json", "csv", "txt").
            include_system_info: Whether to include system information.
            anonymize: Whether to anonymize sensitive data.
            
        Returns:
            True if the export was successful, False otherwise.
        """
        return self.enhanced_handler.export_error_history(
            file_path=file_path,
            format=format,
            include_system_info=include_system_info,
            anonymize=anonymize
        )
    
    def report_error(self, 
                    error_id: str, 
                    include_system_info: bool = True, 
                    anonymize: bool = False,
                    additional_info: Optional[Dict[str, Any]] = None,
                    report_service: Optional[str] = None) -> bool:
        """
        Report an error to the error reporting system.
        
        Args:
            error_id: The ID of the error to report.
            include_system_info: Whether to include system information in the report.
            anonymize: Whether to anonymize sensitive data in the report.
            additional_info: Additional information to include in the report.
            report_service: The reporting service to use (default: configured service).
            
        Returns:
            True if the report was sent successfully, False otherwise.
        """
        return self.enhanced_handler.report_error(
            error_id=error_id,
            include_system_info=include_system_info,
            anonymize=anonymize,
            additional_info=additional_info,
            report_service=report_service
        )
    
    def set_error_callback(self, 
                          error_type: Optional[str] = None, 
                          severity: Optional[ErrorSeverity] = None, 
                          component: Optional[str] = None, 
                          callback: Optional[Callable[[ErrorRecord], None]] = None) -> str:
        """
        Set a callback for errors of a specific type, severity, and/or component.
        
        Args:
            error_type: The type of error to match.
            severity: The severity level to match.
            component: The component to match.
            callback: The callback function.
            
        Returns:
            A callback ID that can be used to remove the callback.
        """
        return self.enhanced_handler.set_error_callback(
            error_type=error_type,
            severity=severity,
            component=component,
            callback=callback
        )
    
    def remove_error_callback(self, callback_id: str) -> bool:
        """
        Remove an error callback by its ID.
        
        Args:
            callback_id: The ID of the callback to remove.
            
        Returns:
            True if the callback was removed, False if it wasn't found.
        """
        return self.enhanced_handler.remove_error_callback(callback_id)
    
    def register_component(self, 
                          component_name: str, 
                          parent_component: Optional[str] = None, 
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a component with the error handler.
        
        Args:
            component_name: The name of the component.
            parent_component: The name of the parent component, if any.
            metadata: Additional metadata for the component.
        """
        self.enhanced_handler.register_component(
            component_name=component_name,
            parent_component=parent_component,
            metadata=metadata
        )
    
    def unregister_component(self, component_name: str) -> bool:
        """
        Unregister a component from the error handler.
        
        Args:
            component_name: The name of the component.
            
        Returns:
            True if the component was unregistered, False if it wasn't found.
        """
        return self.enhanced_handler.unregister_component(component_name)


# Create a singleton instance of the error handler integration
_integration_instance: Optional[ErrorHandlerIntegration] = None

def get_integrated_error_handler(parent=None) -> ErrorHandlerIntegration:
    """
    Get the singleton instance of the error handler integration.
    
    Args:
        parent: The parent QObject.
        
    Returns:
        The error handler integration instance.
    """
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = ErrorHandlerIntegration(parent)
    return _integration_instance


def replace_error_handler():
    """
    Replace the original error handler with the enhanced one.
    
    This function replaces the get_error_handler function in the error_handler module
    with the get_integrated_error_handler function from this module, ensuring that
    all code that uses the original error handler will now use the enhanced one.
    """
    import src.ui.error_handler
    src.ui.error_handler.get_error_handler = get_integrated_error_handler
    logger.info("Original error handler replaced with enhanced error handler")
