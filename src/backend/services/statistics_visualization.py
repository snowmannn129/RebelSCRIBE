#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Visualization module for RebelSCRIBE.

This module provides functionality for generating visualization data
from writing statistics, including charts, graphs, and heatmaps.
"""

import datetime
from typing import Dict, List, Optional, Any, Union

import logging
logger = logging.getLogger(__name__)


class StatisticsVisualization:
    """
    Provides visualization data generation for writing statistics.
    """
    
    @staticmethod
    def get_daily_words_data(history: Dict[str, int]) -> Dict[str, Any]:
        """
        Generate data for daily word count visualization.
        
        Args:
            history: A dictionary mapping dates to word counts.
            
        Returns:
            A dictionary with visualization data.
        """
        try:
            # Sort dates
            dates = sorted(history.keys())
            
            return {
                "type": "daily_words",
                "labels": dates,
                "values": [history[date] for date in dates]
            }
        
        except Exception as e:
            logger.error(f"Error generating daily words data: {e}", exc_info=True)
            return {
                "type": "daily_words",
                "labels": [],
                "values": [],
                "error": str(e)
            }
    
    @staticmethod
    def get_cumulative_words_data(history: Dict[str, int]) -> Dict[str, Any]:
        """
        Generate data for cumulative word count visualization.
        
        Args:
            history: A dictionary mapping dates to word counts.
            
        Returns:
            A dictionary with visualization data.
        """
        try:
            # Sort dates
            dates = sorted(history.keys())
            
            # Calculate cumulative values
            cumulative = 0
            values = []
            
            for date in dates:
                cumulative += history[date]
                values.append(cumulative)
            
            return {
                "type": "cumulative_words",
                "labels": dates,
                "values": values
            }
        
        except Exception as e:
            logger.error(f"Error generating cumulative words data: {e}", exc_info=True)
            return {
                "type": "cumulative_words",
                "labels": [],
                "values": [],
                "error": str(e)
            }
    
    @staticmethod
    def get_writing_pace_data(history: Dict[str, int]) -> Dict[str, Any]:
        """
        Generate data for writing pace visualization.
        
        Args:
            history: A dictionary mapping dates to word counts.
            
        Returns:
            A dictionary with visualization data.
        """
        try:
            # Calculate total words and days
            total_words = sum(history.values())
            total_days = len(history)
            avg_words_per_day = total_words / total_days if total_days > 0 else 0
            
            return {
                "type": "writing_pace",
                "average_words_per_day": avg_words_per_day,
                "total_words": total_words,
                "total_days": total_days
            }
        
        except Exception as e:
            logger.error(f"Error generating writing pace data: {e}", exc_info=True)
            return {
                "type": "writing_pace",
                "average_words_per_day": 0,
                "total_words": 0,
                "total_days": 0,
                "error": str(e)
            }
    
    @staticmethod
    def get_writing_heatmap_data(history: Dict[str, int]) -> Dict[str, Any]:
        """
        Generate data for writing heatmap visualization.
        
        Args:
            history: A dictionary mapping dates to word counts.
            
        Returns:
            A dictionary with visualization data.
        """
        try:
            return {
                "type": "writing_heatmap",
                "heatmap": history
            }
        
        except Exception as e:
            logger.error(f"Error generating writing heatmap data: {e}", exc_info=True)
            return {
                "type": "writing_heatmap",
                "heatmap": {},
                "error": str(e)
            }
    
    @classmethod
    def get_visualization_data(cls, visualization_type: str, 
                              history: Dict[str, int]) -> Dict[str, Any]:
        """
        Get data for a specific visualization type.
        
        Args:
            visualization_type: The type of visualization.
            history: A dictionary mapping dates to word counts.
            
        Returns:
            A dictionary with visualization data.
        """
        try:
            # Get visualization data based on type
            if visualization_type == "daily_words":
                return cls.get_daily_words_data(history)
            
            elif visualization_type == "cumulative_words":
                return cls.get_cumulative_words_data(history)
            
            elif visualization_type == "writing_pace":
                return cls.get_writing_pace_data(history)
            
            elif visualization_type == "writing_heatmap":
                return cls.get_writing_heatmap_data(history)
            
            else:
                # Unknown visualization type
                return {
                    "type": visualization_type,
                    "error": f"Unknown visualization type: {visualization_type}"
                }
        
        except Exception as e:
            logger.error(f"Error getting visualization data: {e}", exc_info=True)
            return {
                "type": visualization_type,
                "error": f"Error: {str(e)}"
            }
