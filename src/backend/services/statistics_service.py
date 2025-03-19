#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Service for RebelSCRIBE.

This module provides the main statistics service that integrates all the
statistics-related functionality, including word counts, writing sessions,
goals, and visualization.
"""

import os
import datetime
from typing import Dict, List, Optional, Any, Union

from ..models.document import Document
from src.utils import file_utils
from src.utils.config_manager import get_config

from .writing_session import WritingSession
from .writing_goal import WritingGoal
from .statistics_utils import count_words, format_duration
from .statistics_visualization import StatisticsVisualization
from .statistics_export import StatisticsExport
from .session_manager import SessionManager
from .goal_manager import GoalManager
from .word_count_tracker import WordCountTracker

import logging
logger = logging.getLogger(__name__)


class StatisticsService:
    """
    Provides statistics tracking and analysis for RebelSCRIBE.
    
    This class integrates all the statistics-related functionality,
    including word counts, writing sessions, goals, and visualization.
    """
    
    # Statistics file name
    STATISTICS_FILE = "statistics.json"
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize the StatisticsService.
        
        Args:
            project_path: The path to the project directory. If None, statistics will be
                         managed independently of a project.
        """
        self.config_manager = get_config()
        self.project_path = project_path
        
        # Get settings from config
        session_timeout = self.config_manager.get("statistics", "session_timeout", 30)
        words_per_page = self.config_manager.get("statistics", "words_per_page", 250)
        
        # Initialize components
        self.word_tracker = WordCountTracker()
        self.session_manager = SessionManager(session_timeout=session_timeout)
        self.goal_manager = GoalManager(words_per_page=words_per_page)
        
        # Initialize statistics directory
        if self.project_path:
            self.statistics_dir = os.path.join(self.project_path, "statistics")
            file_utils.ensure_directory(self.statistics_dir)
            self.statistics_file = os.path.join(self.statistics_dir, self.STATISTICS_FILE)
            
            # Load statistics if file exists
            if file_utils.file_exists(self.statistics_file):
                self._load_statistics()
        else:
            # If no project path, use default data directory
            data_dir = self.config_manager.get("application", "data_directory", "/tmp")
            self.statistics_dir = os.path.join(data_dir, "statistics")
            file_utils.ensure_directory(self.statistics_dir)
            self.statistics_file = os.path.join(self.statistics_dir, self.STATISTICS_FILE)
            
            # Load statistics if file exists
            if file_utils.file_exists(self.statistics_file):
                self._load_statistics()
    
    def set_project_path(self, project_path: str) -> None:
        """
        Set the project path.
        
        Args:
            project_path: The path to the project directory.
        """
        self.project_path = project_path
        self.statistics_dir = os.path.join(project_path, "statistics")
        file_utils.ensure_directory(self.statistics_dir)
        self.statistics_file = os.path.join(self.statistics_dir, self.STATISTICS_FILE)
        
        # Reset statistics
        self.word_tracker.clear_word_counts()
        self.session_manager.clear_sessions()
        self.goal_manager.clear_goals()
        
        # Load statistics if file exists
        if file_utils.file_exists(self.statistics_file):
            self._load_statistics()
        
        logger.info(f"Set project path to: {project_path}")
    
    def _load_statistics(self) -> None:
        """Load statistics from file."""
        try:
            # Read statistics data
            stats_data = file_utils.read_json_file(self.statistics_file)
            if not stats_data:
                logger.warning(f"Failed to read statistics data from: {self.statistics_file}")
                return
            
            # Load word counts
            self.word_tracker.word_counts = {}
            for doc_id, counts in stats_data.get("word_counts", {}).items():
                self.word_tracker.word_counts[doc_id] = {}
                for date_str, count in counts.items():
                    self.word_tracker.word_counts[doc_id][date_str] = count
            
            # Load writing sessions
            self.session_manager.sessions = []
            for session_data in stats_data.get("writing_sessions", []):
                session = WritingSession.from_dict(session_data)
                self.session_manager.sessions.append(session)
            
            # Load goals
            self.goal_manager.goals = {}
            for goal_data in stats_data.get("goals", []):
                goal = WritingGoal.from_dict(goal_data)
                self.goal_manager.goals[goal.id] = goal
            
            logger.info(f"Loaded statistics from: {self.statistics_file}")
        
        except Exception as e:
            logger.error(f"Error loading statistics: {e}", exc_info=True)
    
    def _save_statistics(self) -> bool:
        """
        Save statistics to file.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Prepare statistics data
            stats_data = {
                "word_counts": self.word_tracker.word_counts,
                "writing_sessions": [session.to_dict() for session in self.session_manager.sessions],
                "goals": [goal.to_dict() for goal in self.goal_manager.goals.values()]
            }
            
            # Save to file
            success = file_utils.write_json_file(self.statistics_file, stats_data)
            if not success:
                logger.error(f"Failed to write statistics data to: {self.statistics_file}")
                return False
            
            logger.info(f"Saved statistics to: {self.statistics_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving statistics: {e}", exc_info=True)
            return False
    
    # Word count methods
    
    def count_words(self, text: str) -> int:
        """
        Count the number of words in text.
        
        Args:
            text: The text to count words in.
            
        Returns:
            The word count.
        """
        return count_words(text)
    
    def update_document_word_count(self, document_id: str, document: Document) -> int:
        """
        Update the word count for a document.
        
        Args:
            document_id: The document ID.
            document: The document.
            
        Returns:
            The word count.
        """
        # Update word count
        word_count = self.word_tracker.update_document_word_count(document_id, document)
        
        # Save statistics
        self._save_statistics()
        
        # Update current session if active
        if self.session_manager.current_session:
            self.session_manager.add_document_to_session(document_id)
        
        return word_count
    
    def get_document_word_count(self, document_id: str, date: Optional[datetime.date] = None) -> int:
        """
        Get the word count for a document.
        
        Args:
            document_id: The document ID.
            date: The date to get the word count for. If None, uses the latest count.
            
        Returns:
            The word count.
        """
        return self.word_tracker.get_document_word_count(document_id, date)
    
    def get_total_word_count(self, document_ids: Optional[List[str]] = None, 
                            date: Optional[datetime.date] = None) -> int:
        """
        Get the total word count for multiple documents.
        
        Args:
            document_ids: The document IDs to include. If None, includes all documents.
            date: The date to get the word count for. If None, uses the latest count for each document.
            
        Returns:
            The total word count.
        """
        return self.word_tracker.get_total_word_count(document_ids, date)
    
    def get_word_count_history(self, document_id: Optional[str] = None, 
                              start_date: Optional[datetime.date] = None,
                              end_date: Optional[datetime.date] = None) -> Dict[str, int]:
        """
        Get the word count history for a document or all documents.
        
        Args:
            document_id: The document ID. If None, gets history for all documents combined.
            start_date: The start date for the history. If None, includes all dates.
            end_date: The end date for the history. If None, includes all dates.
            
        Returns:
            A dictionary mapping dates to word counts.
        """
        return self.word_tracker.get_word_count_history(document_id, start_date, end_date)
    
    def get_words_written_today(self, document_ids: Optional[List[str]] = None) -> int:
        """
        Get the number of words written today.
        
        Args:
            document_ids: The document IDs to include. If None, includes all documents.
            
        Returns:
            The number of words written today.
        """
        return self.word_tracker.get_words_written_today(document_ids)
    
    def get_words_written_this_week(self, document_ids: Optional[List[str]] = None) -> int:
        """
        Get the number of words written this week.
        
        Args:
            document_ids: The document IDs to include. If None, includes all documents.
            
        Returns:
            The number of words written this week.
        """
        return self.word_tracker.get_words_written_this_week(document_ids)
    
    def get_words_written_this_month(self, document_ids: Optional[List[str]] = None) -> int:
        """
        Get the number of words written this month.
        
        Args:
            document_ids: The document IDs to include. If None, includes all documents.
            
        Returns:
            The number of words written this month.
        """
        return self.word_tracker.get_words_written_this_month(document_ids)
    
    def get_daily_writing_streak(self) -> int:
        """
        Get the current daily writing streak.
        
        Returns:
            The number of consecutive days with writing activity.
        """
        return self.word_tracker.get_daily_writing_streak()
    
    # Session methods
    
    def start_writing_session(self, document_ids: Optional[List[str]] = None) -> WritingSession:
        """
        Start a new writing session.
        
        Args:
            document_ids: The document IDs to include in the session.
            
        Returns:
            The new writing session.
        """
        # Get initial word count
        initial_count = self.get_total_word_count(document_ids)
        
        # Start session
        session = self.session_manager.start_session(document_ids, initial_count)
        
        return session
    
    def end_writing_session(self, document_ids: Optional[List[str]] = None) -> Optional[WritingSession]:
        """
        End the current writing session.
        
        Args:
            document_ids: The document IDs to include in the final word count.
            
        Returns:
            The completed writing session, or None if there is no active session.
        """
        if not self.session_manager.current_session:
            return None
        
        # Get final word count
        final_count = self.get_total_word_count(
            document_ids or self.session_manager.current_session.document_ids
        )
        
        # End session
        session = self.session_manager.end_session(final_count)
        
        # Save statistics
        if session:
            self._save_statistics()
        
        return session
    
    def check_session_timeout(self) -> bool:
        """
        Check if the current writing session has timed out.
        
        Returns:
            True if the session has timed out, False otherwise.
        """
        return self.session_manager.check_session_timeout()
    
    def get_writing_sessions(self, start_date: Optional[datetime.date] = None,
                            end_date: Optional[datetime.date] = None) -> List[WritingSession]:
        """
        Get writing sessions in a date range.
        
        Args:
            start_date: The start date for the range. If None, includes all dates.
            end_date: The end date for the range. If None, includes all dates.
            
        Returns:
            A list of writing sessions in the date range.
        """
        return self.session_manager.get_sessions(start_date, end_date)
    
    def get_writing_stats(self, start_date: Optional[datetime.date] = None,
                         end_date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """
        Get writing statistics for a date range.
        
        Args:
            start_date: The start date for the range. If None, includes all dates.
            end_date: The end date for the range. If None, includes all dates.
            
        Returns:
            A dictionary of writing statistics.
        """
        try:
            # Get sessions in date range
            sessions = self.get_writing_sessions(start_date, end_date)
            
            # Calculate statistics
            total_sessions = len(sessions)
            total_duration_seconds = sum(session.duration_seconds for session in sessions)
            total_words_added = sum(session.words_added for session in sessions)
            total_words_deleted = sum(session.words_deleted for session in sessions)
            
            # Calculate averages
            avg_session_duration = total_duration_seconds / total_sessions if total_sessions > 0 else 0
            avg_words_per_session = total_words_added / total_sessions if total_sessions > 0 else 0
            avg_words_per_minute = sum(session.words_per_minute for session in sessions) / total_sessions if total_sessions > 0 else 0
            
            # Format durations
            total_duration_formatted = format_duration(total_duration_seconds)
            avg_session_duration_formatted = format_duration(avg_session_duration)
            
            # Return statistics
            return {
                "total_sessions": total_sessions,
                "total_duration_seconds": total_duration_seconds,
                "total_duration_formatted": total_duration_formatted,
                "total_words_added": total_words_added,
                "total_words_deleted": total_words_deleted,
                "avg_session_duration": avg_session_duration,
                "avg_session_duration_formatted": avg_session_duration_formatted,
                "avg_words_per_session": avg_words_per_session,
                "avg_words_per_minute": avg_words_per_minute,
                "sessions": sessions
            }
        
        except Exception as e:
            logger.error(f"Error getting writing stats: {e}", exc_info=True)
            return {
                "total_sessions": 0,
                "total_duration_seconds": 0,
                "total_duration_formatted": "0m 0s",
                "total_words_added": 0,
                "total_words_deleted": 0,
                "avg_session_duration": 0,
                "avg_session_duration_formatted": "0m 0s",
                "avg_words_per_session": 0,
                "avg_words_per_minute": 0,
                "sessions": []
            }
    
    # Goal methods
    
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
        # Create goal
        goal = self.goal_manager.create_goal(
            name, target_type, target_value, start_date, end_date, document_ids
        )
        
        # Update goal progress
        self._update_goal_progress(goal)
        
        # Save statistics
        self._save_statistics()
        
        return goal
    
    def _update_goal_progress(self, goal: WritingGoal) -> None:
        """
        Update the progress of a writing goal.
        
        Args:
            goal: The writing goal to update.
        """
        # Get current value based on target type
        if goal.target_type == WritingGoal.TARGET_WORDS:
            # Get word count for documents
            current_value = self.get_total_word_count(goal.document_ids)
        
        elif goal.target_type == WritingGoal.TARGET_PAGES:
            # Get word count and convert to pages
            word_count = self.get_total_word_count(goal.document_ids)
            current_value = word_count // self.goal_manager.words_per_page
        
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
        self.goal_manager.update_goal_progress(goal, current_value)
    
    def update_all_goals(self) -> None:
        """Update the progress of all writing goals."""
        # Update each goal
        for goal in self.goal_manager.goals.values():
            self._update_goal_progress(goal)
        
        # Save statistics
        self._save_statistics()
    
    def get_goal(self, goal_id: str) -> Optional[WritingGoal]:
        """
        Get a writing goal by ID.
        
        Args:
            goal_id: The ID of the goal.
            
        Returns:
            The writing goal, or None if not found.
        """
        return self.goal_manager.get_goal(goal_id)
    
    def get_active_goals(self) -> List[WritingGoal]:
        """
        Get all active writing goals.
        
        Returns:
            A list of active writing goals.
        """
        return self.goal_manager.get_active_goals()
    
    def get_completed_goals(self) -> List[WritingGoal]:
        """
        Get all completed writing goals.
        
        Returns:
            A list of completed writing goals.
        """
        return self.goal_manager.get_completed_goals()
    
    def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a writing goal.
        
        Args:
            goal_id: The ID of the goal.
            
        Returns:
            True if the goal was deleted, False otherwise.
        """
        # Delete goal
        result = self.goal_manager.delete_goal(goal_id)
        
        # Save statistics
        if result:
            self._save_statistics()
        
        return result
    
    # Visualization methods
    
    def get_visualization_data(self, visualization_type: str,
                              start_date: Optional[datetime.date] = None,
                              end_date: Optional[datetime.date] = None,
                              document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get data for visualizations.
        
        Args:
            visualization_type: The type of visualization.
            start_date: The start date for the data. If None, includes all dates.
            end_date: The end date for the data. If None, includes all dates.
            document_ids: The document IDs to include. If None, includes all documents.
            
        Returns:
            A dictionary of visualization data.
        """
        # Get word count history
        history = self.get_word_count_history(
            document_id=document_ids[0] if document_ids and len(document_ids) == 1 else None,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get visualization data
        return StatisticsVisualization.get_visualization_data(visualization_type, history)
    
    # Export methods
    
    def export_statistics(self, file_path: str, format: str = "json") -> bool:
        """
        Export statistics to a file.
        
        Args:
            file_path: The path to the file.
            format: The format of the file (json, csv, txt).
            
        Returns:
            True if successful, False otherwise.
        """
        return StatisticsExport.export_statistics(
            file_path,
            self.word_tracker.word_counts,
            self.session_manager.sessions,
            self.goal_manager.goals,
            format
        )
