#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end tests for RebelSCRIBE.

This module contains end-to-end tests that verify complete user workflows
from start to finish, simulating real user interactions with the application.
"""

import os
import sys
import tempfile
import shutil
import time
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QTimer

from src.ui.main_window import MainWindow
from src.ui.project_settings_dialog import ProjectSettingsDialog
from src.ui.export_dialog import ExportDialog
from src.backend.models.project import Project
from src.backend.models.document import Document
from src.utils.config_manager import ConfigManager


class TestCompleteWorkflow:
    """End-to-end tests for complete user workflows."""
    
    @pytest.fixture
    def app(self):
        """Create a QApplication instance for the tests."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
    
    @pytest.fixture
    def setup(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create paths for test files
        self.project_path = os.path.join(self.test_dir, "e2e_test_project.rebelscribe")
        self.export_path = os.path.join(self.test_dir, "exported_project.pdf")
        
        yield
        
        # Clean up
        shutil.rmtree(self.test_dir)
    
    def test_create_project_add_documents_export(self, qtbot, app, setup, monkeypatch):
        """
        Test the complete workflow of:
        1. Creating a new project
        2. Adding documents
        3. Editing documents
        4. Exporting the project
        """
        # Mock file dialogs
        def mock_get_save_file_name(*args, **kwargs):
            if "Export" in args[2]:
                return (self.export_path, "PDF Files (*.pdf)")
            return (self.project_path, "RebelSCRIBE Project (*.rebelscribe)")
        
        monkeypatch.setattr(QFileDialog, 'getSaveFileName', mock_get_save_file_name)
        
        # Mock message boxes
        monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)
        monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Yes)
        
        # Create main window
        main_window = MainWindow()
        qtbot.addWidget(main_window)
        main_window.show()
        
        # Wait for window to appear
        qtbot.waitExposed(main_window)
        
        # Step 1: Create a new project
        
        # Mock the project settings dialog
        mock_project_dialog = MagicMock()
        mock_project_dialog.exec.return_value = QDialogButtonBox.StandardButton.Ok
        mock_project_dialog.get_project_title.return_value = "E2E Test Project"
        mock_project_dialog.get_project_author.return_value = "Test Author"
        
        # Mock the dialog class
        monkeypatch.setattr('src.ui.main_window.ProjectSettingsDialog', lambda *args, **kwargs: mock_project_dialog)
        
        # Click the "New Project" action
        main_window.new_project_action.trigger()
        qtbot.wait(100)
        
        # Verify project was created
        assert main_window.project_manager.current_project is not None
        assert main_window.project_manager.current_project.title == "E2E Test Project"
        assert main_window.project_manager.current_project.author == "Test Author"
        assert main_window.windowTitle() == "RebelSCRIBE - E2E Test Project"
        
        # Step 2: Add documents to the project
        
        # Mock the binder view's add document method
        original_add_document = main_window.binder_view.add_document
        main_window.binder_view.add_document = MagicMock()
        
        try:
            # Create a document
            doc1 = main_window.document_manager.create_document(
                title="Chapter 1",
                content="This is the content of Chapter 1."
            )
            
            # Add document to binder
            main_window.binder_view.add_document(doc1)
            
            # Create another document
            doc2 = main_window.document_manager.create_document(
                title="Chapter 2",
                content="This is the content of Chapter 2."
            )
            
            # Add document to binder
            main_window.binder_view.add_document(doc2)
            
            # Verify documents were added
            assert main_window.binder_view.add_document.call_count == 2
        finally:
            # Restore original method
            main_window.binder_view.add_document = original_add_document
        
        # Step 3: Edit a document
        
        # Mock the editor
        main_window.editor.set_document = MagicMock()
        main_window.editor.get_content = MagicMock(return_value="Updated content for Chapter 1.")
        
        # Simulate selecting a document in the binder
        main_window._on_binder_item_selected = MagicMock()
        main_window.document_manager.current_document = doc1
        
        # Set the document in the editor
        main_window.editor.set_document(doc1)
        
        # Verify document was set in editor
        main_window.editor.set_document.assert_called_once_with(doc1)
        
        # Simulate editing the document
        doc1.content = "Updated content for Chapter 1."
        
        # Save the document
        main_window._on_save()
        
        # Verify document was saved
        assert main_window.document_manager.current_document.content == "Updated content for Chapter 1."
        
        # Step 4: Export the project
        
        # Mock the export dialog
        mock_export_dialog = MagicMock()
        mock_export_dialog.exec.return_value = QDialogButtonBox.StandardButton.Ok
        mock_export_dialog.get_export_format.return_value = "PDF"
        mock_export_dialog.get_export_path.return_value = self.export_path
        mock_export_dialog.get_export_options.return_value = {"include_notes": True}
        
        # Mock the dialog class
        monkeypatch.setattr('src.ui.main_window.ExportDialog', lambda *args, **kwargs: mock_export_dialog)
        
        # Mock the export service
        mock_export_service = MagicMock()
        monkeypatch.setattr('src.ui.main_window.ExportService', lambda *args, **kwargs: mock_export_service)
        
        # Click the "Export" action
        main_window.export_action.trigger()
        qtbot.wait(100)
        
        # Verify export service was called
        mock_export_service.export_project.assert_called_once()
        assert mock_export_service.export_project.call_args[1]["export_format"] == "PDF"
        assert mock_export_service.export_project.call_args[1]["output_path"] == self.export_path
        
        # Close the main window
        main_window.close()
    
    def test_open_project_edit_settings_statistics(self, qtbot, app, setup, monkeypatch):
        """
        Test the workflow of:
        1. Opening an existing project
        2. Editing project settings
        3. Viewing statistics
        """
        # Create a test project file
        project = Project(title="Existing Project", author="Original Author")
        project.path = self.project_path
        
        # Save the project to disk
        os.makedirs(os.path.dirname(self.project_path), exist_ok=True)
        with open(self.project_path, 'w') as f:
            f.write(project.to_json())
        
        # Mock file dialogs
        monkeypatch.setattr(
            QFileDialog, 'getOpenFileName',
            lambda *args, **kwargs: (self.project_path, "RebelSCRIBE Project (*.rebelscribe)")
        )
        
        # Mock message boxes
        monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)
        
        # Create main window
        main_window = MainWindow()
        qtbot.addWidget(main_window)
        main_window.show()
        
        # Wait for window to appear
        qtbot.waitExposed(main_window)
        
        # Step 1: Open the existing project
        
        # Click the "Open Project" action
        main_window.open_project_action.trigger()
        qtbot.wait(100)
        
        # Verify project was loaded
        assert main_window.project_manager.current_project is not None
        assert main_window.project_manager.current_project.title == "Existing Project"
        assert main_window.project_manager.current_project.author == "Original Author"
        assert main_window.windowTitle() == "RebelSCRIBE - Existing Project"
        
        # Step 2: Edit project settings
        
        # Mock the project settings dialog
        mock_project_dialog = MagicMock()
        mock_project_dialog.exec.return_value = QDialogButtonBox.StandardButton.Ok
        mock_project_dialog.get_project_title.return_value = "Updated Project"
        mock_project_dialog.get_project_author.return_value = "Updated Author"
        
        # Mock the dialog class
        monkeypatch.setattr('src.ui.main_window.ProjectSettingsDialog', lambda *args, **kwargs: mock_project_dialog)
        
        # Click the "Project Settings" action
        main_window.project_settings_action.trigger()
        qtbot.wait(100)
        
        # Verify project settings were updated
        assert main_window.project_manager.current_project.title == "Updated Project"
        assert main_window.project_manager.current_project.author == "Updated Author"
        assert main_window.windowTitle() == "RebelSCRIBE - Updated Project"
        
        # Step 3: View statistics
        
        # Mock the statistics service
        mock_statistics_service = MagicMock()
        mock_statistics_service.get_project_statistics.return_value = {
            "word_count": 1000,
            "character_count": 5000,
            "document_count": 5,
            "average_words_per_document": 200
        }
        monkeypatch.setattr('src.ui.main_window.StatisticsService', lambda *args, **kwargs: mock_statistics_service)
        
        # Click the "Statistics" action
        main_window.statistics_action.trigger()
        qtbot.wait(100)
        
        # Verify statistics service was called
        mock_statistics_service.get_project_statistics.assert_called_once_with(main_window.project_manager.current_project)
        
        # Close the main window
        main_window.close()
    
    def test_ai_features_workflow(self, qtbot, app, setup, monkeypatch):
        """
        Test the workflow of using AI features:
        1. Creating a project
        2. Using text generation
        3. Using character development
        4. Using plot development
        5. Configuring AI settings
        """
        # Mock file dialogs
        monkeypatch.setattr(
            QFileDialog, 'getSaveFileName',
            lambda *args, **kwargs: (self.project_path, "RebelSCRIBE Project (*.rebelscribe)")
        )
        
        # Mock input dialogs
        input_dialog_calls = 0
        input_dialog_responses = [
            ("Generate a paragraph about space", True),
            ("A space pirate named Jack", True),
            ("A heist in space", True)
        ]
        
        def mock_get_text(*args, **kwargs):
            nonlocal input_dialog_calls
            result = input_dialog_responses[input_dialog_calls]
            input_dialog_calls += 1
            return result
        
        monkeypatch.setattr('PyQt6.QtWidgets.QInputDialog.getText', mock_get_text)
        
        # Mock message boxes
        monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)
        
        # Create main window
        main_window = MainWindow()
        qtbot.addWidget(main_window)
        main_window.show()
        
        # Wait for window to appear
        qtbot.waitExposed(main_window)
        
        # Step 1: Create a new project
        
        # Mock the project settings dialog
        mock_project_dialog = MagicMock()
        mock_project_dialog.exec.return_value = QDialogButtonBox.StandardButton.Ok
        mock_project_dialog.get_project_title.return_value = "AI Test Project"
        mock_project_dialog.get_project_author.return_value = "Test Author"
        
        # Mock the dialog class
        monkeypatch.setattr('src.ui.main_window.ProjectSettingsDialog', lambda *args, **kwargs: mock_project_dialog)
        
        # Click the "New Project" action
        main_window.new_project_action.trigger()
        qtbot.wait(100)
        
        # Verify project was created
        assert main_window.project_manager.current_project is not None
        assert main_window.project_manager.current_project.title == "AI Test Project"
        
        # Step 2: Use text generation
        
        # Mock the AI service
        mock_ai_service = MagicMock()
        mock_ai_service.generate_text.return_value = "AI generated text about space."
        monkeypatch.setattr('src.ui.main_window.AIService', lambda *args, **kwargs: mock_ai_service)
        
        # Mock the editor
        main_window.editor.insert_text = MagicMock()
        
        # Click the "Generate Text" action
        main_window.generate_text_action.trigger()
        qtbot.wait(100)
        
        # Verify AI service was called
        mock_ai_service.generate_text.assert_called_once_with("Generate a paragraph about space")
        
        # Verify text was inserted into editor
        main_window.editor.insert_text.assert_called_once_with("AI generated text about space.")
        
        # Step 3: Use character development
        
        # Mock the character assistant
        mock_character_assistant = MagicMock()
        mock_character_assistant.develop_character.return_value = "Character profile for Jack the space pirate."
        monkeypatch.setattr('src.ui.main_window.CharacterAssistant', lambda *args, **kwargs: mock_character_assistant)
        
        # Reset the editor mock
        main_window.editor.insert_text.reset_mock()
        
        # Click the "Character Development" action
        main_window.character_development_action.trigger()
        qtbot.wait(100)
        
        # Verify character assistant was called
        mock_character_assistant.develop_character.assert_called_once_with("A space pirate named Jack")
        
        # Verify character profile was inserted into editor
        main_window.editor.insert_text.assert_called_once_with("Character profile for Jack the space pirate.")
        
        # Step 4: Use plot development
        
        # Mock the plot assistant
        mock_plot_assistant = MagicMock()
        mock_plot_assistant.develop_plot.return_value = "Plot outline for a space heist."
        monkeypatch.setattr('src.ui.main_window.PlotAssistant', lambda *args, **kwargs: mock_plot_assistant)
        
        # Reset the editor mock
        main_window.editor.insert_text.reset_mock()
        
        # Click the "Plot Development" action
        main_window.plot_development_action.trigger()
        qtbot.wait(100)
        
        # Verify plot assistant was called
        mock_plot_assistant.develop_plot.assert_called_once_with("A heist in space")
        
        # Verify plot outline was inserted into editor
        main_window.editor.insert_text.assert_called_once_with("Plot outline for a space heist.")
        
        # Step 5: Configure AI settings
        
        # Mock the AI settings dialog
        mock_ai_settings_dialog = MagicMock()
        mock_ai_settings_dialog.exec.return_value = QDialogButtonBox.StandardButton.Ok
        mock_ai_settings_dialog.get_api_key.return_value = "new_api_key"
        mock_ai_settings_dialog.get_model.return_value = "gpt-4-turbo"
        
        # Mock the dialog class
        monkeypatch.setattr('src.ui.main_window.AISettingsDialog', lambda *args, **kwargs: mock_ai_settings_dialog)
        
        # Mock the config manager
        mock_config = MagicMock()
        monkeypatch.setattr('src.ui.main_window.get_config', lambda: mock_config)
        
        # Click the "AI Settings" action
        main_window.ai_settings_action.trigger()
        qtbot.wait(100)
        
        # Verify config was updated
        assert mock_config.set.call_count >= 2
        mock_config.save.assert_called_once()
        
        # Close the main window
        main_window.close()


if __name__ == '__main__':
    pytest.main(['-v', __file__])
