#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word Count Tracker module for RebelSCRIBE.

This module provides functionality for tracking word counts over time,
including daily, weekly, and monthly statistics.
"""

import datetime
import re
from typing import Dict, List, Optional, Any, Set

from ..models.document import Document
from .statistics_utils import count_words

import logging
logger = logging.getLogger(__name__)


class WordCountTracker:
    """
    Tracks word counts for documents over time.
    """
    
    def __init__(self):
        """Initialize the WordCountTracker."""
        self.word_counts: Dict[str, Dict[str, int]] = {}  # document_id -> date -> count
    
    def update_document_word_count(self, document_id: str, document: Document) -> int:
        """
        Update the word count for a document.
        
        Args:
            document_id: The document ID.
            document: The document.
            
        Returns:
            The word count.
        """
        try:
            # Count words in document
            word_count = count_words(document.content)
            
            # Get today's date as string
            today = datetime.date.today().isoformat()
            
            # Initialize document in word counts if needed
            if document_id not in self.word_counts:
                self.word_counts[document_id] = {}
            
            # Update word count for today
            self.word_counts[document_id][today] = word_count
            
            logger.debug(f"Updated word count for document {document_id}: {word_count} words")
            return word_count
        
        except Exception as e:
            logger.error(f"Error updating document word count: {e}", exc_info=True)
            return 0
    
    def get_document_word_count(self, document_id: str, date: Optional[datetime.date] = None) -> int:
        """
        Get the word count for a document.
        
        Args:
            document_id: The document ID.
            date: The date to get the word count for. If None, uses the latest count.
            
        Returns:
            The word count.
        """
        if document_id not in self.word_counts:
            return 0
        
        try:
            if date:
                # Get count for specific date
                date_str = date.isoformat()
                return self.word_counts[document_id].get(date_str, 0)
            else:
                # Get latest count
                if not self.word_counts[document_id]:
                    return 0
                
                # Sort dates and get the latest
                dates = sorted(self.word_counts[document_id].keys())
                latest_date = dates[-1]
                return self.word_counts[document_id][latest_date]
        
        except Exception as e:
            logger.error(f"Error getting document word count: {e}", exc_info=True)
            return 0
    
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
        total = 0
        
        try:
            # Determine which documents to include
            docs_to_include = document_ids if document_ids else list(self.word_counts.keys())
            
            # Sum word counts
            for doc_id in docs_to_include:
                if doc_id in self.word_counts:
                    total += self.get_document_word_count(doc_id, date)
            
            return total
        
        except Exception as e:
            logger.error(f"Error getting total word count: {e}", exc_info=True)
            return 0
    
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
        history = {}
        
        try:
            # Convert dates to strings
            start_date_str = start_date.isoformat() if start_date else None
            end_date_str = end_date.isoformat() if end_date else None
            
            if document_id:
                # Get history for specific document
                if document_id in self.word_counts:
                    for date_str, count in self.word_counts[document_id].items():
                        # Filter by date range
                        if (not start_date_str or date_str >= start_date_str) and \
                           (not end_date_str or date_str <= end_date_str):
                            history[date_str] = count
            else:
                # Get history for all documents combined
                all_dates = set()
                for doc_id in self.word_counts:
                    all_dates.update(self.word_counts[doc_id].keys())
                
                # Sort dates
                sorted_dates = sorted(all_dates)
                
                # Sum counts for each date
                for date_str in sorted_dates:
                    # Filter by date range
                    if (not start_date_str or date_str >= start_date_str) and \
                       (not end_date_str or date_str <= end_date_str):
                        total = 0
                        for doc_id in self.word_counts:
                            total += self.word_counts[doc_id].get(date_str, 0)
                        history[date_str] = total
            
            return history
        
        except Exception as e:
            logger.error(f"Error getting word count history: {e}", exc_info=True)
            return {}
    
    def get_words_written_today(self, document_ids: Optional[List[str]] = None) -> int:
        """
        Get the number of words written today.
        
        Args:
            document_ids: The document IDs to include. If None, includes all documents.
            
        Returns:
            The number of words written today.
        """
        try:
            # Get today's date
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            
            # Get today's and yesterday's word counts
            today_count = self.get_total_word_count(document_ids, today)
            yesterday_count = self.get_total_word_count(document_ids, yesterday)
            
            # Calculate difference
            words_written = today_count - yesterday_count
            return max(words_written, 0)  # Don't return negative values
        
        except Exception as e:
            logger.error(f"Error getting words written today: {e}", exc_info=True)
            return 0
    
    def get_words_written_this_week(self, document_ids: Optional[List[str]] = None) -> int:
        """
        Get the number of words written this week.
        
        Args:
            document_ids: The document IDs to include. If None, includes all documents.
            
        Returns:
            The number of words written this week.
        """
        try:
            # Get today's date
            today = datetime.date.today()
            
            # Calculate start of week (Monday)
            start_of_week = today - datetime.timedelta(days=today.weekday())
            end_of_last_week = start_of_week - datetime.timedelta(days=1)
            
            # Get word counts
            current_count = self.get_total_word_count(document_ids, today)
            last_week_count = self.get_total_word_count(document_ids, end_of_last_week)
            
            # Calculate difference
            words_written = current_count - last_week_count
            return max(words_written, 0)  # Don't return negative values
        
        except Exception as e:
            logger.error(f"Error getting words written this week: {e}", exc_info=True)
            return 0
    
    def get_words_written_this_month(self, document_ids: Optional[List[str]] = None) -> int:
        """
        Get the number of words written this month.
        
        Args:
            document_ids: The document IDs to include. If None, includes all documents.
            
        Returns:
            The number of words written this month.
        """
        try:
            # Get today's date
            today = datetime.date.today()
            
            # Calculate start of month
            start_of_month = datetime.date(today.year, today.month, 1)
            
            # Calculate end of last month
            if today.month == 1:
                end_of_last_month = datetime.date(today.year - 1, 12, 31)
            else:
                end_of_last_month = datetime.date(today.year, today.month - 1, 1)
                # Adjust to last day of previous month
                next_month = datetime.date(today.year, today.month, 1)
                end_of_last_month = next_month - datetime.timedelta(days=1)
            
            # Get word counts
            current_count = self.get_total_word_count(document_ids, today)
            last_month_count = self.get_total_word_count(document_ids, end_of_last_month)
            
            # Calculate difference
            words_written = current_count - last_month_count
            return max(words_written, 0)  # Don't return negative values
        
        except Exception as e:
            logger.error(f"Error getting words written this month: {e}", exc_info=True)
            return 0
    
    def get_daily_writing_streak(self) -> int:
        """
        Get the current daily writing streak.
        
        Returns:
            The number of consecutive days with writing activity.
        """
        try:
            # Get today's date
            today = datetime.date.today()
            
            # Check if there's writing activity today
            today_str = today.isoformat()
            has_writing_today = False
            
            for doc_id in self.word_counts:
                if today_str in self.word_counts[doc_id]:
                    has_writing_today = True
                    break
            
            if not has_writing_today:
                return 0  # No writing today, streak is 0
            
            # Count consecutive days with writing activity
            streak = 1  # Start with today
            current_date = today
            
            while True:
                # Move to previous day
                current_date = current_date - datetime.timedelta(days=1)
                current_date_str = current_date.isoformat()
                
                # Check if there's writing activity on this day
                has_writing = False
                
                for doc_id in self.word_counts:
                    if current_date_str in self.word_counts[doc_id]:
                        has_writing = True
                        break
                
                if has_writing:
                    streak += 1
                else:
                    break  # Streak ends
            
            return streak
        
        except Exception as e:
            logger.error(f"Error getting daily writing streak: {e}", exc_info=True)
            return 0
    
    def clear_word_counts(self) -> None:
        """Clear all word counts."""
        self.word_counts = {}
