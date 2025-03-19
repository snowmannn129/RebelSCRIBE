#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Location Model for RebelSCRIBE.

This module defines the Location class that represents a location in a writing project.
"""

import logging
import datetime
from typing import Dict, List, Optional, Set, Any

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Location(BaseModel):
    """
    Represents a location in a writing project.
    
    A location is a place where scenes occur. Locations can be real or fictional,
    and can have various attributes such as description, history, etc.
    """
    
    # Class variables
    _required_properties: Set[str] = {'name'}
    
    # Location types
    TYPE_REAL = "Real"
    TYPE_FICTIONAL = "Fictional"
    
    # Valid location types
    VALID_TYPES = {TYPE_REAL, TYPE_FICTIONAL}
    
    def __init__(self, **kwargs):
        """
        Initialize a new Location instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.name = kwargs.get("name", "")
        self.type = kwargs.get("type", self.TYPE_FICTIONAL)  # Default type
        self.description = kwargs.get("description", "")
        self.address = kwargs.get("address", None)
        self.city = kwargs.get("city", None)
        self.region = kwargs.get("region", None)
        self.country = kwargs.get("country", None)
        self.coordinates = kwargs.get("coordinates", None)  # Latitude, longitude
        self.history = kwargs.get("history", "")
        self.significance = kwargs.get("significance", "")  # Significance to the story
        self.notes = kwargs.get("notes", "")
        self.project_id = kwargs.get("project_id", "")  # ID of the project this location belongs to
        self.document_id = kwargs.get("document_id", None)  # ID of the document representing this location
        self.scene_ids = kwargs.get("scene_ids", [])  # IDs of scenes that take place at this location
        self.parent_location_id = kwargs.get("parent_location_id", None)  # ID of the parent location (e.g., a room in a building)
        self.child_location_ids = kwargs.get("child_location_ids", [])  # IDs of child locations
        self.metadata = kwargs.get("metadata", {})  # Additional metadata
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
        self.color = kwargs.get("color", None)  # For visual organization
        self.tags = kwargs.get("tags", [])  # Tags for categorization
        self.image_path = kwargs.get("image_path", None)  # Path to location image
        self.map_path = kwargs.get("map_path", None)  # Path to location map
        
        # Validate location type
        if self.type not in self.VALID_TYPES:
            logger.warning(f"Invalid location type '{self.type}'. Using '{self.TYPE_FICTIONAL}' instead.")
            self.type = self.TYPE_FICTIONAL
    
    def set_type(self, location_type: str) -> None:
        """
        Set the location type.
        
        Args:
            location_type: The new location type.
        """
        if location_type not in self.VALID_TYPES:
            logger.warning(f"Invalid location type '{location_type}'. Using current type '{self.type}' instead.")
            return
        
        self.type = location_type
        self.mark_updated()
        logger.debug(f"Set type to '{location_type}' for location '{self.name}'")
    
    def set_description(self, description: str) -> None:
        """
        Set the location description.
        
        Args:
            description: The new description.
        """
        self.description = description
        self.mark_updated()
        logger.debug(f"Updated description for location '{self.name}'")
    
    def set_address(self, address: Optional[str]) -> None:
        """
        Set the location address.
        
        Args:
            address: The new address, or None to clear it.
        """
        self.address = address
        self.mark_updated()
        if address:
            logger.debug(f"Set address to '{address}' for location '{self.name}'")
        else:
            logger.debug(f"Cleared address for location '{self.name}'")
    
    def set_coordinates(self, coordinates: Optional[str]) -> None:
        """
        Set the location coordinates.
        
        Args:
            coordinates: The new coordinates (latitude, longitude), or None to clear them.
        """
        self.coordinates = coordinates
        self.mark_updated()
        if coordinates:
            logger.debug(f"Set coordinates to '{coordinates}' for location '{self.name}'")
        else:
            logger.debug(f"Cleared coordinates for location '{self.name}'")
    
    def set_history(self, history: str) -> None:
        """
        Set the location history.
        
        Args:
            history: The new history.
        """
        self.history = history
        self.mark_updated()
        logger.debug(f"Updated history for location '{self.name}'")
    
    def set_significance(self, significance: str) -> None:
        """
        Set the location significance.
        
        Args:
            significance: The new significance.
        """
        self.significance = significance
        self.mark_updated()
        logger.debug(f"Updated significance for location '{self.name}'")
    
    def set_notes(self, notes: str) -> None:
        """
        Set the location notes.
        
        Args:
            notes: The new notes.
        """
        self.notes = notes
        self.mark_updated()
        logger.debug(f"Updated notes for location '{self.name}'")
    
    def add_scene(self, scene_id: str) -> None:
        """
        Add a scene that takes place at this location.
        
        Args:
            scene_id: The ID of the scene to add.
        """
        if scene_id not in self.scene_ids:
            self.scene_ids.append(scene_id)
            self.mark_updated()
            logger.debug(f"Added scene {scene_id} for location '{self.name}'")
    
    def remove_scene(self, scene_id: str) -> None:
        """
        Remove a scene that takes place at this location.
        
        Args:
            scene_id: The ID of the scene to remove.
        """
        if scene_id in self.scene_ids:
            self.scene_ids.remove(scene_id)
            self.mark_updated()
            logger.debug(f"Removed scene {scene_id} for location '{self.name}'")
    
    def set_parent_location(self, parent_id: Optional[str]) -> None:
        """
        Set the parent location.
        
        Args:
            parent_id: The ID of the parent location, or None to clear it.
        """
        self.parent_location_id = parent_id
        self.mark_updated()
        if parent_id:
            logger.debug(f"Set parent location to {parent_id} for location '{self.name}'")
        else:
            logger.debug(f"Cleared parent location for location '{self.name}'")
    
    def add_child_location(self, child_id: str) -> None:
        """
        Add a child location.
        
        Args:
            child_id: The ID of the child location to add.
        """
        if child_id not in self.child_location_ids:
            self.child_location_ids.append(child_id)
            self.mark_updated()
            logger.debug(f"Added child location {child_id} for location '{self.name}'")
    
    def remove_child_location(self, child_id: str) -> None:
        """
        Remove a child location.
        
        Args:
            child_id: The ID of the child location to remove.
        """
        if child_id in self.child_location_ids:
            self.child_location_ids.remove(child_id)
            self.mark_updated()
            logger.debug(f"Removed child location {child_id} for location '{self.name}'")
    
    def set_image_path(self, path: Optional[str]) -> None:
        """
        Set the path to the location's image.
        
        Args:
            path: The path to the image, or None to clear it.
        """
        self.image_path = path
        self.mark_updated()
        if path:
            logger.debug(f"Set image path to '{path}' for location '{self.name}'")
        else:
            logger.debug(f"Cleared image path for location '{self.name}'")
    
    def set_map_path(self, path: Optional[str]) -> None:
        """
        Set the path to the location's map.
        
        Args:
            path: The path to the map, or None to clear it.
        """
        self.map_path = path
        self.mark_updated()
        if path:
            logger.debug(f"Set map path to '{path}' for location '{self.name}'")
        else:
            logger.debug(f"Cleared map path for location '{self.name}'")
    
    def set_color(self, color: Optional[str]) -> None:
        """
        Set the location's color.
        
        Args:
            color: The new color, or None to remove the color.
        """
        self.color = color
        self.mark_updated()
        if color:
            logger.debug(f"Set color to '{color}' for location '{self.name}'")
        else:
            logger.debug(f"Removed color for location '{self.name}'")
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the location.
        
        Args:
            tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.mark_updated()
            logger.debug(f"Added tag '{tag}' to location '{self.name}'")
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the location.
        
        Args:
            tag: The tag to remove.
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_updated()
            logger.debug(f"Removed tag '{tag}' from location '{self.name}'")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for location '{self.name}'")
    
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
            logger.debug(f"Removed metadata '{key}' from location '{self.name}'")
    
    def __str__(self) -> str:
        """
        Get a string representation of the location.
        
        Returns:
            A string representation of the location.
        """
        return f"Location('{self.name}', type='{self.type}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the location to a dictionary.
        
        Returns:
            A dictionary representation of the location.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "address": self.address,
            "city": self.city,
            "region": self.region,
            "country": self.country,
            "coordinates": self.coordinates,
            "history": self.history,
            "significance": self.significance,
            "notes": self.notes,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "scene_ids": self.scene_ids,
            "parent_location_id": self.parent_location_id,
            "child_location_ids": self.child_location_ids,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "color": self.color,
            "tags": self.tags,
            "image_path": self.image_path,
            "map_path": self.map_path
        }
    
    def to_json(self) -> str:
        """
        Convert the location to a JSON string.
        
        Returns:
            A JSON string representation of the location.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Location':
        """
        Create a Location instance from a dictionary.
        
        Args:
            data: The dictionary containing the location data.
            
        Returns:
            A new Location instance.
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Location':
        """
        Create a Location instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the location data.
            
        Returns:
            A new Location instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_document(self, document):
        """
        Update a document with this location's data.
        
        Args:
            document: The document to update.
        """
        document.title = self.name
        document.metadata = self.metadata.copy()
        document.set_metadata("location_data", self.to_dict())
        document.color = self.color
        document.tags = self.tags.copy()
        return document
    
    @classmethod
    def from_document(cls, document):
        """
        Create a Location instance from a document.
        
        Args:
            document: The document containing the location data.
            
        Returns:
            A new Location instance.
        """
        # Try to get location data from metadata
        location_data = document.metadata.get("location_data", {})
        
        # If no location data, create a basic location
        if not location_data:
            return cls(
                name=document.title,
                document_id=document.id,
                metadata=document.metadata.copy(),
                color=document.color,
                tags=document.tags.copy()
            )
        
        # Create location from data
        location = cls.from_dict(location_data)
        
        # Ensure document ID is set
        location.document_id = document.id
        
        return location
