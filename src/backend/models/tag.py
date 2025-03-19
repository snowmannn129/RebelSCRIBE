#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag Model for RebelSCRIBE.

This module defines the Tag class that represents a tag in a writing project.
"""

import logging
import datetime
from typing import Dict, List, Optional, Set, Any

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Tag(BaseModel):
    """
    Represents a tag in a writing project.
    
    A tag is a label that can be applied to various elements in a writing project,
    such as characters, locations, scenes, etc. Tags help with organization and filtering.
    """
    
    # Class variables
    _required_properties: Set[str] = {'name'}
    
    def __init__(self, **kwargs):
        """
        Initialize a new Tag instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.color = kwargs.get("color", None)  # Color for visual identification
        self.project_id = kwargs.get("project_id", "")  # ID of the project this tag belongs to
        self.item_ids = kwargs.get("item_ids", {  # IDs of items with this tag
            "character": [],
            "location": [],
            "scene": [],
            "chapter": [],
            "note": [],
            "document": []
        })
        self.parent_tag_id = kwargs.get("parent_tag_id", None)  # ID of the parent tag (for hierarchical tags)
        self.child_tag_ids = kwargs.get("child_tag_ids", [])  # IDs of child tags
        self.metadata = kwargs.get("metadata", {})  # Additional metadata
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
    
    def set_description(self, description: str) -> None:
        """
        Set the tag description.
        
        Args:
            description: The new description.
        """
        self.description = description
        self.mark_updated()
        logger.debug(f"Updated description for tag '{self.name}'")
    
    def set_color(self, color: Optional[str]) -> None:
        """
        Set the tag color.
        
        Args:
            color: The new color, or None to remove the color.
        """
        self.color = color
        self.mark_updated()
        if color:
            logger.debug(f"Set color to '{color}' for tag '{self.name}'")
        else:
            logger.debug(f"Removed color for tag '{self.name}'")
    
    def add_item(self, item_type: str, item_id: str) -> bool:
        """
        Add an item to the tag.
        
        Args:
            item_type: The type of the item (character, location, etc.).
            item_id: The ID of the item.
            
        Returns:
            True if successful, False otherwise.
        """
        if item_type not in self.item_ids:
            logger.warning(f"Invalid item type '{item_type}' for tag '{self.name}'")
            return False
        
        if item_id not in self.item_ids[item_type]:
            self.item_ids[item_type].append(item_id)
            self.mark_updated()
            logger.debug(f"Added {item_type} {item_id} to tag '{self.name}'")
        
        return True
    
    def remove_item(self, item_type: str, item_id: str) -> bool:
        """
        Remove an item from the tag.
        
        Args:
            item_type: The type of the item (character, location, etc.).
            item_id: The ID of the item.
            
        Returns:
            True if successful, False otherwise.
        """
        if item_type not in self.item_ids:
            logger.warning(f"Invalid item type '{item_type}' for tag '{self.name}'")
            return False
        
        if item_id in self.item_ids[item_type]:
            self.item_ids[item_type].remove(item_id)
            self.mark_updated()
            logger.debug(f"Removed {item_type} {item_id} from tag '{self.name}'")
        
        return True
    
    def get_items(self, item_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get items with this tag.
        
        Args:
            item_type: The type of items to get, or None to get all.
            
        Returns:
            A dictionary of item IDs by type, or a list of IDs if item_type is specified.
        """
        if item_type is not None:
            if item_type not in self.item_ids:
                logger.warning(f"Invalid item type '{item_type}' for tag '{self.name}'")
                return {}
            return {item_type: self.item_ids[item_type]}
        
        return self.item_ids
    
    def get_item_count(self, item_type: Optional[str] = None) -> int:
        """
        Get the number of items with this tag.
        
        Args:
            item_type: The type of items to count, or None to count all.
            
        Returns:
            The number of items.
        """
        if item_type is not None:
            if item_type not in self.item_ids:
                logger.warning(f"Invalid item type '{item_type}' for tag '{self.name}'")
                return 0
            return len(self.item_ids[item_type])
        
        return sum(len(items) for items in self.item_ids.values())
    
    def set_parent_tag(self, parent_id: Optional[str]) -> None:
        """
        Set the parent tag.
        
        Args:
            parent_id: The ID of the parent tag, or None to clear it.
        """
        self.parent_tag_id = parent_id
        self.mark_updated()
        if parent_id:
            logger.debug(f"Set parent tag to {parent_id} for tag '{self.name}'")
        else:
            logger.debug(f"Cleared parent tag for tag '{self.name}'")
    
    def add_child_tag(self, child_id: str) -> None:
        """
        Add a child tag.
        
        Args:
            child_id: The ID of the child tag to add.
        """
        if child_id not in self.child_tag_ids:
            self.child_tag_ids.append(child_id)
            self.mark_updated()
            logger.debug(f"Added child tag {child_id} for tag '{self.name}'")
    
    def remove_child_tag(self, child_id: str) -> None:
        """
        Remove a child tag.
        
        Args:
            child_id: The ID of the child tag to remove.
        """
        if child_id in self.child_tag_ids:
            self.child_tag_ids.remove(child_id)
            self.mark_updated()
            logger.debug(f"Removed child tag {child_id} for tag '{self.name}'")
    
    def has_children(self) -> bool:
        """
        Check if the tag has child tags.
        
        Returns:
            True if the tag has child tags, False otherwise.
        """
        return len(self.child_tag_ids) > 0
    
    def is_child_of(self, parent_id: str) -> bool:
        """
        Check if the tag is a child of the specified parent tag.
        
        Args:
            parent_id: The ID of the potential parent tag.
            
        Returns:
            True if the tag is a child of the parent, False otherwise.
        """
        return self.parent_tag_id == parent_id
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for tag '{self.name}'")
    
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
            logger.debug(f"Removed metadata '{key}' from tag '{self.name}'")
    
    def __str__(self) -> str:
        """
        Get a string representation of the tag.
        
        Returns:
            A string representation of the tag.
        """
        item_count = self.get_item_count()
        return f"Tag('{self.name}', items={item_count})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tag to a dictionary.
        
        Returns:
            A dictionary representation of the tag.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "project_id": self.project_id,
            "item_ids": self.item_ids,
            "parent_tag_id": self.parent_tag_id,
            "child_tag_ids": self.child_tag_ids,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def to_json(self) -> str:
        """
        Convert the tag to a JSON string.
        
        Returns:
            A JSON string representation of the tag.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """
        Create a Tag instance from a dictionary.
        
        Args:
            data: The dictionary containing the tag data.
            
        Returns:
            A new Tag instance.
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Tag':
        """
        Create a Tag instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the tag data.
            
        Returns:
            A new Tag instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
