#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Goal Manager module for RebelSCRIBE.

This module provides functionality for managing writing goals,
including creating, updating, and tracking goal progress.
"""

import datetime
import uuid
from typing import Dict, List, Optional, Any, Callable

from .writing_goal import WritingGoal

import logging
logger = logging.getLogger(__name__)


class GoalManager:
    """
    Manages writing goals for the statistics service.
    """
    
    def __init__(self, words_per_page: int = 250):
        """
        Initialize the GoalManager.
        
        Args:
            words_per_page: The number of words per page for page count goals.
        """
        self.words_per_page = words_per_page
        self.goals: Dict[str, WritingGoal] = {}
    
    def create_goal(self, name: str, target_type: str, target_value: int,
                   start_date: datetime.date, end_date: Optional[datetime.date] = None,
                   document_ids: Optional[List[str]] = None) -> WritingGoal:
        """
        Create a new writing goal.
        
        Args:
            name: The name of the goal.
            target_type: The type of target (words, pages, etc.).
            target_value: The target value to reach.
            start_date: The start date of the goal.
            end_date: The end date of the goal.
            document_ids: The IDs of documents to track for this goal.
            
        Returns:
            The new writing goal.
        """
        try:
            # Create goal ID
            goal_id = f"goal_{uuid.uuid4().hex[:8]}"
            
            # Convert dates to datetime
            start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
            end_datetime = datetime.datetime.combine(end_date, datetime.time.max) if end_date else None
            
            # Create goal
            goal = WritingGoal(
                id=goal_id,
                name=name,
                target_type=target_type,
                target_value=target_value,
                start_date=start_datetime,
                end_date=end_datetime,
                document_ids=document_ids or []
            )
            
            # Add to goals
            self.goals[goal_id] = goal
            
            logger.info(f"Created new writing goal: {name}")
            return goal
        
        except Exception as e:
            logger.error(f"Error creating writing goal: {e}", exc_info=True)
            # Create a default goal
            return WritingGoal(
                id=f"goal_{uuid.uuid4().hex[:8]}",
                name=name,
                target_type=target_type,
                target_value=target_value,
                start_date=datetime.datetime.now()
            )
    
    def update_goal_progress(self, goal: WritingGoal, current_value: int) -> None:
        """
        Update the progress of a writing goal.
        
        Args:
            goal: The writing goal to update.
            current_value: The current value towards the goal.
        """
        try:
            # Update goal progress
            goal.update_progress(current_value)
            
            logger.debug(f"Updated goal progress: {goal.name} - {goal.current_value}/{goal.target_value}")
        
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}", exc_info=True)
    
    def get_goal(self, goal_id: str) -> Optional[WritingGoal]:
        """
        Get a writing goal by ID.
        
        Args:
            goal_id: The ID of the goal.
            
        Returns:
            The writing goal, or None if not found.
        """
        try:
            return self.goals.get(goal_id)
        
        except Exception as e:
            logger.error(f"Error getting goal: {e}", exc_info=True)
            return None
    
    def get_active_goals(self) -> List[WritingGoal]:
        """
        Get all active writing goals.
        
        Returns:
            A list of active writing goals.
        """
        try:
            # Filter active goals
            active_goals = [goal for goal in self.goals.values() if goal.is_active()]
            
            # Sort by start date (most recent first)
            active_goals.sort(key=lambda g: g.start_date, reverse=True)
            
            return active_goals
        
        except Exception as e:
            logger.error(f"Error getting active goals: {e}", exc_info=True)
            return []
    
    def get_completed_goals(self) -> List[WritingGoal]:
        """
        Get all completed writing goals.
        
        Returns:
            A list of completed writing goals.
        """
        try:
            # Filter completed goals
            completed_goals = [goal for goal in self.goals.values() if goal.completed]
            
            # Sort by completion date (most recent first)
            completed_goals.sort(key=lambda g: g.completed_date, reverse=True)
            
            return completed_goals
        
        except Exception as e:
            logger.error(f"Error getting completed goals: {e}", exc_info=True)
            return []
    
    def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a writing goal.
        
        Args:
            goal_id: The ID of the goal.
            
        Returns:
            True if the goal was deleted, False otherwise.
        """
        try:
            # Check if goal exists
            if goal_id not in self.goals:
                logger.warning(f"Goal not found: {goal_id}")
                return False
            
            # Delete goal
            del self.goals[goal_id]
            
            logger.info(f"Deleted writing goal: {goal_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting goal: {e}", exc_info=True)
            return False
    
    def update_all_goals(self, get_word_count_func: Callable[[Optional[List[str]]], int]) -> None:
        """
        Update the progress of all writing goals.
        
        Args:
            get_word_count_func: A function that returns the word count for a list of document IDs.
        """
        try:
            # Update each goal
            for goal in self.goals.values():
                # Get current value based on target type
                if goal.target_type == WritingGoal.TARGET_WORDS:
                    # Get word count for documents
                    current_value = get_word_count_func(goal.document_ids)
                
                elif goal.target_type == WritingGoal.TARGET_PAGES:
                    # Get word count and convert to pages
                    word_count = get_word_count_func(goal.document_ids)
                    current_value = word_count // self.words_per_page
                
                elif goal.target_type == WritingGoal.TARGET_CHAPTERS:
                    # Count documents of type chapter
                    current_value = 0
                    # This would require access to the document repository
                    # For now, just use the current value
                
                elif goal.target_type == WritingGoal.TARGET_SCENES:
                    # Count documents of type scene
                    current_value = 0
                    # This would require access to the document repository
                    # For now, just use the current value
                
                else:
                    # Unknown target type
                    current_value = 0
                
                # Update goal progress
                self.update_goal_progress(goal, current_value)
            
            logger.info("Updated all writing goals")
        
        except Exception as e:
            logger.error(f"Error updating all goals: {e}", exc_info=True)
    
    def clear_goals(self) -> None:
        """Clear all goals."""
        self.goals = {}
