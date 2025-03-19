#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Outline model.
"""

import pytest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.outline import Outline, OutlineItem


class TestOutlineItem:
    """Test suite for the OutlineItem model."""

    def test_init_default_values(self):
        """Test that an outline item is initialized with default values."""
        item = OutlineItem()
        
        assert item.title == ""
        assert item.description == ""
        assert item.order == 0
        assert item.parent_id is None
        assert item.child_ids == []
        assert item.references == {
            "character": [],
            "location": [],
            "scene": [],
            "chapter": [],
            "note": [],
            "tag": []
        }
        assert item.metadata == {}
        assert isinstance(item.created_at, datetime.datetime)
        assert isinstance(item.updated_at, datetime.datetime)
        assert item.color is None
        assert item.is_completed is False

    def test_init_with_values(self):
        """Test that an outline item is initialized with provided values."""
        title = "Introduction"
        description = "The opening chapter of the novel"
        order = 1
        color = "#FF5733"
        
        item = OutlineItem(
            title=title,
            description=description,
            order=order,
            color=color
        )
        
        assert item.title == title
        assert item.description == description
        assert item.order == order
        assert item.color == color

    def test_set_description(self):
        """Test setting the item description."""
        item = OutlineItem(title="Introduction")
        description = "The opening chapter of the novel"
        
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_description(description)
            
            assert item.description == description
            mock_mark_updated.assert_called_once()

    def test_set_completed(self):
        """Test setting the completion status of an item."""
        item = OutlineItem(title="Introduction")
        
        # Set to completed
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_completed(True)
            
            assert item.is_completed is True
            mock_mark_updated.assert_called_once()
        
        # Set to not completed
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_completed(False)
            
            assert item.is_completed is False
            mock_mark_updated.assert_called_once()

    def test_set_parent(self):
        """Test setting the parent item."""
        item = OutlineItem(title="Introduction")
        parent_id = "parent123"
        
        # Set parent
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_parent(parent_id)
            
            assert item.parent_id == parent_id
            mock_mark_updated.assert_called_once()
        
        # Clear parent
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_parent(None)
            
            assert item.parent_id is None
            mock_mark_updated.assert_called_once()

    def test_add_child(self):
        """Test adding a child item."""
        item = OutlineItem(title="Introduction")
        child_id = "child123"
        
        # Add child
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.add_child(child_id)
            
            assert child_id in item.child_ids
            mock_mark_updated.assert_called_once()
        
        # Adding the same child again should not duplicate
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.add_child(child_id)
            
            assert item.child_ids.count(child_id) == 1
            mock_mark_updated.assert_not_called()

    def test_remove_child(self):
        """Test removing a child item."""
        item = OutlineItem(title="Introduction")
        child_id = "child123"
        
        # Add child
        item.add_child(child_id)
        
        # Remove child
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.remove_child(child_id)
            
            assert child_id not in item.child_ids
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent child should not error
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.remove_child("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_add_reference_valid(self):
        """Test adding a valid reference."""
        item = OutlineItem(title="Introduction")
        
        # Add character reference
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.add_reference("character", "char123")
            
            assert result is True
            assert "char123" in item.references["character"]
            mock_mark_updated.assert_called_once()
        
        # Add location reference
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.add_reference("location", "loc123")
            
            assert result is True
            assert "loc123" in item.references["location"]
            mock_mark_updated.assert_called_once()
        
        # Adding the same reference again should not duplicate
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.add_reference("character", "char123")
            
            assert result is True
            assert item.references["character"].count("char123") == 1
            mock_mark_updated.assert_not_called()

    def test_add_reference_invalid(self):
        """Test adding an invalid reference."""
        item = OutlineItem(title="Introduction")
        
        # Add invalid reference type
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.add_reference("invalid_type", "id123")
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_remove_reference_valid(self):
        """Test removing a valid reference."""
        item = OutlineItem(title="Introduction")
        
        # Add references
        item.add_reference("character", "char123")
        item.add_reference("location", "loc123")
        
        # Remove character reference
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.remove_reference("character", "char123")
            
            assert result is True
            assert "char123" not in item.references["character"]
            mock_mark_updated.assert_called_once()
        
        # Remove location reference
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.remove_reference("location", "loc123")
            
            assert result is True
            assert "loc123" not in item.references["location"]
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent reference should not error
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.remove_reference("character", "nonexistent")
            
            assert result is True
            mock_mark_updated.assert_not_called()

    def test_remove_reference_invalid(self):
        """Test removing an invalid reference."""
        item = OutlineItem(title="Introduction")
        
        # Remove invalid reference type
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            result = item.remove_reference("invalid_type", "id123")
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_get_references(self):
        """Test getting references."""
        item = OutlineItem(title="Introduction")
        
        # Add references
        item.add_reference("character", "char123")
        item.add_reference("location", "loc123")
        
        # Get all references
        all_refs = item.get_references()
        assert all_refs["character"] == ["char123"]
        assert all_refs["location"] == ["loc123"]
        assert all_refs["scene"] == []
        
        # Get specific type of references
        character_refs = item.get_references("character")
        assert character_refs == {"character": ["char123"]}
        
        # Get invalid type of references
        invalid_refs = item.get_references("invalid_type")
        assert invalid_refs == {}

    def test_set_color(self):
        """Test setting the color."""
        item = OutlineItem(title="Introduction")
        color = "#FF5733"
        
        # Set color
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_color(color)
            
            assert item.color == color
            mock_mark_updated.assert_called_once()
        
        # Clear color
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_color(None)
            
            assert item.color is None
            mock_mark_updated.assert_called_once()

    def test_metadata_operations(self):
        """Test metadata operations."""
        item = OutlineItem(title="Introduction")
        
        # Set metadata
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_metadata("key1", "value1")
            
            assert item.metadata["key1"] == "value1"
            mock_mark_updated.assert_called_once()
        
        # Get metadata
        assert item.get_metadata("key1") == "value1"
        assert item.get_metadata("nonexistent") is None
        assert item.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.set_metadata("key1", "updated")
            
            assert item.get_metadata("key1") == "updated"
            mock_mark_updated.assert_called_once()
        
        # Remove metadata
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.remove_metadata("key1")
            
            assert "key1" not in item.metadata
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent metadata should not error
        with patch.object(item, 'mark_updated') as mock_mark_updated:
            item.remove_metadata("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_str_representation(self):
        """Test the string representation of an outline item."""
        # Not completed
        item = OutlineItem(title="Introduction")
        expected = "OutlineItem('Introduction')"
        assert str(item) == expected
        
        # Completed
        item.set_completed(True)
        expected = "OutlineItem('Introduction' (Completed))"
        assert str(item) == expected

    def test_to_dict(self):
        """Test converting an outline item to a dictionary."""
        item = OutlineItem(
            title="Introduction",
            description="The opening chapter of the novel",
            order=1,
            color="#FF5733"
        )
        
        item_dict = item.to_dict()
        
        assert item_dict["title"] == "Introduction"
        assert item_dict["description"] == "The opening chapter of the novel"
        assert item_dict["order"] == 1
        assert item_dict["color"] == "#FF5733"
        assert "id" in item_dict
        assert "created_at" in item_dict
        assert "updated_at" in item_dict

    def test_from_dict(self):
        """Test creating an outline item from a dictionary."""
        data: Dict[str, Any] = {
            "title": "Introduction",
            "description": "The opening chapter of the novel",
            "order": 1,
            "color": "#FF5733",
            "parent_id": "parent123",
            "child_ids": ["child123"],
            "is_completed": True
        }
        
        item = OutlineItem.from_dict(data)
        
        assert item.title == "Introduction"
        assert item.description == "The opening chapter of the novel"
        assert item.order == 1
        assert item.color == "#FF5733"
        assert item.parent_id == "parent123"
        assert item.child_ids == ["child123"]
        assert item.is_completed is True

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = OutlineItem(
            title="Introduction",
            description="The opening chapter of the novel",
            order=1,
            color="#FF5733"
        )
        
        original.set_parent("parent123")
        original.add_child("child123")
        original.add_reference("character", "char123")
        original.set_metadata("key1", "value1")
        original.set_completed(True)
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = OutlineItem.from_json(json_str)
        
        # Check that the restored item has the same properties
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.order == original.order
        assert restored.color == original.color
        assert restored.parent_id == original.parent_id
        assert restored.child_ids == original.child_ids
        assert restored.references["character"] == original.references["character"]
        assert restored.metadata == original.metadata
        assert restored.is_completed == original.is_completed


class TestOutline:
    """Test suite for the Outline model."""

    def test_init_default_values(self):
        """Test that an outline is initialized with default values."""
        outline = Outline()
        
        assert outline.title == ""
        assert outline.description == ""
        assert outline.project_id == ""
        assert outline.document_id is None
        assert outline.root_item_ids == []
        assert outline.items == {}
        assert outline.metadata == {}
        assert isinstance(outline.created_at, datetime.datetime)
        assert isinstance(outline.updated_at, datetime.datetime)

    def test_init_with_values(self):
        """Test that an outline is initialized with provided values."""
        title = "Novel Outline"
        description = "Outline for my fantasy novel"
        project_id = "project123"
        
        outline = Outline(
            title=title,
            description=description,
            project_id=project_id
        )
        
        assert outline.title == title
        assert outline.description == description
        assert outline.project_id == project_id

    def test_set_description(self):
        """Test setting the outline description."""
        outline = Outline(title="Novel Outline")
        description = "Outline for my fantasy novel"
        
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.set_description(description)
            
            assert outline.description == description
            mock_mark_updated.assert_called_once()

    def test_add_item_as_root(self):
        """Test adding an item as a root item."""
        outline = Outline(title="Novel Outline")
        item = OutlineItem(title="Introduction")
        
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.add_item(item)
            
            assert item.id in outline.items
            assert item.id in outline.root_item_ids
            assert item.parent_id is None
            mock_mark_updated.assert_called_once()

    def test_add_item_with_parent(self):
        """Test adding an item with a parent."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        child = OutlineItem(title="Chapter 1")
        
        # Add parent
        outline.add_item(parent)
        
        # Add child with parent
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.add_item(child, parent.id)
            
            assert child.id in outline.items
            assert child.id not in outline.root_item_ids
            assert child.parent_id == parent.id
            assert child.id in outline.items[parent.id].child_ids
            mock_mark_updated.assert_called_once()

    def test_add_item_with_nonexistent_parent(self):
        """Test adding an item with a non-existent parent."""
        outline = Outline(title="Novel Outline")
        item = OutlineItem(title="Chapter 1")
        
        # Add with non-existent parent
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.add_item(item, "nonexistent")
            
            assert item.id in outline.items
            assert item.id in outline.root_item_ids
            assert item.parent_id is None
            mock_mark_updated.assert_called_once()

    def test_remove_item_root(self):
        """Test removing a root item."""
        outline = Outline(title="Novel Outline")
        item = OutlineItem(title="Introduction")
        
        # Add item
        outline.add_item(item)
        
        # Remove item
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.remove_item(item.id)
            
            assert result is True
            assert item.id not in outline.items
            assert item.id not in outline.root_item_ids
            mock_mark_updated.assert_called_once()

    def test_remove_item_with_parent(self):
        """Test removing an item with a parent."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        child = OutlineItem(title="Chapter 1")
        
        # Add parent and child
        outline.add_item(parent)
        outline.add_item(child, parent.id)
        
        # Remove child
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.remove_item(child.id)
            
            assert result is True
            assert child.id not in outline.items
            assert child.id not in outline.items[parent.id].child_ids
            mock_mark_updated.assert_called_once()

    def test_remove_item_with_children(self):
        """Test removing an item with children."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        child1 = OutlineItem(title="Chapter 1")
        child2 = OutlineItem(title="Chapter 2")
        
        # Add parent and children
        outline.add_item(parent)
        outline.add_item(child1, parent.id)
        outline.add_item(child2, parent.id)
        
        # Remove parent
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.remove_item(parent.id)
            
            assert result is True
            assert parent.id not in outline.items
            assert parent.id not in outline.root_item_ids
            
            # Children should become root items
            assert child1.id in outline.root_item_ids
            assert child2.id in outline.root_item_ids
            assert outline.items[child1.id].parent_id is None
            assert outline.items[child2.id].parent_id is None
            
            mock_mark_updated.assert_called_once()

    def test_remove_item_with_parent_and_children(self):
        """Test removing an item with a parent and children."""
        outline = Outline(title="Novel Outline")
        grandparent = OutlineItem(title="Book")
        parent = OutlineItem(title="Part 1")
        child1 = OutlineItem(title="Chapter 1")
        child2 = OutlineItem(title="Chapter 2")
        
        # Add items
        outline.add_item(grandparent)
        outline.add_item(parent, grandparent.id)
        outline.add_item(child1, parent.id)
        outline.add_item(child2, parent.id)
        
        # Remove parent
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.remove_item(parent.id)
            
            assert result is True
            assert parent.id not in outline.items
            
            # Children should be connected to grandparent
            assert child1.id not in outline.root_item_ids
            assert child2.id not in outline.root_item_ids
            assert outline.items[child1.id].parent_id == grandparent.id
            assert outline.items[child2.id].parent_id == grandparent.id
            assert child1.id in outline.items[grandparent.id].child_ids
            assert child2.id in outline.items[grandparent.id].child_ids
            
            mock_mark_updated.assert_called_once()

    def test_remove_nonexistent_item(self):
        """Test removing a non-existent item."""
        outline = Outline(title="Novel Outline")
        
        # Remove non-existent item
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.remove_item("nonexistent")
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_get_item(self):
        """Test getting an item."""
        outline = Outline(title="Novel Outline")
        item = OutlineItem(title="Introduction")
        
        # Add item
        outline.add_item(item)
        
        # Get item
        retrieved = outline.get_item(item.id)
        assert retrieved is not None
        assert retrieved.title == "Introduction"
        
        # Get non-existent item
        assert outline.get_item("nonexistent") is None

    def test_get_root_items(self):
        """Test getting root items."""
        outline = Outline(title="Novel Outline")
        item1 = OutlineItem(title="Introduction")
        item2 = OutlineItem(title="Part 1")
        child = OutlineItem(title="Chapter 1")
        
        # Add items
        outline.add_item(item1)
        outline.add_item(item2)
        outline.add_item(child, item2.id)
        
        # Get root items
        root_items = outline.get_root_items()
        assert len(root_items) == 2
        assert any(item.title == "Introduction" for item in root_items)
        assert any(item.title == "Part 1" for item in root_items)

    def test_get_children(self):
        """Test getting children of an item."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        child1 = OutlineItem(title="Chapter 1")
        child2 = OutlineItem(title="Chapter 2")
        
        # Add items
        outline.add_item(parent)
        outline.add_item(child1, parent.id)
        outline.add_item(child2, parent.id)
        
        # Get children
        children = outline.get_children(parent.id)
        assert len(children) == 2
        assert any(item.title == "Chapter 1" for item in children)
        assert any(item.title == "Chapter 2" for item in children)
        
        # Get children of non-existent item
        assert outline.get_children("nonexistent") == []

    def test_move_item(self):
        """Test moving an item."""
        outline = Outline(title="Novel Outline")
        part1 = OutlineItem(title="Part 1")
        part2 = OutlineItem(title="Part 2")
        chapter1 = OutlineItem(title="Chapter 1")
        
        # Add items
        outline.add_item(part1)
        outline.add_item(part2)
        outline.add_item(chapter1, part1.id)
        
        # Move chapter from part1 to part2
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.move_item(chapter1.id, part2.id, 0)
            
            assert result is True
            assert chapter1.id not in outline.items[part1.id].child_ids
            assert chapter1.id in outline.items[part2.id].child_ids
            assert outline.items[chapter1.id].parent_id == part2.id
            mock_mark_updated.assert_called_once()

    def test_move_item_to_root(self):
        """Test moving an item to the root level."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        child = OutlineItem(title="Chapter 1")
        
        # Add items
        outline.add_item(parent)
        outline.add_item(child, parent.id)
        
        # Move child to root
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.move_item(child.id, None, 0)
            
            assert result is True
            assert child.id not in outline.items[parent.id].child_ids
            assert child.id in outline.root_item_ids
            assert outline.items[child.id].parent_id is None
            mock_mark_updated.assert_called_once()

    def test_move_nonexistent_item(self):
        """Test moving a non-existent item."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        
        # Add parent
        outline.add_item(parent)
        
        # Move non-existent item
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.move_item("nonexistent", parent.id, 0)
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_move_to_nonexistent_parent(self):
        """Test moving an item to a non-existent parent."""
        outline = Outline(title="Novel Outline")
        item = OutlineItem(title="Chapter 1")
        
        # Add item
        outline.add_item(item)
        
        # Move to non-existent parent
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.move_item(item.id, "nonexistent", 0)
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_move_to_descendant(self):
        """Test moving an item to its own descendant (circular reference)."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        child = OutlineItem(title="Chapter 1")
        grandchild = OutlineItem(title="Section 1")
        
        # Add items
        outline.add_item(parent)
        outline.add_item(child, parent.id)
        outline.add_item(grandchild, child.id)
        
        # Try to move parent to grandchild (circular reference)
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            result = outline.move_item(parent.id, grandchild.id, 0)
            
            assert result is False
            mock_mark_updated.assert_not_called()

    def test_is_descendant(self):
        """Test checking if an item is a descendant of another item."""
        outline = Outline(title="Novel Outline")
        parent = OutlineItem(title="Part 1")
        child = OutlineItem(title="Chapter 1")
        grandchild = OutlineItem(title="Section 1")
        
        # Add items
        outline.add_item(parent)
        outline.add_item(child, parent.id)
        outline.add_item(grandchild, child.id)
        
        # Check relationships
        assert outline._is_descendant(child.id, parent.id) is True
        assert outline._is_descendant(grandchild.id, parent.id) is True
        assert outline._is_descendant(grandchild.id, child.id) is True
        assert outline._is_descendant(parent.id, child.id) is False
        assert outline._is_descendant(parent.id, grandchild.id) is False
        assert outline._is_descendant(child.id, grandchild.id) is False
        assert outline._is_descendant("nonexistent", parent.id) is False
        assert outline._is_descendant(parent.id, "nonexistent") is False

    def test_get_item_count(self):
        """Test getting the number of items in the outline."""
        outline = Outline(title="Novel Outline")
        
        # Initially empty
        assert outline.get_item_count() == 0
        
        # Add items
        outline.add_item(OutlineItem(title="Introduction"))
        outline.add_item(OutlineItem(title="Part 1"))
        
        # Now has 2 items
        assert outline.get_item_count() == 2

    def test_get_completed_count(self):
        """Test getting the number of completed items in the outline."""
        outline = Outline(title="Novel Outline")
        
        # Add items
        item1 = OutlineItem(title="Introduction")
        item2 = OutlineItem(title="Part 1")
        item3 = OutlineItem(title="Part 2")
        
        outline.add_item(item1)
        outline.add_item(item2)
        outline.add_item(item3)
        
        # Initially none completed
        assert outline.get_completed_count() == 0
        
        # Mark some as completed
        outline.items[item1.id].set_completed(True)
        outline.items[item2.id].set_completed(True)
        
        # Now 2 completed
        assert outline.get_completed_count() == 2

    def test_get_completion_percentage(self):
        """Test getting the completion percentage of the outline."""
        outline = Outline(title="Novel Outline")
        
        # Empty outline
        assert outline.get_completion_percentage() == 0.0
        
        # Add items
        item1 = OutlineItem(title="Introduction")
        item2 = OutlineItem(title="Part 1")
        item3 = OutlineItem(title="Part 2")
        
        outline.add_item(item1)
        outline.add_item(item2)
        outline.add_item(item3)
        
        # Initially none completed
        assert outline.get_completion_percentage() == 0.0
        
        # Mark some as completed
        outline.items[item1.id].set_completed(True)
        outline.items[item2.id].set_completed(True)
        
        # Now 2/3 completed (66.67%)
        assert outline.get_completion_percentage() == pytest.approx(66.67, 0.01)

    def test_metadata_operations(self):
        """Test metadata operations."""
        outline = Outline(title="Novel Outline")
        
        # Set metadata
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.set_metadata("key1", "value1")
            
            assert outline.metadata["key1"] == "value1"
            mock_mark_updated.assert_called_once()
        
        # Get metadata
        assert outline.get_metadata("key1") == "value1"
        assert outline.get_metadata("nonexistent") is None
        assert outline.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.set_metadata("key1", "updated")
            
            assert outline.get_metadata("key1") == "updated"
            mock_mark_updated.assert_called_once()
        
        # Remove metadata
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.remove_metadata("key1")
            
            assert "key1" not in outline.metadata
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent metadata should not error
        with patch.object(outline, 'mark_updated') as mock_mark_updated:
            outline.remove_metadata("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_str_representation(self):
        """Test the string representation of an outline."""
        # Empty outline
        outline = Outline(title="Novel Outline")
        expected = "Outline('Novel Outline', items=0, completion=0.0%)"
        assert str(outline) == expected
        
        # Outline with items
        item1 = OutlineItem(title="Introduction")
        item2 = OutlineItem(title="Part 1")
        
        outline.add_item(item1)
        outline.add_item(item2)
        
        expected = "Outline('Novel Outline', items=2, completion=0.0%)"
        assert str(outline) == expected
        
        # Outline with completed items
        outline.items[item1.id].set_completed(True)
        
        expected = "Outline('Novel Outline', items=2, completion=50.0%)"
        assert str(outline) == expected

    def test_to_dict(self):
        """Test converting an outline to a dictionary."""
        outline = Outline(
            title="Novel Outline",
            description="Outline for my fantasy novel",
            project_id="project123"
        )
        
        # Add some items
        item1 = OutlineItem(title="Introduction")
        item2 = OutlineItem(title="Part 1")
        
        outline.add_item(item1)
        outline.add_item(item2)
        
        outline_dict = outline.to_dict()
        
        assert outline_dict["title"] == "Novel Outline"
        assert outline_dict["description"] == "Outline for my fantasy novel"
        assert outline_dict["project_id"] == "project123"
        assert len(outline_dict["items"]) == 2
        assert "id" in outline_dict
        assert "created_at" in outline_dict
        assert "updated_at" in outline_dict

    def test_from_dict(self):
        """Test creating an outline from a dictionary."""
        item1_data = {
            "id": "item1",
            "title": "Introduction",
            "description": "The opening chapter",
            "is_completed": True
        }
        
        item2_data = {
            "id": "item2",
            "title": "Part 1",
            "description": "The first part",
            "is_completed": False
        }
        
        data: Dict[str, Any] = {
            "title": "Novel Outline",
            "description": "Outline for my fantasy novel",
            "project_id": "project123",
            "root_item_ids": ["item1", "item2"],
            "items": {
                "item1": item1_data,
                "item2": item2_data
            }
        }
        
        outline = Outline.from_dict(data)
        
        assert outline.title == "Novel Outline"
        assert outline.description == "Outline for my fantasy novel"
        assert outline.project_id == "project123"
        assert outline.root_item_ids == ["item1", "item2"]
        assert len(outline.items) == 2
        assert outline.items["item1"].title == "Introduction"
        assert outline.items["item2"].title == "Part 1"
        assert outline.items["item1"].is_completed is True
        assert outline.items["item2"].is_completed is False

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Outline(
            title="Novel Outline",
            description="Outline for my fantasy novel",
            project_id="project123"
        )
        
        # Add some items
        item1 = OutlineItem(title="Introduction")
        item2 = OutlineItem(title="Part 1")
        child = OutlineItem(title="Chapter 1")
        
        original.add_item(item1)
        original.add_item(item2)
        original.add_item(child, item2.id)
        
        # Set some properties
        original.items[item1.id].set_completed(True)
        original.items[item1.id].set_metadata("key1", "value1")
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Outline.from_json(json_str)
        
        # Check that the restored outline has the same properties
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.project_id == original.project_id
        assert len(restored.items) == len(original.items)
        assert restored.root_item_ids == original.root_item_ids
        
        # Check that the items have the same properties
        for item_id, item in original.items.items():
            assert item_id in restored.items
            restored_item = restored.items[item_id]
            assert restored_item.title == item.title
            assert restored_item.is_completed == item.is_completed
            
            # Check parent-child relationships
            if item.parent_id is not None:
                assert restored_item.parent_id == item.parent_id
                assert item_id in restored.items[item.parent_id].child_ids
