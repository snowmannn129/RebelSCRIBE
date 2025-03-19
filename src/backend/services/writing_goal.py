#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Writing Goal module for RebelSCRIBE.

This module defines the WritingGoal class which represents a writing goal
with target values, progress tracking, and completion status.
"""

import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import logging
logger = logging.getLogger(__name__)


@dataclass
class WritingGoal:
    """
    Represents a writing goal.
    
    Attributes:
        id: The unique identifier for the goal.
        name: The name of the goal.
        target_type: The type of target (words, pages, etc.).
        target_value: The target value to reach.
        start_date: The start date of the goal.
        end_date: The end date of the goal.
        document_ids: The IDs of documents to track for this goal.
        current_value: The current value towards the goal.
        completed: Whether the goal has been completed.
        completed_date: The date the goal was completed.
    """
    id: str
    name: str
    target_type: str
    target_value: int
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime] = None
    document_ids: List[str] = field(default_factory=list)
    current_value: int = 0
    completed: bool = False
    completed_date: Optional[datetime.datetime] = None
    
    # Target types
    TARGET_WORDS = "words"
    TARGET_PAGES = "pages"
    TARGET_CHAPTERS = "chapters"
    TARGET_SCENES = "scenes"
    
    def update_progress(self, current_value: int) -> None:
        """
        Update the progress towards the goal.
        
        Args:
            current_value: The current value towards the goal.
        """
        self.current_value = current_value
        
        # Check if goal is completed
        if not self.completed and self.current_value >= self.target_value:
            self.completed = True
            self.completed_date = datetime.datetime.now()
    
    def get_progress_percentage(self) -> float:
        """
        Get the progress percentage towards the goal.
        
        Returns:
            The progress percentage (0-100).
        """
        if self.target_value <= 0:
            return 0.0
        
        percentage = (self.current_value / self.target_value) * 100
        return min(percentage, 100.0)  # Cap at 100%
    
    def get_remaining(self) -> int:
        """
        Get the remaining value to reach the goal.
        
        Returns:
            The remaining value.
        """
        remaining = self.target_value - self.current_value
        return max(remaining, 0)  # Don't return negative values
    
    def is_active(self) -> bool:
        """
        Check if the goal is active.
        
        Returns:
            True if the goal is active, False otherwise.
        """
        if self.completed:
            return False
        
        now = datetime.datetime.now()
        
        # Check if goal has started
        if self.start_date and self.start_date > now:
            return False
        
        # Check if goal has ended
        if self.end_date and self.end_date < now:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the writing goal to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "target_type": self.target_type,
            "target_value": self.target_value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "document_ids": self.document_ids,
            "current_value": self.current_value,
            "completed": self.completed,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WritingGoal':
        """Create a writing goal from a dictionary."""
        start_date = datetime.datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None
        end_date = datetime.datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None
        completed_date = datetime.datetime.fromisoformat(data["completed_date"]) if data.get("completed_date") else None
        
        goal = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            target_type=data.get("target_type", ""),
            target_value=data.get("target_value", 0),
            start_date=start_date,
            end_date=end_date,
            document_ids=data.get("document_ids", []),
            current_value=data.get("current_value", 0),
            completed=data.get("completed", False),
            completed_date=completed_date
        )
        
        return goal
