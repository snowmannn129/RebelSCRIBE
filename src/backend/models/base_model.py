#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Model for RebelSCRIBE.

This module defines the BaseModel class that all models inherit from.
"""

import uuid
import json
import logging
import datetime
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, ClassVar, get_type_hints

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseModel')

class BaseModel:
    """
    Base class for all models in the application.
    
    This class provides common functionality for all models, including:
    - Unique ID generation
    - JSON serialization/deserialization
    - Property validation
    - Change tracking
    """
    
    # Class variables
    _property_types: ClassVar[Dict[str, Type]] = {}
    _required_properties: ClassVar[Set[str]] = set()
    
    def __init__(self, **kwargs):
        """
        Initialize a new model instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Initialize basic properties
        self.id: str = kwargs.get('id', str(uuid.uuid4()))
        self.created_at: datetime.datetime = kwargs.get(
            'created_at', 
            datetime.datetime.fromisoformat(kwargs.get('created_at_iso', '')) if 'created_at_iso' in kwargs 
            else datetime.datetime.now()
        )
        self.updated_at: datetime.datetime = kwargs.get(
            'updated_at', 
            datetime.datetime.fromisoformat(kwargs.get('updated_at_iso', '')) if 'updated_at_iso' in kwargs 
            else datetime.datetime.now()
        )
        
        # Set up change tracking
        self._changed_properties: Set[str] = set()
        self._original_values: Dict[str, Any] = {}
        
        # Get property types from annotations
        self._property_types = get_type_hints(self.__class__)
        
        # Set properties from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ('id', 'created_at', 'updated_at'):
                setattr(self, key, value)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set an attribute value and track changes.
        
        Args:
            name: Attribute name.
            value: Attribute value.
        """
        # Track changes for existing properties
        if name != '_changed_properties' and name != '_original_values' and hasattr(self, name):
            if name not in self._original_values:
                self._original_values[name] = getattr(self, name)
            self._changed_properties.add(name)
        
        # Set the attribute
        super().__setattr__(name, value)
    
    def mark_updated(self) -> None:
        """Mark the model as updated."""
        self.updated_at = datetime.datetime.now()
    
    def reset_change_tracking(self) -> None:
        """Reset change tracking."""
        self._changed_properties = set()
        self._original_values = {}
    
    def has_changes(self) -> bool:
        """
        Check if the model has changes.
        
        Returns:
            True if the model has changes, False otherwise.
        """
        return len(self._changed_properties) > 0
    
    def get_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the changes made to the model.
        
        Returns:
            A dictionary of changes, with property names as keys and dictionaries
            containing 'old' and 'new' values as values.
        """
        changes = {}
        for prop in self._changed_properties:
            changes[prop] = {
                'old': self._original_values.get(prop),
                'new': getattr(self, prop)
            }
        return changes
    
    def validate(self) -> List[str]:
        """
        Validate the model.
        
        Returns:
            A list of validation error messages. Empty if valid.
        """
        errors = []
        
        # Check required properties
        for prop in self._required_properties:
            if not hasattr(self, prop) or getattr(self, prop) is None:
                errors.append(f"Required property '{prop}' is missing or None")
        
        # Check property types
        for prop, prop_type in self._property_types.items():
            if hasattr(self, prop) and getattr(self, prop) is not None:
                value = getattr(self, prop)
                # Skip validation for Any type
                if prop_type == Any:
                    continue
                
                # Handle Optional types
                origin = getattr(prop_type, '__origin__', None)
                if origin is Optional:
                    args = getattr(prop_type, '__args__', [])
                    if len(args) > 0:
                        prop_type = args[0]
                
                # Check if value is of the correct type
                try:
                    if not isinstance(value, prop_type):
                        errors.append(f"Property '{prop}' has invalid type. Expected {prop_type}, got {type(value)}")
                except TypeError:
                    # Some types like List[str] will cause TypeError in isinstance
                    logger.debug(f"Could not check type of property '{prop}' with value {value}")
        
        return errors
    
    def is_valid(self) -> bool:
        """
        Check if the model is valid.
        
        Returns:
            True if the model is valid, False otherwise.
        """
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            A dictionary representation of the model.
        """
        result = {}
        
        # Add all public properties
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                # Handle datetime objects
                if isinstance(value, datetime.datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        
        return result
    
    def to_json(self) -> str:
        """
        Convert the model to a JSON string.
        
        Returns:
            A JSON string representation of the model.
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary.
        
        Args:
            data: Dictionary containing model data.
            
        Returns:
            A new model instance.
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """
        Create a model instance from a JSON string.
        
        Args:
            json_str: JSON string containing model data.
            
        Returns:
            A new model instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """
        Get a string representation of the model.
        
        Returns:
            A string representation of the model.
        """
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self) -> str:
        """
        Get a detailed string representation of the model.
        
        Returns:
            A detailed string representation of the model.
        """
        properties = []
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                properties.append(f"{key}={value!r}")
        
        return f"{self.__class__.__name__}({', '.join(properties)})"
    
    def __eq__(self, other: object) -> bool:
        """
        Check if two models are equal.
        
        Args:
            other: The other model to compare with.
            
        Returns:
            True if the models are equal, False otherwise.
        """
        if not isinstance(other, BaseModel):
            return False
        
        return self.id == other.id
    
    def __hash__(self) -> int:
        """
        Get a hash value for the model.
        
        Returns:
            A hash value for the model.
        """
        return hash(self.id)
