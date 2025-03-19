#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the NotesInspector component.

This module contains tests for the NotesInspector class.
"""

from unittest.mock import MagicMock
import pytest
from PyQt6.QtCore import Qt

from src.ui.inspector.inspector_view import NotesInspector
from src.backend.models.note import Note
from src.tests.ui.inspector.fixtures import app, notes_inspector


class TestNotesInspector:
    """Test cases for the NotesInspector class."""
    
    def test_init(self, notes_inspector):
        """Test initialization of the notes inspector."""
        # Check that components are created
        assert notes_inspector.title_edit is not None
        assert notes_inspector.content_edit is not None
        
        # Check that fields are disabled initially
        assert not notes_inspector.title_edit.isEnabled()
        assert not notes_inspector.content_edit.isEnabled()
    
    def test_set_note(self, notes_inspector):
        """Test setting a note."""
        # Create mock note
        mock_note = MagicMock(spec=Note)
        mock_note.title = "Important Note"
        mock_note.content = "This is an important note."
        
        # Set note
        notes_inspector.set_note(mock_note)
        
        # Check that fields are enabled
        assert notes_inspector.title_edit.isEnabled()
        assert notes_inspector.content_edit.isEnabled()
        
        # Check field values
        assert notes_inspector.title_edit.text() == "Important Note"
        assert notes_inspector.content_edit.toPlainText() == "This is an important note."
        
        # Clear note
        notes_inspector.set_note(None)
        
        # Check that fields are disabled
        assert not notes_inspector.title_edit.isEnabled()
        assert not notes_inspector.content_edit.isEnabled()
        
        # Check field values are cleared
        assert notes_inspector.title_edit.text() == ""
        assert notes_inspector.content_edit.toPlainText() == ""
    
    def test_note_changed_signals(self, qtbot, notes_inspector):
        """Test note changed signals."""
        # Create mock note
        mock_note = MagicMock(spec=Note)
        mock_note.title = "Important Note"
        mock_note.content = "This is an important note."
        
        # Set note
        notes_inspector.set_note(mock_note)
        
        # Mock note_changed signal
        notes_inspector.note_changed = MagicMock()
        
        # Change title
        notes_inspector.title_edit.setText("Updated Note")
        notes_inspector.note_changed.emit.assert_called_with("title", "Updated Note")
        
        # Change content
        notes_inspector.content_edit.setText("This is an updated note.")
        notes_inspector.note_changed.emit.assert_called_with("content", "This is an updated note.")
