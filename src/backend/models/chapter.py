#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chapter Model for RebelSCRIBE.

This module defines the Chapter class that represents a chapter in a writing project.
"""

import logging
import datetime
from typing import Dict, List, Optional, Set, Any

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Chapter(BaseModel):
    """
    Represents a chapter in a writing project.
    
    A chapter is a major division of a written work, typically consisting of multiple scenes.
    Chapters organize content and provide structure to the narrative.
    """
    
    # Class variables
    _required_properties: Set[str] = {'title'}
    
    def __init__(self, **kwargs):
        """
        Initialize a new Chapter instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Initialize with default values
        self.title: str = ""
        self.number: Optional[int] = None  # Chapter number (optional)
        self.project_id: str = ""  # ID of the project this chapter belongs to
        self.document_id: Optional[str] = None  # ID of the document representing this chapter
        self.scene_ids: List[str] = []  # IDs of scenes in this chapter
        self.synopsis: str = ""  # Brief summary of the chapter
        self.notes: str = ""  # Additional notes about the chapter
        self.status: str = "Draft"  # Draft, Revised, Final, etc.
        self.word_count: int = 0  # Total word count for the chapter
        self.order: int = 0  # Order within the project
        self.is_included_in_compile: bool = True  # Whether to include in compilation
        self.metadata: Dict[str, Any] = {}  # Additional metadata
        self.created_at: datetime.datetime = datetime.datetime.now()
        self.updated_at: datetime.datetime = datetime.datetime.now()
        self.color: Optional[str] = None  # For visual organization
        self.tags: List[str] = []  # Tags for categorization
        
        # Call parent constructor
        super().__init__(**kwargs)
    
    def add_scene(self, scene_id: str) -> None:
        """
        Add a scene to the chapter.
        
        Args:
            scene_id: The ID of the scene to add.
        """
        if scene_id not in self.scene_ids:
            self.scene_ids.append(scene_id)
            self.mark_updated()
            logger.debug(f"Added scene {scene_id} to chapter '{self.title}'")
    
    def remove_scene(self, scene_id: str) -> None:
        """
        Remove a scene from the chapter.
        
        Args:
            scene_id: The ID of the scene to remove.
        """
        if scene_id in self.scene_ids:
            self.scene_ids.remove(scene_id)
            self.mark_updated()
            logger.debug(f"Removed scene {scene_id} from chapter '{self.title}'")
    
    def reorder_scene(self, scene_id: str, new_position: int) -> bool:
        """
        Change the order of a scene within the chapter.
        
        Args:
            scene_id: The ID of the scene to reorder.
            new_position: The new position (0-based index).
            
        Returns:
            True if successful, False otherwise.
        """
        if scene_id not in self.scene_ids:
            logger.warning(f"Scene {scene_id} not found in chapter '{self.title}'")
            return False
        
        if new_position < 0 or new_position >= len(self.scene_ids):
            logger.warning(f"Invalid position {new_position} for scene {scene_id} in chapter '{self.title}'")
            return False
        
        # Remove the scene from its current position
        current_position = self.scene_ids.index(scene_id)
        self.scene_ids.pop(current_position)
        
        # Insert the scene at the new position
        self.scene_ids.insert(new_position, scene_id)
        self.mark_updated()
        logger.debug(f"Moved scene {scene_id} from position {current_position} to {new_position} in chapter '{self.title}'")
        return True
    
    def update_word_count(self, word_count: int) -> None:
        """
        Update the word count for the chapter.
        
        Args:
            word_count: The new word count.
        """
        self.word_count = word_count
        self.mark_updated()
        logger.debug(f"Updated word count to {word_count} for chapter '{self.title}'")
    
    def set_status(self, status: str) -> None:
        """
        Set the chapter status.
        
        Args:
            status: The new status.
        """
        self.status = status
        self.mark_updated()
        logger.debug(f"Set status to '{status}' for chapter '{self.title}'")
    
    def set_synopsis(self, synopsis: str) -> None:
        """
        Set the chapter synopsis.
        
        Args:
            synopsis: The new synopsis.
        """
        self.synopsis = synopsis
        self.mark_updated()
        logger.debug(f"Updated synopsis for chapter '{self.title}'")
    
    def set_notes(self, notes: str) -> None:
        """
        Set the chapter notes.
        
        Args:
            notes: The new notes.
        """
        self.notes = notes
        self.mark_updated()
        logger.debug(f"Updated notes for chapter '{self.title}'")
    
    def set_color(self, color: Optional[str]) -> None:
        """
        Set the chapter color.
        
        Args:
            color: The new color, or None to remove the color.
        """
        self.color = color
        self.mark_updated()
        if color:
            logger.debug(f"Set color to '{color}' for chapter '{self.title}'")
        else:
            logger.debug(f"Removed color for chapter '{self.title}'")
    
    def set_compile_inclusion(self, included: bool) -> None:
        """
        Set whether the chapter is included in compilation.
        
        Args:
            included: Whether to include the chapter in compilation.
        """
        self.is_included_in_compile = included
        self.mark_updated()
        if included:
            logger.debug(f"Chapter '{self.title}' will be included in compilation")
        else:
            logger.debug(f"Chapter '{self.title}' will be excluded from compilation")
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the chapter.
        
        Args:
            tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.mark_updated()
            logger.debug(f"Added tag '{tag}' to chapter '{self.title}'")
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the chapter.
        
        Args:
            tag: The tag to remove.
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_updated()
            logger.debug(f"Removed tag '{tag}' from chapter '{self.title}'")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for chapter '{self.title}'")
    
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
            logger.debug(f"Removed metadata '{key}' from chapter '{self.title}'")
    
    def __str__(self) -> str:
        """
        Get a string representation of the chapter.
        
        Returns:
            A string representation of the chapter.
        """
        chapter_num = f"#{self.number} " if self.number is not None else ""
        return f"Chapter({chapter_num}'{self.title}', scenes={len(self.scene_ids)}, words={self.word_count})"
