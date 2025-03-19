#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the StatisticsService class.

This module contains unit tests for the StatisticsService class and its components.
"""

import os
import unittest
import datetime
import tempfile
import shutil
from unittest.mock import MagicMock, patch

from src.backend.services.statistics_service import StatisticsService
from src.backend.services.writing_session import WritingSession
from src.backend.services.writing_goal import WritingGoal
from src.backend.models.document import Document
from src.utils.config_manager import get_config


class TestStatisticsService(unittest.TestCase):
    """Test cases for the StatisticsService class."""
    
    @patch('src.utils.config_manager.get_config')
    def setUp(self, mock_get_config):
        """Set up test fixtures."""
        # Mock the config
        mock_get_config.return_value = {
            "statistics": {
                "session_timeout": 30,
                "words_per_page": 250
            },
            "application": {
                "data_directory": "/tmp"
            }
        }
        
        # Create a temporary directory for the project
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a statistics service with the temporary directory
        self.stats_service = StatisticsService(self.temp_dir)
        
        # Create a mock document
        self.mock_document = Document(
            id="doc1",
            title="Test Document",
            content="This is a test document with some words.",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_count_words(self):
        """Test counting words in text."""
        # Test with empty text
        self.assertEqual(self.stats_service.count_words(""), 0)
        
        # Test with simple text
        self.assertEqual(self.stats_service.count_words("Hello world"), 2)
        
        # Test with multiple spaces
        self.assertEqual(self.stats_service.count_words("Hello  world"), 2)
        
        # Test with punctuation
        self.assertEqual(self.stats_service.count_words("Hello, world!"), 2)
        
        # Test with newlines
        self.assertEqual(self.stats_service.count_words("Hello\nworld"), 2)
    
    def test_update_document_word_count(self):
        """Test updating document word count."""
        # Update word count for a document
        word_count = self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Check word count
        self.assertEqual(word_count, 8)
        
        # Check that word count is stored
        self.assertEqual(self.stats_service.get_document_word_count("doc1"), 8)
    
    def test_get_document_word_count(self):
        """Test getting document word count."""
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Get word count
        word_count = self.stats_service.get_document_word_count("doc1")
        
        # Check word count
        self.assertEqual(word_count, 8)
        
        # Test with non-existent document
        self.assertEqual(self.stats_service.get_document_word_count("doc2"), 0)
    
    def test_get_total_word_count(self):
        """Test getting total word count."""
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Create another document
        mock_document2 = Document(
            id="doc2",
            title="Test Document 2",
            content="This is another test document.",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        # Update word count for the second document
        self.stats_service.update_document_word_count("doc2", mock_document2)
        
        # Get total word count
        total_count = self.stats_service.get_total_word_count()
        
        # Check total count (8 + 5 = 13)
        self.assertEqual(total_count, 13)
        
        # Test with specific document IDs
        self.assertEqual(self.stats_service.get_total_word_count(["doc1"]), 8)
        self.assertEqual(self.stats_service.get_total_word_count(["doc2"]), 5)
        self.assertEqual(self.stats_service.get_total_word_count(["doc1", "doc2"]), 13)
    
    def test_get_word_count_history(self):
        """Test getting word count history."""
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Get word count history
        history = self.stats_service.get_word_count_history("doc1")
        
        # Check history
        self.assertEqual(len(history), 1)
        
        # Get history for all documents
        all_history = self.stats_service.get_word_count_history()
        
        # Check history
        self.assertEqual(len(all_history), 1)
    
    def test_start_writing_session(self):
        """Test starting a writing session."""
        # Start a writing session
        session = self.stats_service.start_writing_session(["doc1"])
        
        # Check session
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.start_time)
        self.assertIsNone(session.end_time)
        self.assertEqual(session.word_count_start, 0)
        self.assertEqual(session.document_ids, ["doc1"])
    
    def test_end_writing_session(self):
        """Test ending a writing session."""
        # Start a writing session
        self.stats_service.start_writing_session(["doc1"])
        
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # End the session
        session = self.stats_service.end_writing_session(["doc1"])
        
        # Check session
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.start_time)
        self.assertIsNotNone(session.end_time)
        self.assertEqual(session.word_count_start, 0)
        self.assertEqual(session.word_count_end, 8)
        self.assertEqual(session.words_added, 8)
        self.assertEqual(session.document_ids, ["doc1"])
    
    def test_check_session_timeout(self):
        """Test checking session timeout."""
        # Start a writing session
        self.stats_service.start_writing_session(["doc1"])
        
        # Check timeout (should be False)
        self.assertFalse(self.stats_service.check_session_timeout())
    
    def test_get_writing_sessions(self):
        """Test getting writing sessions."""
        # Start and end a writing session
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        self.stats_service.start_writing_session(["doc1"])
        self.stats_service.end_writing_session(["doc1"])
        
        # Get writing sessions
        sessions = self.stats_service.get_writing_sessions()
        
        # Check sessions
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].document_ids, ["doc1"])
    
    def test_get_writing_stats(self):
        """Test getting writing statistics."""
        # Start a writing session
        self.stats_service.start_writing_session(["doc1"])
        
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # End the session
        self.stats_service.end_writing_session(["doc1"])
        
        # Get writing stats
        stats = self.stats_service.get_writing_stats()
        
        # Check stats
        self.assertEqual(stats["total_sessions"], 1)
        self.assertGreaterEqual(stats["total_duration_seconds"], 0)
        self.assertEqual(stats["total_words_added"], 8)
    
    def test_create_goal(self):
        """Test creating a writing goal."""
        # Create a goal
        goal = self.stats_service.create_goal(
            name="Test Goal",
            target_type=WritingGoal.TARGET_WORDS,
            target_value=1000,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            document_ids=["doc1"]
        )
        
        # Check goal
        self.assertIsNotNone(goal)
        self.assertEqual(goal.name, "Test Goal")
        self.assertEqual(goal.target_type, WritingGoal.TARGET_WORDS)
        self.assertEqual(goal.target_value, 1000)
        self.assertEqual(goal.document_ids, ["doc1"])
    
    def test_update_all_goals(self):
        """Test updating all goals."""
        # Create a goal
        self.stats_service.create_goal(
            name="Test Goal",
            target_type=WritingGoal.TARGET_WORDS,
            target_value=1000,
            start_date=datetime.date.today(),
            document_ids=["doc1"]
        )
        
        # Update document word count
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Update all goals
        self.stats_service.update_all_goals()
        
        # Get active goals
        goals = self.stats_service.get_active_goals()
        
        # Check goals
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0].current_value, 8)
    
    def test_get_goal(self):
        """Test getting a goal by ID."""
        # Create a goal
        goal = self.stats_service.create_goal(
            name="Test Goal",
            target_type=WritingGoal.TARGET_WORDS,
            target_value=1000,
            start_date=datetime.date.today(),
            document_ids=["doc1"]
        )
        
        # Get goal
        retrieved_goal = self.stats_service.get_goal(goal.id)
        
        # Check goal
        self.assertIsNotNone(retrieved_goal)
        self.assertEqual(retrieved_goal.id, goal.id)
        self.assertEqual(retrieved_goal.name, "Test Goal")
    
    def test_get_active_goals(self):
        """Test getting active goals."""
        # Create a goal
        self.stats_service.create_goal(
            name="Test Goal",
            target_type=WritingGoal.TARGET_WORDS,
            target_value=1000,
            start_date=datetime.date.today(),
            document_ids=["doc1"]
        )
        
        # Get active goals
        goals = self.stats_service.get_active_goals()
        
        # Check goals
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0].name, "Test Goal")
    
    def test_get_completed_goals(self):
        """Test getting completed goals."""
        # Create a goal with a small target
        goal = self.stats_service.create_goal(
            name="Test Goal",
            target_type=WritingGoal.TARGET_WORDS,
            target_value=5,
            start_date=datetime.date.today(),
            document_ids=["doc1"]
        )
        
        # Update document word count to complete the goal
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Update all goals
        self.stats_service.update_all_goals()
        
        # Get completed goals
        goals = self.stats_service.get_completed_goals()
        
        # Check goals
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0].name, "Test Goal")
        self.assertTrue(goals[0].completed)
    
    def test_delete_goal(self):
        """Test deleting a goal."""
        # Create a goal
        goal = self.stats_service.create_goal(
            name="Test Goal",
            target_type=WritingGoal.TARGET_WORDS,
            target_value=1000,
            start_date=datetime.date.today(),
            document_ids=["doc1"]
        )
        
        # Delete goal
        result = self.stats_service.delete_goal(goal.id)
        
        # Check result
        self.assertTrue(result)
        
        # Check that goal is deleted
        self.assertIsNone(self.stats_service.get_goal(goal.id))
    
    def test_get_visualization_data(self):
        """Test getting visualization data."""
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Get visualization data
        data = self.stats_service.get_visualization_data("daily_words")
        
        # Check data
        self.assertIsNotNone(data)
        self.assertEqual(data["type"], "daily_words")
        self.assertEqual(len(data["labels"]), 1)
        self.assertEqual(len(data["values"]), 1)
    
    def test_export_statistics(self):
        """Test exporting statistics."""
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Export statistics to a file
        file_path = os.path.join(self.temp_dir, "stats_export.json")
        result = self.stats_service.export_statistics(file_path)
        
        # Check result
        self.assertTrue(result)
        
        # Check that file exists
        self.assertTrue(os.path.exists(file_path))
    
    @patch('src.utils.config_manager.get_config')
    def test_save_and_load_statistics(self, mock_get_config):
        """Test saving and loading statistics."""
        # Mock the config for the second service instance
        mock_get_config.return_value = {
            "statistics": {
                "session_timeout": 30,
                "words_per_page": 250
            },
            "application": {
                "data_directory": "/tmp"
            }
        }
        
        # Update word count for a document
        self.stats_service.update_document_word_count("doc1", self.mock_document)
        
        # Create a goal
        self.stats_service.create_goal(
            name="Test Goal",
            target_type=WritingGoal.TARGET_WORDS,
            target_value=1000,
            start_date=datetime.date.today(),
            document_ids=["doc1"]
        )
        
        # Start and end a writing session
        self.stats_service.start_writing_session(["doc1"])
        self.stats_service.end_writing_session(["doc1"])
        
        # Create a new statistics service with the same directory
        new_stats_service = StatisticsService(self.temp_dir)
        
        # Check that data is loaded
        self.assertEqual(new_stats_service.get_document_word_count("doc1"), 8)
        self.assertEqual(len(new_stats_service.get_active_goals()), 1)
        self.assertEqual(len(new_stats_service.get_writing_sessions()), 1)


if __name__ == "__main__":
    unittest.main()
