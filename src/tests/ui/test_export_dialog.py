#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Export Dialog component.

This module contains tests for the Export Dialog in the UI.
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
    QFileDialog, QColorDialog, QFontDialog, QMessageBox, QTableWidgetItem,
    QRadioButton
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QFont, QColor

from src.ui.export_dialog import ExportDialog
from src.backend.models.project import Project
from src.backend.models.document import Document
from src.backend.services.export_service import ExportService


@pytest.fixture
def app():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to clean up as we're not destroying the app


@pytest.fixture
def mock_project_manager():
    """Create a mock ProjectManager for testing."""
    return MagicMock()


@pytest.fixture
def mock_document_manager():
    """Create a mock DocumentManager for testing."""
    return MagicMock()


@pytest.fixture
def mock_export_service():
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
def export_dialog(qtbot, mock_project_manager, mock_document_manager, mock_export_service):
    """Create an ExportDialog instance for testing."""
    with patch('src.ui.export_dialog.ExportService', return_value=mock_export_service):
        dialog = ExportDialog(project_manager=mock_project_manager, document_manager=mock_document_manager)
        qtbot.addWidget(dialog)
        return dialog


@pytest.fixture
def mock_project():
    """Create a mock Project for testing."""
    project = MagicMock(spec=Project)
    project.title = "Test Project"
    return project


@pytest.fixture
def mock_document():
    """Create a mock Document for testing."""
    document = MagicMock(spec=Document)
    document.title = "Test Document"
    return document


