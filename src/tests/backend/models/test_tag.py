#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Tag model.
"""

import pytest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.tag import Tag


class TestTag:
    """Test suite for the Tag model."""

    def test_init_default_values(self):
        """Test that a tag is initialized with default values."""
        tag = Tag()
        
        assert tag.name == ""
        assert tag.description == ""
        assert tag.color is None
        assert tag.project_id == ""
        assert tag.item_ids == {
            "character": [],
            "location": [],
            "scene": [],
            "chapter": [],
            "note": [],
            "document": []
        }
        assert tag.parent_tag_id is None
        assert tag.child_tag_ids == []
        assert tag.metadata == {}
        assert isinstance(tag.created_at, datetime.datetime)
        assert isinstance(tag.updated_at, datetime.datetime)

    def test_init_with_values(self):
        """Test that a tag is initialized with provided values."""
        name = "Fantasy"
        description = "Elements related to fantasy genre"
        color = "#FF5733"
        project_id = "project123"
        
        tag = Tag(
            name=name,
            description=description,
            color=color,
            project_id=project_id
        )
        
        assert tag.name == name
        assert tag.description == description
        assert tag.color == color
        assert tag.project_id == project_id

    def test_set_description(self):
        """Test setting the tag description."""
        tag = Tag(name="Fantasy")
        description = "Elements related to fantasy genre"
        
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.set_description(description)
            
            assert tag.description == description
            mock_mark_updated.assert_called_once()

    def test_set_color(self):
        """Test setting the tag color."""
        tag = Tag(name="Fantasy")
        color = "#FF5733"
        
        # Set color
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.set_color(color)
            
            assert tag.color == color
            mock_mark_updated.assert_called_once()
        
        # Clear color
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.set_color(None)
            
            assert tag.color is None
            mock_mark_updated.assert_called_once()

    def test_add_item_valid(self):
        """Test adding a valid item to the tag."""
        tag = Tag(name="Fantasy")
        
        # Add character
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("character", "char123")
            
            assert result is True
            assert "char123" in tag.item_ids["character"]
            mock_mark_updated.assert_called_once()
        
        # Add location
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("location", "loc123")
            
            assert result is True
            assert "loc123" in tag.item_ids["location"]
            mock_mark_updated.assert_called_once()
        
        # Add scene
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("scene", "scene123")
            
            assert result is True
            assert "scene123" in tag.item_ids["scene"]
            mock_mark_updated.assert_called_once()
        
        # Add chapter
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("chapter", "chapter123")
            
            assert result is True
            assert "chapter123" in tag.item_ids["chapter"]
            mock_mark_updated.assert_called_once()
        
        # Add note
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("note", "note123")
            
            assert result is True
            assert "note123" in tag.item_ids["note"]
            mock_mark_updated.assert_called_once()
        
        # Add document
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("document", "doc123")
            
            assert result is True
            assert "doc123" in tag.item_ids["document"]
            mock_mark_updated.assert_called_once()
        
        # Adding the same item again should not duplicate
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("character", "char123")
            
            assert result is True
            assert tag.item_ids["character"].count("char123") == 1
            mock_mark_updated.assert_not_called()

    def test_add_item_invalid(self):
        """Test adding an invalid item to the tag."""
        tag = Tag(name="Fantasy")
        
        # Add invalid item type
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.add_item("invalid_type", "id123")
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_remove_item_valid(self):
        """Test removing a valid item from the tag."""
        tag = Tag(name="Fantasy")
        
        # Add items
        tag.add_item("character", "char123")
        tag.add_item("location", "loc123")
        
        # Remove character
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.remove_item("character", "char123")
            
            assert result is True
            assert "char123" not in tag.item_ids["character"]
            mock_mark_updated.assert_called_once()
        
        # Remove location
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.remove_item("location", "loc123")
            
            assert result is True
            assert "loc123" not in tag.item_ids["location"]
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent item should not error
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.remove_item("character", "nonexistent")
            
            assert result is True
            mock_mark_updated.assert_not_called()

    def test_remove_item_invalid(self):
        """Test removing an invalid item from the tag."""
        tag = Tag(name="Fantasy")
        
        # Remove invalid item type
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            result = tag.remove_item("invalid_type", "id123")
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_get_items(self):
        """Test getting items with the tag."""
        tag = Tag(name="Fantasy")
        
        # Add items
        tag.add_item("character", "char123")
        tag.add_item("location", "loc123")
        
        # Get all items
        all_items = tag.get_items()
        assert all_items["character"] == ["char123"]
        assert all_items["location"] == ["loc123"]
        assert all_items["scene"] == []
        
        # Get specific type of items
        character_items = tag.get_items("character")
        assert character_items == {"character": ["char123"]}
        
        # Get invalid type of items
        invalid_items = tag.get_items("invalid_type")
        assert invalid_items == {}

    def test_get_item_count(self):
        """Test getting the count of items with the tag."""
        tag = Tag(name="Fantasy")
        
        # Add items
        tag.add_item("character", "char123")
        tag.add_item("character", "char456")
        tag.add_item("location", "loc123")
        
        # Get total count
        total_count = tag.get_item_count()
        assert total_count == 3
        
        # Get count for specific type
        character_count = tag.get_item_count("character")
        assert character_count == 2
        
        # Get count for invalid type
        invalid_count = tag.get_item_count("invalid_type")
        assert invalid_count == 0

    def test_set_parent_tag(self):
        """Test setting the parent tag."""
        tag = Tag(name="Fantasy")
        parent_id = "parent123"
        
        # Set parent tag
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.set_parent_tag(parent_id)
            
            assert tag.parent_tag_id == parent_id
            mock_mark_updated.assert_called_once()
        
        # Clear parent tag
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.set_parent_tag(None)
            
            assert tag.parent_tag_id is None
            mock_mark_updated.assert_called_once()

    def test_add_child_tag(self):
        """Test adding a child tag."""
        tag = Tag(name="Fantasy")
        child_id = "child123"
        
        # Add child tag
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.add_child_tag(child_id)
            
            assert child_id in tag.child_tag_ids
            mock_mark_updated.assert_called_once()
        
        # Adding the same child tag again should not duplicate
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.add_child_tag(child_id)
            
            assert tag.child_tag_ids.count(child_id) == 1
            mock_mark_updated.assert_not_called()

    def test_remove_child_tag(self):
        """Test removing a child tag."""
        tag = Tag(name="Fantasy")
        child_id = "child123"
        
        # Add child tag
        tag.add_child_tag(child_id)
        
        # Remove child tag
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.remove_child_tag(child_id)
            
            assert child_id not in tag.child_tag_ids
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent child tag should not error
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.remove_child_tag("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_has_children(self):
        """Test checking if the tag has children."""
        tag = Tag(name="Fantasy")
        
        # Initially no children
        assert tag.has_children() is False
        
        # Add child tag
        tag.add_child_tag("child123")
        
        # Now has children
        assert tag.has_children() is True
        
        # Remove child tag
        tag.remove_child_tag("child123")
        
        # No children again
        assert tag.has_children() is False

    def test_is_child_of(self):
        """Test checking if the tag is a child of another tag."""
        tag = Tag(name="Fantasy")
        parent_id = "parent123"
        
        # Initially not a child of any tag
        assert tag.is_child_of(parent_id) is False
        
        # Set parent tag
        tag.set_parent_tag(parent_id)
        
        # Now a child of the parent tag
        assert tag.is_child_of(parent_id) is True
        
        # Not a child of another tag
        assert tag.is_child_of("other_parent") is False
        
        # Clear parent tag
        tag.set_parent_tag(None)
        
        # Not a child of any tag again
        assert tag.is_child_of(parent_id) is False

    def test_metadata_operations(self):
        """Test metadata operations."""
        tag = Tag(name="Fantasy")
        
        # Set metadata
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.set_metadata("key1", "value1")
            
            assert tag.metadata["key1"] == "value1"
            mock_mark_updated.assert_called_once()
        
        # Get metadata
        assert tag.get_metadata("key1") == "value1"
        assert tag.get_metadata("nonexistent") is None
        assert tag.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.set_metadata("key1", "updated")
            
            assert tag.get_metadata("key1") == "updated"
            mock_mark_updated.assert_called_once()
        
        # Remove metadata
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.remove_metadata("key1")
            
            assert "key1" not in tag.metadata
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent metadata should not error
        with patch.object(tag, 'mark_updated') as mock_mark_updated:
            tag.remove_metadata("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_str_representation(self):
        """Test the string representation of a tag."""
        # Empty tag
        tag = Tag(name="Fantasy")
        expected = "Tag('Fantasy', items=0)"
        assert str(tag) == expected
        
        # Tag with items
        tag.add_item("character", "char123")
        tag.add_item("location", "loc123")
        expected = "Tag('Fantasy', items=2)"
        assert str(tag) == expected

    def test_to_dict(self):
        """Test converting a tag to a dictionary."""
        tag = Tag(
            name="Fantasy",
            description="Elements related to fantasy genre",
            color="#FF5733",
            project_id="project123"
        )
        
        tag_dict = tag.to_dict()
        
        assert tag_dict["name"] == "Fantasy"
        assert tag_dict["description"] == "Elements related to fantasy genre"
        assert tag_dict["color"] == "#FF5733"
        assert tag_dict["project_id"] == "project123"
        assert "id" in tag_dict
        assert "created_at" in tag_dict
        assert "updated_at" in tag_dict

    def test_from_dict(self):
        """Test creating a tag from a dictionary."""
        data: Dict[str, Any] = {
            "name": "Fantasy",
            "description": "Elements related to fantasy genre",
            "color": "#FF5733",
            "project_id": "project123",
            "item_ids": {
                "character": ["char123"],
                "location": ["loc123"]
            },
            "parent_tag_id": "parent123",
            "child_tag_ids": ["child123"]
        }
        
        tag = Tag.from_dict(data)
        
        assert tag.name == "Fantasy"
        assert tag.description == "Elements related to fantasy genre"
        assert tag.color == "#FF5733"
        assert tag.project_id == "project123"
        assert tag.item_ids["character"] == ["char123"]
        assert tag.item_ids["location"] == ["loc123"]
        assert tag.parent_tag_id == "parent123"
        assert tag.child_tag_ids == ["child123"]

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Tag(
            name="Fantasy",
            description="Elements related to fantasy genre",
            color="#FF5733",
            project_id="project123"
        )
        
        original.add_item("character", "char123")
        original.add_item("location", "loc123")
        original.set_parent_tag("parent123")
        original.add_child_tag("child123")
        original.set_metadata("key1", "value1")
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Tag.from_json(json_str)
        
        # Check that the restored tag has the same properties
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.color == original.color
        assert restored.project_id == original.project_id
        assert restored.item_ids["character"] == original.item_ids["character"]
        assert restored.item_ids["location"] == original.item_ids["location"]
        assert restored.parent_tag_id == original.parent_tag_id
        assert restored.child_tag_ids == original.child_tag_ids
        assert restored.metadata == original.metadata
