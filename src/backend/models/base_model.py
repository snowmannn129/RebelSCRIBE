#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base model for RebelSCRIBE.

This module defines the BaseModel class which is the base class for all models.
"""

import datetime
import uuid
from typing import Dict, List, Optional, Set, Any

class BaseModel:
    """
    Base class for all models.
    
    This class provides common functionality for all models, such as
    tracking changes and serialization.
    
    Attributes:
        id: The unique identifier for the model.
        created_at: The creation date of the model.
        updated_at: The last update date of the model.
    """
    
    # Class variables
    _required_properties: Set[str] = set()
    
    def __init__(self, **kwargs):
        """
        Initialize a new BaseModel.
        
        Args:
            **kwargs: Property values to set.
        """
        # Store original values for change tracking
        self._original_values = {}
        
        # Set ID if provided, otherwise generate a new one
        self.id = kwargs.get("id", str(uuid.uuid4()))
        
        # Set timestamps
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
        
        # Check required properties
        for prop in self._required_properties:
            if prop not in kwargs:
                raise ValueError(f"Required property '{prop}' not provided")
    
    def mark_updated(self):
        """Mark the model as updated."""
        self.updated_at = datetime.datetime.now()
    
    def has_changed(self, property_name: str) -> bool:
        """
        Check if a property has changed.
        
        Args:
            property_name: The property name.
            
        Returns:
            bool: True if the property has changed, False otherwise.
        """
        if property_name not in self._original_values:
            return True
        
        current_value = getattr(self, property_name, None)
        original_value = self._original_values[property_name]
        
        return current_value != original_value
    
    def get_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all changes.
        
        Returns:
            A dictionary of property names to dictionaries containing 'old' and 'new' values.
        """
        changes = {}
        
        for prop, original_value in self._original_values.items():
            current_value = getattr(self, prop, None)
            
            if current_value != original_value:
                changes[prop] = {
                    "old": original_value,
                    "new": current_value
                }
        
        return changes
    
    def reset_changes(self):
        """Reset change tracking."""
        self._original_values = {}
        
        for prop in dir(self):
            # Skip private properties and methods
            if prop.startswith("_") or callable(getattr(self, prop)):
                continue
            
            self._original_values[prop] = getattr(self, prop)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            A dictionary representation of the model.
        """
        result = {}
        
        for prop in dir(self):
            # Skip private properties and methods
            if prop.startswith("_") or callable(getattr(self, prop)):
                continue
            
            result[prop] = getattr(self, prop)
        
        return result
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update the model from a dictionary.
        
        Args:
            data: The dictionary containing the model data.
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.mark_updated()
