#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Writing Session module for RebelSCRIBE.

This module defines the WritingSession class which represents a single writing session
with tracking for duration, word counts, and productivity metrics.
"""

import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import logging
logger = logging.getLogger(__name__)


@dataclass
class WritingSession:
    """
    Represents a writing session.
    
    Attributes:
        start_time: The start time of the session.
        end_time: The end time of the session.
        word_count_start: The word count at the start of the session.
        word_count_end: The word count at the end of the session.
        document_ids: The IDs of documents modified during the session.
        duration_seconds: The duration of the session in seconds.
        words_added: The number of words added during the session.
        words_deleted: The number of words deleted during the session.
        words_per_minute: The average words per minute during the session.
    """
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    word_count_start: int = 0
    word_count_end: int = 0
    document_ids: List[str] = field(default_factory=list)
    duration_seconds: int = 0
    words_added: int = 0
    words_deleted: int = 0
    words_per_minute: float = 0.0
    
    def end_session(self, word_count_end: int) -> None:
        """
        End the writing session.
        
        Args:
            word_count_end: The word count at the end of the session.
        """
        self.end_time = datetime.datetime.now()
        self.word_count_end = word_count_end
        
        # Calculate duration
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
        
        # Calculate words added/deleted
        word_diff = self.word_count_end - self.word_count_start
        if word_diff >= 0:
            self.words_added = word_diff
            self.words_deleted = 0
        else:
            self.words_added = 0
            self.words_deleted = abs(word_diff)
        
        # Calculate words per minute
        if self.duration_seconds > 0:
            minutes = self.duration_seconds / 60
            self.words_per_minute = self.words_added / minutes if minutes > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the writing session to a dictionary."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "word_count_start": self.word_count_start,
            "word_count_end": self.word_count_end,
            "document_ids": self.document_ids,
            "duration_seconds": self.duration_seconds,
            "words_added": self.words_added,
            "words_deleted": self.words_deleted,
            "words_per_minute": self.words_per_minute
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WritingSession':
        """Create a writing session from a dictionary."""
        start_time = datetime.datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        end_time = datetime.datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        
        session = cls(
            start_time=start_time,
            end_time=end_time,
            word_count_start=data.get("word_count_start", 0),
            word_count_end=data.get("word_count_end", 0),
            document_ids=data.get("document_ids", []),
            duration_seconds=data.get("duration_seconds", 0),
            words_added=data.get("words_added", 0),
            words_deleted=data.get("words_deleted", 0),
            words_per_minute=data.get("words_per_minute", 0.0)
        )
        
        return session
