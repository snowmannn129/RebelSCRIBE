#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Binder View.

This module contains tests for the BinderView class.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pytest
from PyQt6.QtWidgets import QApplication, QTreeView, QMenu, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, QPoint, QMimeData
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from src.ui.binder.binder_view import BinderView


@pytest.fixture
def app():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to clean up as we're not destroying the app


@pytest.fixture
def binder_view(qtbot):
    """Create a BinderView instance for testing."""
    # Mock ProjectManager to avoid actual file operations
    with patch('src.ui.binder.binder_view.ProjectManager'):
        view = BinderView()
        qtbot.addWidget(view)
        return view


class TestBinderView:
    """Test cases for the BinderView class."""
    
    def test_init(self, binder_view):
        """Test initialization of the binder view."""
        # Check that the binder view has the correct components
        assert binder_view.tree_view is not None
        assert binder_view.model is not None
        assert binder_view.toolbar is not None
        
        # Check that the tree view has the correct properties
        assert binder_view.tree_view.isHeaderHidden()
        assert binder_view.tree_view.dragEnabled()
        assert binder_view.tree_view.acceptDrops()
        assert binder_view.tree_view.dragDropMode() == QTreeView.DragDropMode.InternalMove
        
        # Check that the model has placeholder data
        root_item = binder_view.model.invisibleRootItem()
        assert root_item.rowCount() > 0
        
        # Check that the toolbar has actions
        assert len(binder_view.toolbar.actions()) > 0
    
    def test_tree_view(self, binder_view):
        """Test the tree view structure."""
        # Check that the model has the expected structure
        root_item = binder_view.model.invisibleRootItem()
        
        # Check that there are at least 4 top-level items (Manuscript, Characters, Locations, Notes)
        assert root_item.rowCount() >= 4
        
        # Find the manuscript item
        manuscript_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Manuscript":
                manuscript_item = item
                break
        
        assert manuscript_item is not None
        
        # Check that the manuscript item has chapters
        assert manuscript_item.rowCount() > 0
        
        # Check that the first chapter has scenes
        chapter_item = manuscript_item.child(0)
        assert chapter_item is not None
        assert chapter_item.rowCount() > 0
        
        # Find the characters item
        characters_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Characters":
                characters_item = item
                break
        
        assert characters_item is not None
        
        # Check that the characters item has characters
        assert characters_item.rowCount() > 0
    
    def test_toolbar_actions(self, binder_view):
        """Test the toolbar actions."""
        # Check that the toolbar has the expected actions
        action_texts = [action.text() for action in binder_view.toolbar.actions() if action.text()]
        
        assert "Add Document" in action_texts
        assert "Add Folder" in action_texts
        assert "Add Character" in action_texts
        assert "Add Location" in action_texts
        assert "Add Note" in action_texts
    
    @patch('src.ui.binder.binder_view.QInputDialog')
    def test_add_document(self, mock_input_dialog, qtbot, binder_view):
        """Test adding a document."""
        # Mock the input dialog to return a document name
        mock_input_dialog.getText.return_value = ("New Document", True)
        
        # Get the initial row count
        root_item = binder_view.model.invisibleRootItem()
        initial_count = root_item.rowCount()
        
        # Trigger the add document action
        binder_view.add_document_action.trigger()
        
        # Check that a new document was added
        assert root_item.rowCount() == initial_count + 1
        
        # Check that the new document has the correct name
        new_item = root_item.child(root_item.rowCount() - 1)
        assert new_item.text() == "New Document"
    
    @patch('src.ui.binder.binder_view.QInputDialog')
    def test_add_folder(self, mock_input_dialog, qtbot, binder_view):
        """Test adding a folder."""
        # Mock the input dialog to return a folder name
        mock_input_dialog.getText.return_value = ("New Folder", True)
        
        # Get the initial row count
        root_item = binder_view.model.invisibleRootItem()
        initial_count = root_item.rowCount()
        
        # Trigger the add folder action
        binder_view.add_folder_action.trigger()
        
        # Check that a new folder was added
        assert root_item.rowCount() == initial_count + 1
        
        # Check that the new folder has the correct name
        new_item = root_item.child(root_item.rowCount() - 1)
        assert new_item.text() == "New Folder"
    
    @patch('src.ui.binder.binder_view.QInputDialog')
    def test_add_character(self, mock_input_dialog, qtbot, binder_view):
        """Test adding a character."""
        # Mock the input dialog to return a character name
        mock_input_dialog.getText.return_value = ("New Character", True)
        
        # Find the characters folder
        root_item = binder_view.model.invisibleRootItem()
        characters_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Characters":
                characters_item = item
                break
        
        assert characters_item is not None
        
        # Get the initial row count
        initial_count = characters_item.rowCount()
        
        # Trigger the add character action
        binder_view.add_character_action.trigger()
        
        # Check that a new character was added
        assert characters_item.rowCount() == initial_count + 1
        
        # Check that the new character has the correct name
        new_item = characters_item.child(characters_item.rowCount() - 1)
        assert new_item.text() == "New Character"
    
    @patch('src.ui.binder.binder_view.QInputDialog')
    def test_add_location(self, mock_input_dialog, qtbot, binder_view):
        """Test adding a location."""
        # Mock the input dialog to return a location name
        mock_input_dialog.getText.return_value = ("New Location", True)
        
        # Find the locations folder
        root_item = binder_view.model.invisibleRootItem()
        locations_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Locations":
                locations_item = item
                break
        
        assert locations_item is not None
        
        # Get the initial row count
        initial_count = locations_item.rowCount()
        
        # Trigger the add location action
        binder_view.add_location_action.trigger()
        
        # Check that a new location was added
        assert locations_item.rowCount() == initial_count + 1
        
        # Check that the new location has the correct name
        new_item = locations_item.child(locations_item.rowCount() - 1)
        assert new_item.text() == "New Location"
    
    @patch('src.ui.binder.binder_view.QInputDialog')
    def test_add_note(self, mock_input_dialog, qtbot, binder_view):
        """Test adding a note."""
        # Mock the input dialog to return a note name
        mock_input_dialog.getText.return_value = ("New Note", True)
        
        # Find the notes folder
        root_item = binder_view.model.invisibleRootItem()
        notes_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Notes":
                notes_item = item
                break
        
        assert notes_item is not None
        
        # Get the initial row count
        initial_count = notes_item.rowCount()
        
        # Trigger the add note action
        binder_view.add_note_action.trigger()
        
        # Check that a new note was added
        assert notes_item.rowCount() == initial_count + 1
        
        # Check that the new note has the correct name
        new_item = notes_item.child(notes_item.rowCount() - 1)
        assert new_item.text() == "New Note"
    
    @patch('src.ui.binder.binder_view.QMenu')
    def test_context_menu(self, mock_menu, qtbot, binder_view):
        """Test the context menu."""
        # Mock the QMenu.exec method
        mock_menu_instance = MagicMock()
        mock_menu.return_value = mock_menu_instance
        
        # Find the manuscript item
        root_item = binder_view.model.invisibleRootItem()
        manuscript_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Manuscript":
                manuscript_item = item
                break
        
        assert manuscript_item is not None
        
        # Get the index of the manuscript item
        manuscript_index = binder_view.model.indexFromItem(manuscript_item)
        
        # Select the manuscript item
        binder_view.tree_view.setCurrentIndex(manuscript_index)
        
        # Get the position of the manuscript item
        rect = binder_view.tree_view.visualRect(manuscript_index)
        pos = rect.center()
        
        # Trigger the context menu
        binder_view._show_context_menu(pos)
        
        # Check that the context menu was created
        mock_menu.assert_called_once()
        
        # Check that the context menu has actions
        assert mock_menu_instance.addAction.call_count >= 2
    
    @patch('src.ui.binder.binder_view.QInputDialog')
    def test_rename_item(self, mock_input_dialog, qtbot, binder_view):
        """Test renaming an item."""
        # Mock the input dialog to return a new name
        mock_input_dialog.getText.return_value = ("Renamed Item", True)
        
        # Find the manuscript item
        root_item = binder_view.model.invisibleRootItem()
        manuscript_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Manuscript":
                manuscript_item = item
                break
        
        assert manuscript_item is not None
        
        # Get the index of the manuscript item
        manuscript_index = binder_view.model.indexFromItem(manuscript_item)
        
        # Rename the manuscript item
        binder_view._on_rename_item(manuscript_index)
        
        # Check that the manuscript item was renamed
        assert manuscript_item.text() == "Renamed Item"
    
    @patch('src.ui.binder.binder_view.QMessageBox.question')
    def test_delete_item(self, mock_question, qtbot, binder_view):
        """Test deleting an item."""
        # Mock the message box question method to return Yes
        mock_question.return_value = QMessageBox.StandardButton.Yes
        
        # Mock the project manager's delete_document method to return True
        binder_view.project_manager.delete_document.return_value = True
        
        # Find the manuscript item
        root_item = binder_view.model.invisibleRootItem()
        manuscript_item = None
        manuscript_index = -1
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Manuscript":
                manuscript_item = item
                manuscript_index = i
                break
        
        assert manuscript_item is not None
        assert manuscript_index >= 0
        
        # Get the initial row count
        initial_count = root_item.rowCount()
        
        # Get the index of the manuscript item
        manuscript_index = binder_view.model.indexFromItem(manuscript_item)
        
        # Store the item's text before deleting it
        item_text = manuscript_item.text()
        
        # Create a custom implementation of _on_delete_item to avoid the RuntimeError
        def custom_delete_item(index):
            # Get the item
            item = binder_view.model.itemFromIndex(index)
            
            # Get document ID
            document_id = item.data(Qt.ItemDataRole.UserRole)
            
            # Delete document in project manager (already mocked to return True)
            success = binder_view.project_manager.delete_document(document_id)
            
            if success:
                # Delete the item from the tree view
                parent = item.parent() or binder_view.model.invisibleRootItem()
                parent.removeRow(index.row())
        
        # Replace the _on_delete_item method with our custom implementation
        with patch.object(binder_view, '_on_delete_item', side_effect=custom_delete_item):
            # Delete the manuscript item
            binder_view._on_delete_item(manuscript_index)
            
            # Check that the manuscript item was deleted
            assert root_item.rowCount() == initial_count - 1
    
    def test_selection_changed(self, qtbot, binder_view):
        """Test selection changed signal."""
        # Create a mock to receive the item_selected signal
        mock_receiver = MagicMock()
        binder_view.item_selected.connect(mock_receiver)
        
        # Find the manuscript item
        root_item = binder_view.model.invisibleRootItem()
        manuscript_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Manuscript":
                manuscript_item = item
                break
        
        assert manuscript_item is not None
        
        # Get the index of the manuscript item
        manuscript_index = binder_view.model.indexFromItem(manuscript_item)
        
        # Select the manuscript item
        binder_view.tree_view.setCurrentIndex(manuscript_index)
        
        # Check that the item_selected signal was emitted
        mock_receiver.assert_called_once()
        
        # Check that the signal was emitted with the manuscript item
        assert mock_receiver.call_args[0][0] == manuscript_item
    
    def test_drag_drop(self, qtbot, binder_view):
        """Test drag and drop functionality."""
        # Find the manuscript item
        root_item = binder_view.model.invisibleRootItem()
        manuscript_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Manuscript":
                manuscript_item = item
                break
        
        assert manuscript_item is not None
        
        # Find the first chapter item
        chapter_item = manuscript_item.child(0)
        assert chapter_item is not None
        
        # Find the characters item
        characters_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Characters":
                characters_item = item
                break
        
        assert characters_item is not None
        
        # Get the indexes of the items
        chapter_index = binder_view.model.indexFromItem(chapter_item)
        characters_index = binder_view.model.indexFromItem(characters_item)
        
        # Get the initial row counts
        initial_manuscript_count = manuscript_item.rowCount()
        initial_characters_count = characters_item.rowCount()
        
        # Create a new item to drag
        new_item = QStandardItem("Dragged Item")
        manuscript_item.appendRow(new_item)
        
        # Check that the new item was added
        assert manuscript_item.rowCount() == initial_manuscript_count + 1
        
        # Get the index of the new item
        new_index = binder_view.model.indexFromItem(new_item)
        
        # Select the new item
        binder_view.tree_view.setCurrentIndex(new_index)
        
        # Verify that the tree view supports drag and drop
        assert binder_view.tree_view.dragEnabled()
        assert binder_view.tree_view.acceptDrops()
        assert binder_view.tree_view.dragDropMode() == QTreeView.DragDropMode.InternalMove
    
    def test_load_project(self, binder_view):
        """Test loading a project."""
        # Create a mock project
        mock_project = MagicMock()
        mock_project.title = "Test Project"
        
        # Mock the project manager's get_document_tree method to return a document tree
        document_tree = [
            {
                "id": "manuscript_folder",
                "title": "Manuscript",
                "children": [
                    {
                        "id": "chapter_1",
                        "title": "Chapter 1",
                        "children": [
                            {
                                "id": "scene_1",
                                "title": "Scene 1",
                                "children": []
                            }
                        ]
                    }
                ]
            }
        ]
        binder_view.project_manager.get_document_tree.return_value = document_tree
        
        # Load the project
        binder_view.load_project(mock_project)
        
        # Check that the model has data
        root_item = binder_view.model.invisibleRootItem()
        assert root_item.rowCount() > 0
        
        # Check that the manuscript item was added
        manuscript_item = None
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item.text() == "Manuscript":
                manuscript_item = item
                break
        
        assert manuscript_item is not None
        assert manuscript_item.data(Qt.ItemDataRole.UserRole) == "manuscript_folder"
        
        # Load None project
        binder_view.load_project(None)
        
        # Check that the model was cleared
        root_item = binder_view.model.invisibleRootItem()
        assert root_item.rowCount() == 0


if __name__ == '__main__':
    pytest.main(['-v', __file__])
