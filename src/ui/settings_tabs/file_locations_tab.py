#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - File Locations Settings Tab

This module implements the file locations settings tab for the settings dialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, 
    QPushButton, QLabel, QCheckBox, QSpinBox, QLineEdit
)
from PyQt6.QtCore import Qt

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class FileLocationsTab(QWidget):
    """File locations settings tab for the settings dialog."""
    
    def __init__(self, parent=None):
        """
        Initialize the file locations tab.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Initialize UI components
        self._init_ui()
        
        logger.debug("File locations tab initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        layout = QVBoxLayout(self)
        
        # Default save location group
        save_location_group = QGroupBox("Default Save Location")
        save_location_layout = QHBoxLayout(save_location_group)
        
        self.save_location_edit = QLineEdit()
        self.save_location_edit.setReadOnly(True)
        save_location_layout.addWidget(self.save_location_edit)
        
        self.save_location_button = QPushButton("Browse...")
        save_location_layout.addWidget(self.save_location_button)
        
        layout.addWidget(save_location_group)
        
        # Backup directory group
        backup_group = QGroupBox("Backup Directory")
        backup_layout = QHBoxLayout(backup_group)
        
        self.backup_location_edit = QLineEdit()
        self.backup_location_edit.setReadOnly(True)
        backup_layout.addWidget(self.backup_location_edit)
        
        self.backup_location_button = QPushButton("Browse...")
        backup_layout.addWidget(self.backup_location_button)
        
        layout.addWidget(backup_group)
        
        # Backup settings group
        backup_settings_group = QGroupBox("Backup Settings")
        backup_settings_layout = QFormLayout(backup_settings_group)
        
        self.enable_backups_checkbox = QCheckBox("Enable Automatic Backups")
        backup_settings_layout.addRow(self.enable_backups_checkbox)
        
        self.backup_interval_spinbox = QSpinBox()
        self.backup_interval_spinbox.setMinimum(5)
        self.backup_interval_spinbox.setMaximum(120)
        self.backup_interval_spinbox.setValue(30)
        self.backup_interval_spinbox.setSuffix(" minutes")
        backup_settings_layout.addRow("Backup Interval:", self.backup_interval_spinbox)
        
        self.max_backups_spinbox = QSpinBox()
        self.max_backups_spinbox.setMinimum(1)
        self.max_backups_spinbox.setMaximum(100)
        self.max_backups_spinbox.setValue(10)
        backup_settings_layout.addRow("Maximum Backups:", self.max_backups_spinbox)
        
        layout.addWidget(backup_settings_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def load_settings(self, settings):
        """
        Load settings into the tab.
        
        Args:
            settings: The settings dictionary.
        """
        file_locations = settings.get("file_locations", {})
        
        # Save location
        save_location = file_locations.get("save_location", "")
        self.save_location_edit.setText(save_location)
        
        # Backup location
        backup_location = file_locations.get("backup_location", "")
        self.backup_location_edit.setText(backup_location)
        
        # Backup settings
        enable_backups = file_locations.get("enable_backups", True)
        self.enable_backups_checkbox.setChecked(enable_backups)
        
        backup_interval = file_locations.get("backup_interval", 30)
        self.backup_interval_spinbox.setValue(backup_interval)
        self.backup_interval_spinbox.setEnabled(enable_backups)
        
        max_backups = file_locations.get("max_backups", 10)
        self.max_backups_spinbox.setValue(max_backups)
        self.max_backups_spinbox.setEnabled(enable_backups)
    
    def get_settings(self):
        """
        Get the current settings from the tab.
        
        Returns:
            A dictionary containing the current settings.
        """
        settings = {}
        
        # Save location
        settings["save_location"] = self.save_location_edit.text()
        
        # Backup location
        settings["backup_location"] = self.backup_location_edit.text()
        
        # Backup settings
        settings["enable_backups"] = self.enable_backups_checkbox.isChecked()
        settings["backup_interval"] = self.backup_interval_spinbox.value()
        settings["max_backups"] = self.max_backups_spinbox.value()
        
        return settings
    
    def connect_signals(self, dialog):
        """
        Connect signals to the dialog.
        
        Args:
            dialog: The parent dialog.
        """
        self.save_location_button.clicked.connect(dialog._on_select_save_location)
        self.backup_location_button.clicked.connect(dialog._on_select_backup_location)
        self.enable_backups_checkbox.toggled.connect(dialog._on_enable_backups_toggled)
