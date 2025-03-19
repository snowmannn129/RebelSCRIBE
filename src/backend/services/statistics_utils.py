#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Utilities for RebelSCRIBE.

This module provides utility functions for statistics processing,
including formatting, calculations, and data transformations.
"""

import datetime
import re
from typing import Dict, List, Optional, Any, Union

import logging
logger = logging.getLogger(__name__)


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as a human-readable string.
    
    Args:
        seconds: The duration in seconds.
        
    Returns:
        A formatted string (e.g., "2h 30m" or "45m 20s").
    """
    try:
        # Calculate hours, minutes, and seconds
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = int(seconds % 60)
        
        # Format string
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{remaining_seconds}s"
    
    except Exception as e:
        logger.error(f"Error formatting duration: {e}", exc_info=True)
        return "0m 0s"


def count_words(text: str) -> int:
    """
    Count the number of words in text.
    
    Args:
        text: The text to count words in.
        
    Returns:
        The word count.
    """
    try:
        if not text:
            return 0
        
        # Split by whitespace and count non-empty words
        words = [word for word in re.split(r'\s+', text) if word]
        return len(words)
    except Exception as e:
        logger.error(f"Error counting words: {e}", exc_info=True)
        return 0


def get_date_range(start_date: Optional[datetime.date] = None,
                  end_date: Optional[datetime.date] = None) -> List[datetime.date]:
    """
    Get a list of dates in a range.
    
    Args:
        start_date: The start date. If None, uses today.
        end_date: The end date. If None, uses today.
        
    Returns:
        A list of dates in the range.
    """
    try:
        # Default to today
        if not start_date:
            start_date = datetime.date.today()
        if not end_date:
            end_date = datetime.date.today()
        
        # Ensure start_date <= end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        # Generate date range
        date_range = []
        current_date = start_date
        
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += datetime.timedelta(days=1)
        
        return date_range
    
    except Exception as e:
        logger.error(f"Error getting date range: {e}", exc_info=True)
        return [datetime.date.today()]


def get_week_start_date(date: Optional[datetime.date] = None) -> datetime.date:
    """
    Get the start date of the week (Monday).
    
    Args:
        date: The date to get the week start for. If None, uses today.
        
    Returns:
        The start date of the week.
    """
    try:
        if not date:
            date = datetime.date.today()
        
        # Calculate start of week (Monday)
        return date - datetime.timedelta(days=date.weekday())
    
    except Exception as e:
        logger.error(f"Error getting week start date: {e}", exc_info=True)
        return datetime.date.today()


def get_month_start_date(date: Optional[datetime.date] = None) -> datetime.date:
    """
    Get the start date of the month.
    
    Args:
        date: The date to get the month start for. If None, uses today.
        
    Returns:
        The start date of the month.
    """
    try:
        if not date:
            date = datetime.date.today()
        
        # Calculate start of month
        return datetime.date(date.year, date.month, 1)
    
    except Exception as e:
        logger.error(f"Error getting month start date: {e}", exc_info=True)
        return datetime.date.today()


def get_month_end_date(date: Optional[datetime.date] = None) -> datetime.date:
    """
    Get the end date of the month.
    
    Args:
        date: The date to get the month end for. If None, uses today.
        
    Returns:
        The end date of the month.
    """
    try:
        if not date:
            date = datetime.date.today()
        
        # Calculate next month
        if date.month == 12:
            next_month = datetime.date(date.year + 1, 1, 1)
        else:
            next_month = datetime.date(date.year, date.month + 1, 1)
        
        # Subtract one day to get end of current month
        return next_month - datetime.timedelta(days=1)
    
    except Exception as e:
        logger.error(f"Error getting month end date: {e}", exc_info=True)
        return datetime.date.today()