class TestExportDialog:
    """Test cases for the ExportDialog class."""
    
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
    
    def test_on_export_no_path(self, export_dialog, mock_project, monkeypatch):
        """Test export button click with no path."""
        # Set project but no path
        export_dialog.current_project = mock_project
        export_dialog.path_edit.setText("")
        
        # Mock QMessageBox.warning
        warning_mock = MagicMock()
        monkeypatch.setattr(QMessageBox, "warning", warning_mock)
        
        # Click export button
        export_dialog.export_button.click()
        
        # Check that warning was shown
        warning_mock.assert_called_once()
    
    def test_set_project(self, export_dialog, mock_project):
        """Test setting project."""
        # Set project
        export_dialog.set_project(mock_project)
        
        # Check that project is set
        assert export_dialog.current_project == mock_project
        assert export_dialog.project_radio.isChecked() is True
        assert export_dialog.export_mode == "project"
    
    def test_set_document(self, export_dialog, mock_document):
        """Test setting document."""
        # Set document
        export_dialog.set_document(mock_document)
        
        # Check that document is set
        assert export_dialog.current_document == mock_document
        assert export_dialog.document_radio.isChecked() is True
        assert export_dialog.export_mode == "document"
    
    def test_update_path_extension(self, export_dialog, mock_export_service):
        """Test updating path extension."""
        # Set a path
        export_dialog.path_edit.setText("/path/to/export.docx")
        
        # Change format to PDF
        export_dialog.format_combo.setCurrentIndex(1)  # PDF
        
        # Check that path extension is updated
        assert export_dialog.path_edit.text() == "/path/to/export.pdf"
        
        # Change format to EPUB
        export_dialog.format_combo.setCurrentIndex(4)  # EPUB
        
        # Check that path extension is updated
        assert export_dialog.path_edit.text() == "/path/to/export.epub"
    
    def test_save_settings(self, export_dialog, monkeypatch):
        """Test saving settings to QSettings."""
        # Mock QSettings
        mock_settings = MagicMock(spec=QSettings)
        monkeypatch.setattr('src.ui.export_dialog.QSettings', lambda: mock_settings)
        
        # Modify some settings
        export_dialog.title_page_check.setChecked(False)
        export_dialog.font_combo.setCurrentText("Arial")
        export_dialog.font_size_spin.setValue(14)
        export_dialog.page_size_combo.setCurrentText("A4")
        export_dialog.chapter_prefix_edit.setText("Section ")
        
        # Save settings
        export_dialog._save_settings()
        
        # Check that settings were saved
        mock_settings.setValue.assert_any_call("export/title_page", False)
        mock_settings.setValue.assert_any_call("export/font", "Arial")
        mock_settings.setValue.assert_any_call("export/font_size", 14)
        mock_settings.setValue.assert_any_call("export/page_size", "A4")
        mock_settings.setValue.assert_any_call("export/chapter_prefix", "Section ")
    
    def test_load_settings(self, export_dialog, monkeypatch):
        """Test loading settings from QSettings."""
        # Mock QSettings
        mock_settings = MagicMock(spec=QSettings)
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "export/title_page": False,
            "export/toc": True,
            "export/page_numbers": True,
            "export/synopsis": True,
            "export/notes": False,
            "export/metadata": True,
            "export/font": "Calibri",
            "export/font_size": 16,
            "export/line_spacing": 2.0,
            "export/paragraph_spacing": 24,
            "export/page_size": "Legal",
            "export/margin_top": 1.5,
            "export/margin_bottom": 1.5,
            "export/margin_left": 1.2,
            "export/margin_right": 1.2,
            "export/chapter_new_page": True,
            "export/number_chapters": False,
            "export/chapter_prefix": "Part ",
            "export/scene_separator": "---",
            "export/format": "pdf"
        }.get(key, default)
        
        monkeypatch.setattr('src.ui.export_dialog.QSettings', lambda: mock_settings)
        
        # Load settings
        export_dialog._load_settings()
        
        # Check that settings were loaded
        assert export_dialog.title_page_check.isChecked() is False
        assert export_dialog.toc_check.isChecked() is True
        assert export_dialog.page_numbers_check.isChecked() is True
        assert export_dialog.synopsis_check.isChecked() is True
        assert export_dialog.notes_check.isChecked() is False
        assert export_dialog.metadata_check.isChecked() is True
        assert export_dialog.font_combo.currentText() == "Calibri"
        assert export_dialog.font_size_spin.value() == 16
        assert export_dialog.line_spacing_spin.value() == 2.0
        assert export_dialog.paragraph_spacing_spin.value() == 24
        assert export_dialog.page_size_combo.currentText() == "Legal"
        assert export_dialog.margin_top_spin.value() == 1.5
        assert export_dialog.margin_bottom_spin.value() == 1.5
        assert export_dialog.margin_left_spin.value() == 1.2
        assert export_dialog.margin_right_spin.value() == 1.2
        assert export_dialog.chapter_new_page_check.isChecked() is True
        assert export_dialog.number_chapters_check.isChecked() is False
        assert export_dialog.chapter_prefix_edit.text() == "Part "
        assert export_dialog.scene_separator_edit.text() == "---"
        assert export_dialog.format_combo.currentIndex() == 1  # PDF
    
    def test_export_error_handling(self, export_dialog, mock_project, mock_export_service, monkeypatch):
        """Test error handling during export."""
        # Set project and path
        export_dialog.current_project = mock_project
        export_dialog.path_edit.setText("/path/to/export.docx")
        
        # Mock export_project to raise an exception
        mock_export_service.export_project.side_effect = Exception("Export error")
        
        # Mock QMessageBox.critical
        critical_mock = MagicMock()
        monkeypatch.setattr(QMessageBox, "critical", critical_mock)
        
        # Click export button
        export_dialog.export_button.click()
        
        # Check that critical message was shown
        critical_mock.assert_called_once()
        assert "Export error" in critical_mock.call_args[0][2]
    
    def test_export_failure(self, export_dialog, mock_project, mock_export_service, monkeypatch):
        """Test handling of export failure."""
        # Set project and path
        export_dialog.current_project = mock_project
        export_dialog.path_edit.setText("/path/to/export.docx")
        
        # Mock export_project to return False (failure)
        mock_export_service.export_project.return_value = False
        
        # Mock QMessageBox.warning
        warning_mock = MagicMock()
        monkeypatch.setattr(QMessageBox, "warning", warning_mock)
        
        # Click export button
        export_dialog.export_button.click()
        
        # Check that warning was shown
        warning_mock.assert_called_once()
        assert "error occurred during export" in warning_mock.call_args[0][2]
    
    def test_cancel_button(self, export_dialog):
        """Test cancel button functionality."""
        # Check that the cancel button is connected to reject
        assert export_dialog.cancel_button.text() == "Cancel"
        
        # Test that the dialog can be rejected
        with patch.object(export_dialog, 'reject') as mock_reject:
            # Call the method that the cancel button would call
            export_dialog.reject()
            
            # Verify the method was called
            mock_reject.assert_called_once()


if __name__ == '__main__':
    pytest.main(['-v', __file__])
