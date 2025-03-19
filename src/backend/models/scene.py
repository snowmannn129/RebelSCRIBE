#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scene Model for RebelSCRIBE.

This module defines the Scene class that represents a scene in a writing project.
"""

import logging
import datetime
from typing import Dict, List, Optional, Set, Any

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Scene(BaseModel):
    """
    Represents a scene in a writing project.
    
    A scene is a discrete unit of narrative that takes place in a specific
    location and time. Scenes are the building blocks of chapters and are
    typically focused on a specific event, conversation, or moment.
    """
    
    # Class variables
    _required_properties: Set[str] = {'title'}
    
    # Scene status options
    STATUS_OUTLINE = "Outline"
    STATUS_DRAFT = "Draft"
    STATUS_REVISED = "Revised"
    STATUS_FINAL = "Final"
    
    # Valid status values
    VALID_STATUSES = {STATUS_OUTLINE, STATUS_DRAFT, STATUS_REVISED, STATUS_FINAL}
    
    # POV types
    POV_FIRST_PERSON = "First Person"
    POV_SECOND_PERSON = "Second Person"
    POV_THIRD_PERSON_LIMITED = "Third Person Limited"
    POV_THIRD_PERSON_OMNISCIENT = "Third Person Omniscient"
    
    # Valid POV types
    VALID_POV_TYPES = {
        POV_FIRST_PERSON, 
        POV_SECOND_PERSON, 
        POV_THIRD_PERSON_LIMITED, 
        POV_THIRD_PERSON_OMNISCIENT
    }
    
    def __init__(self, **kwargs):
        """
        Initialize a new Scene instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.title = kwargs.get("title", "")
        self.content = kwargs.get("content", "")
        self.chapter_id = kwargs.get("chapter_id", None)  # ID of the chapter this scene belongs to
        self.project_id = kwargs.get("project_id", "")  # ID of the project this scene belongs to
        self.document_id = kwargs.get("document_id", None)  # ID of the document representing this scene
        self.synopsis = kwargs.get("synopsis", "")  # Brief summary of the scene
        self.notes = kwargs.get("notes", "")  # Additional notes about the scene
        self.status = kwargs.get("status", self.STATUS_DRAFT)  # Default status
        self.pov = kwargs.get("pov", None)  # Point of view
        self.pov_character_id = kwargs.get("pov_character_id", None)  # ID of the POV character
        self.location_ids = kwargs.get("location_ids", [])  # IDs of locations in this scene
        self.character_ids = kwargs.get("character_ids", [])  # IDs of characters in this scene
        self.word_count = kwargs.get("word_count", 0)  # Word count for the scene
        self.goal_word_count = kwargs.get("goal_word_count", None)  # Target word count
        self.order = kwargs.get("order", 0)  # Order within the chapter
        self.date_time = kwargs.get("date_time", None)  # When the scene takes place
        self.is_included_in_compile = kwargs.get("is_included_in_compile", True)  # Whether to include in compilation
        self.metadata = kwargs.get("metadata", {})  # Additional metadata
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
        self.color = kwargs.get("color", None)  # For visual organization
        self.tags = kwargs.get("tags", [])  # Tags for categorization
        
        # Validate scene status
        if self.status not in self.VALID_STATUSES:
            logger.warning(f"Invalid scene status '{self.status}'. Using '{self.STATUS_DRAFT}' instead.")
            self.status = self.STATUS_DRAFT
        
        # Validate POV type if set
        if self.pov is not None and self.pov not in self.VALID_POV_TYPES:
            logger.warning(f"Invalid POV type '{self.pov}'. Setting to None.")
            self.pov = None
        
        # Update word count
        self.update_word_count()
    
    def update_word_count(self) -> None:
        """Update word count based on content."""
        if not self.content:
            self.word_count = 0
            return
        
        # Count words (split by whitespace and handle multiple spaces)
        # Using a more sophisticated approach to match the test expectations
        import re
        words = re.findall(r'\S+', self.content)
        self.word_count = len(words)
        logger.debug(f"Updated word count for scene '{self.title}': {self.word_count} words")
    
    def set_content(self, content: str) -> None:
        """
        Set the scene content.
        
        Args:
            content: The new content.
        """
        self.content = content
        self.mark_updated()
        self.update_word_count()
        logger.debug(f"Updated content for scene '{self.title}'")
    
    def append_content(self, content: str) -> None:
        """
        Append content to the scene.
        
        Args:
            content: The content to append.
        """
        self.content += content
        self.mark_updated()
        self.update_word_count()
        logger.debug(f"Appended content to scene '{self.title}'")
    
    def set_status(self, status: str) -> None:
        """
        Set the scene status.
        
        Args:
            status: The new status.
        """
        if status not in self.VALID_STATUSES:
            logger.warning(f"Invalid scene status '{status}'. Using current status '{self.status}' instead.")
            return
        
        self.status = status
        self.mark_updated()
        logger.debug(f"Set status to '{status}' for scene '{self.title}'")
    
    def set_pov(self, pov: Optional[str]) -> None:
        """
        Set the point of view for the scene.
        
        Args:
            pov: The new POV, or None to clear it.
        """
        if pov is not None and pov not in self.VALID_POV_TYPES:
            logger.warning(f"Invalid POV type '{pov}'. Using None instead.")
            pov = None
        
        self.pov = pov
        self.mark_updated()
        if pov:
            logger.debug(f"Set POV to '{pov}' for scene '{self.title}'")
        else:
            logger.debug(f"Cleared POV for scene '{self.title}'")
    
    def set_pov_character(self, character_id: Optional[str]) -> None:
        """
        Set the POV character for the scene.
        
        Args:
            character_id: The ID of the POV character, or None to clear it.
        """
        self.pov_character_id = character_id
        self.mark_updated()
        if character_id:
            logger.debug(f"Set POV character to {character_id} for scene '{self.title}'")
        else:
            logger.debug(f"Cleared POV character for scene '{self.title}'")
    
    def add_character(self, character_id: str) -> None:
        """
        Add a character to the scene.
        
        Args:
            character_id: The ID of the character to add.
        """
        if character_id not in self.character_ids:
            self.character_ids.append(character_id)
            self.mark_updated()
            logger.debug(f"Added character {character_id} to scene '{self.title}'")
    
    def remove_character(self, character_id: str) -> None:
        """
        Remove a character from the scene.
        
        Args:
            character_id: The ID of the character to remove.
        """
        if character_id in self.character_ids:
            self.character_ids.remove(character_id)
            self.mark_updated()
            logger.debug(f"Removed character {character_id} from scene '{self.title}'")
            
            # If this was the POV character, clear that as well
            if self.pov_character_id == character_id:
                self.pov_character_id = None
                logger.debug(f"Cleared POV character for scene '{self.title}' (character was removed)")
    
    def add_location(self, location_id: str) -> None:
        """
        Add a location to the scene.
        
        Args:
            location_id: The ID of the location to add.
        """
        if location_id not in self.location_ids:
            self.location_ids.append(location_id)
            self.mark_updated()
            logger.debug(f"Added location {location_id} to scene '{self.title}'")
    
    def remove_location(self, location_id: str) -> None:
        """
        Remove a location from the scene.
        
        Args:
            location_id: The ID of the location to remove.
        """
        if location_id in self.location_ids:
            self.location_ids.remove(location_id)
            self.mark_updated()
            logger.debug(f"Removed location {location_id} from scene '{self.title}'")
    
    def set_synopsis(self, synopsis: str) -> None:
        """
        Set the scene synopsis.
        
        Args:
            synopsis: The new synopsis.
        """
        self.synopsis = synopsis
        self.mark_updated()
        logger.debug(f"Updated synopsis for scene '{self.title}'")
    
    def set_notes(self, notes: str) -> None:
        """
        Set the scene notes.
        
        Args:
            notes: The new notes.
        """
        self.notes = notes
        self.mark_updated()
        logger.debug(f"Updated notes for scene '{self.title}'")
    
    def set_date_time(self, date_time: Optional[str]) -> None:
        """
        Set when the scene takes place.
        
        Args:
            date_time: A string describing when the scene takes place, or None to clear it.
        """
        self.date_time = date_time
        self.mark_updated()
        if date_time:
            logger.debug(f"Set date/time to '{date_time}' for scene '{self.title}'")
        else:
            logger.debug(f"Cleared date/time for scene '{self.title}'")
    
    def set_goal_word_count(self, goal: Optional[int]) -> None:
        """
        Set the goal word count for the scene.
        
        Args:
            goal: The goal word count, or None to clear it.
        """
        self.goal_word_count = goal
        self.mark_updated()
        if goal is not None:
            logger.debug(f"Set goal word count to {goal} for scene '{self.title}'")
        else:
            logger.debug(f"Cleared goal word count for scene '{self.title}'")
    
    def set_color(self, color: Optional[str]) -> None:
        """
        Set the scene color.
        
        Args:
            color: The new color, or None to remove the color.
        """
        self.color = color
        self.mark_updated()
        if color:
            logger.debug(f"Set color to '{color}' for scene '{self.title}'")
        else:
            logger.debug(f"Removed color for scene '{self.title}'")
    
    def set_compile_inclusion(self, included: bool) -> None:
        """
        Set whether the scene is included in compilation.
        
        Args:
            included: Whether to include the scene in compilation.
        """
        self.is_included_in_compile = included
        self.mark_updated()
        if included:
            logger.debug(f"Scene '{self.title}' will be included in compilation")
        else:
            logger.debug(f"Scene '{self.title}' will be excluded from compilation")
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the scene.
        
        Args:
            tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.mark_updated()
            logger.debug(f"Added tag '{tag}' to scene '{self.title}'")
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the scene.
        
        Args:
            tag: The tag to remove.
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_updated()
            logger.debug(f"Removed tag '{tag}' from scene '{self.title}'")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for scene '{self.title}'")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.
        
        Args:
            key: The metadata key.
            default: The default value to return if the key doesn't exist.
            
        Returns:
            The metadata value, or the default if the key doesn't exist.
        """
        return self.metadata.get(key, default)
    
    def remove_metadata(self, key: str) -> None:
        """
        Remove a metadata value.
        
        Args:
            key: The metadata key.
        """
        if key in self.metadata:
            del self.metadata[key]
            self.mark_updated()
            logger.debug(f"Removed metadata '{key}' from scene '{self.title}'")
    
    def get_word_count_progress(self) -> Optional[float]:
        """
        Get the progress towards the goal word count.
        
        Returns:
            The progress as a percentage (0-100), or None if there's no goal.
        """
        if self.goal_word_count is None or self.goal_word_count <= 0:
            return None
        
        progress = (self.word_count / self.goal_word_count) * 100
        return min(progress, 100.0)  # Cap at 100%
    
    def __str__(self) -> str:
        """
        Get a string representation of the scene.
        
        Returns:
            A string representation of the scene.
        """
        return f"Scene('{self.title}', status='{self.status}', words={self.word_count})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the scene to a dictionary.
        
        Returns:
            A dictionary representation of the scene.
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "chapter_id": self.chapter_id,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "synopsis": self.synopsis,
            "notes": self.notes,
            "status": self.status,
            "pov": self.pov,
            "pov_character_id": self.pov_character_id,
            "location_ids": self.location_ids,
            "character_ids": self.character_ids,
            "word_count": self.word_count,
            "goal_word_count": self.goal_word_count,
            "order": self.order,
            "date_time": self.date_time,
            "is_included_in_compile": self.is_included_in_compile,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "color": self.color,
            "tags": self.tags
        }
    
    def to_json(self) -> str:
        """
        Convert the scene to a JSON string.
        
        Returns:
            A JSON string representation of the scene.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """
        Create a Scene instance from a dictionary.
        
        Args:
            data: The dictionary containing the scene data.
            
        Returns:
            A new Scene instance.
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Scene':
        """
        Create a Scene instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the scene data.
            
        Returns:
            A new Scene instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
