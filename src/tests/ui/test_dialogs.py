#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Dialog components.

This module contains tests for the various dialog components in the UI.
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

from src.ui.settings_dialog import SettingsDialog
from src.ui.export_dialog import ExportDialog
from src.ui.project_settings_dialog import ProjectSettingsDialog
from src.ui.ai_settings_dialog import AISettingsDialog
from src.backend.models.project import Project
from src.backend.models.document import Document
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
def mock_config():
    """Create a mock ConfigManager for testing."""
    with patch('src.ui.settings_dialog.get_config', return_value=MagicMock()) as mock_get_config:
        mock_instance = mock_get_config.return_value
        
        # Mock settings
        mock_settings = {
            "editor": {
                "font_family": "Arial",
                "font_size": 12,
                "text_color": "#000000",
                "background_color": "#FFFFFF",
                "autosave_enabled": True,
                "autosave_interval": 5,
                "spellcheck_enabled": True,
                "spellcheck_language": "English (US)"
            },
            "interface": {
                "theme": "Light",
                "accent_color": "#0078D7",
                "show_toolbar": True,
                "show_statusbar": True,
                "show_line_numbers": True,
                "restore_session": True,
                "show_welcome": True
            },
            "file_locations": {
                "save_location": "/path/to/save",
                "backup_location": "/path/to/backup",
                "enable_backups": True,
                "backup_interval": 30,
                "max_backups": 10
            },
            "shortcuts": {
                "new_project": "Ctrl+N",
                "open_project": "Ctrl+O",
                "save": "Ctrl+S",
                "save_as": "Ctrl+Shift+S",
                "undo": "Ctrl+Z",
                "redo": "Ctrl+Y",
                "cut": "Ctrl+X",
                "copy": "Ctrl+C",
                "paste": "Ctrl+V",
                "distraction_free": "F11",
                "focus_mode": "Ctrl+Shift+F"
            }
        }
        
        mock_instance.get_settings.return_value = mock_settings
        mock_instance.update_settings.return_value = True
        mock_instance.reset_to_defaults.return_value = True
        
        yield mock_instance


@pytest.fixture
def settings_dialog(qtbot, mock_config):
    """Create a SettingsDialog instance for testing."""
    dialog = SettingsDialog()
    qtbot.addWidget(dialog)
    return dialog


