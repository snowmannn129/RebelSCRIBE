#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Character model.
"""

import pytest
import unittest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.character import Character


class TestCharacter(unittest.TestCase):
    """Test suite for the Character model."""

    def test_init_default_values(self):
        """Test that a character is initialized with default values."""
        character = Character()
        
        assert character.name == ""
        assert character.full_name is None
        assert character.nickname is None
        assert character.role == Character.ROLE_SUPPORTING
        assert character.age is None
        assert character.gender is None
        assert character.occupation is None
        assert character.physical_description == ""
        assert character.personality == ""
        assert character.background == ""
        assert character.goals == ""
        assert character.motivations == ""
        assert character.conflicts == ""
        assert character.relationships == {}
        assert character.notes == ""
        assert character.arc == ""
        assert character.project_id == ""
        assert character.document_id is None
        assert character.scene_ids == []
        assert character.metadata == {}
        assert isinstance(character.created_at, datetime.datetime)
        assert isinstance(character.updated_at, datetime.datetime)
        assert character.color is None
        assert character.tags == []
        assert character.image_path is None

    def test_init_with_values(self):
        """Test that a character is initialized with provided values."""
        name = "John Doe"
        role = Character.ROLE_PROTAGONIST
        age = 30
        
        character = Character(
            name=name,
            role=role,
            age=age
        )
        
        assert character.name == name
        assert character.role == role
        assert character.age == age

    def test_init_with_invalid_role(self):
        """Test that a character with invalid role defaults to supporting."""
        character = Character(role="invalid_role")
        
        assert character.role == Character.ROLE_SUPPORTING

    def test_set_role_valid(self):
        """Test setting a valid role."""
        character = Character(name="Test Character")
        
        # Set to protagonist
        character.set_role(Character.ROLE_PROTAGONIST)
        assert character.role == Character.ROLE_PROTAGONIST
        
        # Set to antagonist
        character.set_role(Character.ROLE_ANTAGONIST)
        assert character.role == Character.ROLE_ANTAGONIST
        
        # Set to supporting
        character.set_role(Character.ROLE_SUPPORTING)
        assert character.role == Character.ROLE_SUPPORTING
        
        # Set to minor
        character.set_role(Character.ROLE_MINOR)
        assert character.role == Character.ROLE_MINOR

    def test_set_role_invalid(self):
        """Test setting an invalid role."""
        character = Character(name="Test Character", role=Character.ROLE_PROTAGONIST)
        
        # Set to invalid role
        character.set_role("Invalid Role")
        
        # Role should remain unchanged
        assert character.role == Character.ROLE_PROTAGONIST

    def test_set_physical_description(self):
        """Test setting the physical description."""
        character = Character(name="Test Character")
        description = "Tall with brown hair and blue eyes."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_physical_description(description)
            
            assert character.physical_description == description
            mock_mark_updated.assert_called_once()

    def test_set_personality(self):
        """Test setting the personality."""
        character = Character(name="Test Character")
        personality = "Introverted but kind-hearted."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_personality(personality)
            
            assert character.personality == personality
            mock_mark_updated.assert_called_once()

    def test_set_background(self):
        """Test setting the background."""
        character = Character(name="Test Character")
        background = "Grew up in a small town, moved to the city at 18."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_background(background)
            
            assert character.background == background
            mock_mark_updated.assert_called_once()

    def test_set_goals(self):
        """Test setting the goals."""
        character = Character(name="Test Character")
        goals = "Become a successful writer."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_goals(goals)
            
            assert character.goals == goals
            mock_mark_updated.assert_called_once()

    def test_set_motivations(self):
        """Test setting the motivations."""
        character = Character(name="Test Character")
        motivations = "Wants to prove critics wrong."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_motivations(motivations)
            
            assert character.motivations == motivations
            mock_mark_updated.assert_called_once()

    def test_set_conflicts(self):
        """Test setting the conflicts."""
        character = Character(name="Test Character")
        conflicts = "Struggles with self-doubt and financial problems."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_conflicts(conflicts)
            
            assert character.conflicts == conflicts
            mock_mark_updated.assert_called_once()

    def test_set_arc(self):
        """Test setting the character arc."""
        character = Character(name="Test Character")
        arc = "Learns to believe in themselves and overcomes obstacles."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_arc(arc)
            
            assert character.arc == arc
            mock_mark_updated.assert_called_once()

    def test_set_notes(self):
        """Test setting the notes."""
        character = Character(name="Test Character")
        notes = "Remember to develop backstory further."
        
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_notes(notes)
            
            assert character.notes == notes
            mock_mark_updated.assert_called_once()

    def test_relationship_operations(self):
        """Test relationship operations."""
        character = Character(name="Test Character")
        other_character_id = "character123"
        relationship = "Best friend and confidant."
        
        # Add relationship
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.add_relationship(other_character_id, relationship)
            
            assert character.relationships[other_character_id] == relationship
            mock_mark_updated.assert_called_once()
        
        # Get relationship
        assert character.get_relationship(other_character_id) == relationship
        assert character.get_relationship("nonexistent") is None
        
        # Update relationship
        updated_relationship = "Former friend, now rival."
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.add_relationship(other_character_id, updated_relationship)
            
            assert character.relationships[other_character_id] == updated_relationship
            mock_mark_updated.assert_called_once()
        
        # Remove relationship
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_relationship(other_character_id)
            
            assert other_character_id not in character.relationships
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent relationship should not error
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_relationship("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_scene_operations(self):
        """Test scene operations."""
        character = Character(name="Test Character")
        scene_id = "scene123"
        
        # Add scene
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.add_scene(scene_id)
            
            assert scene_id in character.scene_ids
            mock_mark_updated.assert_called_once()
        
        # Adding the same scene again should not duplicate
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.add_scene(scene_id)
            
            assert character.scene_ids.count(scene_id) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove scene
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_scene(scene_id)
            
            assert scene_id not in character.scene_ids
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent scene should not error
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_scene("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_set_image_path(self):
        """Test setting the image path."""
        character = Character(name="Test Character")
        path = "/path/to/image.jpg"
        
        # Set path
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_image_path(path)
            
            assert character.image_path == path
            mock_mark_updated.assert_called_once()
        
        # Clear path
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_image_path(None)
            
            assert character.image_path is None
            mock_mark_updated.assert_called_once()

    def test_set_color(self):
        """Test setting the color."""
        character = Character(name="Test Character")
        color = "#FF0000"
        
        # Set color
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_color(color)
            
            assert character.color == color
            mock_mark_updated.assert_called_once()
        
        # Clear color
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_color(None)
            
            assert character.color is None
            mock_mark_updated.assert_called_once()

    def test_tag_operations(self):
        """Test tag operations."""
        character = Character(name="Test Character")
        tag = "protagonist"
        
        # Add tag
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.add_tag(tag)
            
            assert tag in character.tags
            mock_mark_updated.assert_called_once()
        
        # Adding the same tag again should not duplicate
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.add_tag(tag)
            
            assert character.tags.count(tag) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove tag
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_tag(tag)
            
            assert tag not in character.tags
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent tag should not error
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_tag("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_metadata_operations(self):
        """Test metadata operations."""
        character = Character(name="Test Character")
        
        # Set metadata
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_metadata("key1", "value1")
            
            assert character.metadata["key1"] == "value1"
            mock_mark_updated.assert_called_once()
        
        # Get metadata
        assert character.get_metadata("key1") == "value1"
        assert character.get_metadata("nonexistent") is None
        assert character.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.set_metadata("key1", "updated")
            
            assert character.get_metadata("key1") == "updated"
            mock_mark_updated.assert_called_once()
        
        # Remove metadata
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_metadata("key1")
            
            assert "key1" not in character.metadata
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent metadata should not error
        with patch.object(character, 'mark_updated') as mock_mark_updated:
            character.remove_metadata("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_str_representation(self):
        """Test the string representation of a character."""
        character = Character(name="John Doe", role=Character.ROLE_PROTAGONIST)
        
        expected = "Character('John Doe', role='Protagonist')"
        assert str(character) == expected

    def test_to_dict(self):
        """Test converting a character to a dictionary."""
        character = Character(
            name="John Doe",
            role=Character.ROLE_PROTAGONIST,
            age=30
        )
        
        character_dict = character.to_dict()
        
        assert character_dict["name"] == "John Doe"
        assert character_dict["role"] == Character.ROLE_PROTAGONIST
        assert character_dict["age"] == 30
        assert "id" in character_dict
        assert "created_at" in character_dict
        assert "updated_at" in character_dict

    def test_from_dict(self):
        """Test creating a character from a dictionary."""
        data: Dict[str, Any] = {
            "name": "John Doe",
            "role": Character.ROLE_PROTAGONIST,
            "age": 30,
            "tags": ["protagonist", "hero"],
            "physical_description": "Tall with brown hair."
        }
        
        character = Character.from_dict(data)
        
        assert character.name == "John Doe"
        assert character.role == Character.ROLE_PROTAGONIST
        assert character.age == 30
        assert character.tags == ["protagonist", "hero"]
        assert character.physical_description == "Tall with brown hair."

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Character(
            name="John Doe",
            role=Character.ROLE_PROTAGONIST,
            age=30,
            tags=["protagonist", "hero"],
            physical_description="Tall with brown hair."
        )
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Character.from_json(json_str)
        
        # Check that the restored character has the same properties
        assert restored.name == original.name
        assert restored.role == original.role
        assert restored.age == original.age
        assert restored.tags == original.tags
        assert restored.physical_description == original.physical_description
