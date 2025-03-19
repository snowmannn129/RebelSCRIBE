#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Model for RebelSCRIBE.

This module defines the Project class that represents a writing project.
"""

import os
import logging
import datetime
from typing import Dict, List, Optional, Set, Any
from pathlib import Path

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class Project(BaseModel):
    """
    Represents a writing project in RebelSCRIBE.
    
    A project is the top-level container for all content and metadata
    related to a writing project, such as a novel, short story, etc.
    """
    
    # Class variables
    _required_properties: Set[str] = {'title'}
    
    def __init__(self, **kwargs):
        """
        Initialize a new Project instance.
        
        Args:
            **kwargs: Property values to set.
        """
        # Call parent constructor first to initialize _original_values
        super().__init__(**kwargs)
        
        # Initialize with default values if not provided in kwargs
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.author = kwargs.get("author", "")
        self.created_at = kwargs.get("created_at", datetime.datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.datetime.now())
        self.word_count_goal = kwargs.get("word_count_goal", None)
        self.deadline = kwargs.get("deadline", None)
        self.genre = kwargs.get("genre", "")
        self.tags = kwargs.get("tags", [])
        self.path = kwargs.get("path", None)
        self.version = kwargs.get("version", "1.0.0")
        self.language = kwargs.get("language", "en")
        self.status = kwargs.get("status", "In Progress")  # In Progress, Completed, On Hold, Abandoned
        self.metadata = kwargs.get("metadata", {})
    
    @property
    def filename(self) -> str:
        """
        Get the filename for the project.
        
        Returns:
            The filename for the project.
        """
        if self.path:
            return os.path.basename(self.path)
        
        # Create a filename from the title
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in self.title)
        return f"{safe_title.replace(' ', '_')}.rebelscribe"
    
    @property
    def directory(self) -> Optional[str]:
        """
        Get the directory containing the project.
        
        Returns:
            The directory containing the project, or None if the project has no path.
        """
        if not self.path:
            return None
        
        # Use Path for cross-platform compatibility
        return str(Path(self.path).parent)
    
    def set_path(self, path: str) -> None:
        """
        Set the path for the project.
        
        Args:
            path: The path to the project file.
        """
        # Use Path for cross-platform compatibility
        self.path = str(Path(path).absolute())
        self.mark_updated()
        logger.debug(f"Set project path to {self.path}")
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the project.
        
        Args:
            tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.mark_updated()
            logger.debug(f"Added tag '{tag}' to project {self.title}")
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the project.
        
        Args:
            tag: The tag to remove.
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_updated()
            logger.debug(f"Removed tag '{tag}' from project {self.title}")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.mark_updated()
        logger.debug(f"Set metadata '{key}' to '{value}' for project {self.title}")
    
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
            logger.debug(f"Removed metadata '{key}' from project {self.title}")
    
    def update_word_count_goal(self, goal: Optional[int]) -> None:
        """
        Update the word count goal.
        
        Args:
            goal: The new word count goal, or None to remove the goal.
        """
        self.word_count_goal = goal
        self.mark_updated()
        if goal is None:
            logger.debug(f"Removed word count goal for project {self.title}")
        else:
            logger.debug(f"Set word count goal to {goal} for project {self.title}")
    
    def update_deadline(self, deadline: Optional[datetime.datetime]) -> None:
        """
        Update the deadline.
        
        Args:
            deadline: The new deadline, or None to remove the deadline.
        """
        self.deadline = deadline
        self.mark_updated()
        if deadline is None:
            logger.debug(f"Removed deadline for project {self.title}")
        else:
            logger.debug(f"Set deadline to {deadline} for project {self.title}")
    
    def update_status(self, status: str) -> None:
        """
        Update the project status.
        
        Args:
            status: The new status.
        """
        valid_statuses = ["In Progress", "Completed", "On Hold", "Abandoned"]
        if status not in valid_statuses:
            logger.warning(f"Invalid status '{status}'. Using 'In Progress' instead.")
            status = "In Progress"
        
        self.status = status
        self.mark_updated()
        logger.debug(f"Set status to '{status}' for project {self.title}")
    
    def __str__(self) -> str:
        """
        Get a string representation of the project.
        
        Returns:
            A string representation of the project.
        """
        return f"Project(title='{self.title}', author='{self.author}', status='{self.status}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the project to a dictionary.
        
        Returns:
            A dictionary representation of the project.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "word_count_goal": self.word_count_goal,
            "deadline": self.deadline,
            "genre": self.genre,
            "tags": self.tags,
            "path": self.path,
            "version": self.version,
            "language": self.language,
            "status": self.status,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """
        Convert the project to a JSON string.
        
        Returns:
            A JSON string representation of the project.
        """
        import json
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        Create a Project instance from a dictionary.
        
        Args:
            data: The dictionary containing the project data.
            
        Returns:
            A new Project instance.
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Project':
        """
        Create a Project instance from a JSON string.
        
        Args:
            json_str: The JSON string containing the project data.
            
        Returns:
            A new Project instance.
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
