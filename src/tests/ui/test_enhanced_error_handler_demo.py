#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Enhanced Error Handler Demo

This script demonstrates the enhanced error handler in action.
It shows various error handling scenarios and features.
"""

import sys
import os
import time
from pathlib import Path

# Add src directory to path to allow imports
src_dir = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(src_dir))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QComboBox
from PyQt6.QtCore import Qt

from src.utils.logging_utils import setup_logging, get_logger
from src.ui.error_handler_init import initialize_error_handler
from src.ui.enhanced_error_handler import ErrorSeverity
from src.ui.error_handler_integration import get_integrated_error_handler

# Set up logging
setup_logging(
    log_file="error_handler_demo.log",
    console_output=True,
    file_output=True
)

logger = get_logger(__name__)


class ErrorHandlerDemoWindow(QMainWindow):
    """
    Demo window for showcasing the enhanced error handler.
    """
    
    def __init__(self):
        """Initialize the demo window."""
        super().__init__()
        
        # Initialize enhanced error handler
        initialize_error_handler()
        
        # Get error handler instance
        self.error_handler = get_integrated_error_handler(self)
        
        # Set up window properties
        self.setWindowTitle("Enhanced Error Handler Demo")
        self.setMinimumSize(600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title_label = QLabel("Enhanced Error Handler Demo")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # Add description
        description_label = QLabel(
            "This demo showcases the enhanced error handler features.\n"
            "Click the buttons below to trigger different types of errors and see how they are handled."
        )
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        # Add severity selector
        severity_layout = QVBoxLayout()
        severity_label = QLabel("Select Error Severity:")
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["INFO", "WARNING", "ERROR", "CRITICAL"])
        self.severity_combo.setCurrentIndex(2)  # Default to ERROR
        severity_layout.addWidget(severity_label)
        severity_layout.addWidget(self.severity_combo)
        layout.addLayout(severity_layout)
        
        # Add buttons
        self._add_button(layout, "Trigger Simple Error", self._on_simple_error)
        self._add_button(layout, "Trigger Exception", self._on_exception)
        self._add_button(layout, "Trigger Multiple Errors", self._on_multiple_errors)
        self._add_button(layout, "Trigger Component Error", self._on_component_error)
        self._add_button(layout, "Export Error History", self._on_export_history)
        self._add_button(layout, "Clear Error History", self._on_clear_history)
        
        # Add status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-style: italic; margin-top: 20px;")
        layout.addWidget(self.status_label)
        
        # Register components
        self._register_components()
        
        logger.info("Error Handler Demo window initialized")
    
    def _add_button(self, layout, text, callback):
        """
        Add a button to the layout.
        
        Args:
            layout: The layout to add the button to.
            text: The button text.
            callback: The button callback function.
        """
        button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(button)
    
    def _register_components(self):
        """Register components with the error handler."""
        # Register main component
        self.error_handler.register_component(
            component_name="ErrorHandlerDemo",
            metadata={"description": "Error Handler Demo Application"}
        )
        
        # Register sub-components
        self.error_handler.register_component(
            component_name="ErrorHandlerDemo.UI",
            parent_component="ErrorHandlerDemo",
            metadata={"description": "UI Components"}
        )
        
        self.error_handler.register_component(
            component_name="ErrorHandlerDemo.Logic",
            parent_component="ErrorHandlerDemo",
            metadata={"description": "Business Logic"}
        )
        
        self.error_handler.register_component(
            component_name="ErrorHandlerDemo.Data",
            parent_component="ErrorHandlerDemo",
            metadata={"description": "Data Management"}
        )
    
    def _get_selected_severity(self):
        """
        Get the selected error severity.
        
        Returns:
            The selected ErrorSeverity.
        """
        severity_text = self.severity_combo.currentText()
        return ErrorSeverity.from_string(severity_text)
    
    def _on_simple_error(self):
        """Handle simple error button click."""
        logger.debug("Simple error button clicked")
        
        # Get selected severity
        severity = self._get_selected_severity()
        
        # Trigger error
        error_id = self.error_handler.handle_error(
            error_type="SimpleError",
            error_message="This is a simple error message",
            severity=severity,
            component="ErrorHandlerDemo.UI",
            parent=self
        )
        
        # Update status
        self.status_label.setText(f"Simple error triggered with ID: {error_id}")
    
    def _on_exception(self):
        """Handle exception button click."""
        logger.debug("Exception button clicked")
        
        try:
            # Simulate an exception
            result = 1 / 0
        except Exception as e:
            # Handle the exception
            error_id = self.error_handler.handle_exception(
                exception=e,
                context="Division operation in _on_exception",
                severity=self._get_selected_severity(),
                component="ErrorHandlerDemo.Logic",
                parent=self
            )
            
            # Update status
            self.status_label.setText(f"Exception handled with ID: {error_id}")
    
    def _on_multiple_errors(self):
        """Handle multiple errors button click."""
        logger.debug("Multiple errors button clicked")
        
        # Get selected severity
        severity = self._get_selected_severity()
        
        # Trigger multiple errors
        error_ids = []
        for i in range(5):
            error_id = self.error_handler.handle_error(
                error_type="MultipleError",
                error_message=f"This is error #{i+1} in a series",
                severity=severity,
                component="ErrorHandlerDemo.Logic",
                parent=self
            )
            error_ids.append(error_id)
            time.sleep(0.5)  # Small delay between errors
        
        # Update status
        self.status_label.setText(f"Multiple errors triggered: {len(error_ids)}")
    
    def _on_component_error(self):
        """Handle component error button click."""
        logger.debug("Component error button clicked")
        
        # Get selected severity
        severity = self._get_selected_severity()
        
        # Trigger errors in different components
        components = [
            "ErrorHandlerDemo.UI",
            "ErrorHandlerDemo.Logic",
            "ErrorHandlerDemo.Data"
        ]
        
        error_ids = []
        for component in components:
            error_id = self.error_handler.handle_error(
                error_type="ComponentError",
                error_message=f"Error in component: {component}",
                severity=severity,
                component=component,
                parent=self
            )
            error_ids.append(error_id)
            time.sleep(0.5)  # Small delay between errors
        
        # Update status
        self.status_label.setText(f"Component errors triggered: {len(error_ids)}")
    
    def _on_export_history(self):
        """Handle export history button click."""
        logger.debug("Export history button clicked")
        
        # Create export directory if it doesn't exist
        export_dir = Path.home() / ".rebelscribe" / "error_reports"
        os.makedirs(export_dir, exist_ok=True)
        
        # Export error history
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Export as JSON
        json_path = export_dir / f"error_history_{timestamp}.json"
        json_success = self.error_handler.export_error_history(
            file_path=str(json_path),
            format="json",
            include_system_info=True,
            anonymize=False
        )
        
        # Export as CSV
        csv_path = export_dir / f"error_history_{timestamp}.csv"
        csv_success = self.error_handler.export_error_history(
            file_path=str(csv_path),
            format="csv",
            include_system_info=True,
            anonymize=False
        )
        
        # Export as TXT
        txt_path = export_dir / f"error_history_{timestamp}.txt"
        txt_success = self.error_handler.export_error_history(
            file_path=str(txt_path),
            format="txt",
            include_system_info=True,
            anonymize=False
        )
        
        # Update status
        if json_success and csv_success and txt_success:
            self.status_label.setText(f"Error history exported to {export_dir}")
        else:
            self.status_label.setText("Error exporting error history")
    
    def _on_clear_history(self):
        """Handle clear history button click."""
        logger.debug("Clear history button clicked")
        
        # Clear error history
        self.error_handler.clear_error_history()
        
        # Update status
        self.status_label.setText("Error history cleared")


def main():
    """Main entry point for the demo."""
    logger.info("Starting Enhanced Error Handler Demo")
    
    try:
        # Create application
        app = QApplication(sys.argv)
        
        # Create and show main window
        window = ErrorHandlerDemoWindow()
        window.show()
        
        # Run application
        return app.exec()
        
    except Exception as e:
        logger.error(f"Error running demo: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
