#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the file watcher module.
"""

import os
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.tests.base_test import BaseTest
from src.utils.file_watcher import (
    FileWatcher,
    get_file_watcher,
    watch_file,
    unwatch_file,
    watch_directory,
    unwatch_directory,
    stop_file_watcher
)


class TestFileWatcher(BaseTest):
    """Test case for the file watcher module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("Test content")
        
        # Create a test directory
        self.test_dir_path = os.path.join(self.temp_dir, "test_dir")
        os.makedirs(self.test_dir_path)
        
        # Create a test file in the test directory
        self.test_dir_file_path = os.path.join(self.test_dir_path, "test_file.txt")
        with open(self.test_dir_file_path, "w", encoding="utf-8") as f:
            f.write("Test content")
        
        # Create a FileWatcher instance
        self.watcher = FileWatcher(poll_interval=0.1)
    
    def tearDown(self):
        """Tear down test fixtures."""
        super().tearDown()
        
        # Stop the watcher
        self.watcher.stop()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_start_stop(self):
        """Test starting and stopping the file watcher."""
        # Test starting
        self.assertTrue(self.watcher.start())
        self.assertTrue(self.watcher.is_running())
        
        # Test starting again (should return False)
        self.assertFalse(self.watcher.start())
        
        # Test stopping
        self.assertTrue(self.watcher.stop())
        self.assertFalse(self.watcher.is_running())
        
        # Test stopping again (should return False)
        self.assertFalse(self.watcher.stop())
    
    def test_watch_file(self):
        """Test watching a file."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the file
        self.assertTrue(self.watcher.watch_file(self.test_file_path, callback))
        
        # Check that the file is in the watch list
        self.assertIn(self.test_file_path, self.watcher.get_watched_files())
        
        # Test watching a non-existent file
        non_existent_file = os.path.join(self.temp_dir, "non_existent_file.txt")
        with patch("logging.Logger.error") as mock_error:
            self.assertFalse(self.watcher.watch_file(non_existent_file, callback))
            mock_error.assert_called_once()
        
        # Test watching a file with an exception
        with patch("os.path.isfile", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(self.watcher.watch_file(self.test_file_path, callback))
                mock_error.assert_called_once()
    
    def test_unwatch_file(self):
        """Test unwatching a file."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the file
        self.watcher.watch_file(self.test_file_path, callback)
        
        # Unwatch the file
        self.assertTrue(self.watcher.unwatch_file(self.test_file_path))
        
        # Check that the file is not in the watch list
        self.assertNotIn(self.test_file_path, self.watcher.get_watched_files())
        
        # Test unwatching a non-existent file
        non_existent_file = os.path.join(self.temp_dir, "non_existent_file.txt")
        self.assertFalse(self.watcher.unwatch_file(non_existent_file))
        
        # Test unwatching a specific callback
        callback1 = MagicMock()
        callback2 = MagicMock()
        self.watcher.watch_file(self.test_file_path, callback1)
        self.watcher.watch_file(self.test_file_path, callback2)
        self.assertTrue(self.watcher.unwatch_file(self.test_file_path, callback1))
        self.assertIn(self.test_file_path, self.watcher.get_watched_files())
        self.assertTrue(self.watcher.unwatch_file(self.test_file_path, callback2))
        self.assertNotIn(self.test_file_path, self.watcher.get_watched_files())
        
        # Test unwatching with an exception
        with patch("os.path.abspath", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(self.watcher.unwatch_file(self.test_file_path))
                mock_error.assert_called_once()
    
    def test_watch_directory(self):
        """Test watching a directory."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the directory
        self.assertTrue(self.watcher.watch_directory(self.test_dir_path, callback))
        
        # Check that the directory is in the watch list
        self.assertIn(self.test_dir_path, self.watcher.get_watched_directories())
        
        # Test watching a non-existent directory
        non_existent_dir = os.path.join(self.temp_dir, "non_existent_dir")
        with patch("logging.Logger.error") as mock_error:
            self.assertFalse(self.watcher.watch_directory(non_existent_dir, callback))
            mock_error.assert_called_once()
        
        # Test watching a directory with an exception
        with patch("os.path.isdir", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(self.watcher.watch_directory(self.test_dir_path, callback))
                mock_error.assert_called_once()
    
    def test_unwatch_directory(self):
        """Test unwatching a directory."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the directory
        self.watcher.watch_directory(self.test_dir_path, callback)
        
        # Unwatch the directory
        self.assertTrue(self.watcher.unwatch_directory(self.test_dir_path))
        
        # Check that the directory is not in the watch list
        self.assertNotIn(self.test_dir_path, self.watcher.get_watched_directories())
        
        # Test unwatching a non-existent directory
        non_existent_dir = os.path.join(self.temp_dir, "non_existent_dir")
        self.assertFalse(self.watcher.unwatch_directory(non_existent_dir))
        
        # Test unwatching a specific callback
        callback1 = MagicMock()
        callback2 = MagicMock()
        self.watcher.watch_directory(self.test_dir_path, callback1)
        self.watcher.watch_directory(self.test_dir_path, callback2)
        self.assertTrue(self.watcher.unwatch_directory(self.test_dir_path, callback1))
        self.assertIn(self.test_dir_path, self.watcher.get_watched_directories())
        self.assertTrue(self.watcher.unwatch_directory(self.test_dir_path, callback2))
        self.assertNotIn(self.test_dir_path, self.watcher.get_watched_directories())
        
        # Test unwatching with an exception
        with patch("os.path.abspath", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(self.watcher.unwatch_directory(self.test_dir_path))
                mock_error.assert_called_once()
    
    def test_file_change_detection(self):
        """Test file change detection."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the file
        self.watcher.watch_file(self.test_file_path, callback)
        
        # Start the watcher
        self.watcher.start()
        
        # Modify the file
        time.sleep(0.2)  # Wait for the watcher to start
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("Modified content")
        
        # Wait for the watcher to detect the change
        time.sleep(0.2)
        
        # Check that the callback was called
        callback.assert_called_once_with(self.test_file_path)
        
        # Reset the mock
        callback.reset_mock()
        
        # Delete the file
        os.remove(self.test_file_path)
        
        # Wait for the watcher to detect the change
        time.sleep(0.2)
        
        # Check that the callback was called
        callback.assert_called_once_with(self.test_file_path)
        
        # Check that the file is not in the watch list
        self.assertNotIn(self.test_file_path, self.watcher.get_watched_files())
    
    def test_directory_change_detection(self):
        """Test directory change detection."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the directory
        self.watcher.watch_directory(self.test_dir_path, callback)
        
        # Start the watcher
        self.watcher.start()
        
        # Modify a file in the directory
        time.sleep(0.2)  # Wait for the watcher to start
        with open(self.test_dir_file_path, "w", encoding="utf-8") as f:
            f.write("Modified content")
        
        # Wait for the watcher to detect the change
        time.sleep(0.2)
        
        # Check that the callback was called
        callback.assert_called_once_with(self.test_dir_path, self.test_dir_file_path)
        
        # Reset the mock
        callback.reset_mock()
        
        # Create a new file in the directory
        new_file_path = os.path.join(self.test_dir_path, "new_file.txt")
        with open(new_file_path, "w", encoding="utf-8") as f:
            f.write("New content")
        
        # Wait for the watcher to detect the change
        time.sleep(0.2)
        
        # Check that the callback was called
        callback.assert_called_once_with(self.test_dir_path, new_file_path)
        
        # Reset the mock
        callback.reset_mock()
        
        # Delete a file in the directory
        os.remove(self.test_dir_file_path)
        
        # Wait for the watcher to detect the change
        time.sleep(0.2)
        
        # Check that the callback was called
        callback.assert_called_once_with(self.test_dir_path, self.test_dir_file_path)
    
    def test_recursive_directory_watching(self):
        """Test recursive directory watching."""
        # Create a mock callback
        callback = MagicMock()
        
        # Create a subdirectory
        subdir_path = os.path.join(self.test_dir_path, "subdir")
        os.makedirs(subdir_path)
        
        # Create a file in the subdirectory
        subdir_file_path = os.path.join(subdir_path, "test_file.txt")
        with open(subdir_file_path, "w", encoding="utf-8") as f:
            f.write("Test content")
        
        # Watch the directory recursively
        self.watcher.watch_directory(self.test_dir_path, callback, recursive=True)
        
        # Start the watcher
        self.watcher.start()
        
        # Modify the file in the subdirectory
        time.sleep(0.2)  # Wait for the watcher to start
        with open(subdir_file_path, "w", encoding="utf-8") as f:
            f.write("Modified content")
        
        # Wait for the watcher to detect the change
        time.sleep(0.2)
        
        # Check that the callback was called
        callback.assert_called_once_with(self.test_dir_path, subdir_file_path)
    
    def test_singleton_instance(self):
        """Test the singleton instance."""
        # Get the singleton instance
        watcher1 = get_file_watcher()
        watcher2 = get_file_watcher()
        
        # Check that they are the same instance
        self.assertIs(watcher1, watcher2)
    
    def test_watch_file_function(self):
        """Test the watch_file function."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the file
        with patch("src.utils.file_watcher.get_file_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.is_running.return_value = False
            mock_watcher.watch_file.return_value = True
            mock_get_watcher.return_value = mock_watcher
            
            self.assertTrue(watch_file(self.test_file_path, callback))
            
            # Check that the watcher was started
            mock_watcher.start.assert_called_once()
            
            # Check that the file was watched
            mock_watcher.watch_file.assert_called_once()
        
        # Test with an exception
        with patch("src.utils.file_watcher.get_file_watcher", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(watch_file(self.test_file_path, callback))
                mock_error.assert_called_once()
    
    def test_unwatch_file_function(self):
        """Test the unwatch_file function."""
        # Create a mock callback
        callback = MagicMock()
        
        # Unwatch the file
        with patch("src.utils.file_watcher.get_file_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.unwatch_file.return_value = True
            mock_get_watcher.return_value = mock_watcher
            
            self.assertTrue(unwatch_file(self.test_file_path, callback))
            
            # Check that the file was unwatched
            mock_watcher.unwatch_file.assert_called_once()
        
        # Test with an exception
        with patch("src.utils.file_watcher.get_file_watcher", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(unwatch_file(self.test_file_path, callback))
                mock_error.assert_called_once()
    
    def test_watch_directory_function(self):
        """Test the watch_directory function."""
        # Create a mock callback
        callback = MagicMock()
        
        # Watch the directory
        with patch("src.utils.file_watcher.get_file_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.is_running.return_value = False
            mock_watcher.watch_directory.return_value = True
            mock_get_watcher.return_value = mock_watcher
            
            self.assertTrue(watch_directory(self.test_dir_path, callback))
            
            # Check that the watcher was started
            mock_watcher.start.assert_called_once()
            
            # Check that the directory was watched
            mock_watcher.watch_directory.assert_called_once()
        
        # Test with an exception
        with patch("src.utils.file_watcher.get_file_watcher", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(watch_directory(self.test_dir_path, callback))
                mock_error.assert_called_once()
    
    def test_unwatch_directory_function(self):
        """Test the unwatch_directory function."""
        # Create a mock callback
        callback = MagicMock()
        
        # Unwatch the directory
        with patch("src.utils.file_watcher.get_file_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.unwatch_directory.return_value = True
            mock_get_watcher.return_value = mock_watcher
            
            self.assertTrue(unwatch_directory(self.test_dir_path, callback))
            
            # Check that the directory was unwatched
            mock_watcher.unwatch_directory.assert_called_once()
        
        # Test with an exception
        with patch("src.utils.file_watcher.get_file_watcher", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(unwatch_directory(self.test_dir_path, callback))
                mock_error.assert_called_once()
    
    def test_stop_file_watcher_function(self):
        """Test the stop_file_watcher function."""
        # Stop the watcher
        with patch("src.utils.file_watcher.get_file_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.stop.return_value = True
            mock_get_watcher.return_value = mock_watcher
            
            self.assertTrue(stop_file_watcher())
            
            # Check that the watcher was stopped
            mock_watcher.stop.assert_called_once()
        
        # Test with an exception
        with patch("src.utils.file_watcher.get_file_watcher", side_effect=Exception("Test exception")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(stop_file_watcher())
                mock_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
