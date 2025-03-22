#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - AI Settings Dialog

This module implements the AI settings dialog for RebelSCRIBE.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFormLayout, QGroupBox, QCheckBox,
    QSpinBox, QDialogButtonBox, QLineEdit
)
from PyQt6.QtCore import Qt, QSettings

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class AISettingsDialog(QDialog):
    """
    AI settings dialog for RebelSCRIBE.
    
    This dialog allows the user to customize the AI settings for RebelSCRIBE.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the AI settings dialog.
        
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
        # Set up dialog properties
        self.setWindowTitle("AI Settings")
        self.setMinimumWidth(400)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create model selection group
        self.create_model_selection_group()
        
        # Create generation settings group
        self.create_generation_settings_group()
        
        # Create API settings group
        self.create_api_settings_group()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Add button box to layout
        self.layout.addWidget(self.button_box)
        
        # Load settings
        self.load_settings()
        
        logger.debug("AI settings dialog initialized")
    
    def create_model_selection_group(self):
        """Create model selection group."""
        group_box = QGroupBox("Model")
        layout = QFormLayout(group_box)
        
        # Model combo box
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "llama-3-70b",
            "llama-3-8b",
            "mistral-large",
            "mistral-medium",
            "mistral-small"
        ])
        layout.addRow("Model:", self.model_combo)
        
        # Add group box to layout
        self.layout.addWidget(group_box)
    
    def create_generation_settings_group(self):
        """Create generation settings group."""
        group_box = QGroupBox("Generation Settings")
        layout = QFormLayout(group_box)
        
        # Temperature spin box
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 100)
        self.temperature_spin.setSingleStep(5)
        layout.addRow("Temperature (0-100):", self.temperature_spin)
        
        # Max tokens spin box
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 10000)
        self.max_tokens_spin.setSingleStep(100)
        layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Top P spin box
        self.top_p_spin = QSpinBox()
        self.top_p_spin.setRange(0, 100)
        self.top_p_spin.setSingleStep(5)
        layout.addRow("Top P (0-100):", self.top_p_spin)
        
        # Add group box to layout
        self.layout.addWidget(group_box)
    
    def create_api_settings_group(self):
        """Create API settings group."""
        group_box = QGroupBox("API Settings")
        layout = QFormLayout(group_box)
        
        # API key line edit
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("API Key:", self.api_key_edit)
        
        # API endpoint line edit
        self.api_endpoint_edit = QLineEdit()
        layout.addRow("API Endpoint:", self.api_endpoint_edit)
        
        # Use local model checkbox
        self.use_local_model_check = QCheckBox()
        layout.addRow("Use Local Model:", self.use_local_model_check)
        
        # Local model path line edit
        self.local_model_path_edit = QLineEdit()
        layout.addRow("Local Model Path:", self.local_model_path_edit)
        
        # Add group box to layout
        self.layout.addWidget(group_box)
    
    def load_settings(self):
        """Load settings."""
        settings = QSettings()
        
        # Load model
        model = settings.value("ai/model", "gpt-4")
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        # Load generation settings
        temperature = settings.value("ai/temperature", 70, type=int)
        self.temperature_spin.setValue(temperature)
        
        max_tokens = settings.value("ai/maxTokens", 2000, type=int)
        self.max_tokens_spin.setValue(max_tokens)
        
        top_p = settings.value("ai/topP", 95, type=int)
        self.top_p_spin.setValue(top_p)
        
        # Load API settings
        api_key = settings.value("ai/apiKey", "")
        self.api_key_edit.setText(api_key)
        
        api_endpoint = settings.value("ai/apiEndpoint", "https://api.openai.com/v1")
        self.api_endpoint_edit.setText(api_endpoint)
        
        use_local_model = settings.value("ai/useLocalModel", False, type=bool)
        self.use_local_model_check.setChecked(use_local_model)
        
        local_model_path = settings.value("ai/localModelPath", "")
        self.local_model_path_edit.setText(local_model_path)
    
    def save_settings(self):
        """Save settings."""
        settings = QSettings()
        
        # Save model
        settings.setValue("ai/model", self.model_combo.currentText())
        
        # Save generation settings
        settings.setValue("ai/temperature", self.temperature_spin.value())
        settings.setValue("ai/maxTokens", self.max_tokens_spin.value())
        settings.setValue("ai/topP", self.top_p_spin.value())
        
        # Save API settings
        settings.setValue("ai/apiKey", self.api_key_edit.text())
        settings.setValue("ai/apiEndpoint", self.api_endpoint_edit.text())
        settings.setValue("ai/useLocalModel", self.use_local_model_check.isChecked())
        settings.setValue("ai/localModelPath", self.local_model_path_edit.text())
    
    def accept(self):
        """Handle dialog acceptance."""
        logger.debug("AI settings dialog accepted")
        
        # Save settings
        self.save_settings()
        
        # Accept dialog
        super().accept()
