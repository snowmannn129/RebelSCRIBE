#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Note model.
"""

import pytest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.note import Note


class TestNote:
    """Test suite for the Note model."""

    def test_init_default_values(self):
        """Test that a note is initialized with default values."""
        note = Note()
        
        assert note.title == ""
        assert note.content == ""
        assert note.type == Note.TYPE_GENERAL
        assert note.priority == Note.PRIORITY_MEDIUM
        assert note.is_completed is False
        assert note.project_id == ""
        assert note.document_id is None
        assert note.related_ids == {
            "character": [],
            "location": [],
            "scene": [],
            "chapter": [],
            "note": [],
            "tag": []
        }
        assert note.metadata == {}
        assert isinstance(note.created_at, datetime.datetime)
        assert isinstance(note.updated_at, datetime.datetime)
        assert note.color is None
        assert note.tags == []

    def test_init_with_values(self):
        """Test that a note is initialized with provided values."""
        title = "Research on Medieval Weapons"
        content = "Swords, bows, and siege weapons were common in medieval warfare."
        note_type = Note.TYPE_RESEARCH
        priority = Note.PRIORITY_HIGH
        
        note = Note(
            title=title,
            content=content,
            type=note_type,
            priority=priority
        )
        
        assert note.title == title
        assert note.content == content
        assert note.type == note_type
        assert note.priority == priority

    def test_init_with_invalid_type(self):
        """Test that a note with invalid type defaults to general."""
        note = Note(type="invalid_type")
        
        assert note.type == Note.TYPE_GENERAL

    def test_init_with_invalid_priority(self):
        """Test that a note with invalid priority defaults to medium."""
        note = Note(priority="invalid_priority")
        
        assert note.priority == Note.PRIORITY_MEDIUM

    def test_set_type_valid(self):
        """Test setting a valid note type."""
        note = Note(title="Test Note")
        
        # Set to research
        note.set_type(Note.TYPE_RESEARCH)
        assert note.type == Note.TYPE_RESEARCH
        
        # Set to idea
        note.set_type(Note.TYPE_IDEA)
        assert note.type == Note.TYPE_IDEA
        
        # Set to todo
        note.set_type(Note.TYPE_TODO)
        assert note.type == Note.TYPE_TODO
        
        # Set to question
        note.set_type(Note.TYPE_QUESTION)
        assert note.type == Note.TYPE_QUESTION
        
        # Set to general
        note.set_type(Note.TYPE_GENERAL)
        assert note.type == Note.TYPE_GENERAL

    def test_set_type_invalid(self):
        """Test setting an invalid note type."""
        note = Note(title="Test Note", type=Note.TYPE_GENERAL)
        
        # Set to invalid type
        note.set_type("Invalid Type")
        
        # Type should remain unchanged
        assert note.type == Note.TYPE_GENERAL

    def test_set_priority_valid(self):
        """Test setting a valid priority."""
        note = Note(title="Test Note")
        
        # Set to low
        note.set_priority(Note.PRIORITY_LOW)
        assert note.priority == Note.PRIORITY_LOW
        
        # Set to medium
        note.set_priority(Note.PRIORITY_MEDIUM)
        assert note.priority == Note.PRIORITY_MEDIUM
        
        # Set to high
        note.set_priority(Note.PRIORITY_HIGH)
        assert note.priority == Note.PRIORITY_HIGH

    def test_set_priority_invalid(self):
        """Test setting an invalid priority."""
        note = Note(title="Test Note", priority=Note.PRIORITY_MEDIUM)
        
        # Set to invalid priority
        note.set_priority("Invalid Priority")
        
        # Priority should remain unchanged
        assert note.priority == Note.PRIORITY_MEDIUM

    def test_set_content(self):
        """Test setting the note content."""
        note = Note(title="Test Note")
        content = "This is the content of the note."
        
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.set_content(content)
            
            assert note.content == content
            mock_mark_updated.assert_called_once()

    def test_append_content(self):
        """Test appending content to the note."""
        note = Note(title="Test Note", content="Initial content. ")
        content_to_append = "Additional content."
        
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.append_content(content_to_append)
            
            assert note.content == "Initial content. Additional content."
            mock_mark_updated.assert_called_once()

    def test_set_completed(self):
        """Test setting the completion status of a note."""
        note = Note(title="Test Note", type=Note.TYPE_TODO)
        
        # Set to completed
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.set_completed(True)
            
            assert note.is_completed is True
            mock_mark_updated.assert_called_once()
        
        # Set to not completed
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.set_completed(False)
            
            assert note.is_completed is False
            mock_mark_updated.assert_called_once()

    def test_add_related_item_valid(self):
        """Test adding a valid related item."""
        note = Note(title="Test Note")
        
        # Add character
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("character", "char123")
            
            assert result is True
            assert "char123" in note.related_ids["character"]
            mock_mark_updated.assert_called_once()
        
        # Add location
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("location", "loc123")
            
            assert result is True
            assert "loc123" in note.related_ids["location"]
            mock_mark_updated.assert_called_once()
        
        # Add scene
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("scene", "scene123")
            
            assert result is True
            assert "scene123" in note.related_ids["scene"]
            mock_mark_updated.assert_called_once()
        
        # Add chapter
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("chapter", "chapter123")
            
            assert result is True
            assert "chapter123" in note.related_ids["chapter"]
            mock_mark_updated.assert_called_once()
        
        # Add note
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("note", "note123")
            
            assert result is True
            assert "note123" in note.related_ids["note"]
            mock_mark_updated.assert_called_once()
        
        # Add tag
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("tag", "tag123")
            
            assert result is True
            assert "tag123" in note.related_ids["tag"]
            mock_mark_updated.assert_called_once()
        
        # Adding the same item again should not duplicate
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("character", "char123")
            
            assert result is True
            assert note.related_ids["character"].count("char123") == 1
            mock_mark_updated.assert_not_called()

    def test_add_related_item_invalid(self):
        """Test adding an invalid related item."""
        note = Note(title="Test Note")
        
        # Add invalid item type
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.add_related_item("invalid_type", "id123")
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_remove_related_item_valid(self):
        """Test removing a valid related item."""
        note = Note(title="Test Note")
        
        # Add items
        note.add_related_item("character", "char123")
        note.add_related_item("location", "loc123")
        
        # Remove character
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.remove_related_item("character", "char123")
            
            assert result is True
            assert "char123" not in note.related_ids["character"]
            mock_mark_updated.assert_called_once()
        
        # Remove location
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.remove_related_item("location", "loc123")
            
            assert result is True
            assert "loc123" not in note.related_ids["location"]
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent item should not error
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.remove_related_item("character", "nonexistent")
            
            assert result is True
            mock_mark_updated.assert_not_called()

    def test_remove_related_item_invalid(self):
        """Test removing an invalid related item."""
        note = Note(title="Test Note")
        
        # Remove invalid item type
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            result = note.remove_related_item("invalid_type", "id123")
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_get_related_items(self):
        """Test getting related items."""
        note = Note(title="Test Note")
        
        # Add items
        note.add_related_item("character", "char123")
        note.add_related_item("location", "loc123")
        
        # Get all related items
        all_items = note.get_related_items()
        assert all_items["character"] == ["char123"]
        assert all_items["location"] == ["loc123"]
        assert all_items["scene"] == []
        
        # Get specific type of related items
        character_items = note.get_related_items("character")
        assert character_items == {"character": ["char123"]}
        
        # Get invalid type of related items
        invalid_items = note.get_related_items("invalid_type")
        assert invalid_items == {}

    def test_set_color(self):
        """Test setting the color."""
        note = Note(title="Test Note")
        color = "#FF0000"
        
        # Set color
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.set_color(color)
            
            assert note.color == color
            mock_mark_updated.assert_called_once()
        
        # Clear color
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.set_color(None)
            
            assert note.color is None
            mock_mark_updated.assert_called_once()

    def test_tag_operations(self):
        """Test tag operations."""
        note = Note(title="Test Note")
        tag = "research"
        
        # Add tag
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.add_tag(tag)
            
            assert tag in note.tags
            mock_mark_updated.assert_called_once()
        
        # Adding the same tag again should not duplicate
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.add_tag(tag)
            
            assert note.tags.count(tag) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove tag
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.remove_tag(tag)
            
            assert tag not in note.tags
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent tag should not error
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.remove_tag("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_metadata_operations(self):
        """Test metadata operations."""
        note = Note(title="Test Note")
        
        # Set metadata
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.set_metadata("key1", "value1")
            
            assert note.metadata["key1"] == "value1"
            mock_mark_updated.assert_called_once()
        
        # Get metadata
        assert note.get_metadata("key1") == "value1"
        assert note.get_metadata("nonexistent") is None
        assert note.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.set_metadata("key1", "updated")
            
            assert note.get_metadata("key1") == "updated"
            mock_mark_updated.assert_called_once()
        
        # Remove metadata
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.remove_metadata("key1")
            
            assert "key1" not in note.metadata
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent metadata should not error
        with patch.object(note, 'mark_updated') as mock_mark_updated:
            note.remove_metadata("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_str_representation(self):
        """Test the string representation of a note."""
        # General note
        note = Note(title="Research Note", type=Note.TYPE_GENERAL)
        expected = "Note('Research Note', type='General', priority='Medium')"
        assert str(note) == expected
        
        # Todo note (not completed)
        note = Note(title="Todo Note", type=Note.TYPE_TODO, is_completed=False)
        expected = "Note('Todo Note', type='Todo', priority='Medium')"
        assert str(note) == expected
        
        # Todo note (completed)
        note = Note(title="Todo Note", type=Note.TYPE_TODO, is_completed=True)
        expected = "Note('Todo Note', type='Todo', priority='Medium' (Completed))"
        assert str(note) == expected

    def test_to_dict(self):
        """Test converting a note to a dictionary."""
        note = Note(
            title="Research Note",
            content="This is research content.",
            type=Note.TYPE_RESEARCH,
            priority=Note.PRIORITY_HIGH
        )
        
        note_dict = note.to_dict()
        
        assert note_dict["title"] == "Research Note"
        assert note_dict["content"] == "This is research content."
        assert note_dict["type"] == Note.TYPE_RESEARCH
        assert note_dict["priority"] == Note.PRIORITY_HIGH
        assert "id" in note_dict
        assert "created_at" in note_dict
        assert "updated_at" in note_dict

    def test_from_dict(self):
        """Test creating a note from a dictionary."""
        data: Dict[str, Any] = {
            "title": "Research Note",
            "content": "This is research content.",
            "type": Note.TYPE_RESEARCH,
            "priority": Note.PRIORITY_HIGH,
            "tags": ["research", "important"],
            "is_completed": False
        }
        
        note = Note.from_dict(data)
        
        assert note.title == "Research Note"
        assert note.content == "This is research content."
        assert note.type == Note.TYPE_RESEARCH
        assert note.priority == Note.PRIORITY_HIGH
        assert note.tags == ["research", "important"]
        assert note.is_completed is False

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Note(
            title="Research Note",
            content="This is research content.",
            type=Note.TYPE_RESEARCH,
            priority=Note.PRIORITY_HIGH,
            tags=["research", "important"],
            is_completed=False
        )
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Note.from_json(json_str)
        
        # Check that the restored note has the same properties
        assert restored.title == original.title
        assert restored.content == original.content
        assert restored.type == original.type
        assert restored.priority == original.priority
        assert restored.tags == original.tags
        assert restored.is_completed == original.is_completed
