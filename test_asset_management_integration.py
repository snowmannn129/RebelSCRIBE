#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the RebelSUITE Unified Asset Management System integration with RebelSCRIBE.

This script demonstrates how to use the asset management integration in RebelSCRIBE.
"""

import os
import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the RebelSCRIBE directory to the Python path
rebelsuite_path = os.path.abspath(os.path.dirname(__file__))
if rebelsuite_path not in sys.path:
    sys.path.append(rebelsuite_path)

from src.integrations.asset_management_integration import AssetManagementIntegration

class AssetManagementTestWindow(QMainWindow):
    """Test window for the asset management integration."""
    
    def __init__(self):
        """Initialize the test window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("RebelSCRIBE Asset Management Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create status label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Create button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Create import button
        self.import_button = QPushButton("Import Asset")
        self.import_button.clicked.connect(self.import_asset)
        button_layout.addWidget(self.import_button)
        
        # Create browse button
        self.browse_button = QPushButton("Browse Assets")
        self.browse_button.clicked.connect(self.browse_assets)
        button_layout.addWidget(self.browse_button)
        
        # Create search button
        self.search_button = QPushButton("Search Assets")
        self.search_button.clicked.connect(self.search_assets)
        button_layout.addWidget(self.search_button)
        
        # Create export button
        self.export_button = QPushButton("Export Asset")
        self.export_button.clicked.connect(self.export_asset)
        button_layout.addWidget(self.export_button)
        
        # Create content layout
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
        # Initialize asset management integration
        self.asset_integration = AssetManagementIntegration()
        success = self.asset_integration.initialize()
        
        if success:
            self.status_label.setText("Asset Management Integration loaded successfully")
            
            # Connect signals
            self.asset_integration.asset_imported.connect(self.on_asset_imported)
            self.asset_integration.asset_exported.connect(self.on_asset_exported)
            self.asset_integration.asset_selected.connect(self.on_asset_selected)
        else:
            self.status_label.setText("Failed to load Asset Management Integration")
            self.import_button.setEnabled(False)
            self.browse_button.setEnabled(False)
            self.search_button.setEnabled(False)
            self.export_button.setEnabled(False)
        
    def import_asset(self):
        """Import an asset."""
        try:
            # Create import dialog
            dialog = self.asset_integration.create_asset_import_dialog(self)
            
            if dialog:
                # Show dialog
                dialog.show()
            else:
                self.status_label.setText("Failed to create import dialog")
        except Exception as e:
            logger.error(f"Failed to import asset: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            
    def browse_assets(self):
        """Browse assets."""
        try:
            # Clear content layout
            self.clear_content_layout()
            
            # Create browser widget
            browser = self.asset_integration.create_asset_browser_widget(self)
            
            if browser:
                # Add to content layout
                self.content_layout.addWidget(browser)
            else:
                self.status_label.setText("Failed to create browser widget")
        except Exception as e:
            logger.error(f"Failed to browse assets: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            
    def search_assets(self):
        """Search assets."""
        try:
            # Clear content layout
            self.clear_content_layout()
            
            # Create search widget
            search = self.asset_integration.create_asset_search_widget(self)
            
            if search:
                # Add to content layout
                self.content_layout.addWidget(search)
            else:
                self.status_label.setText("Failed to create search widget")
        except Exception as e:
            logger.error(f"Failed to search assets: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            
    def export_asset(self):
        """Export an asset."""
        try:
            # Create export dialog
            dialog = self.asset_integration.create_asset_export_dialog(self)
            
            if dialog:
                # Set asset (in a real application, this would be the selected asset)
                # For this test, we'll use a hardcoded asset path
                dialog.set_asset("test.txt")
                
                # Show dialog
                dialog.show()
            else:
                self.status_label.setText("Failed to create export dialog")
        except Exception as e:
            logger.error(f"Failed to export asset: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            
    def on_asset_imported(self, asset_path):
        """
        Handle asset imported event.
        
        Args:
            asset_path (str): The asset path.
        """
        self.status_label.setText(f"Asset imported: {asset_path}")
        
    def on_asset_exported(self, asset_path, export_path):
        """
        Handle asset exported event.
        
        Args:
            asset_path (str): The asset path.
            export_path (str): The export path.
        """
        self.status_label.setText(f"Asset exported: {asset_path} to {export_path}")
        
    def on_asset_selected(self, asset_path):
        """
        Handle asset selected event.
        
        Args:
            asset_path (str): The asset path.
        """
        self.status_label.setText(f"Asset selected: {asset_path}")
        
    def clear_content_layout(self):
        """Clear the content layout."""
        # Remove all widgets from the content layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
    def closeEvent(self, event):
        """
        Handle close event.
        
        Args:
            event: The close event.
        """
        # Shut down asset management integration
        self.asset_integration.shutdown()
        
        # Accept event
        event.accept()


if __name__ == "__main__":
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show window
    window = AssetManagementTestWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())
