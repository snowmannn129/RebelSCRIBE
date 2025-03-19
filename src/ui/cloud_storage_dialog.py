#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - Cloud Storage Dialog

This module implements a dialog for configuring cloud storage settings.
"""

import os
import sys
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton,
    QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.backend.services.cloud_storage_service import CloudStorageService, CloudProvider

logger = get_logger(__name__)
config = ConfigManager()


class CloudStorageDialog(QDialog):
    """
    Cloud storage settings dialog for RebelSCRIBE.
    
    This dialog allows users to configure cloud storage settings including:
    - Cloud storage provider selection (Dropbox, Google Drive, OneDrive)
    - Authentication and connection settings
    - Synchronization options
    - File management
    """
    
    # Signal emitted when settings are changed
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, cloud_storage_service=None):
        """
        Initialize the cloud storage dialog.
        
        Args:
            parent: The parent widget.
            cloud_storage_service: The cloud storage service instance.
        """
        super().__init__(parent)
        
        self.cloud_storage_service = cloud_storage_service or CloudStorageService()
        
        # Initialize UI components
        self._init_ui()
        
        # Load current settings
        self._load_settings()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Cloud storage dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing cloud storage dialog UI components")
        
        # Set window properties
        self.setWindowTitle("Cloud Storage Settings")
        self.setMinimumSize(600, 450)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_provider_tab()
        self._create_sync_tab()
        self._create_files_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel | 
            QDialogButtonBox.StandardButton.Apply
        )
        self.main_layout.addWidget(self.button_box)
        
        # Initialize UI state
        # Disable provider radios initially
        for radio in self.provider_radios.values():
            radio.setEnabled(False)
        
        # Disable sync interval spin initially
        self.sync_interval_spin.setEnabled(False)
        
        # Set default conflict resolution
        self.conflict_ask_radio.setChecked(True)
        
        # Show Dropbox settings initially if Dropbox is selected
        if self.provider_radios[CloudProvider.DROPBOX.value].isChecked():
            self.dropbox_settings_widget.show()
            self.google_drive_settings_widget.hide()
            self.onedrive_settings_widget.hide()
        
        logger.debug("Cloud storage dialog UI components initialized")
    
    def _create_provider_tab(self):
        """Create the cloud storage provider settings tab."""
        logger.debug("Creating cloud storage provider settings tab")
        
        # Create tab widget
        self.provider_tab = QWidget()
        self.tab_widget.addTab(self.provider_tab, "Provider")
        
        # Create layout
        layout = QVBoxLayout(self.provider_tab)
        
        # Enable cloud storage checkbox
        self.enable_cloud_storage_checkbox = QCheckBox("Enable Cloud Storage")
        layout.addWidget(self.enable_cloud_storage_checkbox)
        
        # Provider selection group
        provider_group = QGroupBox("Cloud Storage Provider")
        provider_layout = QVBoxLayout(provider_group)
        
        # Provider radio buttons
        self.provider_radios = {}
        
        for provider in CloudProvider:
            radio = QRadioButton(self._get_provider_display_name(provider.value))
            provider_layout.addWidget(radio)
            self.provider_radios[provider.value] = radio
        
        layout.addWidget(provider_group)
        
        # Provider settings stacked widget (will contain different settings for each provider)
        self.provider_settings_group = QGroupBox("Provider Settings")
        self.provider_settings_layout = QVBoxLayout(self.provider_settings_group)
        
        # Dropbox settings
        self.dropbox_settings_widget = QWidget()
        dropbox_layout = QFormLayout(self.dropbox_settings_widget)
        
        self.dropbox_api_key_edit = QLineEdit()
        self.dropbox_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(self.dropbox_api_key_edit)
        
        self.dropbox_show_api_key_button = QPushButton("Show")
        self.dropbox_show_api_key_button.setCheckable(True)
        self.dropbox_show_api_key_button.setFixedWidth(60)
        api_key_layout.addWidget(self.dropbox_show_api_key_button)
        
        dropbox_layout.addRow("API Key:", api_key_layout)
        
        self.dropbox_folder_edit = QLineEdit()
        self.dropbox_folder_edit.setPlaceholderText("/RebelSCRIBE")
        dropbox_layout.addRow("Folder:", self.dropbox_folder_edit)
        
        # Google Drive settings
        self.google_drive_settings_widget = QWidget()
        google_drive_layout = QFormLayout(self.google_drive_settings_widget)
        
        self.google_drive_credentials_edit = QLineEdit()
        credentials_layout = QHBoxLayout()
        credentials_layout.addWidget(self.google_drive_credentials_edit)
        
        self.google_drive_browse_button = QPushButton("Browse...")
        self.google_drive_browse_button.setFixedWidth(80)
        credentials_layout.addWidget(self.google_drive_browse_button)
        
        google_drive_layout.addRow("Credentials File:", credentials_layout)
        
        self.google_drive_folder_edit = QLineEdit()
        self.google_drive_folder_edit.setPlaceholderText("RebelSCRIBE")
        google_drive_layout.addRow("Folder:", self.google_drive_folder_edit)
        
        # OneDrive settings
        self.onedrive_settings_widget = QWidget()
        onedrive_layout = QFormLayout(self.onedrive_settings_widget)
        
        self.onedrive_client_id_edit = QLineEdit()
        onedrive_layout.addRow("Client ID:", self.onedrive_client_id_edit)
        
        self.onedrive_folder_edit = QLineEdit()
        self.onedrive_folder_edit.setPlaceholderText("RebelSCRIBE")
        onedrive_layout.addRow("Folder:", self.onedrive_folder_edit)
        
        # Add all provider settings widgets to the layout
        self.provider_settings_layout.addWidget(self.dropbox_settings_widget)
        self.provider_settings_layout.addWidget(self.google_drive_settings_widget)
        self.provider_settings_layout.addWidget(self.onedrive_settings_widget)
        
        # Hide all provider settings initially
        self.dropbox_settings_widget.hide()
        self.google_drive_settings_widget.hide()
        self.onedrive_settings_widget.hide()
        
        layout.addWidget(self.provider_settings_group)
        
        # Connection status group
        connection_group = QGroupBox("Connection Status")
        connection_layout = QVBoxLayout(connection_group)
        
        # Status label
        self.connection_status_label = QLabel("Not connected")
        connection_layout.addWidget(self.connection_status_label)
        
        # Last sync time label
        self.last_sync_label = QLabel("Last sync: Never")
        connection_layout.addWidget(self.last_sync_label)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        connection_layout.addWidget(self.connect_button)
        
        layout.addWidget(connection_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Cloud storage provider settings tab created")
    
    def _create_sync_tab(self):
        """Create the synchronization settings tab."""
        logger.debug("Creating synchronization settings tab")
        
        # Create tab widget
        self.sync_tab = QWidget()
        self.tab_widget.addTab(self.sync_tab, "Synchronization")
        
        # Create layout
        layout = QVBoxLayout(self.sync_tab)
        
        # Sync options group
        sync_options_group = QGroupBox("Synchronization Options")
        sync_options_layout = QVBoxLayout(sync_options_group)
        
        # Auto sync checkbox
        self.auto_sync_checkbox = QCheckBox("Enable automatic synchronization")
        sync_options_layout.addWidget(self.auto_sync_checkbox)
        
        # Sync interval
        sync_interval_layout = QHBoxLayout()
        sync_interval_layout.addWidget(QLabel("Sync interval:"))
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(1, 1440)  # 1 minute to 24 hours
        self.sync_interval_spin.setValue(30)
        self.sync_interval_spin.setSuffix(" minutes")
        sync_interval_layout.addWidget(self.sync_interval_spin)
        
        sync_interval_layout.addStretch()
        sync_options_layout.addLayout(sync_interval_layout)
        
        # Sync on save checkbox
        self.sync_on_save_checkbox = QCheckBox("Synchronize on save")
        sync_options_layout.addWidget(self.sync_on_save_checkbox)
        
        # Sync on open checkbox
        self.sync_on_open_checkbox = QCheckBox("Synchronize on project open")
        sync_options_layout.addWidget(self.sync_on_open_checkbox)
        
        layout.addWidget(sync_options_group)
        
        # Conflict resolution group
        conflict_group = QGroupBox("Conflict Resolution")
        conflict_layout = QVBoxLayout(conflict_group)
        
        # Conflict resolution radio buttons
        self.conflict_local_radio = QRadioButton("Use local version")
        conflict_layout.addWidget(self.conflict_local_radio)
        
        self.conflict_remote_radio = QRadioButton("Use remote version")
        conflict_layout.addWidget(self.conflict_remote_radio)
        
        self.conflict_ask_radio = QRadioButton("Ask me every time")
        conflict_layout.addWidget(self.conflict_ask_radio)
        
        layout.addWidget(conflict_group)
        
        # Folders to sync group
        folders_group = QGroupBox("Folders to Synchronize")
        folders_layout = QVBoxLayout(folders_group)
        
        # Folder checkboxes
        self.folder_checkboxes = {}
        
        for folder in ["documents", "research", "notes", "images", "exports"]:
            checkbox = QCheckBox(folder)
            folders_layout.addWidget(checkbox)
            self.folder_checkboxes[folder] = checkbox
        
        layout.addWidget(folders_group)
        
        # Manual sync group
        manual_sync_group = QGroupBox("Manual Synchronization")
        manual_sync_layout = QHBoxLayout(manual_sync_group)
        
        # Sync now button
        self.sync_now_button = QPushButton("Sync Now")
        manual_sync_layout.addWidget(self.sync_now_button)
        
        layout.addWidget(manual_sync_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Synchronization settings tab created")
    
    def _create_files_tab(self):
        """Create the files tab."""
        logger.debug("Creating files tab")
        
        # Create tab widget
        self.files_tab = QWidget()
        self.tab_widget.addTab(self.files_tab, "Files")
        
        # Create layout
        layout = QVBoxLayout(self.files_tab)
        
        # Files list group
        files_group = QGroupBox("Cloud Files")
        files_layout = QVBoxLayout(files_group)
        
        # Files table
        self.files_table = QTableWidget(0, 4)  # 0 rows, 4 columns
        self.files_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Modified"])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.verticalHeader().setVisible(False)
        self.files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        files_layout.addWidget(self.files_table)
        
        # Files buttons
        files_buttons_layout = QHBoxLayout()
        
        self.refresh_files_button = QPushButton("Refresh")
        files_buttons_layout.addWidget(self.refresh_files_button)
        
        self.download_file_button = QPushButton("Download")
        files_buttons_layout.addWidget(self.download_file_button)
        
        self.upload_file_button = QPushButton("Upload")
        files_buttons_layout.addWidget(self.upload_file_button)
        
        self.delete_file_button = QPushButton("Delete")
        files_buttons_layout.addWidget(self.delete_file_button)
        
        files_layout.addLayout(files_buttons_layout)
        
        layout.addWidget(files_group)
        
        # Progress group
        progress_group = QGroupBox("Transfer Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Files tab created")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        
        # Connect provider tab signals
        self.enable_cloud_storage_checkbox.toggled.connect(self._on_enable_cloud_storage_toggled)
        
        for provider, radio in self.provider_radios.items():
            radio.toggled.connect(lambda checked, p=provider: self._on_provider_changed(p, checked))
        
        self.dropbox_show_api_key_button.toggled.connect(lambda checked: 
            self.dropbox_api_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        
        self.google_drive_browse_button.clicked.connect(self._on_browse_credentials)
        
        self.connect_button.clicked.connect(self._on_connect)
        
        # Connect sync tab signals
        self.auto_sync_checkbox.toggled.connect(self._on_auto_sync_toggled)
        self.sync_now_button.clicked.connect(self._on_sync_now)
        
        # Connect files tab signals
        self.refresh_files_button.clicked.connect(self._on_refresh_files)
        self.download_file_button.clicked.connect(self._on_download_file)
        self.upload_file_button.clicked.connect(self._on_upload_file)
        self.delete_file_button.clicked.connect(self._on_delete_file)
        
        logger.debug("Signals connected")
    
    def _load_settings(self):
        """Load current cloud storage settings."""
        logger.debug("Loading current cloud storage settings")
        
        try:
            # Get settings from service
            settings = self.cloud_storage_service.get_settings()
            
            # Load enable cloud storage
            self.enable_cloud_storage_checkbox.setChecked(settings.get("enabled", False))
            
            # Load provider
            provider = settings.get("provider", CloudProvider.DROPBOX.value)
            if provider in self.provider_radios:
                self.provider_radios[provider].setChecked(True)
            
            # Handle potential MagicMock objects in config
            try:
                # Load Dropbox settings
                dropbox_config = config.config.get("cloud_storage", {}).get("dropbox", {})
                if isinstance(dropbox_config.get("api_key"), str):
                    self.dropbox_api_key_edit.setText(dropbox_config.get("api_key", ""))
                else:
                    self.dropbox_api_key_edit.setText("")
                    
                if isinstance(dropbox_config.get("folder"), str):
                    self.dropbox_folder_edit.setText(dropbox_config.get("folder", "/RebelSCRIBE"))
                else:
                    self.dropbox_folder_edit.setText("/RebelSCRIBE")
                
                # Load Google Drive settings
                google_drive_config = config.config.get("cloud_storage", {}).get("google_drive", {})
                if isinstance(google_drive_config.get("credentials_file"), str):
                    self.google_drive_credentials_edit.setText(google_drive_config.get("credentials_file", ""))
                else:
                    self.google_drive_credentials_edit.setText("")
                    
                if isinstance(google_drive_config.get("folder"), str):
                    self.google_drive_folder_edit.setText(google_drive_config.get("folder", "RebelSCRIBE"))
                else:
                    self.google_drive_folder_edit.setText("RebelSCRIBE")
                
                # Load OneDrive settings
                onedrive_config = config.config.get("cloud_storage", {}).get("onedrive", {})
                if isinstance(onedrive_config.get("client_id"), str):
                    self.onedrive_client_id_edit.setText(onedrive_config.get("client_id", ""))
                else:
                    self.onedrive_client_id_edit.setText("")
                    
                if isinstance(onedrive_config.get("folder"), str):
                    self.onedrive_folder_edit.setText(onedrive_config.get("folder", "RebelSCRIBE"))
                else:
                    self.onedrive_folder_edit.setText("RebelSCRIBE")
            except Exception as config_error:
                logger.error(f"Error loading config settings: {config_error}")
                # Set default values
                self.dropbox_api_key_edit.setText("")
                self.dropbox_folder_edit.setText("/RebelSCRIBE")
                self.google_drive_credentials_edit.setText("")
                self.google_drive_folder_edit.setText("RebelSCRIBE")
                self.onedrive_client_id_edit.setText("")
                self.onedrive_folder_edit.setText("RebelSCRIBE")
            
            # Load sync settings
            self.auto_sync_checkbox.setChecked(settings.get("auto_sync", False))
            self.sync_interval_spin.setValue(settings.get("sync_interval_minutes", 30))
            self.sync_on_save_checkbox.setChecked(settings.get("sync_on_save", False))
            self.sync_on_open_checkbox.setChecked(settings.get("sync_on_open", False))
            
            # Load conflict resolution
            conflict_resolution = settings.get("conflict_resolution", "ask")
            if conflict_resolution == "local":
                self.conflict_local_radio.setChecked(True)
            elif conflict_resolution == "remote":
                self.conflict_remote_radio.setChecked(True)
            else:
                # Default to "ask" for conflict resolution
                self.conflict_ask_radio.setChecked(True)
            
            # Load folders to sync
            sync_folders = settings.get("sync_folders", [])
            for folder, checkbox in self.folder_checkboxes.items():
                checkbox.setChecked(folder in sync_folders)
            
            # Update connection status
            self._update_connection_status()
            
            # Set default conflict resolution
            self.conflict_ask_radio.setChecked(True)
            
            # Update UI state based on settings
            self._update_ui_state()
            
            logger.debug("Cloud storage settings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading cloud storage settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load cloud storage settings: {e}")
    
    def _update_connection_status(self):
        """Update the connection status display."""
        logger.debug("Updating connection status")
        
        try:
            # Get connection status
            status = self.cloud_storage_service.get_connection_status()
            
            # Update status label
            if status["connected"]:
                self.connection_status_label.setText(f"Connected to {status['provider']}")
                self.connection_status_label.setStyleSheet("color: green;")
                self.connect_button.setText("Disconnect")
            else:
                if status["error"]:
                    self.connection_status_label.setText(f"Not connected: {status['error']}")
                    self.connection_status_label.setStyleSheet("color: red;")
                else:
                    self.connection_status_label.setText("Not connected")
                    self.connection_status_label.setStyleSheet("")
                
                self.connect_button.setText("Connect")
            
            # Update last sync time
            if status["last_sync_time"]:
                self.last_sync_label.setText(f"Last sync: {status['last_sync_time']}")
            else:
                self.last_sync_label.setText("Last sync: Never")
            
            logger.debug("Connection status updated successfully")
        except Exception as e:
            logger.error(f"Error updating connection status: {e}")
    
    def _update_ui_state(self):
        """Update UI state based on current settings."""
        logger.debug("Updating UI state")
        
        # Enable/disable provider settings based on cloud storage enabled
        enabled = self.enable_cloud_storage_checkbox.isChecked()
        
        # Disable provider radios when cloud storage is disabled
        for radio in self.provider_radios.values():
            radio.setEnabled(enabled)
        
        self.provider_settings_group.setEnabled(enabled)
        self.connect_button.setEnabled(enabled)
        
        # Show/hide provider settings based on selected provider
        # First hide all provider settings
        self.dropbox_settings_widget.hide()
        self.google_drive_settings_widget.hide()
        self.onedrive_settings_widget.hide()
        
        # Then show only the selected provider's settings
        for provider in CloudProvider:
            if self.provider_radios[provider.value].isChecked():
                if provider == CloudProvider.DROPBOX:
                    self.dropbox_settings_widget.show()
                elif provider == CloudProvider.GOOGLE_DRIVE:
                    self.google_drive_settings_widget.show()
                elif provider == CloudProvider.ONEDRIVE:
                    self.onedrive_settings_widget.show()
                break
        
        # Enable/disable sync settings based on auto sync enabled
        auto_sync_enabled = self.auto_sync_checkbox.isChecked()
        self.sync_interval_spin.setEnabled(auto_sync_enabled)
        
        # Enable/disable files tab buttons based on connection status
        connected = self.cloud_storage_service.is_connected()
        self.refresh_files_button.setEnabled(connected)
        self.download_file_button.setEnabled(connected and self.files_table.selectedItems())
        self.upload_file_button.setEnabled(connected)
        self.delete_file_button.setEnabled(connected and self.files_table.selectedItems())
        self.sync_now_button.setEnabled(connected)
        
        logger.debug("UI state updated successfully")
    
    def _get_current_settings(self) -> Dict[str, Any]:
        """
        Get current settings from the dialog.
        
        Returns:
            A dictionary containing the current settings.
        """
        logger.debug("Getting current settings from dialog")
        
        settings = {}
        
        # Get enable cloud storage
        settings["enabled"] = self.enable_cloud_storage_checkbox.isChecked()
        
        # Get provider
        for provider, radio in self.provider_radios.items():
            if radio.isChecked():
                settings["provider"] = provider
                break
        
        # Get sync settings
        settings["auto_sync"] = self.auto_sync_checkbox.isChecked()
        settings["sync_interval_minutes"] = self.sync_interval_spin.value()
        settings["sync_on_save"] = self.sync_on_save_checkbox.isChecked()
        settings["sync_on_open"] = self.sync_on_open_checkbox.isChecked()
        
        # Get conflict resolution
        if self.conflict_local_radio.isChecked():
            settings["conflict_resolution"] = "local"
        elif self.conflict_remote_radio.isChecked():
            settings["conflict_resolution"] = "remote"
        else:
            settings["conflict_resolution"] = "ask"
        
        # Get folders to sync
        sync_folders = []
        for folder, checkbox in self.folder_checkboxes.items():
            if checkbox.isChecked():
                sync_folders.append(folder)
        
        settings["sync_folders"] = sync_folders
        
        # Get provider-specific settings
        provider_settings = {}
        
        # Dropbox settings
        dropbox_settings = {}
        dropbox_settings["api_key"] = self.dropbox_api_key_edit.text()
        dropbox_settings["folder"] = self.dropbox_folder_edit.text()
        provider_settings["dropbox"] = dropbox_settings
        
        # Google Drive settings
        google_drive_settings = {}
        google_drive_settings["credentials_file"] = self.google_drive_credentials_edit.text()
        google_drive_settings["folder"] = self.google_drive_folder_edit.text()
        provider_settings["google_drive"] = google_drive_settings
        
        # OneDrive settings
        onedrive_settings = {}
        onedrive_settings["client_id"] = self.onedrive_client_id_edit.text()
        onedrive_settings["folder"] = self.onedrive_folder_edit.text()
        provider_settings["onedrive"] = onedrive_settings
        
        # Add provider settings to main settings
        settings["provider_settings"] = provider_settings
        
        logger.debug("Current settings retrieved from dialog")
        
        return settings
    
    def _save_settings(self):
        """Save current cloud storage settings."""
        logger.debug("Saving current cloud storage settings")
        
        try:
            # Get current settings
            settings = self._get_current_settings()
            
            try:
                # Update config
                config_data = config.config
                
                # Update main cloud storage settings
                cloud_storage_config = config_data.get("cloud_storage", {})
                cloud_storage_config["enabled"] = settings["enabled"]
                cloud_storage_config["provider"] = settings["provider"]
                cloud_storage_config["auto_sync"] = settings["auto_sync"]
                cloud_storage_config["sync_interval_minutes"] = settings["sync_interval_minutes"]
                cloud_storage_config["sync_on_save"] = settings["sync_on_save"]
                cloud_storage_config["sync_on_open"] = settings["sync_on_open"]
                cloud_storage_config["conflict_resolution"] = settings["conflict_resolution"]
                cloud_storage_config["sync_folders"] = settings["sync_folders"]
                
                # Update provider-specific settings
                provider_settings = settings["provider_settings"]
                
                for provider, provider_config in provider_settings.items():
                    if provider not in cloud_storage_config:
                        cloud_storage_config[provider] = {}
                    
                    for key, value in provider_config.items():
                        cloud_storage_config[provider][key] = value
                
                config_data["cloud_storage"] = cloud_storage_config
                config.save_config(config_data)
            except Exception as config_error:
                logger.error(f"Error updating config: {config_error}")
                # Continue with the rest of the function
            
            # Update cloud storage service
            try:
                self.cloud_storage_service.update_settings(settings)
            except Exception as service_error:
                logger.error(f"Error updating cloud storage service: {service_error}")
                # Continue with the rest of the function
            
            # Update UI
            self._update_connection_status()
            self._update_ui_state()
            
            # Emit settings changed signal
            try:
                self.settings_changed.emit(settings)
            except Exception as signal_error:
                logger.error(f"Error emitting settings changed signal: {signal_error}")
                # Continue with the rest of the function
            
            logger.debug("Cloud storage settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving cloud storage settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save cloud storage settings: {e}")
            return False
    
    def _get_provider_display_name(self, provider: str) -> str:
        """
        Get the display name for a provider.
        
        Args:
            provider: The provider value.
            
        Returns:
            The display name.
        """
        if provider == CloudProvider.DROPBOX.value:
            return "Dropbox"
        elif provider == CloudProvider.GOOGLE_DRIVE.value:
            return "Google Drive"
        elif provider == CloudProvider.ONEDRIVE.value:
            return "OneDrive"
        else:
            return provider.capitalize()
    
    def _on_enable_cloud_storage_toggled(self, checked: bool):
        """
        Handle enable cloud storage checkbox toggled.
        
        Args:
            checked: Whether the checkbox is checked.
        """
        logger.debug(f"Enable cloud storage toggled: {checked}")
        
        # Enable/disable provider radios
        for radio in self.provider_radios.values():
            radio.setEnabled(checked)
        
        # Update UI state
        self._update_ui_state()
    
    def _on_provider_changed(self, provider: str, checked: bool):
        """
        Handle provider radio button toggled.
        
        Args:
            provider: The provider value.
            checked: Whether the radio button is checked.
        """
        if checked:
            logger.debug(f"Provider changed to: {provider}")
            
            # Hide all provider settings widgets
            self.dropbox_settings_widget.hide()
            self.google_drive_settings_widget.hide()
            self.onedrive_settings_widget.hide()
            
            # Show the selected provider's settings widget
            if provider == CloudProvider.DROPBOX.value:
                self.dropbox_settings_widget.show()
            elif provider == CloudProvider.GOOGLE_DRIVE.value:
                self.google_drive_settings_widget.show()
            elif provider == CloudProvider.ONEDRIVE.value:
                self.onedrive_settings_widget.show()
            
            # Update UI state
            self._update_ui_state()
    
    def _on_browse_credentials(self):
        """Handle browse credentials button clicked."""
        logger.debug("Browse credentials button clicked")
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Google Drive Credentials File",
            self.google_drive_credentials_edit.text() or "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Update credentials edit
            self.google_drive_credentials_edit.setText(file_path)
            
            logger.debug(f"Google Drive credentials file selected: {file_path}")
    
    def _on_connect(self):
        """Handle connect button clicked."""
        logger.debug("Connect button clicked")
        
        # Check if already connected
        if self.cloud_storage_service.is_connected():
            # Disconnect
            # Note: In a real implementation, we would need to add a disconnect method to the service
            # For now, we'll just update the settings to disable cloud storage
            settings = self._get_current_settings()
            settings["enabled"] = False
            
            # Update service
            self.cloud_storage_service.update_settings(settings)
            
            # Update UI
            self._update_connection_status()
            self._update_ui_state()
            
            logger.debug("Disconnected from cloud storage")
        else:
            # Save settings first
            if not self._save_settings():
                return
            
            # Call authenticate_user directly
            result = self.cloud_storage_service.authenticate_user()
            
            # Connect
            if result:
                # Update UI
                self._update_connection_status()
                self._update_ui_state()
                
                # Refresh files
                self._on_refresh_files()
                
                logger.debug("Connected to cloud storage")
                QMessageBox.information(self, "Connection Successful", "Successfully connected to cloud storage.")
            else:
                # Update UI
                self._update_connection_status()
                
                logger.debug("Failed to connect to cloud storage")
                QMessageBox.warning(self, "Connection Failed", "Failed to connect to cloud storage. Please check your settings and try again.")
    
    def _on_auto_sync_toggled(self, checked: bool):
        """
        Handle auto sync checkbox toggled.
        
        Args:
            checked: Whether the checkbox is checked.
        """
        logger.debug(f"Auto sync toggled: {checked}")
        
        # Enable/disable sync interval spinner
        self.sync_interval_spin.setEnabled(checked)
        
        # Update UI state
        self._update_ui_state()
    
    def _on_sync_now(self):
        """Handle sync now button clicked."""
        logger.debug("Sync now button clicked")
        
        # Check if connected
        if not self.cloud_storage_service.is_connected():
            QMessageBox.warning(self, "Not Connected", "Not connected to cloud storage. Please connect first.")
            return
        
        # Show file dialog to select project directory
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Project Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not project_dir:
            return
        
        # Update progress
        self.progress_bar.setValue(0)
        self.progress_label.setText("Synchronizing...")
        
        # Sync project
        result = self.cloud_storage_service.sync_project(project_dir)
        
        # Update progress
        self.progress_bar.setValue(100)
        
        if result["success"]:
            # Update UI
            self._update_connection_status()
            
            # Show success message
            uploaded_count = len(result.get("uploaded", []))
            downloaded_count = len(result.get("downloaded", []))
            
            QMessageBox.information(
                self,
                "Synchronization Complete",
                f"Synchronization completed successfully.\n\n"
                f"Uploaded: {uploaded_count} files\n"
                f"Downloaded: {downloaded_count} files"
            )
            
            self.progress_label.setText("Synchronization complete")
            logger.debug("Project synchronized successfully")
        else:
            # Show error message
            QMessageBox.warning(
                self,
                "Synchronization Failed",
                f"Failed to synchronize project: {result.get('error', 'Unknown error')}"
            )
            
            self.progress_label.setText("Synchronization failed")
            logger.debug(f"Project synchronization failed: {result.get('error')}")
    
    def _on_refresh_files(self):
        """Handle refresh files button clicked."""
        logger.debug("Refresh files button clicked")
        
        # Check if connected
        if not self.cloud_storage_service.is_connected():
            QMessageBox.warning(self, "Not Connected", "Not connected to cloud storage. Please connect first.")
            return
        
        # Clear table
        self.files_table.setRowCount(0)
        
        # Update progress
        self.progress_bar.setValue(0)
        self.progress_label.setText("Refreshing files...")
        
        # List files
        files = self.cloud_storage_service.list_files()
        
        # Update table
        for i, file_info in enumerate(files):
            self.files_table.insertRow(i)
            
            # Name
            name_item = QTableWidgetItem(file_info.get("name", ""))
            self.files_table.setItem(i, 0, name_item)
            
            # Type
            type_item = QTableWidgetItem(file_info.get("type", ""))
            self.files_table.setItem(i, 1, type_item)
            
            # Size
            size = file_info.get("size", 0)
            size_str = self._format_file_size(size)
            size_item = QTableWidgetItem(size_str)
            self.files_table.setItem(i, 2, size_item)
            
            # Modified
            modified = file_info.get("modified", "")
            modified_item = QTableWidgetItem(modified)
            self.files_table.setItem(i, 3, modified_item)
        
        # Update progress
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"Found {len(files)} files")
        
        logger.debug(f"Files refreshed: {len(files)} files found")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes.
            
        Returns:
            Formatted size string.
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0 or unit == 'GB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} {unit}"
    
    def _on_download_file(self):
        """Handle download file button clicked."""
        logger.debug("Download file button clicked")
        
        # Check if connected
        if not self.cloud_storage_service.is_connected():
            QMessageBox.warning(self, "Not Connected", "Not connected to cloud storage. Please connect first.")
            return
        
        # Get selected file
        selected_rows = self.files_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No File Selected", "Please select a file to download.")
            return
        
        # Get file name
        row = selected_rows[0].row()
        file_name = self.files_table.item(row, 0).text()
        file_type = self.files_table.item(row, 1).text()
        
        # Check if it's a folder
        if file_type == "folder":
            QMessageBox.warning(self, "Cannot Download Folder", "Cannot download folders. Please select a file.")
            return
        
        # Show file dialog to select download location
        download_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            file_name,
            "All Files (*)"
        )
        
        if not download_path:
            return
        
        # Update progress
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Downloading {file_name}...")
        
        # Download file
        if self.cloud_storage_service.download_file(file_name, download_path):
            # Update progress
            self.progress_bar.setValue(100)
            self.progress_label.setText(f"Downloaded {file_name}")
            
            QMessageBox.information(self, "Download Complete", f"File downloaded successfully to {download_path}")
            logger.debug(f"File downloaded: {file_name} to {download_path}")
        else:
            # Update progress
            self.progress_bar.setValue(0)
            self.progress_label.setText(f"Failed to download {file_name}")
            
            QMessageBox.warning(self, "Download Failed", f"Failed to download {file_name}")
            logger.debug(f"File download failed: {file_name}")
    
    def _on_upload_file(self):
        """Handle upload file button clicked."""
        logger.debug("Upload file button clicked")
        
        # Check if connected
        if not self.cloud_storage_service.is_connected():
            QMessageBox.warning(self, "Not Connected", "Not connected to cloud storage. Please connect first.")
            return
        
        # Show file dialog to select file to upload
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Upload",
            "",
            "All Files (*)"
        )
        
        if not file_path:
            return
        
        # Get file name
        file_name = os.path.basename(file_path)
        
        # Update progress
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Uploading {file_name}...")
        
        # Upload file
        if self.cloud_storage_service.upload_file(file_path, file_name):
            # Update progress
            self.progress_bar.setValue(100)
            self.progress_label.setText(f"Uploaded {file_name}")
            
            # Refresh files
            self._on_refresh_files()
            
            QMessageBox.information(self, "Upload Complete", f"File uploaded successfully: {file_name}")
            logger.debug(f"File uploaded: {file_name}")
        else:
            # Update progress
            self.progress_bar.setValue(0)
            self.progress_label.setText(f"Failed to upload {file_name}")
            
            QMessageBox.warning(self, "Upload Failed", f"Failed to upload {file_name}")
            logger.debug(f"File upload failed: {file_name}")
    
    def _on_delete_file(self):
        """Handle delete file button clicked."""
        logger.debug("Delete file button clicked")
        
        # Check if connected
        if not self.cloud_storage_service.is_connected():
            QMessageBox.warning(self, "Not Connected", "Not connected to cloud storage. Please connect first.")
            return
        
        # Get selected file
        selected_rows = self.files_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No File Selected", "Please select a file to delete.")
            return
        
        # Get file name
        row = selected_rows[0].row()
        file_name = self.files_table.item(row, 0).text()
        
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {file_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
        
        # Note: In a real implementation, we would need to add a delete_file method to the service
        # For now, we'll just show a message
        QMessageBox.information(self, "Not Implemented", "File deletion is not implemented yet.")
        logger.debug(f"File deletion not implemented: {file_name}")
    
    def _on_accept(self):
        """Handle accept button clicked."""
        logger.debug("Accept button clicked")
        
        # Save settings
        if self._save_settings():
            # Accept dialog
            self.accept()
    
    def _on_apply(self):
        """Handle apply button clicked."""
        logger.debug("Apply button clicked")
        
        # Save settings
        self._save_settings()
    
    def set_cloud_storage_service(self, cloud_storage_service: CloudStorageService):
        """
        Set the cloud storage service for the dialog.
        
        Args:
            cloud_storage_service: The cloud storage service instance.
        """
        logger.debug("Setting cloud storage service")
        
        self.cloud_storage_service = cloud_storage_service
        
        # Load settings
        self._load_settings()
