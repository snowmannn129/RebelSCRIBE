#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the InspectorView component.

This module contains tests for the InspectorView class.
"""

from unittest.mock import patch, MagicMock
import pytest
from PyQt6.QtCore import Qt

from src.ui.inspector.inspector_view import InspectorView
from src.backend.models.document import Document
from src.backend.models.character import Character
from src.backend.models.location import Location
from src.backend.models.note import Note
from src.tests.ui.inspector.fixtures import app, inspector_view


def create_mock_document(doc_id="doc123", title="Test Document", doc_type=None):
    """Create a mock document with all required attributes."""
    mock_document = MagicMock()
    mock_document.id = doc_id
    mock_document.title = title
    mock_document.type = doc_type
    mock_document.synopsis = ""
    mock_document.status = "Draft"
    mock_document.is_included_in_compile = True
    mock_document.tags = []
    mock_document.color = None
    mock_document.word_count = 0
    mock_document.character_count = 0
    
    # Mock datetime attributes
    mock_created_at = MagicMock()
    mock_created_at.strftime.return_value = "2025-03-10 10:00:00"
    mock_document.created_at = mock_created_at
    
    mock_updated_at = MagicMock()
    mock_updated_at.strftime.return_value = "2025-03-10 11:00:00"
    mock_document.updated_at = mock_updated_at
    
    mock_document.metadata = {}
    mock_document.set_metadata = MagicMock()
    
    return mock_document


def create_mock_character():
    """Create a mock character with all required attributes."""
    mock_character = MagicMock()
    mock_character.name = "John Doe"
    mock_character.role = "Protagonist"
    mock_character.age = 30
    mock_character.to_document = MagicMock()
    return mock_character


def create_mock_location():
    """Create a mock location with all required attributes."""
    mock_location = MagicMock()
    mock_location.name = "New York"
    mock_location.type = "City"
    mock_location.to_document = MagicMock()
    return mock_location


def create_mock_note():
    """Create a mock note with all required attributes."""
    mock_note = MagicMock()
    mock_note.title = "Important Note"
    mock_note.content = "This is an important note."
    mock_note.to_document = MagicMock()
    return mock_note


class TestInspectorView:
    """Test cases for the InspectorView class."""
    
    def test_init(self, inspector_view):
        """Test initialization of the inspector view."""
        # Check that components are created
        assert inspector_view.tab_widget is not None
        assert inspector_view.metadata_panel is not None
        assert inspector_view.character_inspector is not None
        assert inspector_view.location_inspector is not None
        assert inspector_view.notes_inspector is not None
        assert inspector_view.document_manager is not None
        
        # Check tab widget
        assert inspector_view.tab_widget.count() == 4
        assert inspector_view.tab_widget.tabText(0) == "Metadata"
        assert inspector_view.tab_widget.tabText(1) == "Character"
        assert inspector_view.tab_widget.tabText(2) == "Location"
        assert inspector_view.tab_widget.tabText(3) == "Notes"
    
    def test_set_document_regular(self, inspector_view):
        """Test setting a regular document."""
        # Create mock document
        mock_document = create_mock_document(doc_type=Document.TYPE_SCENE)
        
        # Set document
        inspector_view.set_document(mock_document)
        
        # Check that document was set
        assert inspector_view.current_document == mock_document
        
        # Check that metadata panel was updated
        assert inspector_view.metadata_panel.document == mock_document
        
        # Check that other panels were cleared
        assert inspector_view.character_inspector.character is None
        assert inspector_view.location_inspector.location is None
        assert inspector_view.notes_inspector.note is None
        
        # Check that metadata tab is selected
        assert inspector_view.tab_widget.currentWidget() == inspector_view.metadata_panel
    
    def test_set_document_character(self, inspector_view):
        """Test setting a character document."""
        # Create mock document
        mock_document = create_mock_document(
            doc_id="char123", 
            title="Character Document", 
            doc_type=Document.TYPE_CHARACTER
        )
        
        # Create mock character
        mock_character = create_mock_character()
        
        # Mock Character.from_document
        with patch('src.ui.inspector.inspector_view.Character.from_document', return_value=mock_character) as mock_from_document:
            # Set document
            inspector_view.set_document(mock_document)
            
            # Check that document was set
            assert inspector_view.current_document == mock_document
            
            # Check that metadata panel was updated
            assert inspector_view.metadata_panel.document == mock_document
            
            # Check that character inspector was updated
            mock_from_document.assert_called_once_with(mock_document)
            assert inspector_view.character_inspector.character == mock_character
            
            # Check that other panels were cleared
            assert inspector_view.location_inspector.location is None
            assert inspector_view.notes_inspector.note is None
            
            # Check that character tab is selected
            assert inspector_view.tab_widget.currentWidget() == inspector_view.character_inspector
    
    def test_set_document_location(self, inspector_view):
        """Test setting a location document."""
        # Create mock document
        mock_document = create_mock_document(
            doc_id="loc123", 
            title="Location Document", 
            doc_type=Document.TYPE_LOCATION
        )
        
        # Create mock location
        mock_location = create_mock_location()
        
        # Mock Location.from_document
        with patch('src.ui.inspector.inspector_view.Location.from_document', return_value=mock_location) as mock_from_document:
            # Set document
            inspector_view.set_document(mock_document)
            
            # Check that document was set
            assert inspector_view.current_document == mock_document
            
            # Check that metadata panel was updated
            assert inspector_view.metadata_panel.document == mock_document
            
            # Check that location inspector was updated
            mock_from_document.assert_called_once_with(mock_document)
            assert inspector_view.location_inspector.location == mock_location
            
            # Check that other panels were cleared
            assert inspector_view.character_inspector.character is None
            assert inspector_view.notes_inspector.note is None
            
            # Check that location tab is selected
            assert inspector_view.tab_widget.currentWidget() == inspector_view.location_inspector
    
    def test_set_document_note(self, inspector_view):
        """Test setting a note document."""
        # Create mock document
        mock_document = create_mock_document(
            doc_id="note123", 
            title="Note Document", 
            doc_type=Document.TYPE_NOTE
        )
        
        # Create mock note
        mock_note = create_mock_note()
        
        # Mock Note.from_document
        with patch('src.ui.inspector.inspector_view.Note.from_document', return_value=mock_note) as mock_from_document:
            # Set document
            inspector_view.set_document(mock_document)
            
            # Check that document was set
            assert inspector_view.current_document == mock_document
            
            # Check that metadata panel was updated
            assert inspector_view.metadata_panel.document == mock_document
            
            # Check that note inspector was updated
            mock_from_document.assert_called_once_with(mock_document)
            assert inspector_view.notes_inspector.note == mock_note
            
            # Check that other panels were cleared
            assert inspector_view.character_inspector.character is None
            assert inspector_view.location_inspector.location is None
            
            # Check that notes tab is selected
            assert inspector_view.tab_widget.currentWidget() == inspector_view.notes_inspector
    
    def test_set_document_none(self, inspector_view):
        """Test clearing the document."""
        # Set document to None
        inspector_view.set_document(None)
        
        # Check that document was cleared
        assert inspector_view.current_document is None
        
        # Check that all panels were cleared
        assert inspector_view.metadata_panel.document is None
        assert inspector_view.character_inspector.character is None
        assert inspector_view.location_inspector.location is None
        assert inspector_view.notes_inspector.note is None
    
    def test_on_metadata_changed(self, inspector_view):
        """Test handling metadata changed event."""
        # Create mock document
        mock_document = create_mock_document(doc_type=Document.TYPE_SCENE)
        
        # Set document
        inspector_view.current_document = mock_document
        
        # Test title change
        inspector_view._on_metadata_changed("title", "Updated Title")
        assert mock_document.title == "Updated Title"
        
        # Test synopsis change
        inspector_view._on_metadata_changed("synopsis", "Updated synopsis.")
        assert mock_document.synopsis == "Updated synopsis."
        
        # Test status change
        inspector_view._on_metadata_changed("status", "Final")
        assert mock_document.status == "Final"
        
        # Test include in compile change
        inspector_view._on_metadata_changed("is_included_in_compile", False)
        assert mock_document.is_included_in_compile is False
        
        # Test tags change
        inspector_view._on_metadata_changed("tags", ["tag1", "tag2"])
        assert mock_document.tags == ["tag1", "tag2"]
        
        # Test color change
        inspector_view._on_metadata_changed("color", "#00FF00")
        assert mock_document.color == "#00FF00"
        
        # Test custom metadata change
        inspector_view._on_metadata_changed("metadata.custom_key", "custom_value")
        mock_document.set_metadata.assert_called_with("custom_key", "custom_value")
        
        # Check that document was saved
        inspector_view.document_manager.update_document.assert_called_with(mock_document.id)
    
    def test_on_character_changed(self, inspector_view):
        """Test handling character changed event."""
        # Create mock document
        mock_document = create_mock_document(
            doc_id="char123", 
            title="Character Document", 
            doc_type=Document.TYPE_CHARACTER
        )
        
        # Create mock character
        mock_character = create_mock_character()
        
        # Set up inspector view
        inspector_view.current_document = mock_document
        inspector_view.character_inspector.character = mock_character
        
        # Test name change
        inspector_view._on_character_changed("name", "Updated Name")
        assert mock_character.name == "Updated Name"
        
        # Test role change
        inspector_view._on_character_changed("role", "Antagonist")
        assert mock_character.role == "Antagonist"
        
        # Test age change
        inspector_view._on_character_changed("age", 35)
        assert mock_character.age == 35
        
        # Check that character was saved to document
        mock_character.to_document.assert_called_with(mock_document)
        
        # Check that document was saved
        inspector_view.document_manager.update_document.assert_called_with(mock_document.id)
    
    def test_on_location_changed(self, inspector_view):
        """Test handling location changed event."""
        # Create mock document
        mock_document = create_mock_document(
            doc_id="loc123", 
            title="Location Document", 
            doc_type=Document.TYPE_LOCATION
        )
        
        # Create mock location
        mock_location = create_mock_location()
        
        # Set up inspector view
        inspector_view.current_document = mock_document
        inspector_view.location_inspector.location = mock_location
        
        # Test name change
        inspector_view._on_location_changed("name", "Updated Location")
        assert mock_location.name == "Updated Location"
        
        # Test type change
        inspector_view._on_location_changed("type", "Town")
        assert mock_location.type == "Town"
        
        # Check that location was saved to document
        mock_location.to_document.assert_called_with(mock_document)
        
        # Check that document was saved
        inspector_view.document_manager.update_document.assert_called_with(mock_document.id)
    
    def test_on_note_changed(self, inspector_view):
        """Test handling note changed event."""
        # Create mock document
        mock_document = create_mock_document(
            doc_id="note123", 
            title="Note Document", 
            doc_type=Document.TYPE_NOTE
        )
        
        # Create mock note
        mock_note = create_mock_note()
        
        # Set up inspector view
        inspector_view.current_document = mock_document
        inspector_view.notes_inspector.note = mock_note
        
        # Test title change
        inspector_view._on_note_changed("title", "Updated Note")
        assert mock_note.title == "Updated Note"
        
        # Test content change
        inspector_view._on_note_changed("content", "Updated content.")
        assert mock_note.content == "Updated content."
        
        # Check that note was saved to document
        mock_note.to_document.assert_called_with(mock_document)
        
        # Check that document was saved
        inspector_view.document_manager.update_document.assert_called_with(mock_document.id)
