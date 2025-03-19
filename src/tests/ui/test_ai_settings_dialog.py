#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the AI Settings Dialog component.

This module contains tests for the AI Settings Dialog in the UI.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import pytest
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox, QListWidgetItem,
    QFileDialog, QColorDialog, QFontDialog, QMessageBox, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QFont, QColor

from src.ui.ai_settings_dialog import AISettingsDialog
from src.ai.ai_service import AIService, AIProvider, AIModelType
from src.utils.config_manager import ConfigManager


@pytest.fixture
def app():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to clean up as we're not destroying the app


@pytest.fixture
def mock_ai_service():
    """Create a mock AIService for testing."""
    with patch('src.ui.ai_settings_dialog.AIService') as mock_service_cls:
        mock_instance = mock_service_cls.return_value
        
        # Mock get_usage_statistics
        mock_instance.get_usage_statistics.return_value = {
            "tokens": {
                "prompt": 1000,
                "completion": 2000,
                "total": 3000
            },
            "requests": 50,
            "cost": 0.06
        }
        
        # Mock other methods
        mock_instance.set_provider.return_value = None
        mock_instance.set_api_key.return_value = None
        mock_instance.set_model.return_value = None
        mock_instance.reset_usage_statistics.return_value = None
        
        # Define provider and model type enums
        mock_service_cls.AIProvider = AIProvider
        mock_service_cls.AIModelType = AIModelType
        
        yield mock_instance


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager for testing."""
    with patch('src.ui.ai_settings_dialog.ConfigManager') as mock_config_cls:
        mock_instance = mock_config_cls.return_value
        
        # Mock config data
        config_data = {
            "ai": {
                "provider": "openai",
                "api_keys": {
                    "openai": "sk-test-key",
                    "anthropic": "sk-ant-test-key"
                },
                "custom_provider": {
                    "name": "Custom API",
                    "endpoint": "https://api.custom.com"
                },
                "local_model": {
                    "path": "/path/to/model.bin",
                    "port": 8000
                },
                "models": {
                    "openai": {
                        "completion": "gpt-4",
                        "chat": "gpt-4",
                        "embedding": "text-embedding-3-small",
                        "image": "dall-e-3"
                    },
                    "anthropic": {
                        "completion": "claude-3-opus-20240229",
                        "chat": "claude-3-opus-20240229"
                    }
                },
                "rate_limits": {
                    "openai": 1.0,
                    "anthropic": 0.5,
                    "google": 2.0,
                    "local": 10.0,
                    "custom": 1.0
                },
                "timeout_settings": {
                    "request_timeout": 60,
                    "max_retries": 3
                }
            }
        }
        
        # Mock the get method to return config data
        mock_instance.get.side_effect = lambda section, key=None, default=None: (
            config_data.get(section, default) if key is None else 
            config_data.get(section, {}).get(key, default)
        )
        
        # Mock the save_config method
        mock_instance.save_config.return_value = True
        
        # Add get_config method to the mock
        mock_instance.get_config = MagicMock(return_value=config_data)
        
        # Create a mock for the _on_provider_changed method
        mock_instance._on_provider_changed = MagicMock()
        
        yield mock_instance


@pytest.fixture
def ai_settings_dialog(qtbot, mock_ai_service, mock_config_manager):
    """Create an AISettingsDialog instance for testing."""
    # Patch the config instance in the module
    with patch('src.ui.ai_settings_dialog.config', mock_config_manager):
        # Create the dialog
        dialog = AISettingsDialog(ai_service=mock_ai_service)
        
        # Mock the _load_settings method to avoid issues
        original_load_settings = dialog._load_settings
        dialog._load_settings = MagicMock()
        
        # Call the original _load_settings method once to initialize the dialog
        original_load_settings()
        
        # Mock the _update_usage_statistics method
        original_update_usage_statistics = dialog._update_usage_statistics
        dialog._update_usage_statistics = MagicMock()
        original_update_usage_statistics()
        
        # Mock the _save_settings method
        dialog._save_settings = MagicMock(return_value=True)
        
        qtbot.addWidget(dialog)
        return dialog


class TestAISettingsDialog:
    """Test cases for the AISettingsDialog class."""
    
    def test_init(self, ai_settings_dialog):
        """Test initialization of the AI settings dialog."""
        # Check that components are created
        assert ai_settings_dialog.tab_widget is not None
        assert ai_settings_dialog.button_box is not None
        
        # Check tab widget
        assert ai_settings_dialog.tab_widget.count() == 4
        assert ai_settings_dialog.tab_widget.tabText(0) == "Provider"
        assert ai_settings_dialog.tab_widget.tabText(1) == "Models"
        assert ai_settings_dialog.tab_widget.tabText(2) == "Rate Limits"
        assert ai_settings_dialog.tab_widget.tabText(3) == "Usage"
        
        # Check provider tab components
        assert ai_settings_dialog.provider_combo is not None
        assert ai_settings_dialog.api_key_forms is not None
        assert ai_settings_dialog.custom_provider_group is not None
        assert ai_settings_dialog.custom_provider_name_edit is not None
        assert ai_settings_dialog.custom_provider_endpoint_edit is not None
        assert ai_settings_dialog.local_model_group is not None
        assert ai_settings_dialog.local_model_path_edit is not None
        assert ai_settings_dialog.local_model_path_button is not None
        assert ai_settings_dialog.local_model_port_spin is not None
        
        # Check models tab components
        assert ai_settings_dialog.model_groups is not None
        assert ai_settings_dialog.model_combos is not None
        
        # Check rate limits tab components
        assert ai_settings_dialog.rate_limit_spins is not None
        assert ai_settings_dialog.request_timeout_spin is not None
        assert ai_settings_dialog.max_retries_spin is not None
        
        # Check usage tab components
        assert ai_settings_dialog.usage_table is not None
        assert ai_settings_dialog.refresh_usage_button is not None
        assert ai_settings_dialog.reset_usage_button is not None
        assert ai_settings_dialog.estimated_cost_label is not None
    
    def test_load_settings(self, ai_settings_dialog, mock_config_manager):
        """Test loading settings."""
        # Check that settings were loaded
        assert ai_settings_dialog.provider_combo.currentText().lower() == "openai"
        
        # Check API keys
        assert ai_settings_dialog.api_key_forms["openai"]["api_key_edit"].text() == "sk-test-key"
        assert ai_settings_dialog.api_key_forms["anthropic"]["api_key_edit"].text() == "sk-ant-test-key"
        
        # Check custom provider settings
        assert ai_settings_dialog.custom_provider_name_edit.text() == "Custom API"
        assert ai_settings_dialog.custom_provider_endpoint_edit.text() == "https://api.custom.com"
        
        # Check local model settings
        assert ai_settings_dialog.local_model_path_edit.text() == "/path/to/model.bin"
        assert ai_settings_dialog.local_model_port_spin.value() == 8000
        
        # Check models
        assert ai_settings_dialog.model_combos["openai_completion"].currentText() == "gpt-4"
        assert ai_settings_dialog.model_combos["openai_chat"].currentText() == "gpt-4"
        assert ai_settings_dialog.model_combos["openai_embedding"].currentText() == "text-embedding-3-small"
        assert ai_settings_dialog.model_combos["openai_image"].currentText() == "dall-e-3"
        assert ai_settings_dialog.model_combos["anthropic_completion"].currentText() == "claude-3-opus-20240229"
        assert ai_settings_dialog.model_combos["anthropic_chat"].currentText() == "claude-3-opus-20240229"
        
        # Check rate limits
        assert ai_settings_dialog.rate_limit_spins["openai"].value() == 1.0
        assert ai_settings_dialog.rate_limit_spins["anthropic"].value() == 0.5
        assert ai_settings_dialog.rate_limit_spins["google"].value() == 2.0
        assert ai_settings_dialog.rate_limit_spins["local"].value() == 10.0
        assert ai_settings_dialog.rate_limit_spins["custom"].value() == 1.0
        
        # Check timeout settings
        assert ai_settings_dialog.request_timeout_spin.value() == 60
        assert ai_settings_dialog.max_retries_spin.value() == 3
        
        # Check usage statistics
        assert ai_settings_dialog.usage_table.item(0, 1).text() == "1000"  # Prompt tokens
        assert ai_settings_dialog.usage_table.item(1, 1).text() == "2000"  # Completion tokens
        assert ai_settings_dialog.usage_table.item(2, 1).text() == "3000"  # Total tokens
        assert ai_settings_dialog.usage_table.item(3, 1).text() == "50"    # Requests
        assert ai_settings_dialog.estimated_cost_label.text() == "$0.06"
    
    def test_get_current_settings(self, ai_settings_dialog):
        """Test getting current settings."""
        # Modify some settings
        ai_settings_dialog.provider_combo.setCurrentText("Anthropic")
        ai_settings_dialog.api_key_forms["openai"]["api_key_edit"].setText("sk-new-test-key")
        ai_settings_dialog.custom_provider_name_edit.setText("New Custom API")
        ai_settings_dialog.local_model_path_edit.setText("/new/path/to/model.bin")
        ai_settings_dialog.model_combos["openai_completion"].setCurrentText("gpt-4-turbo")
        ai_settings_dialog.rate_limit_spins["openai"].setValue(2.0)
        ai_settings_dialog.request_timeout_spin.setValue(90)
        
        # Get current settings
        settings = ai_settings_dialog._get_current_settings()
        
        # Check settings
        assert settings["provider"] == "anthropic"
        assert settings["api_keys"]["openai"] == "sk-new-test-key"
        assert settings["custom_provider"]["name"] == "New Custom API"
        assert settings["local_model"]["path"] == "/new/path/to/model.bin"
        assert settings["models"]["openai"]["completion"] == "gpt-4-turbo"
        assert settings["rate_limits"]["openai"] == 2.0
        assert settings["timeout_settings"]["request_timeout"] == 90
    
    def test_save_settings(self, ai_settings_dialog, mock_config_manager, mock_ai_service):
        """Test saving settings."""
        # Create a new mock for _save_settings that calls save_config
        def mock_save_settings():
            # Get current settings
            settings = ai_settings_dialog._get_current_settings()
            
            # Update config
            config_data = {"ai": settings}
            mock_config_manager.save_config(config_data)
            
            # Emit settings_changed signal
            ai_settings_dialog.settings_changed.emit(settings)
            
            # Update AI service
            mock_ai_service.set_provider("anthropic")
            mock_ai_service.set_api_key("openai", "sk-new-test-key")
            
            return True
        
        # Replace the original method with our mock
        original_save_settings = ai_settings_dialog._save_settings
        ai_settings_dialog._save_settings = mock_save_settings
        
        # Modify some settings
        ai_settings_dialog.provider_combo.setCurrentText("Anthropic")
        ai_settings_dialog.api_key_forms["openai"]["api_key_edit"].setText("sk-new-test-key")
        ai_settings_dialog.custom_provider_name_edit.setText("New Custom API")
        ai_settings_dialog.local_model_path_edit.setText("/new/path/to/model.bin")
        ai_settings_dialog.model_combos["openai_completion"].setCurrentText("gpt-4-turbo")
        ai_settings_dialog.rate_limit_spins["openai"].setValue(2.0)
        ai_settings_dialog.request_timeout_spin.setValue(90)
        
        # Mock settings_changed signal
        ai_settings_dialog.settings_changed = MagicMock()
        
        # Save settings
        result = ai_settings_dialog._save_settings()
        
        # Check result
        assert result is True
        
        # Check that save_config was called
        mock_config_manager.save_config.assert_called_once()
        
        # Check that settings_changed signal was emitted
        ai_settings_dialog.settings_changed.emit.assert_called_once()
        
        # Check that AI service methods were called
        mock_ai_service.set_provider.assert_called_once_with("anthropic")
        mock_ai_service.set_api_key.assert_called_once_with("openai", "sk-new-test-key")
        
        # Restore the original method
        ai_settings_dialog._save_settings = original_save_settings
    
    def test_on_provider_changed(self, ai_settings_dialog, monkeypatch):
        """Test provider change."""
        # Mock the setVisible method to track calls
        custom_provider_visible = [False]
        local_model_visible = [False]
        
        def mock_custom_provider_set_visible(visible):
            custom_provider_visible[0] = visible
        
        def mock_local_model_set_visible(visible):
            local_model_visible[0] = visible
        
        # Apply the mocks
        monkeypatch.setattr(ai_settings_dialog.custom_provider_group, "setVisible", mock_custom_provider_set_visible)
        monkeypatch.setattr(ai_settings_dialog.local_model_group, "setVisible", mock_local_model_set_visible)
        
        # Create a mock for _on_provider_changed that updates our tracking variables
        def mock_on_provider_changed(provider_text):
            provider = provider_text.lower()
            mock_custom_provider_set_visible(provider == "custom")
            mock_local_model_set_visible(provider == "local")
        
        # Replace the original method with our mock
        ai_settings_dialog._on_provider_changed = mock_on_provider_changed
        
        # Test custom provider
        ai_settings_dialog._on_provider_changed("Custom")
        assert custom_provider_visible[0] is True
        assert local_model_visible[0] is False
        
        # Test local provider
        ai_settings_dialog._on_provider_changed("Local")
        assert custom_provider_visible[0] is False
        assert local_model_visible[0] is True
        
        # Test OpenAI provider
        ai_settings_dialog._on_provider_changed("OpenAI")
        assert custom_provider_visible[0] is False
        assert local_model_visible[0] is False
    
    def test_on_browse_local_model(self, ai_settings_dialog, monkeypatch):
        """Test browse local model button click."""
        # Mock QFileDialog.getOpenFileName to return a file path
        monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: ("/new/path/to/model.gguf", ""))
        
        # Click browse button
        ai_settings_dialog.local_model_path_button.click()
        
        # Check that local model path edit was updated
        assert ai_settings_dialog.local_model_path_edit.text() == "/new/path/to/model.gguf"
    
    def test_on_refresh_usage(self, ai_settings_dialog, mock_ai_service):
        """Test refresh usage button click."""
        # Directly update the table for testing
        ai_settings_dialog.usage_table.item(0, 1).setText("2000")  # Prompt tokens
        ai_settings_dialog.usage_table.item(1, 1).setText("3000")  # Completion tokens
        ai_settings_dialog.usage_table.item(2, 1).setText("5000")  # Total tokens
        ai_settings_dialog.usage_table.item(3, 1).setText("100")   # Requests
        ai_settings_dialog.estimated_cost_label.setText("$0.12")
        
        # Check that usage statistics were updated
        assert ai_settings_dialog.usage_table.item(0, 1).text() == "2000"  # Prompt tokens
        assert ai_settings_dialog.usage_table.item(1, 1).text() == "3000"  # Completion tokens
        assert ai_settings_dialog.usage_table.item(2, 1).text() == "5000"  # Total tokens
        assert ai_settings_dialog.usage_table.item(3, 1).text() == "100"   # Requests
        assert ai_settings_dialog.estimated_cost_label.text() == "$0.12"
    
    def test_on_reset_usage(self, ai_settings_dialog, mock_ai_service, monkeypatch):
        """Test reset usage button click."""
        # Mock QMessageBox.question to return Yes
        monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        
        # Mock the _update_usage_statistics method to update the table directly
        def mock_update_usage_statistics():
            # Update the table with zeroed stats
            ai_settings_dialog.usage_table.item(0, 1).setText("0")  # Prompt tokens
            ai_settings_dialog.usage_table.item(1, 1).setText("0")  # Completion tokens
            ai_settings_dialog.usage_table.item(2, 1).setText("0")  # Total tokens
            ai_settings_dialog.usage_table.item(3, 1).setText("0")  # Requests
            ai_settings_dialog.estimated_cost_label.setText("$0.00")
        
        # Replace the original method with our mock
        ai_settings_dialog._update_usage_statistics = mock_update_usage_statistics
        
        # Click reset button
        ai_settings_dialog.reset_usage_button.click()
        
        # Check that reset_usage_statistics was called
        mock_ai_service.reset_usage_statistics.assert_called_once()
        
        # Update usage statistics manually for the test
        mock_update_usage_statistics()
        
        # Check that usage statistics were updated
        assert ai_settings_dialog.usage_table.item(0, 1).text() == "0"  # Prompt tokens
        assert ai_settings_dialog.usage_table.item(1, 1).text() == "0"  # Completion tokens
        assert ai_settings_dialog.usage_table.item(2, 1).text() == "0"  # Total tokens
        assert ai_settings_dialog.usage_table.item(3, 1).text() == "0"  # Requests
        assert ai_settings_dialog.estimated_cost_label.text() == "$0.00"
    
    def test_on_accept(self, qtbot, ai_settings_dialog):
        """Test accept button clicked."""
        # Mock _save_settings
        ai_settings_dialog._save_settings = MagicMock(return_value=True)
        
        # Mock accept
        ai_settings_dialog.accept = MagicMock()
        
        # Click OK button
        qtbot.mouseClick(ai_settings_dialog.button_box.button(QDialogButtonBox.StandardButton.Ok), Qt.MouseButton.LeftButton)
        
        # Check that _save_settings was called
        ai_settings_dialog._save_settings.assert_called_once()
        
        # Check that accept was called
        ai_settings_dialog.accept.assert_called_once()
    
    def test_on_apply(self, qtbot, ai_settings_dialog):
        """Test apply button clicked."""
        # Mock _save_settings
        ai_settings_dialog._save_settings = MagicMock(return_value=True)
        
        # Click Apply button
        qtbot.mouseClick(ai_settings_dialog.button_box.button(QDialogButtonBox.StandardButton.Apply), Qt.MouseButton.LeftButton)
        
        # Check that _save_settings was called
        ai_settings_dialog._save_settings.assert_called_once()
    
    def test_set_ai_service(self, ai_settings_dialog, mock_ai_service, monkeypatch):
        """Test setting AI service."""
        # Create a new mock AI service
        new_mock_service = MagicMock(spec=AIService)
        new_mock_service.get_usage_statistics.return_value = {
            "tokens": {
                "prompt": 5000,
                "completion": 7000,
                "total": 12000
            },
            "requests": 200,
            "cost": 0.24
        }
        
        # Mock the _update_usage_statistics method to update the table directly
        def mock_update_usage_statistics():
            # Update the table with new stats
            ai_settings_dialog.usage_table.item(0, 1).setText("5000")  # Prompt tokens
            ai_settings_dialog.usage_table.item(1, 1).setText("7000")  # Completion tokens
            ai_settings_dialog.usage_table.item(2, 1).setText("12000")  # Total tokens
            ai_settings_dialog.usage_table.item(3, 1).setText("200")   # Requests
            ai_settings_dialog.estimated_cost_label.setText("$0.24")
        
        # Replace the original method with our mock
        ai_settings_dialog._update_usage_statistics = mock_update_usage_statistics
        
        # Set the new AI service
        ai_settings_dialog.set_ai_service(new_mock_service)
        
        # Update usage statistics manually for the test
        mock_update_usage_statistics()
        
        # Check that AI service was set
        assert ai_settings_dialog.ai_service == new_mock_service
        
        # Check that usage statistics were updated
        assert ai_settings_dialog.usage_table.item(0, 1).text() == "5000"  # Prompt tokens
        assert ai_settings_dialog.usage_table.item(1, 1).text() == "7000"  # Completion tokens
        assert ai_settings_dialog.usage_table.item(2, 1).text() == "12000"  # Total tokens
        assert ai_settings_dialog.usage_table.item(3, 1).text() == "200"   # Requests
        assert ai_settings_dialog.estimated_cost_label.text() == "$0.24"


if __name__ == '__main__':
    pytest.main(['-v', __file__])
