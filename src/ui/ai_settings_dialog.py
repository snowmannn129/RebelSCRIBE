#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - AI Settings Dialog

This module implements a dialog for configuring AI-related settings.
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
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize
from PyQt6.QtGui import QFont, QIcon

from src.utils.logging_utils import get_logger
from src.utils.config_manager import ConfigManager
from src.ai.ai_service import AIService, AIProvider, AIModelType

logger = get_logger(__name__)
config = ConfigManager()


class AISettingsDialog(QDialog):
    """
    AI settings dialog for RebelSCRIBE.
    
    This dialog allows users to configure AI-related settings including:
    - AI provider selection (OpenAI, Anthropic, Google, Local, Custom)
    - API key management
    - Model selection for different types (completion, chat, embedding, image)
    - Rate limiting configuration
    - Usage statistics viewing
    """
    
    # Signal emitted when settings are changed
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, ai_service=None):
        """
        Initialize the AI settings dialog.
        
        Args:
            parent: The parent widget.
            ai_service: The AI service instance.
        """
        super().__init__(parent)
        
        self.ai_service = ai_service or AIService()
        
        # Initialize UI components
        self._init_ui()
        
        # Load current settings
        self._load_settings()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("AI settings dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        logger.debug("Initializing AI settings dialog UI components")
        
        # Set window properties
        self.setWindowTitle("AI Settings")
        self.setMinimumSize(600, 450)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_provider_tab()
        self._create_models_tab()
        self._create_rate_limits_tab()
        self._create_usage_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel | 
            QDialogButtonBox.StandardButton.Apply
        )
        self.main_layout.addWidget(self.button_box)
        
        logger.debug("AI settings dialog UI components initialized")
    
    def _create_provider_tab(self):
        """Create the AI provider settings tab."""
        logger.debug("Creating AI provider settings tab")
        
        # Create tab widget
        self.provider_tab = QWidget()
        self.tab_widget.addTab(self.provider_tab, "Provider")
        
        # Create layout
        layout = QVBoxLayout(self.provider_tab)
        
        # Provider selection group
        provider_group = QGroupBox("AI Provider")
        provider_layout = QFormLayout(provider_group)
        
        self.provider_combo = QComboBox()
        for provider in AIProvider:
            self.provider_combo.addItem(provider.value.capitalize())
        provider_layout.addRow("Provider:", self.provider_combo)
        
        layout.addWidget(provider_group)
        
        # API key management group
        api_key_group = QGroupBox("API Keys")
        api_key_layout = QVBoxLayout(api_key_group)
        
        # Create a form layout for each provider
        self.api_key_forms = {}
        
        for provider in AIProvider:
            form_layout = QFormLayout()
            
            # Create API key input for this provider
            api_key_edit = QLineEdit()
            api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            api_key_edit.setPlaceholderText(f"Enter {provider.value.capitalize()} API key")
            
            # Create a show/hide button for the API key
            show_hide_button = QPushButton("Show")
            show_hide_button.setCheckable(True)
            show_hide_button.setFixedWidth(60)
            show_hide_button.toggled.connect(lambda checked, edit=api_key_edit: 
                                            edit.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
            
            # Create a horizontal layout for the API key input and show/hide button
            api_key_layout_h = QHBoxLayout()
            api_key_layout_h.addWidget(api_key_edit)
            api_key_layout_h.addWidget(show_hide_button)
            
            form_layout.addRow(f"{provider.value.capitalize()} API Key:", api_key_layout_h)
            
            # Store the form layout and API key edit
            self.api_key_forms[provider.value] = {
                "layout": form_layout,
                "api_key_edit": api_key_edit,
                "show_hide_button": show_hide_button
            }
            
            # Add the form layout to the API key group
            api_key_layout.addLayout(form_layout)
        
        layout.addWidget(api_key_group)
        
        # Custom provider settings group (only visible when Custom is selected)
        self.custom_provider_group = QGroupBox("Custom Provider Settings")
        custom_provider_layout = QFormLayout(self.custom_provider_group)
        
        self.custom_provider_name_edit = QLineEdit()
        custom_provider_layout.addRow("Provider Name:", self.custom_provider_name_edit)
        
        self.custom_provider_endpoint_edit = QLineEdit()
        custom_provider_layout.addRow("API Endpoint:", self.custom_provider_endpoint_edit)
        
        self.custom_provider_group.setVisible(False)
        layout.addWidget(self.custom_provider_group)
        
        # Local model settings group (only visible when Local is selected)
        self.local_model_group = QGroupBox("Local Model Settings")
        local_model_layout = QFormLayout(self.local_model_group)
        
        self.local_model_path_edit = QLineEdit()
        local_model_path_layout = QHBoxLayout()
        local_model_path_layout.addWidget(self.local_model_path_edit)
        
        self.local_model_path_button = QPushButton("Browse...")
        local_model_path_layout.addWidget(self.local_model_path_button)
        
        local_model_layout.addRow("Model Path:", local_model_path_layout)
        
        self.local_model_port_spin = QSpinBox()
        self.local_model_port_spin.setRange(1024, 65535)
        self.local_model_port_spin.setValue(8000)
        local_model_layout.addRow("Server Port:", self.local_model_port_spin)
        
        self.local_model_group.setVisible(False)
        layout.addWidget(self.local_model_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("AI provider settings tab created")
    
    def _create_models_tab(self):
        """Create the AI models settings tab."""
        logger.debug("Creating AI models settings tab")
        
        # Create tab widget
        self.models_tab = QWidget()
        self.tab_widget.addTab(self.models_tab, "Models")
        
        # Create layout
        layout = QVBoxLayout(self.models_tab)
        
        # Create a group for each model type
        self.model_groups = {}
        self.model_combos = {}
        
        for model_type in AIModelType:
            group = QGroupBox(f"{model_type.value.capitalize()} Model")
            group_layout = QVBoxLayout(group)
            
            # Create a combo box for each provider
            provider_form = QFormLayout()
            
            for provider in AIProvider:
                combo = QComboBox()
                
                # Add placeholder items (these would be populated based on the provider)
                if provider == AIProvider.OPENAI:
                    if model_type == AIModelType.COMPLETION or model_type == AIModelType.CHAT:
                        combo.addItems(["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"])
                    elif model_type == AIModelType.EMBEDDING:
                        combo.addItems(["text-embedding-3-small", "text-embedding-3-large"])
                    elif model_type == AIModelType.IMAGE:
                        combo.addItems(["dall-e-3", "dall-e-2"])
                elif provider == AIProvider.ANTHROPIC:
                    if model_type == AIModelType.COMPLETION or model_type == AIModelType.CHAT:
                        combo.addItems(["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"])
                    else:
                        combo.addItem("Not Available")
                        combo.setEnabled(False)
                elif provider == AIProvider.GOOGLE:
                    if model_type == AIModelType.COMPLETION or model_type == AIModelType.CHAT:
                        combo.addItems(["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"])
                    elif model_type == AIModelType.EMBEDDING:
                        combo.addItems(["embedding-001"])
                    elif model_type == AIModelType.IMAGE:
                        combo.addItems(["imagegeneration"])
                elif provider == AIProvider.LOCAL:
                    if model_type == AIModelType.COMPLETION or model_type == AIModelType.CHAT:
                        combo.addItems(["llama3-70b", "llama3-8b", "mistral-7b"])
                    elif model_type == AIModelType.EMBEDDING:
                        combo.addItems(["all-MiniLM-L6-v2"])
                    elif model_type == AIModelType.IMAGE:
                        combo.addItems(["stable-diffusion-3"])
                elif provider == AIProvider.CUSTOM:
                    combo.addItem("Custom Model")
                    combo.setEditable(True)
                
                provider_form.addRow(f"{provider.value.capitalize()}:", combo)
                
                # Store the combo box
                key = f"{provider.value}_{model_type.value}"
                self.model_combos[key] = combo
            
            group_layout.addLayout(provider_form)
            layout.addWidget(group)
            
            # Store the group
            self.model_groups[model_type.value] = group
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("AI models settings tab created")
    
    def _create_rate_limits_tab(self):
        """Create the rate limits settings tab."""
        logger.debug("Creating rate limits settings tab")
        
        # Create tab widget
        self.rate_limits_tab = QWidget()
        self.tab_widget.addTab(self.rate_limits_tab, "Rate Limits")
        
        # Create layout
        layout = QVBoxLayout(self.rate_limits_tab)
        
        # Rate limits group
        rate_limits_group = QGroupBox("Rate Limits (requests per second)")
        rate_limits_layout = QFormLayout(rate_limits_group)
        
        # Create a spin box for each provider
        self.rate_limit_spins = {}
        
        for provider in AIProvider:
            spin = QDoubleSpinBox()
            spin.setRange(0.1, 100.0)
            spin.setValue(1.0)
            spin.setSingleStep(0.1)
            spin.setDecimals(1)
            
            rate_limits_layout.addRow(f"{provider.value.capitalize()}:", spin)
            
            # Store the spin box
            self.rate_limit_spins[provider.value] = spin
        
        layout.addWidget(rate_limits_group)
        
        # Timeout settings group
        timeout_group = QGroupBox("Timeout Settings")
        timeout_layout = QFormLayout(timeout_group)
        
        self.request_timeout_spin = QSpinBox()
        self.request_timeout_spin.setRange(5, 300)
        self.request_timeout_spin.setValue(60)
        self.request_timeout_spin.setSuffix(" seconds")
        timeout_layout.addRow("Request Timeout:", self.request_timeout_spin)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(3)
        timeout_layout.addRow("Max Retries:", self.max_retries_spin)
        
        layout.addWidget(timeout_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Rate limits settings tab created")
    
    def _create_usage_tab(self):
        """Create the usage statistics tab."""
        logger.debug("Creating usage statistics tab")
        
        # Create tab widget
        self.usage_tab = QWidget()
        self.tab_widget.addTab(self.usage_tab, "Usage")
        
        # Create layout
        layout = QVBoxLayout(self.usage_tab)
        
        # Usage statistics group
        usage_group = QGroupBox("Usage Statistics")
        usage_layout = QVBoxLayout(usage_group)
        
        # Create a table for usage statistics
        self.usage_table = QTableWidget(4, 2)
        self.usage_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.usage_table.verticalHeader().setVisible(False)
        self.usage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Set up the table rows
        self.usage_table.setItem(0, 0, QTableWidgetItem("Prompt Tokens"))
        self.usage_table.setItem(0, 1, QTableWidgetItem("0"))
        
        self.usage_table.setItem(1, 0, QTableWidgetItem("Completion Tokens"))
        self.usage_table.setItem(1, 1, QTableWidgetItem("0"))
        
        self.usage_table.setItem(2, 0, QTableWidgetItem("Total Tokens"))
        self.usage_table.setItem(2, 1, QTableWidgetItem("0"))
        
        self.usage_table.setItem(3, 0, QTableWidgetItem("Requests"))
        self.usage_table.setItem(3, 1, QTableWidgetItem("0"))
        
        usage_layout.addWidget(self.usage_table)
        
        # Add a refresh button and reset button
        buttons_layout = QHBoxLayout()
        
        self.refresh_usage_button = QPushButton("Refresh")
        buttons_layout.addWidget(self.refresh_usage_button)
        
        self.reset_usage_button = QPushButton("Reset Statistics")
        buttons_layout.addWidget(self.reset_usage_button)
        
        usage_layout.addLayout(buttons_layout)
        
        layout.addWidget(usage_group)
        
        # Cost estimation group
        cost_group = QGroupBox("Cost Estimation")
        cost_layout = QFormLayout(cost_group)
        
        self.estimated_cost_label = QLabel("$0.00")
        cost_layout.addRow("Estimated Cost:", self.estimated_cost_label)
        
        layout.addWidget(cost_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        logger.debug("Usage statistics tab created")
    
    def _connect_signals(self):
        """Connect signals."""
        logger.debug("Connecting signals")
        
        # Connect button box signals
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        
        # Connect provider tab signals
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.local_model_path_button.clicked.connect(self._on_browse_local_model)
        
        # Connect usage tab signals
        self.refresh_usage_button.clicked.connect(self._on_refresh_usage)
        self.reset_usage_button.clicked.connect(self._on_reset_usage)
        
        logger.debug("Signals connected")
    
    def _load_settings(self):
        """Load current AI settings."""
        logger.debug("Loading current AI settings")
        
        try:
            # Get AI settings from config
            ai_config = config.get_config().get("ai", {})
            
            # Load provider
            provider = ai_config.get("provider", "openai")
            provider_index = self.provider_combo.findText(provider.capitalize())
            if provider_index >= 0:
                self.provider_combo.setCurrentIndex(provider_index)
            
            # Load API keys
            api_keys = ai_config.get("api_keys", {})
            for provider, key in api_keys.items():
                if provider in self.api_key_forms:
                    self.api_key_forms[provider]["api_key_edit"].setText(key)
            
            # Load custom provider settings
            custom_provider = ai_config.get("custom_provider", {})
            self.custom_provider_name_edit.setText(custom_provider.get("name", ""))
            self.custom_provider_endpoint_edit.setText(custom_provider.get("endpoint", ""))
            
            # Load local model settings
            local_model = ai_config.get("local_model", {})
            self.local_model_path_edit.setText(local_model.get("path", ""))
            self.local_model_port_spin.setValue(local_model.get("port", 8000))
            
            # Load models
            models = ai_config.get("models", {})
            for provider, provider_models in models.items():
                for model_type, model in provider_models.items():
                    key = f"{provider}_{model_type}"
                    if key in self.model_combos:
                        combo = self.model_combos[key]
                        model_index = combo.findText(model)
                        if model_index >= 0:
                            combo.setCurrentIndex(model_index)
                        elif combo.isEditable():
                            combo.setCurrentText(model)
            
            # Load rate limits
            rate_limits = ai_config.get("rate_limits", {})
            for provider, rate in rate_limits.items():
                if provider in self.rate_limit_spins:
                    self.rate_limit_spins[provider].setValue(rate)
            
            # Load timeout settings
            timeout_settings = ai_config.get("timeout_settings", {})
            self.request_timeout_spin.setValue(timeout_settings.get("request_timeout", 60))
            self.max_retries_spin.setValue(timeout_settings.get("max_retries", 3))
            
            # Load usage statistics
            self._update_usage_statistics()
            
            # Update UI based on selected provider
            self._on_provider_changed(self.provider_combo.currentText())
            
            logger.debug("AI settings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading AI settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load AI settings: {e}")
    
    def _update_usage_statistics(self):
        """Update the usage statistics display."""
        logger.debug("Updating usage statistics")
        
        try:
            # Get usage statistics from AI service
            usage = self.ai_service.get_usage_statistics()
            
            # Update the table
            self.usage_table.item(0, 1).setText(str(usage.get("tokens", {}).get("prompt", 0)))
            self.usage_table.item(1, 1).setText(str(usage.get("tokens", {}).get("completion", 0)))
            self.usage_table.item(2, 1).setText(str(usage.get("tokens", {}).get("total", 0)))
            self.usage_table.item(3, 1).setText(str(usage.get("requests", 0)))
            
            # Update the cost estimation
            self.estimated_cost_label.setText(f"${usage.get('cost', 0.0):.2f}")
            
            logger.debug("Usage statistics updated successfully")
        except Exception as e:
            logger.error(f"Error updating usage statistics: {e}")
    
    def _get_current_settings(self) -> Dict[str, Any]:
        """
        Get current settings from the dialog.
        
        Returns:
            A dictionary containing the current settings.
        """
        logger.debug("Getting current settings from dialog")
        
        settings = {}
        
        # Get provider
        provider = self.provider_combo.currentText().lower()
        settings["provider"] = provider
        
        # Get API keys
        api_keys = {}
        for provider_value, form_data in self.api_key_forms.items():
            api_key = form_data["api_key_edit"].text()
            if api_key:
                api_keys[provider_value] = api_key
        settings["api_keys"] = api_keys
        
        # Get custom provider settings
        custom_provider = {}
        custom_provider["name"] = self.custom_provider_name_edit.text()
        custom_provider["endpoint"] = self.custom_provider_endpoint_edit.text()
        settings["custom_provider"] = custom_provider
        
        # Get local model settings
        local_model = {}
        local_model["path"] = self.local_model_path_edit.text()
        local_model["port"] = self.local_model_port_spin.value()
        settings["local_model"] = local_model
        
        # Get models
        models = {}
        for provider in AIProvider:
            provider_models = {}
            for model_type in AIModelType:
                key = f"{provider.value}_{model_type.value}"
                if key in self.model_combos:
                    combo = self.model_combos[key]
                    if combo.isEnabled():
                        model = combo.currentText()
                        if model and model != "Not Available":
                            provider_models[model_type.value] = model
            if provider_models:
                models[provider.value] = provider_models
        settings["models"] = models
        
        # Get rate limits
        rate_limits = {}
        for provider_value, spin in self.rate_limit_spins.items():
            rate_limits[provider_value] = spin.value()
        settings["rate_limits"] = rate_limits
        
        # Get timeout settings
        timeout_settings = {}
        timeout_settings["request_timeout"] = self.request_timeout_spin.value()
        timeout_settings["max_retries"] = self.max_retries_spin.value()
        settings["timeout_settings"] = timeout_settings
        
        logger.debug("Current settings retrieved from dialog")
        
        return settings
    
    def _save_settings(self):
        """Save current AI settings."""
        logger.debug("Saving current AI settings")
        
        try:
            # Get current settings
            settings = self._get_current_settings()
            
            # Update config
            config_data = config.get_config()
            config_data["ai"] = settings
            config.save_config(config_data)
            
            # Update AI service
            if self.ai_service:
                # Set provider
                self.ai_service.set_provider(settings["provider"])
                
                # Set API keys
                for provider, api_key in settings["api_keys"].items():
                    self.ai_service.set_api_key(provider, api_key)
                
                # Set models
                for provider, provider_models in settings["models"].items():
                    for model_type, model in provider_models.items():
                        self.ai_service.set_model(AIModelType(model_type), model)
            
            # Emit settings changed signal
            self.settings_changed.emit(settings)
            
            logger.debug("AI settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving AI settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save AI settings: {e}")
            return False
    
    def _on_provider_changed(self, provider_text: str):
        """
        Handle provider combo box changed.
        
        Args:
            provider_text: The new provider text.
        """
        provider = provider_text.lower()
        logger.debug(f"Provider changed to: {provider}")
        
        # Show/hide custom provider settings
        self.custom_provider_group.setVisible(provider == "custom")
        
        # Show/hide local model settings
        self.local_model_group.setVisible(provider == "local")
    
    def _on_browse_local_model(self):
        """Handle browse local model button clicked."""
        logger.debug("Browse local model button clicked")
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Local Model File",
            self.local_model_path_edit.text() or "",
            "Model Files (*.bin *.gguf *.ggml *.pt *.pth *.onnx);;All Files (*)"
        )
        
        if file_path:
            # Update local model path edit
            self.local_model_path_edit.setText(file_path)
            
            logger.debug(f"Local model path selected: {file_path}")
    
    def _on_refresh_usage(self):
        """Handle refresh usage button clicked."""
        logger.debug("Refresh usage button clicked")
        
        # Update usage statistics
        self._update_usage_statistics()
    
    def _on_reset_usage(self):
        """Handle reset usage button clicked."""
        logger.debug("Reset usage button clicked")
        
        # Confirm with user
        result = QMessageBox.question(
            self,
            "Reset Usage Statistics",
            "Are you sure you want to reset all usage statistics? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Reset usage statistics
            if self.ai_service:
                self.ai_service.reset_usage_statistics()
            
            # Update usage statistics display
            self._update_usage_statistics()
            
            logger.debug("Usage statistics reset")
    
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
    
    def set_ai_service(self, ai_service: AIService):
        """
        Set the AI service for the dialog.
        
        Args:
            ai_service: The AI service instance.
        """
        logger.debug("Setting AI service")
        
        self.ai_service = ai_service
        
        # Load settings
        self._load_settings()
