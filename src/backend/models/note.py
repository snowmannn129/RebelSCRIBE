#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note Model for RebelSCRIBE.

This module defines the Note class that represents a note in a writing project.
"""

import logging
import datetime
from typing import Dict, List, Optional, Set, Any

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Note(BaseModel):
    """
    Represents a note in a writing project.
    
    A note is a piece of information or reminder that is associated with
    a project, character, location, scene, or other element of the writing project.
    Notes help writers organize their thoughts and research.
    """
    
    # Class variables
    _required_properties: Set[str] = {'title'}
    
    # Note types
    TYPE_GENERAL = "General"
    TYPE_RESEARCH = "Research"
    TYPE_IDEA = "Idea"
    TYPE_TODO = "Todo"
    TYPE_QUESTION = "Question"
    
    # Valid note types
    VALID_TYPES = {TYPE_GENERAL, TYPE_RESEARCH, TYPE_IDEA, TYPE_TODO, TYPE_QUESTION}
    
    # Note priorities
    PRIORITY_LOW = "Low"
    PRIORITY_MEDIUM = "Medium"
    PRIORITY_HIGH = "High"
    
    # Valid priorities
    VALID_PRIORITIES = {PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH}
    
    def __init__(self, **kwargs):
        """
        Initialize a new Note instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.title = kwargs.get("title", "")
        self.content = kwargs.get("content", "")
        self.type = kwargs.get("type", self.TYPE_GENERAL)  # Default type
        self.priority = kwargs.get("priority", self.PRIORITY_MEDIUM)  # Default priority
        self.is_completed = kwargs.get("is_completed", False)  # For todo notes
        self.project_id = kwargs.get("project_id", "")  # ID of the project this note belongs to
        self.document_id = kwargs.get("document_id", None)  # ID of the document representing this note
        self.related_ids = kwargs.get("related_ids", {  # IDs of related elements
            "character": [],
            "location": [],
            "scene": [],
            "chapter": [],
            "note": [],
            "tag": []
        })
        self.metadata = kwargs.get("metadata", {})  # Additional metadata
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
        self.color = kwargs.get("color", None)  # For visual organization
        self.tags = kwargs.get("tags", [])  # Tags for categorization
        
        # Validate note type
        if self.type not in self.VALID_TYPES:
            logger.warning(f"Invalid note type '{self.type}'. Using '{self.TYPE_GENERAL}' instead.")
            self.type = self.TYPE_GENERAL
        
        # Validate priority
        if self.priority not in self.VALID_PRIORITIES:
            logger.warning(f"Invalid priority '{self.priority}'. Using '{self.PRIORITY_MEDIUM}' instead.")
            self.priority = self.PRIORITY_MEDIUM
    
    def set_type(self, note_type: str) -> None:
        """
        Set the note type.
        
        Args:
            note_type: The new note type.
        """
        if note_type not in self.VALID_TYPES:
            logger.warning(f"Invalid note type '{note_type}'. Using current type '{self.type}' instead.")
            return
        
        self.type = note_type
        self.mark_updated()
        logger.debug(f"Set type to '{note_type}' for note '{self.title}'")
    
    def set_priority(self, priority: str) -> None:
        """
        Set the note priority.
        
        Args:
            priority: The new priority.
        """
        if priority not in self.VALID_PRIORITIES:
            logger.warning(f"Invalid priority '{priority}'. Using current priority '{self.priority}' instead.")
            return
        
        self.priority = priority
        self.mark_updated()
        logger.debug(f"Set priority to '{priority}' for note '{self.title}'")
    
    def set_content(self, content: str) -> None:
        """
        Set the note content.
        
        Args:
            content: The new content.
        """
        self.content = content
        self.mark_updated()
        logger.debug(f"Updated content for note '{self.title}'")
    
    def append_content(self, content: str) -> None:
        """
        Append content to the note.
        
        Args:
            content: The content to append.
        """
        self.content += content
        self.mark_updated()
        logger.debug(f"Appended content to note '{self.title}'")
    
    def set_completed(self, completed: bool) -> None:
        """
        Set whether the note is completed (for todo notes).
        
        Args:
            completed: Whether the note is completed.
        """
        self.is_completed = completed
        self.mark_updated()
        if completed:
            logger.debug(f"Marked note '{self.title}' as completed")
        else:
            logger.debug(f"Marked note '{self.title}' as not completed")
    
    def add_related_item(self, item_type: str, item_id: str) -> bool:
        """
        Add a related item to the note.
        
        Args:
            item_type: The type of the related item (character, location, etc.).
            item_id: The ID of the related item.
            
        Returns:
            True if successful, False otherwise.
        """
        if item_type not in self.related_ids:
            logger.warning(f"Invalid item type '{item_type}' for note '{self.title}'")
            return False
        
        if item_id not in self.related_ids[item_type]:
            self.related_ids[item_type].append(item_id)
            self.mark_updated()
            logger.debug(f"Added related {item_type} {item_id} to note '{self.title}'")
        
        return True
    
    def remove_related_item(self, item_type: str, item_id: str) -> bool:
        """
        Remove a related item from the note.
        
        Args:
            item_type: The type of the related item (character, location, etc.).
            item_id: The ID of the related item.
            
        Returns:
            True if successful, False otherwise.
        """
        if item_type not in self.related_ids:
            logger.warning(f"Invalid item type '{item_type}' for note '{self.title}'")
            return False
        
        if item_id in self.related_ids[item_type]:
            self.related_ids[item_type].remove(item_id)
            self.mark_updated()
            logger.debug(f"Removed related {item_type} {item_id} from note '{self.title}'")
        
        return True
    
    def get_related_items(self, item_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get related items.
        
        Args:
            item_type: The type of related items to get, or None to get all.
            
        Returns:
            A dictionary of related item IDs by type, or a list of IDs if item_type is specified.
        """
        if item_type is not None:
            if item_type not in self.related_ids:
                logger.warning(f"Invalid item type '{item_type}' for note '{self.title}'")
                return {}
            return {item_type: self.related_ids[item_type]}
        
        return self.related_ids
    
    def set_color(self, color: Optional[str]) -> None:
        """
        Set the note's color.
        
        Args:
            color: The new color, or None to remove the color.
        """
        self.color = color
        self.mark_updated()
        if color:
            logger.debug(f"Set color to '{color}' for note '{self.title}'")
        else:
            logger.debug(f"Removed color for note '{self.title}'")
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the note.
        
        Args:
            tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.mark_updated()
            logger.debug(f"Added tag '{tag}' to note '{self.title}'")
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the note.
        
        Args:
            tag: The tag to remove.
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_updated()
            logger.debug(f"Removed tag '{tag}' from note '{self.title}'")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for note '{self.title}'")
    
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
            logger.debug(f"Removed metadata '{key}' from note '{self.title}'")
    
    def __str__(self) -> str:
        """
        Get a string representation of the note.
        
        Returns:
            A string representation of the note.
        """
        completed_str = " (Completed)" if self.is_completed and self.type == self.TYPE_TODO else ""
        return f"Note('{self.title}', type='{self.type}', priority='{self.priority}'{completed_str})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the note to a dictionary.
        
        Returns:
            A dictionary representation of the note.
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "type": self.type,
            "priority": self.priority,
            "is_completed": self.is_completed,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "related_ids": self.related_ids,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "color": self.color,
            "tags": self.tags
        }
    
    def to_json(self) -> str:
        """
        Convert the note to a JSON string.
        
        Returns:
            A JSON string representation of the note.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """
        Create a Note instance from a dictionary.
        
        Args:
            data: The dictionary containing the note data.
            
        Returns:
            A new Note instance.
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Note':
        """
        Create a Note instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the note data.
            
        Returns:
            A new Note instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_document(self, document):
        """
        Update a document with this note's data.
        
        Args:
            document: The document to update.
        """
        document.title = self.title
        document.metadata = self.metadata.copy()
        document.set_metadata("note_data", self.to_dict())
        document.color = self.color
        document.tags = self.tags.copy()
        return document
    
    @classmethod
    def from_document(cls, document):
        """
        Create a Note instance from a document.
        
        Args:
            document: The document containing the note data.
            
        Returns:
            A new Note instance.
        """
        # Try to get note data from metadata
        note_data = document.metadata.get("note_data", {})
        
        # If no note data, create a basic note
        if not note_data:
            return cls(
                title=document.title,
                document_id=document.id,
                metadata=document.metadata.copy(),
                color=document.color,
                tags=document.tags.copy()
            )
        
        # Create note from data
        note = cls.from_dict(note_data)
        
        # Ensure document ID is set
        note.document_id = document.id
        
        return note
