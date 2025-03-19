#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outline Model for RebelSCRIBE.

This module defines the Outline class that represents an outline in a writing project.
"""

import logging
import datetime
from typing import Dict, List, Optional, Set, Any

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class OutlineItem(BaseModel):
    """
    Represents an item in an outline.
    
    An outline item is a single entry in an outline, with a title, description,
    and optional references to other elements in the project.
    """
    
    # Class variables
    _required_properties: Set[str] = {'title'}
    
    def __init__(self, **kwargs):
        """
        Initialize a new OutlineItem instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.order = kwargs.get("order", 0)  # Order within the parent
        self.parent_id = kwargs.get("parent_id", None)  # ID of the parent item
        self.child_ids = kwargs.get("child_ids", [])  # IDs of child items
        self.references = kwargs.get("references", {  # IDs of referenced elements
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
        self.is_completed = kwargs.get("is_completed", False)  # Whether the item is completed
    
    def set_description(self, description: str) -> None:
        """
        Set the item description.
        
        Args:
            description: The new description.
        """
        self.description = description
        self.mark_updated()
        logger.debug(f"Updated description for outline item '{self.title}'")
    
    def set_completed(self, completed: bool) -> None:
        """
        Set whether the item is completed.
        
        Args:
            completed: Whether the item is completed.
        """
        self.is_completed = completed
        self.mark_updated()
        if completed:
            logger.debug(f"Marked outline item '{self.title}' as completed")
        else:
            logger.debug(f"Marked outline item '{self.title}' as not completed")
    
    def set_parent(self, parent_id: Optional[str]) -> None:
        """
        Set the parent item.
        
        Args:
            parent_id: The ID of the parent item, or None to clear it.
        """
        self.parent_id = parent_id
        self.mark_updated()
        if parent_id:
            logger.debug(f"Set parent item to {parent_id} for outline item '{self.title}'")
        else:
            logger.debug(f"Cleared parent item for outline item '{self.title}'")
    
    def add_child(self, child_id: str) -> None:
        """
        Add a child item.
        
        Args:
            child_id: The ID of the child item to add.
        """
        if child_id not in self.child_ids:
            self.child_ids.append(child_id)
            self.mark_updated()
            logger.debug(f"Added child item {child_id} for outline item '{self.title}'")
    
    def remove_child(self, child_id: str) -> None:
        """
        Remove a child item.
        
        Args:
            child_id: The ID of the child item to remove.
        """
        if child_id in self.child_ids:
            self.child_ids.remove(child_id)
            self.mark_updated()
            logger.debug(f"Removed child item {child_id} for outline item '{self.title}'")
    
    def add_reference(self, ref_type: str, ref_id: str) -> bool:
        """
        Add a reference to another element.
        
        Args:
            ref_type: The type of the referenced element (character, location, etc.).
            ref_id: The ID of the referenced element.
            
        Returns:
            True if successful, False otherwise.
        """
        if ref_type not in self.references:
            logger.warning(f"Invalid reference type '{ref_type}' for outline item '{self.title}'")
            return False
        
        if ref_id not in self.references[ref_type]:
            self.references[ref_type].append(ref_id)
            self.mark_updated()
            logger.debug(f"Added reference to {ref_type} {ref_id} for outline item '{self.title}'")
        
        return True
    
    def remove_reference(self, ref_type: str, ref_id: str) -> bool:
        """
        Remove a reference to another element.
        
        Args:
            ref_type: The type of the referenced element (character, location, etc.).
            ref_id: The ID of the referenced element.
            
        Returns:
            True if successful, False otherwise.
        """
        if ref_type not in self.references:
            logger.warning(f"Invalid reference type '{ref_type}' for outline item '{self.title}'")
            return False
        
        if ref_id in self.references[ref_type]:
            self.references[ref_type].remove(ref_id)
            self.mark_updated()
            logger.debug(f"Removed reference to {ref_type} {ref_id} for outline item '{self.title}'")
        
        return True
    
    def get_references(self, ref_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get references to other elements.
        
        Args:
            ref_type: The type of references to get, or None to get all.
            
        Returns:
            A dictionary of reference IDs by type, or a list of IDs if ref_type is specified.
        """
        if ref_type is not None:
            if ref_type not in self.references:
                logger.warning(f"Invalid reference type '{ref_type}' for outline item '{self.title}'")
                return {}
            return {ref_type: self.references[ref_type]}
        
        return self.references
    
    def set_color(self, color: Optional[str]) -> None:
        """
        Set the item's color.
        
        Args:
            color: The new color, or None to remove the color.
        """
        self.color = color
        self.mark_updated()
        if color:
            logger.debug(f"Set color to '{color}' for outline item '{self.title}'")
        else:
            logger.debug(f"Removed color for outline item '{self.title}'")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for outline item '{self.title}'")
    
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
            logger.debug(f"Removed metadata '{key}' from outline item '{self.title}'")
    
    def __str__(self) -> str:
        """
        Get a string representation of the outline item.
        
        Returns:
            A string representation of the outline item.
        """
        completed_str = " (Completed)" if self.is_completed else ""
        return f"OutlineItem('{self.title}'{completed_str})"
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutlineItem':
        """
        Create an OutlineItem instance from a dictionary.
        
        Args:
            data: The dictionary containing the outline item data.
            
        Returns:
            A new OutlineItem instance.
        """
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            order=data.get("order", 0),
            parent_id=data.get("parent_id"),
            child_ids=data.get("child_ids", []),
            references=data.get("references", {
                "character": [],
                "location": [],
                "scene": [],
                "chapter": [],
                "note": [],
                "tag": []
            }),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            color=data.get("color"),
            is_completed=data.get("is_completed", False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the outline item to a dictionary.
        
        Returns:
            A dictionary representation of the outline item.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "references": self.references,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "color": self.color,
            "is_completed": self.is_completed
        }
    
    def to_json(self) -> str:
        """
        Convert the outline item to a JSON string.
        
        Returns:
            A JSON string representation of the outline item.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'OutlineItem':
        """
        Create an OutlineItem instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the outline item data.
            
        Returns:
            A new OutlineItem instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)


class Outline(BaseModel):
    """
    Represents an outline in a writing project.
    
    An outline is a hierarchical structure of items that represents the
    structure and content of a writing project. It can be used to plan
    and organize the project before writing.
    """
    
    # Class variables
    _required_properties: Set[str] = {'title'}
    
    def __init__(self, **kwargs):
        """
        Initialize a new Outline instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.project_id = kwargs.get("project_id", "")  # ID of the project this outline belongs to
        self.document_id = kwargs.get("document_id", None)  # ID of the document representing this outline
        self.root_item_ids = kwargs.get("root_item_ids", [])  # IDs of root items
        self.items = kwargs.get("items", {})  # All items in the outline
        self.metadata = kwargs.get("metadata", {})  # Additional metadata
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
    
    def set_description(self, description: str) -> None:
        """
        Set the outline description.
        
        Args:
            description: The new description.
        """
        self.description = description
        self.mark_updated()
        logger.debug(f"Updated description for outline '{self.title}'")
    
    def add_item(self, item: OutlineItem, parent_id: Optional[str] = None) -> None:
        """
        Add an item to the outline.
        
        Args:
            item: The item to add.
            parent_id: The ID of the parent item, or None to add as a root item.
        """
        # Add the item to the items dictionary
        self.items[item.id] = item
        self.mark_updated()
        
        # Set the parent-child relationship
        if parent_id is not None:
            if parent_id in self.items:
                item.set_parent(parent_id)
                self.items[parent_id].add_child(item.id)
            else:
                logger.warning(f"Parent item {parent_id} not found for outline item '{item.title}'")
                self.root_item_ids.append(item.id)
        else:
            self.root_item_ids.append(item.id)
        
        logger.debug(f"Added item '{item.title}' to outline '{self.title}'")
    
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from the outline.
        
        Args:
            item_id: The ID of the item to remove.
            
        Returns:
            True if successful, False otherwise.
        """
        if item_id not in self.items:
            logger.warning(f"Item {item_id} not found in outline '{self.title}'")
            return False
        
        item = self.items[item_id]
        
        # Remove from parent's children
        if item.parent_id is not None and item.parent_id in self.items:
            self.items[item.parent_id].remove_child(item_id)
        
        # Remove from root items
        if item_id in self.root_item_ids:
            self.root_item_ids.remove(item_id)
        
        # Handle children
        for child_id in item.child_ids:
            if child_id in self.items:
                # Make children root items or connect to grandparent
                if item.parent_id is not None and item.parent_id in self.items:
                    self.items[child_id].set_parent(item.parent_id)
                    self.items[item.parent_id].add_child(child_id)
                else:
                    self.items[child_id].set_parent(None)
                    if child_id not in self.root_item_ids:
                        self.root_item_ids.append(child_id)
        
        # Remove the item
        del self.items[item_id]
        self.mark_updated()
        logger.debug(f"Removed item {item_id} from outline '{self.title}'")
        
        return True
    
    def get_item(self, item_id: str) -> Optional[OutlineItem]:
        """
        Get an item from the outline.
        
        Args:
            item_id: The ID of the item to get.
            
        Returns:
            The item, or None if not found.
        """
        return self.items.get(item_id)
    
    def get_root_items(self) -> List[OutlineItem]:
        """
        Get the root items of the outline.
        
        Returns:
            A list of root items.
        """
        return [self.items[item_id] for item_id in self.root_item_ids if item_id in self.items]
    
    def get_children(self, item_id: str) -> List[OutlineItem]:
        """
        Get the children of an item.
        
        Args:
            item_id: The ID of the item to get children for.
            
        Returns:
            A list of child items, or an empty list if the item is not found.
        """
        if item_id not in self.items:
            logger.warning(f"Item {item_id} not found in outline '{self.title}'")
            return []
        
        return [self.items[child_id] for child_id in self.items[item_id].child_ids if child_id in self.items]
    
    def move_item(self, item_id: str, new_parent_id: Optional[str], new_order: int) -> bool:
        """
        Move an item to a new parent and/or position.
        
        Args:
            item_id: The ID of the item to move.
            new_parent_id: The ID of the new parent, or None to make a root item.
            new_order: The new order within the parent.
            
        Returns:
            True if successful, False otherwise.
        """
        if item_id not in self.items:
            logger.warning(f"Item {item_id} not found in outline '{self.title}'")
            return False
        
        if new_parent_id is not None and new_parent_id not in self.items:
            logger.warning(f"New parent item {new_parent_id} not found in outline '{self.title}'")
            return False
        
        # Check for circular reference
        if new_parent_id is not None and self._is_descendant(new_parent_id, item_id):
            logger.warning(f"Cannot move item {item_id} to {new_parent_id} (circular reference)")
            return False
        
        item = self.items[item_id]
        old_parent_id = item.parent_id
        
        # Remove from old parent's children
        if old_parent_id is not None and old_parent_id in self.items:
            self.items[old_parent_id].remove_child(item_id)
        
        # Remove from root items if it was a root item
        if item_id in self.root_item_ids:
            self.root_item_ids.remove(item_id)
        
        # Set new parent
        item.set_parent(new_parent_id)
        
        # Add to new parent's children or root items
        if new_parent_id is not None:
            self.items[new_parent_id].add_child(item_id)
            
            # Reorder children
            children = self.items[new_parent_id].child_ids
            if item_id in children:
                children.remove(item_id)
            
            if new_order < 0:
                new_order = 0
            elif new_order > len(children):
                new_order = len(children)
            
            children.insert(new_order, item_id)
            self.items[new_parent_id].child_ids = children
        else:
            # Add to root items
            if item_id not in self.root_item_ids:
                self.root_item_ids.append(item_id)
            
            # Reorder root items
            if item_id in self.root_item_ids:
                self.root_item_ids.remove(item_id)
            
            if new_order < 0:
                new_order = 0
            elif new_order > len(self.root_item_ids):
                new_order = len(self.root_item_ids)
            
            self.root_item_ids.insert(new_order, item_id)
        
        # Update order
        item.order = new_order
        self.mark_updated()
        logger.debug(f"Moved item {item_id} to parent {new_parent_id} at position {new_order}")
        
        return True
    
    def _is_descendant(self, item_id: str, potential_ancestor_id: str) -> bool:
        """
        Check if an item is a descendant of another item.
        
        Args:
            item_id: The ID of the item to check.
            potential_ancestor_id: The ID of the potential ancestor.
            
        Returns:
            True if the item is a descendant of the potential ancestor, False otherwise.
        """
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        
        if item.parent_id is None:
            return False
        
        if item.parent_id == potential_ancestor_id:
            return True
        
        return self._is_descendant(item.parent_id, potential_ancestor_id)
    
    def get_item_count(self) -> int:
        """
        Get the number of items in the outline.
        
        Returns:
            The number of items.
        """
        return len(self.items)
    
    def get_completed_count(self) -> int:
        """
        Get the number of completed items in the outline.
        
        Returns:
            The number of completed items.
        """
        return sum(1 for item in self.items.values() if item.is_completed)
    
    def get_completion_percentage(self) -> float:
        """
        Get the completion percentage of the outline.
        
        Returns:
            The completion percentage (0-100).
        """
        total = self.get_item_count()
        if total == 0:
            return 0.0
        
        completed = self.get_completed_count()
        return (completed / total) * 100.0
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for outline '{self.title}'")
    
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
            logger.debug(f"Removed metadata '{key}' from outline '{self.title}'")
    
    def __str__(self) -> str:
        """
        Get a string representation of the outline.
        
        Returns:
            A string representation of the outline.
        """
        return f"Outline('{self.title}', items={self.get_item_count()}, completion={self.get_completion_percentage():.1f}%)"
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Outline':
        """
        Create an Outline instance from a dictionary.
        
        Args:
            data: The dictionary containing the outline data.
            
        Returns:
            A new Outline instance.
        """
        # Create a new outline with basic properties
        outline = cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            project_id=data.get("project_id", ""),
            document_id=data.get("document_id"),
            root_item_ids=data.get("root_item_ids", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
        
        # Process items
        items_data = data.get("items", {})
        for item_id, item_data in items_data.items():
            # Convert each item data to an OutlineItem
            outline.items[item_id] = OutlineItem.from_dict(item_data)
        
        return outline
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the outline to a dictionary.
        
        Returns:
            A dictionary representation of the outline.
        """
        # Convert items to dictionaries
        items_dict = {}
        for item_id, item in self.items.items():
            items_dict[item_id] = item.to_dict()
        
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "root_item_ids": self.root_item_ids,
            "items": items_dict,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def to_json(self) -> str:
        """
        Convert the outline to a JSON string.
        
        Returns:
            A JSON string representation of the outline.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Outline':
        """
        Create an Outline instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the outline data.
            
        Returns:
            A new Outline instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
