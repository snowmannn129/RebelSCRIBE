#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Character Model for RebelSCRIBE.

This module defines the Character class that represents a character in a writing project.
"""

import logging
import datetime
from typing import Dict, List, Optional, Set, Any

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Character(BaseModel):
    """
    Represents a character in a writing project.
    
    A character is an entity that participates in the narrative.
    Characters have attributes such as name, description, background, etc.
    """
    
    # Class variables
    _required_properties: Set[str] = {'name'}
    
    # Character role types
    ROLE_PROTAGONIST = "Protagonist"
    ROLE_ANTAGONIST = "Antagonist"
    ROLE_SUPPORTING = "Supporting"
    ROLE_MINOR = "Minor"
    
    # Valid role types
    VALID_ROLES = {ROLE_PROTAGONIST, ROLE_ANTAGONIST, ROLE_SUPPORTING, ROLE_MINOR}
    
    def __init__(self, **kwargs):
        """
        Initialize a new Character instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.name = kwargs.get("name", "")
        self.full_name = kwargs.get("full_name", None)
        self.nickname = kwargs.get("nickname", None)
        self.role = kwargs.get("role", self.ROLE_SUPPORTING)  # Default role
        self.age = kwargs.get("age", None)
        self.gender = kwargs.get("gender", None)
        self.occupation = kwargs.get("occupation", None)
        self.physical_description = kwargs.get("physical_description", "")
        self.personality = kwargs.get("personality", "")
        self.background = kwargs.get("background", "")
        self.goals = kwargs.get("goals", "")
        self.motivations = kwargs.get("motivations", "")
        self.conflicts = kwargs.get("conflicts", "")
        self.relationships = kwargs.get("relationships", {})  # Character ID -> relationship description
        self.notes = kwargs.get("notes", "")
        self.arc = kwargs.get("arc", "")  # Character development arc
        self.project_id = kwargs.get("project_id", "")  # ID of the project this character belongs to
        self.document_id = kwargs.get("document_id", None)  # ID of the document representing this character
        self.scene_ids = kwargs.get("scene_ids", [])  # IDs of scenes this character appears in
        self.metadata = kwargs.get("metadata", {})  # Additional metadata
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
        self.color = kwargs.get("color", None)  # For visual organization
        self.tags = kwargs.get("tags", [])  # Tags for categorization
        self.image_path = kwargs.get("image_path", None)  # Path to character image
        
        # Validate character role
        if self.role not in self.VALID_ROLES:
            logger.warning(f"Invalid character role '{self.role}'. Using '{self.ROLE_SUPPORTING}' instead.")
            self.role = self.ROLE_SUPPORTING
    
    def set_role(self, role: str) -> None:
        """
        Set the character's role.
        
        Args:
            role: The new role.
        """
        if role not in self.VALID_ROLES:
            logger.warning(f"Invalid character role '{role}'. Using current role '{self.role}' instead.")
            return
        
        self.role = role
        self.mark_updated()
        logger.debug(f"Set role to '{role}' for character '{self.name}'")
    
    def set_physical_description(self, description: str) -> None:
        """
        Set the character's physical description.
        
        Args:
            description: The new physical description.
        """
        self.physical_description = description
        self.mark_updated()
        logger.debug(f"Updated physical description for character '{self.name}'")
    
    def set_personality(self, personality: str) -> None:
        """
        Set the character's personality.
        
        Args:
            personality: The new personality.
        """
        self.personality = personality
        self.mark_updated()
        logger.debug(f"Updated personality for character '{self.name}'")
    
    def set_background(self, background: str) -> None:
        """
        Set the character's background.
        
        Args:
            background: The new background.
        """
        self.background = background
        self.mark_updated()
        logger.debug(f"Updated background for character '{self.name}'")
    
    def set_goals(self, goals: str) -> None:
        """
        Set the character's goals.
        
        Args:
            goals: The new goals.
        """
        self.goals = goals
        self.mark_updated()
        logger.debug(f"Updated goals for character '{self.name}'")
    
    def set_motivations(self, motivations: str) -> None:
        """
        Set the character's motivations.
        
        Args:
            motivations: The new motivations.
        """
        self.motivations = motivations
        self.mark_updated()
        logger.debug(f"Updated motivations for character '{self.name}'")
    
    def set_conflicts(self, conflicts: str) -> None:
        """
        Set the character's conflicts.
        
        Args:
            conflicts: The new conflicts.
        """
        self.conflicts = conflicts
        self.mark_updated()
        logger.debug(f"Updated conflicts for character '{self.name}'")
    
    def set_arc(self, arc: str) -> None:
        """
        Set the character's development arc.
        
        Args:
            arc: The new development arc.
        """
        self.arc = arc
        self.mark_updated()
        logger.debug(f"Updated development arc for character '{self.name}'")
    
    def set_notes(self, notes: str) -> None:
        """
        Set the character's notes.
        
        Args:
            notes: The new notes.
        """
        self.notes = notes
        self.mark_updated()
        logger.debug(f"Updated notes for character '{self.name}'")
    
    def add_relationship(self, character_id: str, description: str) -> None:
        """
        Add or update a relationship with another character.
        
        Args:
            character_id: The ID of the related character.
            description: Description of the relationship.
        """
        self.relationships[character_id] = description
        self.mark_updated()
        logger.debug(f"Added/updated relationship with character {character_id} for character '{self.name}'")
    
    def remove_relationship(self, character_id: str) -> None:
        """
        Remove a relationship with another character.
        
        Args:
            character_id: The ID of the related character.
        """
        if character_id in self.relationships:
            del self.relationships[character_id]
            self.mark_updated()
            logger.debug(f"Removed relationship with character {character_id} for character '{self.name}'")
    
    def get_relationship(self, character_id: str) -> Optional[str]:
        """
        Get the description of a relationship with another character.
        
        Args:
            character_id: The ID of the related character.
            
        Returns:
            The relationship description, or None if no relationship exists.
        """
        return self.relationships.get(character_id)
    
    def add_scene(self, scene_id: str) -> None:
        """
        Add a scene that this character appears in.
        
        Args:
            scene_id: The ID of the scene to add.
        """
        if scene_id not in self.scene_ids:
            self.scene_ids.append(scene_id)
            self.mark_updated()
            logger.debug(f"Added scene {scene_id} for character '{self.name}'")
    
    def remove_scene(self, scene_id: str) -> None:
        """
        Remove a scene that this character appears in.
        
        Args:
            scene_id: The ID of the scene to remove.
        """
        if scene_id in self.scene_ids:
            self.scene_ids.remove(scene_id)
            self.mark_updated()
            logger.debug(f"Removed scene {scene_id} for character '{self.name}'")
    
    def set_image_path(self, path: Optional[str]) -> None:
        """
        Set the path to the character's image.
        
        Args:
            path: The path to the image, or None to clear it.
        """
        self.image_path = path
        self.mark_updated()
        if path:
            logger.debug(f"Set image path to '{path}' for character '{self.name}'")
        else:
            logger.debug(f"Cleared image path for character '{self.name}'")
    
    def set_color(self, color: Optional[str]) -> None:
        """
        Set the character's color.
        
        Args:
            color: The new color, or None to remove the color.
        """
        self.color = color
        self.mark_updated()
        if color:
            logger.debug(f"Set color to '{color}' for character '{self.name}'")
        else:
            logger.debug(f"Removed color for character '{self.name}'")
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the character.
        
        Args:
            tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.mark_updated()
            logger.debug(f"Added tag '{tag}' to character '{self.name}'")
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the character.
        
        Args:
            tag: The tag to remove.
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_updated()
            logger.debug(f"Removed tag '{tag}' from character '{self.name}'")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for character '{self.name}'")
    
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
            logger.debug(f"Removed metadata '{key}' from character '{self.name}'")
    
    def __str__(self) -> str:
        """
        Get a string representation of the character.
        
        Returns:
            A string representation of the character.
        """
        return f"Character('{self.name}', role='{self.role}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the character to a dictionary.
        
        Returns:
            A dictionary representation of the character.
        """
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "nickname": self.nickname,
            "role": self.role,
            "age": self.age,
            "gender": self.gender,
            "occupation": self.occupation,
            "physical_description": self.physical_description,
            "personality": self.personality,
            "background": self.background,
            "goals": self.goals,
            "motivations": self.motivations,
            "conflicts": self.conflicts,
            "relationships": self.relationships,
            "notes": self.notes,
            "arc": self.arc,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "scene_ids": self.scene_ids,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "color": self.color,
            "tags": self.tags,
            "image_path": self.image_path
        }
    
    def to_json(self) -> str:
        """
        Convert the character to a JSON string.
        
        Returns:
            A JSON string representation of the character.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """
        Create a Character instance from a dictionary.
        
        Args:
            data: The dictionary containing the character data.
            
        Returns:
            A new Character instance.
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Character':
        """
        Create a Character instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the character data.
            
        Returns:
            A new Character instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_document(self, document):
        """
        Update a document with this character's data.
        
        Args:
            document: The document to update.
        """
        document.title = self.name
        document.metadata = self.metadata.copy()
        document.set_metadata("character_data", self.to_dict())
        document.color = self.color
        document.tags = self.tags.copy()
        return document
    
    @classmethod
    def from_document(cls, document):
        """
        Create a Character instance from a document.
        
        Args:
            document: The document containing the character data.
            
        Returns:
            A new Character instance.
        """
        # Try to get character data from metadata
        character_data = document.metadata.get("character_data", {})
        
        # If no character data, create a basic character
        if not character_data:
            return cls(
                name=document.title,
                document_id=document.id,
                metadata=document.metadata.copy(),
                color=document.color,
                tags=document.tags.copy()
            )
        
        # Create character from data
        character = cls.from_dict(character_data)
        
        # Ensure document ID is set
        character.document_id = document.id
        
        return character
