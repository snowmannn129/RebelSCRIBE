#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Manager module for RebelSCRIBE.

This module provides functionality for managing writing sessions,
including starting, ending, and tracking session timeouts.
"""

import datetime
from typing import Dict, List, Optional, Any

from .writing_session import WritingSession

import logging
logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages writing sessions for the statistics service.
    """
    
    def __init__(self, session_timeout: int = 30):
        """
        Initialize the SessionManager.
        
        Args:
            session_timeout: The session timeout in minutes.
        """
        self.session_timeout = session_timeout
        self.current_session: Optional[WritingSession] = None
        self.sessions: List[WritingSession] = []
    
    def start_session(self, document_ids: Optional[List[str]] = None,
                     initial_word_count: int = 0) -> WritingSession:
        """
        Start a new writing session.
        
        Args:
            document_ids: The document IDs to include in the session.
            initial_word_count: The initial word count.
            
        Returns:
            The new writing session.
        """
        try:
            # Check if there's already an active session
            if self.current_session and not self.current_session.end_time:
                logger.warning("There is already an active writing session")
                return self.current_session
            
            # Create new session
            session = WritingSession(
                start_time=datetime.datetime.now(),
                word_count_start=initial_word_count,
                document_ids=document_ids or []
            )
            
            # Set as current session
            self.current_session = session
            
            logger.info("Started new writing session")
            return session
        
        except Exception as e:
            logger.error(f"Error starting writing session: {e}", exc_info=True)
            # Create a default session
            return WritingSession(start_time=datetime.datetime.now())
    
    def end_session(self, final_word_count: int) -> Optional[WritingSession]:
        """
        End the current writing session.
        
        Args:
            final_word_count: The final word count.
            
        Returns:
            The completed writing session, or None if there is no active session.
        """
        if not self.current_session or self.current_session.end_time:
            logger.warning("No active writing session to end")
            return None
        
        try:
            # End session
            self.current_session.end_session(final_word_count)
            
            # Add to sessions
            self.sessions.append(self.current_session)
            
            logger.info(f"Ended writing session: {self.current_session.words_added} words added in {self.current_session.duration_seconds} seconds")
            
            # Get completed session
            completed_session = self.current_session
            
            # Clear current session
            self.current_session = None
            
            return completed_session
        
        except Exception as e:
            logger.error(f"Error ending writing session: {e}", exc_info=True)
            return None
    
    def check_session_timeout(self) -> bool:
        """
        Check if the current writing session has timed out.
        
        Returns:
            True if the session has timed out, False otherwise.
        """
        if not self.current_session or self.current_session.end_time:
            return False
        
        try:
            # Get current time
            now = datetime.datetime.now()
            
            # Calculate time since session start
            if self.current_session.start_time:
                elapsed = now - self.current_session.start_time
                elapsed_minutes = elapsed.total_seconds() / 60
                
                # Check if elapsed time exceeds timeout
                if elapsed_minutes > self.session_timeout:
                    logger.info(f"Writing session timed out after {elapsed_minutes:.1f} minutes")
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking session timeout: {e}", exc_info=True)
            return False
    
    def add_document_to_session(self, document_id: str) -> bool:
        """
        Add a document to the current session.
        
        Args:
            document_id: The document ID to add.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.current_session or self.current_session.end_time:
            logger.warning("No active writing session to add document to")
            return False
        
        try:
            # Check if document is already in session
            if document_id in self.current_session.document_ids:
                return True
            
            # Add document to session
            self.current_session.document_ids.append(document_id)
            
            logger.debug(f"Added document {document_id} to current session")
            return True
        
        except Exception as e:
            logger.error(f"Error adding document to session: {e}", exc_info=True)
            return False
    
    def get_sessions(self, start_date: Optional[datetime.date] = None,
                    end_date: Optional[datetime.date] = None) -> List[WritingSession]:
        """
        Get writing sessions in a date range.
        
        Args:
            start_date: The start date for the range. If None, includes all dates.
            end_date: The end date for the range. If None, includes all dates.
            
        Returns:
            A list of writing sessions in the date range.
        """
        try:
            # Filter sessions by date range
            filtered_sessions = []
            
            for session in self.sessions:
                # Skip sessions without start time
                if not session.start_time:
                    continue
                
                # Get session date
                session_date = session.start_time.date()
                
                # Check if session is in date range
                if (not start_date or session_date >= start_date) and \
                   (not end_date or session_date <= end_date):
                    filtered_sessions.append(session)
            
            return filtered_sessions
        
        except Exception as e:
            logger.error(f"Error getting writing sessions: {e}", exc_info=True)
            return []
    
    def clear_sessions(self) -> None:
        """Clear all sessions."""
        self.current_session = None
        self.sessions = []
