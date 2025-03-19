#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Location model.
"""

import pytest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.location import Location


class TestLocation:
    """Test suite for the Location model."""

    def test_init_default_values(self):
        """Test that a location is initialized with default values."""
        location = Location()
        
        assert location.name == ""
        assert location.type == Location.TYPE_FICTIONAL
        assert location.description == ""
        assert location.address is None
        assert location.city is None
        assert location.region is None
        assert location.country is None
        assert location.coordinates is None
        assert location.history == ""
        assert location.significance == ""
        assert location.notes == ""
        assert location.project_id == ""
        assert location.document_id is None
        assert location.scene_ids == []
        assert location.parent_location_id is None
        assert location.child_location_ids == []
        assert location.metadata == {}
        assert isinstance(location.created_at, datetime.datetime)
        assert isinstance(location.updated_at, datetime.datetime)
        assert location.color is None
        assert location.tags == []
        assert location.image_path is None
        assert location.map_path is None

    def test_init_with_values(self):
        """Test that a location is initialized with provided values."""
        name = "Castle Black"
        location_type = Location.TYPE_FICTIONAL
        description = "A fortress at the Wall"
        
        location = Location(
            name=name,
            type=location_type,
            description=description
        )
        
        assert location.name == name
        assert location.type == location_type
        assert location.description == description

    def test_init_with_invalid_type(self):
        """Test that a location with invalid type defaults to fictional."""
        location = Location(type="invalid_type")
        
        assert location.type == Location.TYPE_FICTIONAL

    def test_set_type_valid(self):
        """Test setting a valid location type."""
        location = Location(name="Test Location")
        
        # Set to real
        location.set_type(Location.TYPE_REAL)
        assert location.type == Location.TYPE_REAL
        
        # Set to fictional
        location.set_type(Location.TYPE_FICTIONAL)
        assert location.type == Location.TYPE_FICTIONAL

    def test_set_type_invalid(self):
        """Test setting an invalid location type."""
        location = Location(name="Test Location", type=Location.TYPE_FICTIONAL)
        
        # Set to invalid type
        location.set_type("Invalid Type")
        
        # Type should remain unchanged
        assert location.type == Location.TYPE_FICTIONAL

    def test_set_description(self):
        """Test setting the location description."""
        location = Location(name="Test Location")
        description = "A beautiful castle on a hill."
        
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_description(description)
            
            assert location.description == description
            mock_mark_updated.assert_called_once()

    def test_set_address(self):
        """Test setting the address."""
        location = Location(name="Test Location")
        address = "123 Main St"
        
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_address(address)
            
            assert location.address == address
            mock_mark_updated.assert_called_once()
        
        # Clear address
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_address(None)
            
            assert location.address is None
            mock_mark_updated.assert_called_once()

    def test_set_coordinates(self):
        """Test setting the coordinates."""
        location = Location(name="Test Location")
        coordinates = "40.7128° N, 74.0060° W"
        
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_coordinates(coordinates)
            
            assert location.coordinates == coordinates
            mock_mark_updated.assert_called_once()
        
        # Clear coordinates
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_coordinates(None)
            
            assert location.coordinates is None
            mock_mark_updated.assert_called_once()

    def test_set_history(self):
        """Test setting the history."""
        location = Location(name="Test Location")
        history = "Built in the 12th century, this castle has seen many battles."
        
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_history(history)
            
            assert location.history == history
            mock_mark_updated.assert_called_once()

    def test_set_significance(self):
        """Test setting the significance."""
        location = Location(name="Test Location")
        significance = "This is where the protagonist first meets their mentor."
        
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_significance(significance)
            
            assert location.significance == significance
            mock_mark_updated.assert_called_once()

    def test_set_notes(self):
        """Test setting the notes."""
        location = Location(name="Test Location")
        notes = "Remember to describe the view from the tower."
        
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_notes(notes)
            
            assert location.notes == notes
            mock_mark_updated.assert_called_once()

    def test_scene_operations(self):
        """Test scene operations."""
        location = Location(name="Test Location")
        scene_id = "scene123"
        
        # Add scene
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.add_scene(scene_id)
            
            assert scene_id in location.scene_ids
            mock_mark_updated.assert_called_once()
        
        # Adding the same scene again should not duplicate
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.add_scene(scene_id)
            
            assert location.scene_ids.count(scene_id) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove scene
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_scene(scene_id)
            
            assert scene_id not in location.scene_ids
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent scene should not error
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_scene("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_parent_location_operations(self):
        """Test parent location operations."""
        location = Location(name="Test Location")
        parent_id = "location123"
        
        # Set parent location
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_parent_location(parent_id)
            
            assert location.parent_location_id == parent_id
            mock_mark_updated.assert_called_once()
        
        # Clear parent location
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_parent_location(None)
            
            assert location.parent_location_id is None
            mock_mark_updated.assert_called_once()

    def test_child_location_operations(self):
        """Test child location operations."""
        location = Location(name="Test Location")
        child_id = "location456"
        
        # Add child location
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.add_child_location(child_id)
            
            assert child_id in location.child_location_ids
            mock_mark_updated.assert_called_once()
        
        # Adding the same child location again should not duplicate
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.add_child_location(child_id)
            
            assert location.child_location_ids.count(child_id) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove child location
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_child_location(child_id)
            
            assert child_id not in location.child_location_ids
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent child location should not error
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_child_location("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_set_image_path(self):
        """Test setting the image path."""
        location = Location(name="Test Location")
        path = "/path/to/image.jpg"
        
        # Set path
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_image_path(path)
            
            assert location.image_path == path
            mock_mark_updated.assert_called_once()
        
        # Clear path
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_image_path(None)
            
            assert location.image_path is None
            mock_mark_updated.assert_called_once()

    def test_set_map_path(self):
        """Test setting the map path."""
        location = Location(name="Test Location")
        path = "/path/to/map.jpg"
        
        # Set path
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_map_path(path)
            
            assert location.map_path == path
            mock_mark_updated.assert_called_once()
        
        # Clear path
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_map_path(None)
            
            assert location.map_path is None
            mock_mark_updated.assert_called_once()

    def test_set_color(self):
        """Test setting the color."""
        location = Location(name="Test Location")
        color = "#FF0000"
        
        # Set color
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_color(color)
            
            assert location.color == color
            mock_mark_updated.assert_called_once()
        
        # Clear color
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_color(None)
            
            assert location.color is None
            mock_mark_updated.assert_called_once()

    def test_tag_operations(self):
        """Test tag operations."""
        location = Location(name="Test Location")
        tag = "castle"
        
        # Add tag
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.add_tag(tag)
            
            assert tag in location.tags
            mock_mark_updated.assert_called_once()
        
        # Adding the same tag again should not duplicate
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.add_tag(tag)
            
            assert location.tags.count(tag) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove tag
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_tag(tag)
            
            assert tag not in location.tags
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent tag should not error
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_tag("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_metadata_operations(self):
        """Test metadata operations."""
        location = Location(name="Test Location")
        
        # Set metadata
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_metadata("key1", "value1")
            
            assert location.metadata["key1"] == "value1"
            mock_mark_updated.assert_called_once()
        
        # Get metadata
        assert location.get_metadata("key1") == "value1"
        assert location.get_metadata("nonexistent") is None
        assert location.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.set_metadata("key1", "updated")
            
            assert location.get_metadata("key1") == "updated"
            mock_mark_updated.assert_called_once()
        
        # Remove metadata
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_metadata("key1")
            
            assert "key1" not in location.metadata
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent metadata should not error
        with patch.object(location, 'mark_updated') as mock_mark_updated:
            location.remove_metadata("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_str_representation(self):
        """Test the string representation of a location."""
        location = Location(name="Castle Black", type=Location.TYPE_FICTIONAL)
        
        expected = "Location('Castle Black', type='Fictional')"
        assert str(location) == expected

    def test_to_dict(self):
        """Test converting a location to a dictionary."""
        location = Location(
            name="Castle Black",
            type=Location.TYPE_FICTIONAL,
            description="A fortress at the Wall"
        )
        
        location_dict = location.to_dict()
        
        assert location_dict["name"] == "Castle Black"
        assert location_dict["type"] == Location.TYPE_FICTIONAL
        assert location_dict["description"] == "A fortress at the Wall"
        assert "id" in location_dict
        assert "created_at" in location_dict
        assert "updated_at" in location_dict

    def test_from_dict(self):
        """Test creating a location from a dictionary."""
        data: Dict[str, Any] = {
            "name": "Castle Black",
            "type": Location.TYPE_FICTIONAL,
            "description": "A fortress at the Wall",
            "tags": ["castle", "fortress"],
            "coordinates": "64.0° N, 20.0° W"
        }
        
        location = Location.from_dict(data)
        
        assert location.name == "Castle Black"
        assert location.type == Location.TYPE_FICTIONAL
        assert location.description == "A fortress at the Wall"
        assert location.tags == ["castle", "fortress"]
        assert location.coordinates == "64.0° N, 20.0° W"

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Location(
            name="Castle Black",
            type=Location.TYPE_FICTIONAL,
            description="A fortress at the Wall",
            tags=["castle", "fortress"],
            coordinates="64.0° N, 20.0° W"
        )
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Location.from_json(json_str)
        
        # Check that the restored location has the same properties
        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.description == original.description
        assert restored.tags == original.tags
        assert restored.coordinates == original.coordinates
