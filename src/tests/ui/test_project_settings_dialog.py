#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Project Settings Dialog component.

This module contains tests for the Project Settings Dialog in the UI.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import pytest
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox, QListWidgetItem,
    QFileDialog, QMessageBox, QListWidget
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QFont, QColor

from src.ui.project_settings_dialog import ProjectSettingsDialog
from src.backend.models.project import Project
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
def mock_project():
    """Create a mock Project for testing."""
    project = MagicMock(spec=Project)
    project.title = "Test Project"
    project.author = "Test Author"
    project.description = "Test Description"
    project.path = "/path/to/project"
    
    # Mock metadata
    project.metadata = {
        "genre": "Fiction",
        "language": "English",
        "copyright": "2025",
        "publisher": "Test Publisher",
        "keywords": ["test", "project", "settings"],
        "structure": {
            "create_chapters": True,
            "create_characters": True,
            "create_locations": True,
            "create_research": True,
            "create_notes": True,
            "create_trash": True,
            "templates": {
                "chapter": "Basic Chapter",
                "character": "Basic Character",
                "location": "Basic Location"
            }
        },
        "compilation": {
            "include_title_page": True,
            "include_toc": True,
            "include_synopsis": False,
            "include_notes": False,
            "include_comments": False,
            "selected_documents": ["Chapter 1", "Chapter 2", "Chapter 3"]
        },
        "formatting": {
            "font_name": "Times New Roman",
            "font_size": 12,
            "line_spacing": "1.5 Lines",
            "paragraph_spacing": 12,
            "first_line_indent": 36,
            "page_size": "Letter",
            "margin": 1
        }
    }
    
    return project


@pytest.fixture
def project_settings_dialog(qtbot, mock_project):
    """Create a ProjectSettingsDialog instance for testing."""
    with patch('src.ui.project_settings_dialog.ConfigManager'):
        dialog = ProjectSettingsDialog(project=mock_project)
        qtbot.addWidget(dialog)
        return dialog


