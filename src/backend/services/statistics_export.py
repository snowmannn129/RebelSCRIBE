#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Export module for RebelSCRIBE.

This module provides functionality for exporting writing statistics
to various file formats (JSON, CSV, TXT).
"""

import os
import json
import csv
import datetime
from typing import Dict, List, Optional, Any, Union

from src.utils import file_utils
from .writing_session import WritingSession
from .writing_goal import WritingGoal
from .statistics_utils import format_duration

import logging
logger = logging.getLogger(__name__)


class StatisticsExport:
    """
    Provides export functionality for writing statistics.
    """
    
    @staticmethod
    def export_to_json(file_path: str, 
                      word_counts: Dict[str, Dict[str, int]],
                      writing_sessions: List[WritingSession],
                      goals: Dict[str, WritingGoal]) -> bool:
        """
        Export statistics to a JSON file.
        
        Args:
            file_path: The path to the file.
            word_counts: The word counts data.
            writing_sessions: The writing sessions data.
            goals: The writing goals data.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Prepare statistics data
            stats_data = {
                "word_counts": word_counts,
                "writing_sessions": [session.to_dict() for session in writing_sessions],
                "goals": [goal.to_dict() for goal in goals.values()]
            }
            
            # Save to file
            return file_utils.write_json_file(file_path, stats_data)
        
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}", exc_info=True)
            return False
    
    @staticmethod
    def export_to_csv(file_path: str, 
                     word_counts: Dict[str, Dict[str, int]]) -> bool:
        """
        Export word counts to a CSV file.
        
        Args:
            file_path: The path to the file.
            word_counts: The word counts data.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(["Date", "Document ID", "Word Count"])
                
                # Write word counts
                for doc_id in word_counts:
                    for date_str, count in word_counts[doc_id].items():
                        writer.writerow([date_str, doc_id, count])
            
            return True
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}", exc_info=True)
            return False
    
    @staticmethod
    def export_to_txt(file_path: str, 
                     word_counts: Dict[str, Dict[str, int]],
                     writing_sessions: List[WritingSession],
                     goals: Dict[str, WritingGoal]) -> bool:
        """
        Export statistics to a plain text file.
        
        Args:
            file_path: The path to the file.
            word_counts: The word counts data.
            writing_sessions: The writing sessions data.
            goals: The writing goals data.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Write word counts
                f.write("Word Counts:\n")
                f.write("===========\n\n")
                
                for doc_id in word_counts:
                    f.write(f"Document: {doc_id}\n")
                    
                    for date_str, count in sorted(word_counts[doc_id].items()):
                        f.write(f"  {date_str}: {count} words\n")
                    
                    f.write("\n")
                
                # Write writing sessions
                f.write("\nWriting Sessions:\n")
                f.write("================\n\n")
                
                for session in writing_sessions:
                    start_time = session.start_time.strftime("%Y-%m-%d %H:%M") if session.start_time else "Unknown"
                    end_time = session.end_time.strftime("%Y-%m-%d %H:%M") if session.end_time else "Unknown"
                    
                    f.write(f"Session: {start_time} to {end_time}\n")
                    f.write(f"  Duration: {format_duration(session.duration_seconds)}\n")
                    f.write(f"  Words added: {session.words_added}\n")
                    f.write(f"  Words per minute: {session.words_per_minute:.2f}\n")
                    f.write("\n")
                
                # Write goals
                f.write("\nWriting Goals:\n")
                f.write("=============\n\n")
                
                for goal in goals.values():
                    f.write(f"Goal: {goal.name}\n")
                    f.write(f"  Target: {goal.target_value} {goal.target_type}\n")
                    f.write(f"  Progress: {goal.current_value} ({goal.get_progress_percentage():.1f}%)\n")
                    f.write(f"  Status: {'Completed' if goal.completed else 'In Progress'}\n")
                    f.write("\n")
            
            return True
        
        except Exception as e:
            logger.error(f"Error exporting to TXT: {e}", exc_info=True)
            return False
    
    @classmethod
    def export_statistics(cls, file_path: str, 
                         word_counts: Dict[str, Dict[str, int]],
                         writing_sessions: List[WritingSession],
                         goals: Dict[str, WritingGoal],
                         format: str = "json") -> bool:
        """
        Export statistics to a file.
        
        Args:
            file_path: The path to the file.
            word_counts: The word counts data.
            writing_sessions: The writing sessions data.
            goals: The writing goals data.
            format: The format of the file (json, csv, txt).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Export based on format
            if format.lower() == "json":
                return cls.export_to_json(file_path, word_counts, writing_sessions, goals)
            
            elif format.lower() == "csv":
                return cls.export_to_csv(file_path, word_counts)
            
            elif format.lower() == "txt":
                return cls.export_to_txt(file_path, word_counts, writing_sessions, goals)
            
            else:
                # Unknown format
                logger.error(f"Unknown export format: {format}")
                return False
        
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}", exc_info=True)
            return False