class TestSettingsDialog:
    """Test cases for the SettingsDialog class."""
    
    def test_init(self, settings_dialog):
        """Test initialization of the settings dialog."""
        # Check that components are created
        assert settings_dialog.tab_widget is not None
        assert settings_dialog.button_box is not None
        
        # Check tab widget
        assert settings_dialog.tab_widget.count() == 4
        assert settings_dialog.tab_widget.tabText(0) == "Editor"
        assert settings_dialog.tab_widget.tabText(1) == "Interface"
        assert settings_dialog.tab_widget.tabText(2) == "File Locations"
        assert settings_dialog.tab_widget.tabText(3) == "Keyboard Shortcuts"
        
        # Check editor tab components
        assert settings_dialog.font_button is not None
        assert settings_dialog.font_label is not None
        assert settings_dialog.text_color_button is not None
        assert settings_dialog.text_color_preview is not None
        assert settings_dialog.background_color_button is not None
        assert settings_dialog.background_color_preview is not None
        assert settings_dialog.autosave_checkbox is not None
        assert settings_dialog.autosave_interval_spinbox is not None
        assert settings_dialog.spellcheck_checkbox is not None
        assert settings_dialog.spellcheck_language_combo is not None
        
        # Check interface tab components
        assert settings_dialog.theme_combo is not None
        assert settings_dialog.accent_color_button is not None
        assert settings_dialog.accent_color_preview is not None
        assert settings_dialog.show_toolbar_checkbox is not None
        assert settings_dialog.show_statusbar_checkbox is not None
        assert settings_dialog.show_line_numbers_checkbox is not None
        assert settings_dialog.restore_session_checkbox is not None
        assert settings_dialog.show_welcome_checkbox is not None
        
        # Check file locations tab components
        assert settings_dialog.save_location_edit is not None
        assert settings_dialog.save_location_button is not None
        assert settings_dialog.backup_location_edit is not None
        assert settings_dialog.backup_location_button is not None
        assert settings_dialog.enable_backups_checkbox is not None
        assert settings_dialog.backup_interval_spinbox is not None
        assert settings_dialog.max_backups_spinbox is not None
        
        # Check shortcuts tab components
        assert settings_dialog.new_project_shortcut is not None
        assert settings_dialog.open_project_shortcut is not None
        assert settings_dialog.save_shortcut is not None
        assert settings_dialog.save_as_shortcut is not None
        assert settings_dialog.undo_shortcut is not None
        assert settings_dialog.redo_shortcut is not None
        assert settings_dialog.cut_shortcut is not None
        assert settings_dialog.copy_shortcut is not None
        assert settings_dialog.paste_shortcut is not None
        assert settings_dialog.distraction_free_shortcut is not None
        assert settings_dialog.focus_mode_shortcut is not None
        assert settings_dialog.reset_shortcuts_button is not None
    
    def test_load_settings(self, settings_dialog, mock_config):
        """Test loading settings."""
        # Check that settings were loaded
        assert settings_dialog.font_label.text() == "Current Font: Arial, 12pt"
        assert "background-color: #000000" in settings_dialog.text_color_preview.styleSheet()
        assert "background-color: #FFFFFF" in settings_dialog.background_color_preview.styleSheet()
        assert settings_dialog.autosave_checkbox.isChecked() is True
        assert settings_dialog.autosave_interval_spinbox.value() == 5
        assert settings_dialog.spellcheck_checkbox.isChecked() is True
        assert settings_dialog.spellcheck_language_combo.currentText() == "English (US)"
        
        assert settings_dialog.theme_combo.currentText() == "Light"
        assert "background-color: #0078D7" in settings_dialog.accent_color_preview.styleSheet()
        assert settings_dialog.show_toolbar_checkbox.isChecked() is True
        assert settings_dialog.show_statusbar_checkbox.isChecked() is True
        assert settings_dialog.show_line_numbers_checkbox.isChecked() is True
        assert settings_dialog.restore_session_checkbox.isChecked() is True
        assert settings_dialog.show_welcome_checkbox.isChecked() is True
        
        assert settings_dialog.save_location_edit.text() == "/path/to/save"
        assert settings_dialog.backup_location_edit.text() == "/path/to/backup"
        assert settings_dialog.enable_backups_checkbox.isChecked() is True
        assert settings_dialog.backup_interval_spinbox.value() == 30
        assert settings_dialog.max_backups_spinbox.value() == 10
        
        assert settings_dialog.new_project_shortcut.text() == "Ctrl+N"
        assert settings_dialog.open_project_shortcut.text() == "Ctrl+O"
        assert settings_dialog.save_shortcut.text() == "Ctrl+S"
        assert settings_dialog.save_as_shortcut.text() == "Ctrl+Shift+S"
        assert settings_dialog.undo_shortcut.text() == "Ctrl+Z"
        assert settings_dialog.redo_shortcut.text() == "Ctrl+Y"
        assert settings_dialog.cut_shortcut.text() == "Ctrl+X"
        assert settings_dialog.copy_shortcut.text() == "Ctrl+C"
        assert settings_dialog.paste_shortcut.text() == "Ctrl+V"
        assert settings_dialog.distraction_free_shortcut.text() == "F11"
        assert settings_dialog.focus_mode_shortcut.text() == "Ctrl+Shift+F"
    
    def test_get_current_settings(self, settings_dialog):
        """Test getting current settings."""
        # Modify some settings
        settings_dialog.font_label.setText("Current Font: Times New Roman, 14pt")
        settings_dialog.text_color_preview.setStyleSheet("background-color: #FF0000; border: 1px solid #CCCCCC;")
        settings_dialog.autosave_checkbox.setChecked(False)
        settings_dialog.theme_combo.setCurrentText("Dark")
        settings_dialog.show_toolbar_checkbox.setChecked(False)
        settings_dialog.save_location_edit.setText("/new/save/path")
        settings_dialog.enable_backups_checkbox.setChecked(False)
        settings_dialog.new_project_shortcut.setText("Ctrl+Shift+N")
        
        # Get current settings
        settings = settings_dialog._get_current_settings()
        
        # Check editor settings
        assert settings["editor"]["font_family"] == "Times New Roman"
        assert settings["editor"]["font_size"] == 14
        assert settings["editor"]["text_color"] == "#FF0000"
        assert settings["editor"]["autosave_enabled"] is False
        
        # Check interface settings
        assert settings["interface"]["theme"] == "Dark"
        assert settings["interface"]["show_toolbar"] is False
        
        # Check file locations settings
        assert settings["file_locations"]["save_location"] == "/new/save/path"
        assert settings["file_locations"]["enable_backups"] is False
        
        # Check shortcuts
        assert settings["shortcuts"]["new_project"] == "Ctrl+Shift+N"
    
    def test_save_settings(self, settings_dialog, mock_config):
        """Test saving settings."""
        # Modify some settings
        settings_dialog.font_label.setText("Current Font: Times New Roman, 14pt")
        settings_dialog.text_color_preview.setStyleSheet("background-color: #FF0000; border: 1px solid #CCCCCC;")
        settings_dialog.autosave_checkbox.setChecked(False)
        settings_dialog.theme_combo.setCurrentText("Dark")
        settings_dialog.show_toolbar_checkbox.setChecked(False)
        settings_dialog.save_location_edit.setText("/new/save/path")
        settings_dialog.enable_backups_checkbox.setChecked(False)
        settings_dialog.new_project_shortcut.setText("Ctrl+Shift+N")
        
        # Mock settings_changed signal
        settings_dialog.settings_changed = MagicMock()
        
        # Save settings
        result = settings_dialog._save_settings()
        
        # Check result
        assert result is True
        
        # Check that update_settings was called
        mock_config.update_settings.assert_called_once()
        
        # Check that settings_changed signal was emitted
        settings_dialog.settings_changed.emit.assert_called_once()
        
        # Check that the correct settings were passed to update_settings
        settings = mock_config.update_settings.call_args[0][0]
        assert settings["editor"]["font_family"] == "Times New Roman"
        assert settings["editor"]["font_size"] == 14
        assert settings["editor"]["text_color"] == "#FF0000"
        assert settings["editor"]["autosave_enabled"] is False
        assert settings["interface"]["theme"] == "Dark"
        assert settings["interface"]["show_toolbar"] is False
        assert settings["file_locations"]["save_location"] == "/new/save/path"
        assert settings["file_locations"]["enable_backups"] is False
        assert settings["shortcuts"]["new_project"] == "Ctrl+Shift+N"
    
    def test_on_accept(self, qtbot, settings_dialog):
        """Test accept button clicked."""
        # Mock _save_settings
        settings_dialog._save_settings = MagicMock(return_value=True)
        
        # Mock accept
        settings_dialog.accept = MagicMock()
        
        # Click OK button
        qtbot.mouseClick(settings_dialog.button_box.button(QDialogButtonBox.StandardButton.Ok), Qt.MouseButton.LeftButton)
        
        # Check that _save_settings was called
        settings_dialog._save_settings.assert_called_once()
        
        # Check that accept was called
        settings_dialog.accept.assert_called_once()
    
    def test_on_apply(self, qtbot, settings_dialog):
        """Test apply button clicked."""
        # Mock _save_settings
        settings_dialog._save_settings = MagicMock(return_value=True)
        
        # Click Apply button
        qtbot.mouseClick(settings_dialog.button_box.button(QDialogButtonBox.StandardButton.Apply), Qt.MouseButton.LeftButton)
        
        # Check that _save_settings was called
        settings_dialog._save_settings.assert_called_once()
    
    def test_on_restore_defaults(self, qtbot, settings_dialog, mock_config, monkeypatch):
        """Test restore defaults button clicked."""
        # Mock QMessageBox.question to return Yes
        monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        
        # Mock _load_settings
        settings_dialog._load_settings = MagicMock()
        
        # Click Restore Defaults button
        qtbot.mouseClick(settings_dialog.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults), Qt.MouseButton.LeftButton)
        
        # Check that reset_to_defaults was called
        mock_config.reset_to_defaults.assert_called_once()
        
        # Check that _load_settings was called
        settings_dialog._load_settings.assert_called_once()
    
    def test_on_select_font(self, qtbot, settings_dialog, monkeypatch):
        """Test select font button clicked."""
        # Mock QFontDialog.getFont to return a font
        font = QFont("Courier New", 16)
        monkeypatch.setattr(QFontDialog, "getFont", lambda *args, **kwargs: (font, True))
        
        # Click font button
        qtbot.mouseClick(settings_dialog.font_button, Qt.MouseButton.LeftButton)
        
        # Check that font label was updated
        assert settings_dialog.font_label.text() == "Current Font: Courier New, 16pt"
    
    def test_on_select_text_color(self, qtbot, settings_dialog, monkeypatch):
        """Test select text color button clicked."""
        # Mock QColorDialog.getColor to return a color
        color = QColor("#FF0000")
        monkeypatch.setattr(QColorDialog, "getColor", lambda *args, **kwargs: color)
        
        # Click text color button
        qtbot.mouseClick(settings_dialog.text_color_button, Qt.MouseButton.LeftButton)
        
        # Check that color preview was updated
        assert "background-color: #ff0000" in settings_dialog.text_color_preview.styleSheet().lower()
    
    def test_on_select_background_color(self, qtbot, settings_dialog, monkeypatch):
        """Test select background color button clicked."""
        # Mock QColorDialog.getColor to return a color
        color = QColor("#EEEEEE")
        monkeypatch.setattr(QColorDialog, "getColor", lambda *args, **kwargs: color)
        
        # Click background color button
        qtbot.mouseClick(settings_dialog.background_color_button, Qt.MouseButton.LeftButton)
        
        # Check that color preview was updated
        assert "background-color: #eeeeee" in settings_dialog.background_color_preview.styleSheet().lower()
    
    def test_on_autosave_toggled(self, qtbot, settings_dialog):
        """Test autosave checkbox toggled."""
        # Uncheck autosave checkbox
        settings_dialog.autosave_checkbox.setChecked(False)
        
        # Check that autosave interval spinbox is disabled
        assert not settings_dialog.autosave_interval_spinbox.isEnabled()
        
        # Check autosave checkbox
        settings_dialog.autosave_checkbox.setChecked(True)
        
        # Check that autosave interval spinbox is enabled
        assert settings_dialog.autosave_interval_spinbox.isEnabled()
    
    def test_on_select_accent_color(self, qtbot, settings_dialog, monkeypatch):
        """Test select accent color button clicked."""
        # Mock QColorDialog.getColor to return a color
        color = QColor("#00FF00")
        monkeypatch.setattr(QColorDialog, "getColor", lambda *args, **kwargs: color)
        
        # Click accent color button
        qtbot.mouseClick(settings_dialog.accent_color_button, Qt.MouseButton.LeftButton)
        
        # Check that color preview was updated
        assert "background-color: #00ff00" in settings_dialog.accent_color_preview.styleSheet().lower()
    
    def test_on_select_save_location(self, qtbot, settings_dialog, monkeypatch):
        """Test select save location button clicked."""
        # Mock QFileDialog.getExistingDirectory to return a directory
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: "/new/save/path")
        
        # Click save location button
        qtbot.mouseClick(settings_dialog.save_location_button, Qt.MouseButton.LeftButton)
        
        # Check that save location edit was updated
        assert settings_dialog.save_location_edit.text() == "/new/save/path"
    
    def test_on_select_backup_location(self, qtbot, settings_dialog, monkeypatch):
        """Test select backup location button clicked."""
        # Mock QFileDialog.getExistingDirectory to return a directory
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: "/new/backup/path")
        
        # Click backup location button
        qtbot.mouseClick(settings_dialog.backup_location_button, Qt.MouseButton.LeftButton)
        
        # Check that backup location edit was updated
        assert settings_dialog.backup_location_edit.text() == "/new/backup/path"
    
    def test_on_enable_backups_toggled(self, qtbot, settings_dialog):
        """Test enable backups checkbox toggled."""
        # Uncheck enable backups checkbox
        settings_dialog.enable_backups_checkbox.setChecked(False)
        
        # Check that backup settings are disabled
        assert not settings_dialog.backup_interval_spinbox.isEnabled()
        assert not settings_dialog.max_backups_spinbox.isEnabled()
        
        # Check enable backups checkbox
        settings_dialog.enable_backups_checkbox.setChecked(True)
        
        # Check that backup settings are enabled
        assert settings_dialog.backup_interval_spinbox.isEnabled()
        assert settings_dialog.max_backups_spinbox.isEnabled()
    
    def test_on_reset_shortcuts(self, qtbot, settings_dialog, monkeypatch):
        """Test reset shortcuts button clicked."""
        # Mock QMessageBox.question to return Yes
        monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        
        # Modify some shortcuts
        settings_dialog.new_project_shortcut.setText("Ctrl+Shift+N")
        settings_dialog.save_shortcut.setText("Ctrl+Alt+S")
        
        # Click reset shortcuts button
        qtbot.mouseClick(settings_dialog.reset_shortcuts_button, Qt.MouseButton.LeftButton)
        
        # Check that shortcuts were reset
        assert settings_dialog.new_project_shortcut.text() == "Ctrl+N"
        assert settings_dialog.save_shortcut.text() == "Ctrl+S"