class TestProjectSettingsDialog:
    """Test cases for the ProjectSettingsDialog class."""
    
    def test_init(self, project_settings_dialog):
        """Test initialization of the project settings dialog."""
        # Check that components are created
        assert project_settings_dialog.tab_widget is not None
        assert project_settings_dialog.button_box is not None
        
        # Check tab widget
        assert project_settings_dialog.tab_widget.count() == 4
        assert project_settings_dialog.tab_widget.tabText(0) == "Metadata"
        assert project_settings_dialog.tab_widget.tabText(1) == "Structure"
        assert project_settings_dialog.tab_widget.tabText(2) == "Compilation"
        assert project_settings_dialog.tab_widget.tabText(3) == "Formatting"
        
        # Check metadata tab components
        assert project_settings_dialog.title_edit is not None
        assert project_settings_dialog.author_edit is not None
        assert project_settings_dialog.description_edit is not None
        assert project_settings_dialog.genre_edit is not None
        assert project_settings_dialog.language_combo is not None
        assert project_settings_dialog.copyright_edit is not None
        assert project_settings_dialog.publisher_edit is not None
        assert project_settings_dialog.keywords_edit is not None
        
        # Check structure tab components
        assert project_settings_dialog.create_chapters_check is not None
        assert project_settings_dialog.create_characters_check is not None
        assert project_settings_dialog.create_locations_check is not None
        assert project_settings_dialog.create_research_check is not None
        assert project_settings_dialog.create_notes_check is not None
        assert project_settings_dialog.create_trash_check is not None
        assert project_settings_dialog.chapter_template_combo is not None
        assert project_settings_dialog.character_template_combo is not None
        assert project_settings_dialog.location_template_combo is not None
        assert project_settings_dialog.location_edit is not None
        assert project_settings_dialog.location_button is not None
        
        # Check compilation tab components
        assert project_settings_dialog.include_title_page_check is not None
        assert project_settings_dialog.include_toc_check is not None
        assert project_settings_dialog.include_synopsis_check is not None
        assert project_settings_dialog.include_notes_check is not None
        assert project_settings_dialog.include_comments_check is not None
        assert project_settings_dialog.documents_list is not None
        assert project_settings_dialog.select_all_button is not None
        assert project_settings_dialog.deselect_all_button is not None
        
        # Check formatting tab components
        assert project_settings_dialog.font_combo is not None
        assert project_settings_dialog.font_size_spin is not None
        assert project_settings_dialog.line_spacing_combo is not None
        assert project_settings_dialog.paragraph_spacing_spin is not None
        assert project_settings_dialog.first_line_indent_spin is not None
        assert project_settings_dialog.page_size_combo is not None
        assert project_settings_dialog.margin_spin is not None
    
    def test_load_settings(self, project_settings_dialog, mock_project):
        """Test loading project settings."""
        # Check that settings were loaded
        assert project_settings_dialog.title_edit.text() == "Test Project"
        assert project_settings_dialog.author_edit.text() == "Test Author"
        assert project_settings_dialog.description_edit.toPlainText() == "Test Description"
        assert project_settings_dialog.genre_edit.text() == "Fiction"
        assert project_settings_dialog.language_combo.currentText() == "English"
        assert project_settings_dialog.copyright_edit.text() == "2025"
        assert project_settings_dialog.publisher_edit.text() == "Test Publisher"
        assert project_settings_dialog.keywords_edit.text() == "test, project, settings"
        
        assert project_settings_dialog.create_chapters_check.isChecked() is True
        assert project_settings_dialog.create_characters_check.isChecked() is True
        assert project_settings_dialog.create_locations_check.isChecked() is True
        assert project_settings_dialog.create_research_check.isChecked() is True
        assert project_settings_dialog.create_notes_check.isChecked() is True
        assert project_settings_dialog.create_trash_check.isChecked() is True
        
        assert project_settings_dialog.chapter_template_combo.currentText() == "Basic Chapter"
        assert project_settings_dialog.character_template_combo.currentText() == "Basic Character"
        assert project_settings_dialog.location_template_combo.currentText() == "Basic Location"
        
        assert project_settings_dialog.location_edit.text() == "/path/to/project"
        
        assert project_settings_dialog.include_title_page_check.isChecked() is True
        assert project_settings_dialog.include_toc_check.isChecked() is True
        assert project_settings_dialog.include_synopsis_check.isChecked() is False
        assert project_settings_dialog.include_notes_check.isChecked() is False
        assert project_settings_dialog.include_comments_check.isChecked() is False
        
        assert project_settings_dialog.font_combo.currentText() == "Times New Roman"
        assert project_settings_dialog.font_size_spin.value() == 12
        assert project_settings_dialog.line_spacing_combo.currentText() == "1.5 Lines"
        assert project_settings_dialog.paragraph_spacing_spin.value() == 12
        assert project_settings_dialog.first_line_indent_spin.value() == 36
        assert project_settings_dialog.page_size_combo.currentText() == "Letter"
        assert project_settings_dialog.margin_spin.value() == 1
    
    def test_get_current_settings(self, project_settings_dialog):
        """Test getting current settings."""
        # Modify some settings
        project_settings_dialog.title_edit.setText("Modified Project")
        project_settings_dialog.genre_edit.setText("Science Fiction")
        project_settings_dialog.create_research_check.setChecked(False)
        project_settings_dialog.chapter_template_combo.setCurrentText("Chapter with Synopsis")
        project_settings_dialog.include_synopsis_check.setChecked(True)
        project_settings_dialog.font_size_spin.setValue(14)
        
        # Get current settings
        settings = project_settings_dialog._get_current_settings()
        
        # Check settings
        assert settings["title"] == "Modified Project"
        assert settings["metadata"]["genre"] == "Science Fiction"
        assert settings["metadata"]["structure"]["create_research"] is False
        assert settings["metadata"]["structure"]["templates"]["chapter"] == "Chapter with Synopsis"
        assert settings["metadata"]["compilation"]["include_synopsis"] is True
        assert settings["metadata"]["formatting"]["font_size"] == 14
    
    def test_save_settings(self, project_settings_dialog, mock_project):
        """Test saving settings."""
        # Modify some settings
        project_settings_dialog.title_edit.setText("Modified Project")
        project_settings_dialog.genre_edit.setText("Science Fiction")
        project_settings_dialog.create_research_check.setChecked(False)
        project_settings_dialog.chapter_template_combo.setCurrentText("Chapter with Synopsis")
        project_settings_dialog.include_synopsis_check.setChecked(True)
        project_settings_dialog.font_size_spin.setValue(14)
        
        # Mock settings_changed signal
        project_settings_dialog.settings_changed = MagicMock()
        
        # Save settings
        result = project_settings_dialog._save_settings()
        
        # Check result
        assert result is True
        
        # Check that project was updated
        assert mock_project.title == "Modified Project"
        assert mock_project.metadata["genre"] == "Science Fiction"
        assert mock_project.metadata["structure"]["create_research"] is False
        assert mock_project.metadata["structure"]["templates"]["chapter"] == "Chapter with Synopsis"
        assert mock_project.metadata["compilation"]["include_synopsis"] is True
        assert mock_project.metadata["formatting"]["font_size"] == 14
        
        # Check that settings_changed signal was emitted
        project_settings_dialog.settings_changed.emit.assert_called_once()
    
    def test_on_accept(self, qtbot, project_settings_dialog):
        """Test accept button clicked."""
        # Mock _save_settings
        project_settings_dialog._save_settings = MagicMock(return_value=True)
        
        # Mock accept
        project_settings_dialog.accept = MagicMock()
        
        # Click OK button
        qtbot.mouseClick(project_settings_dialog.button_box.button(QDialogButtonBox.StandardButton.Ok), Qt.MouseButton.LeftButton)
        
        # Check that _save_settings was called
        project_settings_dialog._save_settings.assert_called_once()
        
        # Check that accept was called
        project_settings_dialog.accept.assert_called_once()
    
    def test_on_apply(self, qtbot, project_settings_dialog):
        """Test apply button clicked."""
        # Mock _save_settings
        project_settings_dialog._save_settings = MagicMock(return_value=True)
        
        # Click Apply button
        qtbot.mouseClick(project_settings_dialog.button_box.button(QDialogButtonBox.StandardButton.Apply), Qt.MouseButton.LeftButton)
        
        # Check that _save_settings was called
        project_settings_dialog._save_settings.assert_called_once()
    
    def test_on_change_location(self, project_settings_dialog, monkeypatch):
        """Test change location button clicked."""
        # Mock QFileDialog.getExistingDirectory to return a directory
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: "/new/project/path")
        
        # Mock QMessageBox.question to return Yes
        monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        
        # Click change location button
        project_settings_dialog.location_button.click()
        
        # Check that location edit was updated
        assert project_settings_dialog.location_edit.text() == "/new/project/path"
        
        # Check that project path was updated
        assert project_settings_dialog.project.path == "/new/project/path"
    
    def test_on_change_location_cancelled(self, project_settings_dialog, monkeypatch):
        """Test change location button clicked but cancelled."""
        # Mock QFileDialog.getExistingDirectory to return an empty string (cancelled)
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: "")
        
        # Store original path
        original_path = project_settings_dialog.location_edit.text()
        
        # Click change location button
        project_settings_dialog.location_button.click()
        
        # Check that location edit was not updated
        assert project_settings_dialog.location_edit.text() == original_path
    
    def test_on_change_location_declined(self, project_settings_dialog, monkeypatch):
        """Test change location button clicked but user declined confirmation."""
        # Mock QFileDialog.getExistingDirectory to return a directory
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: "/new/project/path")
        
        # Mock QMessageBox.question to return No
        monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.No)
        
        # Store original path
        original_path = project_settings_dialog.location_edit.text()
        
        # Click change location button
        project_settings_dialog.location_button.click()
        
        # Check that location edit was reverted
        assert project_settings_dialog.location_edit.text() == original_path
        
        # Check that project path was not updated
        assert project_settings_dialog.project.path == original_path
    
    def test_on_select_all(self, project_settings_dialog):
        """Test select all button clicked."""
        # Add some items to the documents list
        for i in range(3):
            item = QListWidgetItem(f"Item {i}")
            item.setCheckState(Qt.CheckState.Unchecked)
            project_settings_dialog.documents_list.addItem(item)
        
        # Click select all button
        project_settings_dialog.select_all_button.click()
        
        # Check that all items are checked
        for i in range(project_settings_dialog.documents_list.count()):
            assert project_settings_dialog.documents_list.item(i).checkState() == Qt.CheckState.Checked
    
    def test_on_deselect_all(self, project_settings_dialog):
        """Test deselect all button clicked."""
        # Add some items to the documents list
        for i in range(3):
            item = QListWidgetItem(f"Item {i}")
            item.setCheckState(Qt.CheckState.Checked)
            project_settings_dialog.documents_list.addItem(item)
        
        # Click deselect all button
        project_settings_dialog.deselect_all_button.click()
        
        # Check that all items are unchecked
        for i in range(project_settings_dialog.documents_list.count()):
            assert project_settings_dialog.documents_list.item(i).checkState() == Qt.CheckState.Unchecked
    
    def test_set_project(self, project_settings_dialog):
        """Test setting project."""
        # Create a new mock project
        new_project = MagicMock(spec=Project)
        new_project.title = "New Project"
        new_project.author = "New Author"
        new_project.description = "New Description"
        new_project.metadata = {}
        
        # Set the new project
        project_settings_dialog.set_project(new_project)
        
        # Check that project was set
        assert project_settings_dialog.project == new_project
        assert project_settings_dialog.title_edit.text() == "New Project"
        assert project_settings_dialog.author_edit.text() == "New Author"
        assert project_settings_dialog.description_edit.toPlainText() == "New Description"
    
    def test_save_settings_no_project(self, project_settings_dialog, monkeypatch):
        """Test saving settings with no project."""
        # Set project to None
        project_settings_dialog.project = None
        
        # Mock QMessageBox.warning
        warning_mock = MagicMock()
        monkeypatch.setattr(QMessageBox, "warning", warning_mock)
        
        # Save settings
        result = project_settings_dialog._save_settings()
        
        # Check result
        assert result is False
        
        # Check that warning was shown
        warning_mock.assert_called_once()
        assert "No project provided" in warning_mock.call_args[0][2]
    
    def test_save_settings_exception(self, project_settings_dialog, mock_project, monkeypatch):
        """Test saving settings with an exception."""
        # Mock _get_current_settings to raise an exception
        project_settings_dialog._get_current_settings = MagicMock(side_effect=Exception("Test exception"))
        
        # Mock QMessageBox.warning
        warning_mock = MagicMock()
        monkeypatch.setattr(QMessageBox, "warning", warning_mock)
        
        # Save settings
        result = project_settings_dialog._save_settings()
        
        # Check result
        assert result is False
        
        # Check that warning was shown
        warning_mock.assert_called_once()
        assert "Test exception" in warning_mock.call_args[0][2]
    
    def test_load_settings_exception(self, mock_project, monkeypatch, qtbot):
        """Test loading settings with an exception."""
        # Mock QMessageBox.warning
        warning_mock = MagicMock()
        monkeypatch.setattr(QMessageBox, "warning", warning_mock)
        
        # Create a project that will cause an exception during loading
        bad_project = MagicMock(spec=Project)
        bad_project.title = "Bad Project"
        bad_project.author = "Bad Author"
        bad_project.description = "Bad Description"
        
        # Create a property that raises an exception when accessed
        def metadata_property_raiser(self):
            raise Exception("Test exception")
            
        type(bad_project).metadata = property(metadata_property_raiser)
        
        # Create dialog with bad project
        with patch('src.ui.project_settings_dialog.ConfigManager'):
            dialog = ProjectSettingsDialog(project=bad_project)
            qtbot.addWidget(dialog)
        
        # Check that warning was shown
        warning_mock.assert_called_once()
        assert "Test exception" in warning_mock.call_args[0][2]
    
    def test_keywords_handling(self, project_settings_dialog):
        """Test handling of keywords."""
        # Set keywords
        project_settings_dialog.keywords_edit.setText("fiction, novel, fantasy, adventure")
        
        # Get current settings
        settings = project_settings_dialog._get_current_settings()
        
        # Check that keywords were parsed correctly
        assert settings["metadata"]["keywords"] == ["fiction", "novel", "fantasy", "adventure"]
        
        # Set empty keywords
        project_settings_dialog.keywords_edit.setText("")
        
        # Get current settings
        settings = project_settings_dialog._get_current_settings()
        
        # Check that keywords are empty
        assert settings["metadata"]["keywords"] == []


if __name__ == '__main__':
    pytest.main(['-v', __file__])
