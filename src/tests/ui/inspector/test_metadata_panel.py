#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the MetadataPanel component.

This module contains tests for the MetadataPanel class.
"""

import unittest
from unittest.mock import patch, MagicMock
import pytest
from PyQt6.QtWidgets import QFormLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.ui.inspector.inspector_view import MetadataPanel
from src.backend.models.document import Document
from src.tests.ui.inspector.fixtures import app, metadata_panel


class TestMetadataPanel:
    """Test cases for the MetadataPanel class."""
    
    def test_init(self, metadata_panel):
        """Test initialization of the metadata panel."""
        # Check that components are created
        assert metadata_panel.title_edit is not None
        assert metadata_panel.synopsis_edit is not None
        assert metadata_panel.status_combo is not None
        assert metadata_panel.include_check is not None
        assert metadata_panel.tags_edit is not None
        assert metadata_panel.color_button is not None
        assert metadata_panel.word_count_value is not None
        assert metadata_panel.char_count_value is not None
        assert metadata_panel.created_value is not None
        assert metadata_panel.updated_value is not None
        assert metadata_panel.custom_group is not None
        assert metadata_panel.add_custom_button is not None
        
        # Check that fields are disabled initially
        assert not metadata_panel.title_edit.isEnabled()
        assert not metadata_panel.synopsis_edit.isEnabled()
        assert not metadata_panel.status_combo.isEnabled()
        assert not metadata_panel.include_check.isEnabled()
        assert not metadata_panel.tags_edit.isEnabled()
        assert not metadata_panel.color_button.isEnabled()
        assert not metadata_panel.add_custom_button.isEnabled()
    
    def test_set_document(self, metadata_panel):
        """Test setting a document."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.title = "Test Document"
        mock_document.synopsis = "This is a test document."
        mock_document.status = "Draft"
        mock_document.is_included_in_compile = True
        mock_document.tags = ["test", "document"]
        mock_document.color = "#FF0000"
        mock_document.word_count = 100
        mock_document.character_count = 500
        
        # Mock datetime attributes
        mock_created_at = MagicMock()
        mock_created_at.strftime.return_value = "2025-03-10 10:00:00"
        mock_document.created_at = mock_created_at
        
        mock_updated_at = MagicMock()
        mock_updated_at.strftime.return_value = "2025-03-10 11:00:00"
        mock_document.updated_at = mock_updated_at
        
        mock_document.metadata = {"key1": "value1", "key2": "value2"}
        
        # Set document
        metadata_panel.set_document(mock_document)
        
        # Check that fields are enabled
        assert metadata_panel.title_edit.isEnabled()
        assert metadata_panel.synopsis_edit.isEnabled()
        assert metadata_panel.status_combo.isEnabled()
        assert metadata_panel.include_check.isEnabled()
        assert metadata_panel.tags_edit.isEnabled()
        assert metadata_panel.color_button.isEnabled()
        assert metadata_panel.add_custom_button.isEnabled()
        
        # Check field values
        assert metadata_panel.title_edit.text() == "Test Document"
        assert metadata_panel.synopsis_edit.toPlainText() == "This is a test document."
        assert metadata_panel.status_combo.currentText() == "Draft"
        assert metadata_panel.include_check.isChecked() is True
        assert metadata_panel.tags_edit.text() == "test, document"
        assert metadata_panel.word_count_value.text() == "100"
        assert metadata_panel.char_count_value.text() == "500"
        assert metadata_panel.created_value.text() == "2025-03-10 10:00:00"
        assert metadata_panel.updated_value.text() == "2025-03-10 11:00:00"
        
        # Check color button
        assert metadata_panel.color_button.property("color") is not None
        assert metadata_panel.color_button.styleSheet() == "background-color: #FF0000"
        
        # Clear document
        metadata_panel.set_document(None)
        
        # Check that fields are disabled
        assert not metadata_panel.title_edit.isEnabled()
        assert not metadata_panel.synopsis_edit.isEnabled()
        assert not metadata_panel.status_combo.isEnabled()
        assert not metadata_panel.include_check.isEnabled()
        assert not metadata_panel.tags_edit.isEnabled()
        assert not metadata_panel.color_button.isEnabled()
        assert not metadata_panel.add_custom_button.isEnabled()
        
        # Check field values are cleared
        assert metadata_panel.title_edit.text() == ""
        assert metadata_panel.synopsis_edit.toPlainText() == ""
        assert metadata_panel.word_count_value.text() == "0"
        assert metadata_panel.char_count_value.text() == "0"
        assert metadata_panel.created_value.text() == ""
        assert metadata_panel.updated_value.text() == ""
    
    def test_metadata_changed_signals(self, qtbot, metadata_panel):
        """Test metadata changed signals."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.title = "Test Document"
        mock_document.synopsis = "This is a test document."
        mock_document.status = "Draft"
        mock_document.is_included_in_compile = True
        mock_document.tags = ["test", "document"]
        mock_document.color = None
        mock_document.word_count = 100
        mock_document.character_count = 500
        
        # Mock datetime attributes
        mock_created_at = MagicMock()
        mock_created_at.strftime.return_value = "2025-03-10 10:00:00"
        mock_document.created_at = mock_created_at
        
        mock_updated_at = MagicMock()
        mock_updated_at.strftime.return_value = "2025-03-10 11:00:00"
        mock_document.updated_at = mock_updated_at
        
        mock_document.metadata = {}
        
        # Set document
        metadata_panel.set_document(mock_document)
        
        # Mock metadata_changed signal
        metadata_panel.metadata_changed = MagicMock()
        
        # Change title
        metadata_panel.title_edit.setText("Updated Title")
        metadata_panel.metadata_changed.emit.assert_called_with("title", "Updated Title")
        
        # Change synopsis
        metadata_panel.synopsis_edit.setText("Updated synopsis.")
        metadata_panel.metadata_changed.emit.assert_called_with("synopsis", "Updated synopsis.")
        
        # Change status
        metadata_panel.status_combo.setCurrentText("Final")
        metadata_panel.metadata_changed.emit.assert_called_with("status", "Final")
        
        # Change include in compile
        metadata_panel.include_check.setChecked(False)
        metadata_panel.metadata_changed.emit.assert_called_with("is_included_in_compile", False)
        
        # Change tags
        metadata_panel.tags_edit.setText("updated, tags")
        metadata_panel.metadata_changed.emit.assert_called_with("tags", ["updated", "tags"])
    
    def test_color_button(self, qtbot, metadata_panel, monkeypatch):
        """Test color button functionality."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.title = "Test Document"
        mock_document.synopsis = ""
        mock_document.status = "Draft"
        mock_document.is_included_in_compile = True
        mock_document.tags = []
        mock_document.color = None
        mock_document.word_count = 0
        mock_document.character_count = 0
        mock_document.metadata = {}
        
        # Mock datetime attributes
        mock_created_at = MagicMock()
        mock_created_at.strftime.return_value = "2025-03-10 10:00:00"
        mock_document.created_at = mock_created_at
        
        mock_updated_at = MagicMock()
        mock_updated_at.strftime.return_value = "2025-03-10 11:00:00"
        mock_document.updated_at = mock_updated_at
        
        # Set document
        metadata_panel.set_document(mock_document)
        
        # Mock metadata_changed signal
        metadata_panel.metadata_changed = MagicMock()
        
        # Create a mock color that has isValid method returning True
        mock_color = MagicMock()
        mock_color.isValid.return_value = True
        mock_color.name.return_value = "#00FF00"
        
        # Mock QColorDialog
        with patch('src.ui.inspector.inspector_view.QColorDialog') as mock_color_dialog:
            # Configure mock to return a color
            mock_color_dialog.getColor.return_value = mock_color
            
            # Click color button
            metadata_panel._on_color_button_clicked()
            
            # Check that color dialog was shown
            mock_color_dialog.getColor.assert_called_once()
            
            # Check that metadata_changed signal was emitted
            metadata_panel.metadata_changed.emit.assert_called_with("color", "#00FF00")
            
            # Check that button color was updated
            assert metadata_panel.color_button.styleSheet() == "background-color: #00FF00"
            assert metadata_panel.color_button.property("color") == mock_color
    
    def test_add_custom_metadata(self, qtbot, metadata_panel):
        """Test adding custom metadata."""
        # Create mock document
        mock_document = MagicMock()
        mock_document.title = "Test Document"
        mock_document.synopsis = ""
        mock_document.status = "Draft"
        mock_document.is_included_in_compile = True
        mock_document.tags = []
        mock_document.color = None
        mock_document.word_count = 0
        mock_document.character_count = 0
        mock_document.metadata = {}
        
        # Mock datetime attributes
        mock_created_at = MagicMock()
        mock_created_at.strftime.return_value = "2025-03-10 10:00:00"
        mock_document.created_at = mock_created_at
        
        mock_updated_at = MagicMock()
        mock_updated_at.strftime.return_value = "2025-03-10 11:00:00"
        mock_document.updated_at = mock_updated_at
        
        # Set document
        metadata_panel.set_document(mock_document)
        
        # Mock metadata_changed signal
        metadata_panel.metadata_changed = MagicMock()
        
        # Initial form layout row count
        initial_row_count = metadata_panel.custom_form.rowCount()
        
        # Click add custom metadata button
        qtbot.mouseClick(metadata_panel.add_custom_button, Qt.MouseButton.LeftButton)
        
        # Check that a new row was added
        assert metadata_panel.custom_form.rowCount() == initial_row_count + 1
        
        # Get the key and value edit fields
        layout_item = metadata_panel.custom_form.itemAt(initial_row_count, QFormLayout.ItemRole.FieldRole)
        layout = layout_item.layout()
        key_edit = layout.itemAt(0).widget()
        value_edit = layout.itemAt(1).widget()
        
        # Enter key and value
        key_edit.setText("custom_key")
        value_edit.setText("custom_value")
        
        # Check that metadata_changed signal was emitted
        metadata_panel.metadata_changed.emit.assert_called_with("metadata.custom_key", "custom_value")