class TestExportDialog:
    """Test cases for the ExportDialog class."""
    
    @pytest.fixture
    def mock_project_manager(self):
        """Create a mock ProjectManager for testing."""
        return MagicMock()
    
    @pytest.fixture
    def mock_document_manager(self):
        """Create a mock DocumentManager for testing."""
        return MagicMock()
    
    @pytest.fixture
    def mock_export_service(self):
        """Create a mock ExportService for testing."""
        with patch('src.ui.export_dialog.ExportService') as mock_service_cls:
            mock_instance = mock_service_cls.return_value
            mock_instance.export_project.return_value = True
            mock_instance.export_document.return_value = True
            
            # Define format constants
            mock_service_cls.FORMAT_DOCX = "docx"
            mock_service_cls.FORMAT_PDF = "pdf"
            mock_service_cls.FORMAT_MARKDOWN = "md"
            mock_service_cls.FORMAT_HTML = "html"
            mock_service_cls.FORMAT_EPUB = "epub"
            mock_service_cls.FORMAT_TXT = "txt"
            
            yield mock_instance
    
    @pytest.fixture
    def export_dialog(self, qtbot, mock_project_manager, mock_document_manager, mock_export_service):
        """Create an ExportDialog instance for testing."""
        with patch('src.ui.export_dialog.ExportService', return_value=mock_export_service):
            dialog = ExportDialog(project_manager=mock_project_manager, document_manager=mock_document_manager)
            qtbot.addWidget(dialog)
            return dialog
    
    @pytest.fixture
    def mock_project(self):
        """Create a mock Project for testing."""
        project = MagicMock(spec=Project)
        project.title = "Test Project"
        return project
    
    @pytest.fixture
    def mock_document(self):
        """Create a mock Document for testing."""
        document = MagicMock(spec=Document)
        document.title = "Test Document"
        return document
    
    def test_init(self, export_dialog):
        """Test initialization of the export dialog."""
        # Check that components are created
        assert export_dialog.format_combo is not None
        assert export_dialog.settings_tabs is not None
        assert export_dialog.path_edit is not None
        assert export_dialog.browse_button is not None
        assert export_dialog.export_button is not None
        assert export_dialog.cancel_button is not None
        
        # Check format combo
        assert export_dialog.format_combo.count() == 6
        
        # Check settings tabs
        assert export_dialog.settings_tabs.count() == 4
        assert export_dialog.settings_tabs.tabText(0) == "General"
        assert export_dialog.settings_tabs.tabText(1) == "Formatting"
        assert export_dialog.settings_tabs.tabText(2) == "Page"
        assert export_dialog.settings_tabs.tabText(3) == "Chapters"
        
        # Check export mode
        assert export_dialog.export_mode == "project"
        assert export_dialog.project_radio.isChecked() is True
        assert export_dialog.document_radio.isChecked() is False
    
    def test_on_mode_changed(self, export_dialog):
        """Test export mode change."""
        # Change to document mode
        export_dialog.document_radio.setChecked(True)
        
        # Check that export mode is updated
        assert export_dialog.export_mode == "document"
        assert export_dialog.toc_check.isEnabled() is False
        assert export_dialog.chapter_new_page_check.isEnabled() is False
        assert export_dialog.number_chapters_check.isEnabled() is False
        assert export_dialog.chapter_prefix_edit.isEnabled() is False
        
        # Change back to project mode
        export_dialog.project_radio.setChecked(True)
        
        # Check that export mode is updated
        assert export_dialog.export_mode == "project"
        assert export_dialog.toc_check.isEnabled() is True
        assert export_dialog.chapter_new_page_check.isEnabled() is True
        assert export_dialog.number_chapters_check.isEnabled() is True
        assert export_dialog.chapter_prefix_edit.isEnabled() is True
    
    def test_on_format_changed(self, export_dialog, mock_export_service):
        """Test format change."""
        # Set a path
        export_dialog.path_edit.setText("/path/to/export.docx")
        
        # Change format to PDF
        export_dialog.format_combo.setCurrentIndex(1)  # PDF
        
        # Check that path extension is updated
        assert export_dialog.path_edit.text() == "/path/to/export.pdf"
        
        # Check that formatting options are enabled
        assert export_dialog.settings_tabs.isTabEnabled(1) is True  # Formatting tab
        assert export_dialog.settings_tabs.isTabEnabled(2) is True  # Page tab
        assert export_dialog.page_numbers_check.isEnabled() is True
        
        # Change format to Markdown
        export_dialog.format_combo.setCurrentIndex(2)  # Markdown
        
        # Check that path extension is updated
        assert export_dialog.path_edit.text() == "/path/to/export.md"
        
        # Check that formatting options are disabled
        assert export_dialog.settings_tabs.isTabEnabled(1) is False  # Formatting tab
        assert export_dialog.settings_tabs.isTabEnabled(2) is False  # Page tab
        assert export_dialog.page_numbers_check.isEnabled() is False
        
        # Change format to HTML
        export_dialog.format_combo.setCurrentIndex(3)  # HTML
        
        # Check that path extension is updated
        assert export_dialog.path_edit.text() == "/path/to/export.html"
        
        # Check that formatting options are partially enabled
        assert export_dialog.settings_tabs.isTabEnabled(1) is True  # Formatting tab
        assert export_dialog.settings_tabs.isTabEnabled(2) is False  # Page tab
        assert export_dialog.page_numbers_check.isEnabled() is False
    
    def test_on_browse(self, export_dialog, monkeypatch):
        """Test browse button click."""
        # Mock QFileDialog.getSaveFileName to return a file path
        monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: ("/path/to/export.docx", ""))
        
        # Click browse button
        export_dialog.browse_button.click()
        
        # Check that path edit is updated
        assert export_dialog.path_edit.text() == "/path/to/export.docx"
    
    def test_get_export_settings(self, export_dialog):
        """Test getting export settings."""
        # Modify some settings
        export_dialog.title_page_check.setChecked(False)
        export_dialog.font_combo.setCurrentText("Arial")
        export_dialog.font_size_spin.setValue(14)
        export_dialog.page_size_combo.setCurrentText("A4")
        export_dialog.chapter_prefix_edit.setText("Section ")
        
        # Get export settings
        settings = export_dialog._get_export_settings()
        
        # Check settings
        assert settings["include_title_page"] is False
        assert settings["font_name"] == "Arial"
        assert settings["font_size"] == 14
        assert settings["page_size"] == "a4"
        assert settings["chapter_prefix"] == "Section "
    
    def test_on_export_project(self, export_dialog, mock_project, mock_export_service, monkeypatch):
        """Test export button click for project export."""
        # Set project and path
        export_dialog.current_project = mock_project
        export_dialog.path_edit.setText("/path/to/export.docx")
        
        # Mock QMessageBox.information
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
        
        # Mock dialog accept
        export_dialog.accept = MagicMock()
        
        # Click export button
        export_dialog.export_button.click()
        
        # Check that export_project was called
        mock_export_service.export_project.assert_called_once()
        
        # Check that dialog was accepted
        export_dialog.accept.assert_called_once()
    
    def test_on_export_document(self, export_dialog, mock_document, mock_export_service, monkeypatch):
        """Test export button click for document export."""
        # Set document and path
        export_dialog.current_document = mock_document
        export_dialog.document_radio.setChecked(True)
        export_dialog.path_edit.setText("/path/to/export.docx")
        
        # Mock QMessageBox.information
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
        
        # Mock dialog accept
        export_dialog.accept = MagicMock()
        
        # Click export button
        export_dialog.export_button.click()
        
        # Check that export_document was called
        mock_export_service.export_document.assert_called_once()
        
        # Check that dialog was accepted
        export_dialog.accept.assert_called_once()
    
    def test_on_export_no_project(self, export_dialog, monkeypatch):
        """Test export button click with no project."""
        # Set path but no project
        export_dialog.current_project = None
        export_dialog.path_edit.setText("/path/to/export.docx")
        
        # Mock QMessageBox.warning
        warning_mock = MagicMock()
        monkeypatch.setattr(QMessageBox, "warning", warning_mock)
        
        # Click export button
        export_dialog.export_button.click()
        
        # Check that warning was shown
        warning_mock.assert_called_once()
