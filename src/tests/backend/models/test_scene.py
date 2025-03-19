#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Scene model.
"""

import pytest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.scene import Scene


class TestScene:
    """Test suite for the Scene model."""

    def test_init_default_values(self):
        """Test that a scene is initialized with default values."""
        scene = Scene()
        
        assert scene.title == ""
        assert scene.content == ""
        assert scene.chapter_id is None
        assert scene.project_id == ""
        assert scene.document_id is None
        assert scene.synopsis == ""
        assert scene.notes == ""
        assert scene.status == Scene.STATUS_DRAFT
        assert scene.pov is None
        assert scene.pov_character_id is None
        assert scene.location_ids == []
        assert scene.character_ids == []
        assert scene.word_count == 0
        assert scene.goal_word_count is None
        assert scene.order == 0
        assert scene.date_time is None
        assert scene.is_included_in_compile is True
        assert scene.metadata == {}
        assert isinstance(scene.created_at, datetime.datetime)
        assert isinstance(scene.updated_at, datetime.datetime)
        assert scene.color is None
        assert scene.tags == []

    def test_init_with_values(self):
        """Test that a scene is initialized with provided values."""
        title = "The Beginning"
        content = "It was a dark and stormy night..."
        status = Scene.STATUS_REVISED
        
        scene = Scene(
            title=title,
            content=content,
            status=status
        )
        
        assert scene.title == title
        assert scene.content == content
        assert scene.status == status
        assert scene.word_count == 7  # Word count should be calculated automatically

    def test_init_with_invalid_status(self):
        """Test that a scene with invalid status defaults to draft."""
        scene = Scene(status="invalid_status")
        
        assert scene.status == Scene.STATUS_DRAFT

    def test_init_with_invalid_pov(self):
        """Test that a scene with invalid POV defaults to None."""
        scene = Scene(pov="invalid_pov")
        
        assert scene.pov is None

    def test_update_word_count(self):
        """Test updating word count."""
        scene = Scene(title="Test Scene")
        
        # Empty content
        scene.content = ""
        scene.update_word_count()
        assert scene.word_count == 0
        
        # Content with words
        scene.content = "This is a test scene with ten words in it."
        scene.update_word_count()
        assert scene.word_count == 10
        
        # Content with multiple spaces
        scene.content = "This   has   multiple   spaces   between   words."
        scene.update_word_count()
        assert scene.word_count == 6  # There are actually 6 words in this sentence

    def test_set_content(self):
        """Test setting content."""
        scene = Scene(title="Test Scene")
        content = "This is the scene content."
        
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_content(content)
            
            assert scene.content == content
            assert scene.word_count == 5
            mock_mark_updated.assert_called_once()

    def test_append_content(self):
        """Test appending content."""
        scene = Scene(title="Test Scene", content="Initial content.")
        
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.append_content(" Additional content.")
            
            assert scene.content == "Initial content. Additional content."
            assert scene.word_count == 4
            mock_mark_updated.assert_called_once()

    def test_set_status_valid(self):
        """Test setting a valid status."""
        scene = Scene(title="Test Scene")
        
        # Set to outline
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_status(Scene.STATUS_OUTLINE)
            
            assert scene.status == Scene.STATUS_OUTLINE
            mock_mark_updated.assert_called_once()
        
        # Set to draft
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_status(Scene.STATUS_DRAFT)
            
            assert scene.status == Scene.STATUS_DRAFT
            mock_mark_updated.assert_called_once()
        
        # Set to revised
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_status(Scene.STATUS_REVISED)
            
            assert scene.status == Scene.STATUS_REVISED
            mock_mark_updated.assert_called_once()
        
        # Set to final
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_status(Scene.STATUS_FINAL)
            
            assert scene.status == Scene.STATUS_FINAL
            mock_mark_updated.assert_called_once()

    def test_set_status_invalid(self):
        """Test setting an invalid status."""
        scene = Scene(title="Test Scene", status=Scene.STATUS_DRAFT)
        
        # Set to invalid status
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_status("Invalid Status")
            
            # Status should remain unchanged
            assert scene.status == Scene.STATUS_DRAFT
            mock_mark_updated.assert_not_called()

    def test_set_pov_valid(self):
        """Test setting a valid POV."""
        scene = Scene(title="Test Scene")
        
        # Set to first person
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov(Scene.POV_FIRST_PERSON)
            
            assert scene.pov == Scene.POV_FIRST_PERSON
            mock_mark_updated.assert_called_once()
        
        # Set to second person
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov(Scene.POV_SECOND_PERSON)
            
            assert scene.pov == Scene.POV_SECOND_PERSON
            mock_mark_updated.assert_called_once()
        
        # Set to third person limited
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov(Scene.POV_THIRD_PERSON_LIMITED)
            
            assert scene.pov == Scene.POV_THIRD_PERSON_LIMITED
            mock_mark_updated.assert_called_once()
        
        # Set to third person omniscient
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov(Scene.POV_THIRD_PERSON_OMNISCIENT)
            
            assert scene.pov == Scene.POV_THIRD_PERSON_OMNISCIENT
            mock_mark_updated.assert_called_once()
        
        # Clear POV
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov(None)
            
            assert scene.pov is None
            mock_mark_updated.assert_called_once()

    def test_set_pov_invalid(self):
        """Test setting an invalid POV."""
        scene = Scene(title="Test Scene", pov=Scene.POV_FIRST_PERSON)
        
        # Set to invalid POV
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov("Invalid POV")
            
            # POV should be set to None
            assert scene.pov is None
            mock_mark_updated.assert_called_once()

    def test_set_pov_character(self):
        """Test setting the POV character."""
        scene = Scene(title="Test Scene")
        character_id = "character123"
        
        # Set POV character
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov_character(character_id)
            
            assert scene.pov_character_id == character_id
            mock_mark_updated.assert_called_once()
        
        # Clear POV character
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_pov_character(None)
            
            assert scene.pov_character_id is None
            mock_mark_updated.assert_called_once()

    def test_character_operations(self):
        """Test character operations."""
        scene = Scene(title="Test Scene")
        character_id = "character123"
        
        # Add character
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.add_character(character_id)
            
            assert character_id in scene.character_ids
            mock_mark_updated.assert_called_once()
        
        # Adding the same character again should not duplicate
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.add_character(character_id)
            
            assert scene.character_ids.count(character_id) == 1
            mock_mark_updated.assert_not_called()
        
        # Set this character as POV character
        scene.set_pov_character(character_id)
        
        # Remove character
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_character(character_id)
            
            assert character_id not in scene.character_ids
            assert scene.pov_character_id is None  # POV character should be cleared
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent character should not error
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_character("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_location_operations(self):
        """Test location operations."""
        scene = Scene(title="Test Scene")
        location_id = "location123"
        
        # Add location
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.add_location(location_id)
            
            assert location_id in scene.location_ids
            mock_mark_updated.assert_called_once()
        
        # Adding the same location again should not duplicate
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.add_location(location_id)
            
            assert scene.location_ids.count(location_id) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove location
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_location(location_id)
            
            assert location_id not in scene.location_ids
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent location should not error
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_location("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_set_synopsis(self):
        """Test setting the synopsis."""
        scene = Scene(title="Test Scene")
        synopsis = "This scene introduces the main conflict."
        
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_synopsis(synopsis)
            
            assert scene.synopsis == synopsis
            mock_mark_updated.assert_called_once()

    def test_set_notes(self):
        """Test setting the notes."""
        scene = Scene(title="Test Scene")
        notes = "Remember to add more tension."
        
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_notes(notes)
            
            assert scene.notes == notes
            mock_mark_updated.assert_called_once()

    def test_set_date_time(self):
        """Test setting the date/time."""
        scene = Scene(title="Test Scene")
        date_time = "January 1, 2025, morning"
        
        # Set date/time
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_date_time(date_time)
            
            assert scene.date_time == date_time
            mock_mark_updated.assert_called_once()
        
        # Clear date/time
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_date_time(None)
            
            assert scene.date_time is None
            mock_mark_updated.assert_called_once()

    def test_set_goal_word_count(self):
        """Test setting the goal word count."""
        scene = Scene(title="Test Scene")
        goal = 1000
        
        # Set goal
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_goal_word_count(goal)
            
            assert scene.goal_word_count == goal
            mock_mark_updated.assert_called_once()
        
        # Clear goal
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_goal_word_count(None)
            
            assert scene.goal_word_count is None
            mock_mark_updated.assert_called_once()

    def test_get_word_count_progress(self):
        """Test getting word count progress."""
        scene = Scene(title="Test Scene")
        
        # No goal
        assert scene.get_word_count_progress() is None
        
        # With goal, no progress
        scene.set_goal_word_count(1000)
        assert scene.get_word_count_progress() == 0.0
        
        # With goal, some progress
        scene.set_content("This is a test scene with some content to increase the word count.")
        assert scene.get_word_count_progress() == 1.3  # (13 / 1000) * 100 = 1.3%
        
        # With goal, exceeding goal
        scene.set_goal_word_count(10)
        assert scene.get_word_count_progress() == 100.0  # Capped at 100%

    def test_set_color(self):
        """Test setting the color."""
        scene = Scene(title="Test Scene")
        color = "#FF0000"
        
        # Set color
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_color(color)
            
            assert scene.color == color
            mock_mark_updated.assert_called_once()
        
        # Clear color
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_color(None)
            
            assert scene.color is None
            mock_mark_updated.assert_called_once()

    def test_set_compile_inclusion(self):
        """Test setting compile inclusion."""
        scene = Scene(title="Test Scene")
        
        # Exclude from compile
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_compile_inclusion(False)
            
            assert scene.is_included_in_compile is False
            mock_mark_updated.assert_called_once()
        
        # Include in compile
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_compile_inclusion(True)
            
            assert scene.is_included_in_compile is True
            mock_mark_updated.assert_called_once()

    def test_tag_operations(self):
        """Test tag operations."""
        scene = Scene(title="Test Scene")
        tag = "action"
        
        # Add tag
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.add_tag(tag)
            
            assert tag in scene.tags
            mock_mark_updated.assert_called_once()
        
        # Adding the same tag again should not duplicate
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.add_tag(tag)
            
            assert scene.tags.count(tag) == 1
            mock_mark_updated.assert_not_called()
        
        # Remove tag
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_tag(tag)
            
            assert tag not in scene.tags
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent tag should not error
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_tag("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_metadata_operations(self):
        """Test metadata operations."""
        scene = Scene(title="Test Scene")
        
        # Set metadata
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_metadata("key1", "value1")
            
            assert scene.metadata["key1"] == "value1"
            mock_mark_updated.assert_called_once()
        
        # Get metadata
        assert scene.get_metadata("key1") == "value1"
        assert scene.get_metadata("nonexistent") is None
        assert scene.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.set_metadata("key1", "updated")
            
            assert scene.get_metadata("key1") == "updated"
            mock_mark_updated.assert_called_once()
        
        # Remove metadata
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_metadata("key1")
            
            assert "key1" not in scene.metadata
            mock_mark_updated.assert_called_once()
        
        # Removing non-existent metadata should not error
        with patch.object(scene, 'mark_updated') as mock_mark_updated:
            scene.remove_metadata("nonexistent")
            
            mock_mark_updated.assert_not_called()

    def test_str_representation(self):
        """Test the string representation of a scene."""
        scene = Scene(title="The Beginning", status=Scene.STATUS_DRAFT, content="It was a dark and stormy night.")
        
        expected = "Scene('The Beginning', status='Draft', words=7)"
        assert str(scene) == expected

    def test_to_dict(self):
        """Test converting a scene to a dictionary."""
        scene = Scene(
            title="The Beginning",
            content="It was a dark and stormy night.",
            status=Scene.STATUS_DRAFT
        )
        
        scene_dict = scene.to_dict()
        
        assert scene_dict["title"] == "The Beginning"
        assert scene_dict["content"] == "It was a dark and stormy night."
        assert scene_dict["status"] == Scene.STATUS_DRAFT
        assert scene_dict["word_count"] == 7
        assert "id" in scene_dict
        assert "created_at" in scene_dict
        assert "updated_at" in scene_dict

    def test_from_dict(self):
        """Test creating a scene from a dictionary."""
        data: Dict[str, Any] = {
            "title": "The Beginning",
            "content": "It was a dark and stormy night.",
            "status": Scene.STATUS_DRAFT,
            "tags": ["action", "night"],
            "synopsis": "The story begins on a stormy night."
        }
        
        scene = Scene.from_dict(data)
        
        assert scene.title == "The Beginning"
        assert scene.content == "It was a dark and stormy night."
        assert scene.status == Scene.STATUS_DRAFT
        assert scene.tags == ["action", "night"]
        assert scene.synopsis == "The story begins on a stormy night."
        assert scene.word_count == 7  # Word count should be calculated automatically

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Scene(
            title="The Beginning",
            content="It was a dark and stormy night.",
            status=Scene.STATUS_DRAFT,
            tags=["action", "night"],
            synopsis="The story begins on a stormy night."
        )
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Scene.from_json(json_str)
        
        # Check that the restored scene has the same properties
        assert restored.title == original.title
        assert restored.content == original.content
        assert restored.status == original.status
        assert restored.tags == original.tags
        assert restored.synopsis == original.synopsis
        assert restored.word_count == original.word_count
