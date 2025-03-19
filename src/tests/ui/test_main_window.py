#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Main Window.

This module contains tests for the MainWindow class.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pytest
from PyQt6.QtWidgets import QApplication, QMainWindow, QDockWidget, QToolBar, QStatusBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSize, QSettings

from src.ui.main_window import MainWindow


@pytest.fixture
def app():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to clean up as we're not destroying the app


@pytest.fixture
def main_window(qtbot, monkeypatch):
    """Create a MainWindow instance for testing."""
    # Mock QSettings to avoid affecting real settings
    monkeypatch.setattr(QSettings, 'value', lambda *args: None)
    
    # Mock ConfigManager to avoid loading real config
    mock_config = MagicMock()
    # Set up specific returns for different get calls
    mock_config.get.side_effect = lambda section, key=None, default=None: {
        "application": {
            "data_directory": "/tmp"
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
    
    # Mock QApplication to avoid creating a real application
    with patch('src.ui.main_window.QApplication'):
        window = MainWindow()
        qtbot.addWidget(window)
        return window


class TestMainWindow:
    """Test cases for the MainWindow class."""
    
    def test_init(self, main_window):
        """Test initialization of the main window."""
        # Check window properties
        assert main_window.windowTitle() == "RebelSCRIBE"
        assert main_window.minimumSize().width() >= 1024
        assert main_window.minimumSize().height() >= 768
        
        # Check central widget and splitter
        assert main_window.central_splitter is not None
        assert main_window.central_splitter.count() == 3
        
        # Check UI components
        assert main_window.binder_view is not None
        assert main_window.editor is not None
        assert main_window.inspector is not None
        
        # Check status bar
        assert main_window.status_bar is not None
        assert main_window.status_bar.currentMessage() == "Ready"
    
    def test_menu_bar(self, main_window):
        """Test the menu bar."""
        # Check that all menus exist
        assert main_window.file_menu is not None
        assert main_window.edit_menu is not None
        assert main_window.view_menu is not None
        assert main_window.project_menu is not None
        assert main_window.ai_menu is not None
        assert main_window.help_menu is not None
        
        # Check file menu actions
        file_actions = [action.text() for action in main_window.file_menu.actions()]
        assert "&New Project..." in file_actions
        assert "&Open Project..." in file_actions
        assert "&Save" in file_actions
        assert "Save &As..." in file_actions
        assert "&Export..." in file_actions
        assert "E&xit" in file_actions
        
        # Check edit menu actions
        edit_actions = [action.text() for action in main_window.edit_menu.actions()]
        assert "&Undo" in edit_actions
        assert "&Redo" in edit_actions
        assert "Cu&t" in edit_actions
        assert "&Copy" in edit_actions
        assert "&Paste" in edit_actions
        assert "&Find..." in edit_actions
        assert "&Replace..." in edit_actions
        
        # Check view menu actions
        view_actions = [action.text() for action in main_window.view_menu.actions()]
        assert "Show &Binder" in view_actions
        assert "Show &Inspector" in view_actions
        assert "&Distraction Free Mode" in view_actions
        
        # Check project menu actions
        project_actions = [action.text() for action in main_window.project_menu.actions()]
        assert "&Settings..." in project_actions
        assert "St&atistics..." in project_actions
        
        # Check AI menu actions
        ai_actions = [action.text() for action in main_window.ai_menu.actions()]
        assert "&Generate Text..." in ai_actions
        assert "&Character Development..." in ai_actions
        assert "&Plot Development..." in ai_actions
        assert "&Settings..." in ai_actions
        
        # Check help menu actions
        help_actions = [action.text() for action in main_window.help_menu.actions()]
        assert "&About RebelSCRIBE" in help_actions
    
    def test_toolbar(self, main_window):
        """Test the toolbar."""
        # Check that toolbar exists
        assert main_window.toolbar is not None
        
        # Check toolbar properties
        assert not main_window.toolbar.isMovable()
        assert main_window.toolbar.iconSize() == QSize(16, 16)
        
        # Check toolbar actions
        toolbar_actions = [action.text() for action in main_window.toolbar.actions() if isinstance(action, QAction)]
        assert "New Project" in toolbar_actions
        assert "Open Project" in toolbar_actions
        assert "Save" in toolbar_actions
        assert "Cut" in toolbar_actions
        assert "Copy" in toolbar_actions
        assert "Paste" in toolbar_actions
        assert "Find" in toolbar_actions
    
    def test_layout(self, main_window):
        """Test the layout of the main window."""
        # Check splitter sizes
        sizes = main_window.central_splitter.sizes()
        assert len(sizes) == 3
        
        # Check that components exist in the splitter
        assert main_window.binder_view is not None
        assert main_window.editor is not None
        assert main_window.inspector is not None
    
    def test_toggle_binder(self, qtbot, main_window):
        """Test toggling the binder visibility."""
        # Mock the setVisible method
        original_set_visible = main_window.binder_view.setVisible
        main_window.binder_view.setVisible = MagicMock()
        
        try:
            # Toggle off
            main_window.toggle_binder_action.setChecked(False)
            main_window._on_toggle_binder(False)
            
            # Check that setVisible was called with False
            main_window.binder_view.setVisible.assert_called_with(False)
            
            # Toggle on
            main_window.toggle_binder_action.setChecked(True)
            main_window._on_toggle_binder(True)
            
            # Check that setVisible was called with True
            main_window.binder_view.setVisible.assert_called_with(True)
        finally:
            # Restore original method
            main_window.binder_view.setVisible = original_set_visible
    
    def test_toggle_inspector(self, qtbot, main_window):
        """Test toggling the inspector visibility."""
        # Mock the setVisible method
        original_set_visible = main_window.inspector.setVisible
        main_window.inspector.setVisible = MagicMock()
        
        try:
            # Toggle off
            main_window.toggle_inspector_action.setChecked(False)
            main_window._on_toggle_inspector(False)
            
            # Check that setVisible was called with False
            main_window.inspector.setVisible.assert_called_with(False)
            
            # Toggle on
            main_window.toggle_inspector_action.setChecked(True)
            main_window._on_toggle_inspector(True)
            
            # Check that setVisible was called with True
            main_window.inspector.setVisible.assert_called_with(True)
        finally:
            # Restore original method
            main_window.inspector.setVisible = original_set_visible
    
    @patch('src.ui.main_window.DistractionFreeMode')
    def test_distraction_free_mode(self, mock_distraction_free_mode, qtbot, main_window):
        """Test entering distraction-free mode."""
        # Mock editor
        main_window.editor = MagicMock()
        main_window.editor.get_content.return_value = "Test content"
        main_window.editor.current_document = MagicMock()
        main_window.editor.current_document.title = "Test Document"
        
        # Mock distraction-free mode window
        mock_instance = mock_distraction_free_mode.return_value
        
        # Trigger distraction-free mode
        main_window._on_distraction_free()
        
        # Check that distraction-free mode was created
        mock_distraction_free_mode.assert_called_once_with(
            parent=main_window,
            content="Test content",
            document_title="Test Document"
        )
        
        # Check that closed signal was connected
        mock_instance.closed.connect.assert_called_once()
        
        # Check that window was shown
        mock_instance.show.assert_called_once()
    
    def test_distraction_free_mode_no_editor(self, qtbot, main_window):
        """Test entering distraction-free mode with no editor."""
        # Ensure no editor
        if hasattr(main_window, 'editor'):
            delattr(main_window, 'editor')
        
        # Trigger distraction-free mode
        main_window._on_distraction_free()
        
        # Check status bar message
        assert "Cannot enter distraction-free mode" in main_window.status_bar.currentMessage()
    
    def test_distraction_free_closed(self, qtbot, main_window):
        """Test handling distraction-free mode closed."""
        # Mock editor
        main_window.editor = MagicMock()
        
        # Call distraction-free closed handler
        main_window._on_distraction_free_closed("Updated content")
        
        # Check that editor content was updated
        main_window.editor.set_content.assert_called_once_with("Updated content")
        
        # Check status bar message
        assert "Exited distraction-free mode" in main_window.status_bar.currentMessage()
    
    @patch('src.ui.main_window.QMessageBox')
    def test_about(self, mock_message_box, qtbot, main_window):
        """Test the about dialog."""
        # Trigger about action
        main_window._on_about()
        
        # Check that message box was shown
        mock_message_box.about.assert_called_once()
        assert "About RebelSCRIBE" in mock_message_box.about.call_args[0][1]
    
    def test_save_settings(self, monkeypatch, main_window):
        """Test saving settings."""
        # Mock QSettings
        mock_settings = MagicMock()
        monkeypatch.setattr('src.ui.main_window.QSettings', lambda: mock_settings)
        
        # Call save settings
        main_window._save_settings()
        
        # Check that settings were saved
        assert mock_settings.setValue.call_count == 3
        mock_settings.setValue.assert_any_call("geometry", main_window.saveGeometry())
        mock_settings.setValue.assert_any_call("windowState", main_window.saveState())
        mock_settings.setValue.assert_any_call("splitterSizes", main_window.central_splitter.sizes())
    
    def test_load_settings(self, monkeypatch, main_window):
        """Test loading settings."""
        # Mock QSettings
        mock_settings = MagicMock()
        mock_settings.value.side_effect = [b'geometry', b'state', [100, 200, 300]]
        monkeypatch.setattr('src.ui.main_window.QSettings', lambda: mock_settings)
        
        # Mock restore methods
        main_window.restoreGeometry = MagicMock()
        main_window.restoreState = MagicMock()
        main_window.central_splitter.setSizes = MagicMock()
        
        # Call load settings
        main_window._load_settings()
        
        # Check that settings were loaded
        main_window.restoreGeometry.assert_called_once_with(b'geometry')
        main_window.restoreState.assert_called_once_with(b'state')
        main_window.central_splitter.setSizes.assert_called_once_with([100, 200, 300])
    
    def test_close_event(self, qtbot, main_window):
        """Test handling close event."""
        # Mock save settings
        main_window._save_settings = MagicMock()
        
        # Create mock event
        event = MagicMock()
        
        # Call close event handler
        main_window.closeEvent(event)
        
        # Check that settings were saved
        main_window._save_settings.assert_called_once()
        
        # Check that event was accepted
        event.accept.assert_called_once()
    
    def test_binder_item_selected(self, qtbot, main_window):
        """Test handling binder item selection."""
        # Create mock item
        item = MagicMock()
        item.text.return_value = "Test Item"
        
        # Call binder item selected handler
        main_window._on_binder_item_selected(item)
        
        # Check status bar message
        assert "Selected: Test Item" in main_window.status_bar.currentMessage()


if __name__ == '__main__':
    pytest.main(['-v', __file__])
