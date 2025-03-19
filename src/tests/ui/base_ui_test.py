#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base UI test class for RebelSCRIBE UI tests.

This module provides a base test class with common setup and teardown
functionality for UI tests to reduce code duplication across test files.
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt, QSettings

from src.utils.config_manager import ConfigManager
from src.ui.main_window import MainWindow


class BaseUITest:
    """Base class for RebelSCRIBE UI tests with common setup and teardown."""
    
    @pytest.fixture
    def app(self):
        """Create a QApplication instance for the tests."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
        # No need to clean up as we're not destroying the app
    
    @pytest.fixture
    def test_dir(self):
        """Create a temporary directory for test files."""
        test_dir = tempfile.mkdtemp()
        yield test_dir
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
    
    @pytest.fixture
    def mock_config(self, monkeypatch, test_dir):
        """Create a mock configuration."""
        # Mock ConfigManager to avoid loading real config
        mock_config = MagicMock(spec=ConfigManager)
        # Set up specific returns for different get calls
        mock_config.get.side_effect = lambda section, key=None, default=None: {
            "application": {
                "data_directory": test_dir,
                "autosave_interval": 5
            },
            "editor": {
                "font_family": "Arial",
                "font_size": 12,
                "theme": "light"
            },
            "ai": {
                "api_key": "mock_key",
                "model": "gpt-4"
            },
            "export": {
                "default_format": "PDF",
                "include_metadata": True
            },
            "backup": {
                "auto_backup": True,
                "backup_interval": 30,
                "max_backups": 5
            }
        }.get(section, {}).get(key, default) if key else {}
        
        # Mock ConfigManager class
        mock_config_manager_class = MagicMock()
        mock_config_manager_class.return_value = mock_config
        monkeypatch.setattr('src.utils.config_manager.ConfigManager', mock_config_manager_class)
        
        # Mock get_config for services that use it directly
        monkeypatch.setattr('src.utils.config_manager.get_config', lambda *args: mock_config)
        monkeypatch.setattr('src.backend.services.search_service.get_config', lambda *args: mock_config)
        monkeypatch.setattr('src.backend.services.statistics_service.get_config', lambda *args: mock_config)
        
        return mock_config
    
    @pytest.fixture
    def mock_project_manager(self, test_dir):
        """Create a mock project manager."""
        mock_manager = MagicMock()
        mock_project = MagicMock()
        mock_project.title = "Test Project"
        mock_project.author = "Test Author"
        mock_project.path = os.path.join(test_dir, "test_project.rebelscribe")
        mock_manager.current_project = mock_project
        mock_manager.create_project.return_value = mock_project
        mock_manager.load_project.return_value = mock_project
        return mock_manager
    
    @pytest.fixture
    def mock_document_manager(self, test_dir):
        """Create a mock document manager."""
        mock_manager = MagicMock()
        mock_document = MagicMock()
        mock_document.title = "Test Document"
        mock_document.content = "Test content"
        mock_document.id = "doc123"
        mock_document.path = os.path.join(test_dir, "documents", "test_document.json")
        mock_manager.current_document = mock_document
        mock_manager.create_document.return_value = mock_document
        mock_manager.load_document.return_value = mock_document
        mock_manager.get_all_documents.return_value = [mock_document]
        return mock_manager
    
    @pytest.fixture
    def mock_search_service(self):
        """Create a mock search service."""
        mock_service = MagicMock()
        mock_service.search_documents.return_value = []
        return mock_service
    
    @pytest.fixture
    def mock_statistics_service(self):
        """Create a mock statistics service."""
        mock_service = MagicMock()
        mock_service.get_project_statistics.return_value = {
            "word_count": 1000,
            "character_count": 5000,
            "document_count": 5,
            "average_words_per_document": 200
        }
        return mock_service
    
    @pytest.fixture
    def mock_export_service(self):
        """Create a mock export service."""
        mock_service = MagicMock()
        mock_service.export_project.return_value = True
        return mock_service
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        mock_service = MagicMock()
        mock_service.generate_text.return_value = "AI generated text"
        return mock_service
    
    @pytest.fixture
    def mock_character_assistant(self):
        """Create a mock character assistant."""
        mock_assistant = MagicMock()
        mock_assistant.develop_character.return_value = "Character profile"
        return mock_assistant
    
    @pytest.fixture
    def mock_plot_assistant(self):
        """Create a mock plot assistant."""
        mock_assistant = MagicMock()
        mock_assistant.develop_plot.return_value = "Plot outline"
        return mock_assistant
    
    @pytest.fixture
    def main_window(self, qtbot, monkeypatch, mock_config, mock_project_manager, 
                   mock_document_manager, mock_search_service, mock_statistics_service,
                   mock_export_service, mock_ai_service, mock_character_assistant,
                   mock_plot_assistant):
        """Create a MainWindow instance for testing with mocked dependencies."""
        # Mock QSettings to avoid affecting real settings
        monkeypatch.setattr(QSettings, 'value', lambda *args: None)
        
        # Mock QApplication to avoid creating a real application
        with patch('src.ui.main_window.QApplication'):
            # Create window
            window = MainWindow()
            
            # Inject mocked dependencies
            window.project_manager = mock_project_manager
            window.document_manager = mock_document_manager
            
            # Mock services
            monkeypatch.setattr('src.ui.main_window.SearchService', lambda *args: mock_search_service)
            monkeypatch.setattr('src.ui.main_window.StatisticsService', lambda *args: mock_statistics_service)
            monkeypatch.setattr('src.ui.main_window.ExportService', lambda *args: mock_export_service)
            monkeypatch.setattr('src.ui.main_window.AIService', lambda *args: mock_ai_service)
            monkeypatch.setattr('src.ui.main_window.CharacterAssistant', lambda *args: mock_character_assistant)
            monkeypatch.setattr('src.ui.main_window.PlotAssistant', lambda *args: mock_plot_assistant)
            
            # Mock editor
            window.editor = MagicMock()
            window.editor.get_content.return_value = "Test content"
            window.editor.current_document = mock_document_manager.current_document
            
            # Add to qtbot
            qtbot.addWidget(window)
            
            return window
    
    def mock_dialog(self, dialog_class, **kwargs):
        """Create a mock dialog with the given attributes."""
        mock_dialog = MagicMock(spec=dialog_class)
        for key, value in kwargs.items():
            setattr(mock_dialog, key, value)
        return mock_dialog
    
    def mock_file_dialog(self, monkeypatch, return_value):
        """Mock QFileDialog to return a specific value."""
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QFileDialog.getSaveFileName',
            lambda *args, **kwargs: return_value
        )
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QFileDialog.getOpenFileName',
            lambda *args, **kwargs: return_value
        )
    
    def mock_message_box(self, monkeypatch, return_value=None):
        """Mock QMessageBox to return a specific value."""
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QMessageBox.information',
            lambda *args, **kwargs: return_value
        )
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QMessageBox.question',
            lambda *args, **kwargs: return_value
        )
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QMessageBox.warning',
            lambda *args, **kwargs: return_value
        )
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QMessageBox.critical',
            lambda *args, **kwargs: return_value
        )
    
    def mock_input_dialog(self, monkeypatch, return_value):
        """Mock QInputDialog to return a specific value."""
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QInputDialog.getText',
            lambda *args, **kwargs: return_value
        )
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QInputDialog.getInt',
            lambda *args, **kwargs: return_value
        )
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QInputDialog.getDouble',
            lambda *args, **kwargs: return_value
        )
        monkeypatch.setattr(
            'PyQt6.QtWidgets.QInputDialog.getItem',
            lambda *args, **kwargs: return_value
        )
    
    def trigger_action(self, action, qtbot):
        """Trigger an action and wait for it to complete."""
        action.trigger()
        qtbot.wait(100)
    
    def click_button(self, button, qtbot):
        """Click a button and wait for it to complete."""
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
    
    def enter_text(self, widget, text, qtbot):
        """Enter text into a widget and wait for it to complete."""
        qtbot.keyClicks(widget, text)
        qtbot.wait(100)
