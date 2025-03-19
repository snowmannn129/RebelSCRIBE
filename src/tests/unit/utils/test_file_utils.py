#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the file_utils module.

This module contains unit tests for the file utility functions:
- File operations (read, write, delete, copy, move)
- Directory operations (create, list files)
- Path operations (expand, ensure)
- File information (size, modification time)
- Specialized file operations (JSON, pickle, binary)
"""

import os
import json
import pickle
import tempfile
import time
from unittest.mock import patch, MagicMock

import pytest
from src.tests.base_test import BaseTest
from src.utils.file_utils import (
    expand_path, ensure_directory, file_exists, read_file, write_file,
    read_json_file, write_json_file, delete_file, copy_file, list_files,
    read_text_file, write_text_file, read_binary_file, write_binary_file,
    read_pickle_file, write_pickle_file, move_file, create_temp_file,
    create_temp_directory, get_file_size, get_file_modification_time,
    directory_exists
)


class TestFileUtils(BaseTest):
    """Unit tests for the file_utils module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create test files and directories
        self.test_file_path = os.path.join(self.test_dir, "test_file.txt")
        self.test_content = "This is a test file."
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.test_content)
        
        self.test_json_path = os.path.join(self.test_dir, "test_file.json")
        self.test_json_data = {"name": "Test", "value": 42}
        with open(self.test_json_path, "w", encoding="utf-8") as f:
            json.dump(self.test_json_data, f)
        
        self.test_binary_path = os.path.join(self.test_dir, "test_file.bin")
        self.test_binary_data = b"Binary data"
        with open(self.test_binary_path, "wb") as f:
            f.write(self.test_binary_data)
        
        self.test_pickle_path = os.path.join(self.test_dir, "test_file.pkl")
        self.test_pickle_data = {"complex": [1, 2, 3], "nested": {"a": 1, "b": 2}}
        with open(self.test_pickle_path, "wb") as f:
            pickle.dump(self.test_pickle_data, f)
        
        # Create a subdirectory
        self.test_subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.test_subdir)
        
        # Create files in the subdirectory
        for i in range(3):
            file_path = os.path.join(self.test_subdir, f"file{i}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Content of file {i}")
    
    def test_expand_path(self):
        """Test expanding paths."""
        # Test with tilde
        home_dir = os.path.expanduser("~")
        self.assertEqual(expand_path("~/test"), os.path.join(home_dir, "test"))
        
        # Test with normal path
        # Use os.path.normpath to handle platform-specific path separators
        self.assertEqual(expand_path("/path/to/file"), os.path.normpath("/path/to/file"))
        
        # Test with relative path
        self.assertEqual(expand_path("./file"), "file")
        
        # Test with None
        with patch("logging.Logger.error") as mock_error:
            self.assertEqual(expand_path(None), None)
            mock_error.assert_called_once()
    
    def test_ensure_directory(self):
        """Test ensuring directories exist."""
        # Test with existing directory
        self.assertTrue(ensure_directory(self.test_dir))
        
        # Test with new directory
        new_dir = os.path.join(self.test_dir, "new_dir")
        self.assertTrue(ensure_directory(new_dir))
        self.assertTrue(os.path.exists(new_dir))
        
        # Test with nested directory
        nested_dir = os.path.join(self.test_dir, "nested", "dir")
        self.assertTrue(ensure_directory(nested_dir))
        self.assertTrue(os.path.exists(nested_dir))
        
        # Test with invalid path
        with patch("os.makedirs", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(ensure_directory("/invalid/path"))
                mock_error.assert_called_once()
    
    def test_file_exists(self):
        """Test checking if files exist."""
        # Test with existing file
        self.assertTrue(file_exists(self.test_file_path))
        
        # Test with non-existent file
        self.assertFalse(file_exists(os.path.join(self.test_dir, "nonexistent.txt")))
        
        # Test with directory
        self.assertFalse(file_exists(self.test_dir))
    
    def test_read_file(self):
        """Test reading files."""
        # Test with existing file
        self.assertEqual(read_file(self.test_file_path), self.test_content)
        
        # Test with non-existent file
        with patch("logging.Logger.error") as mock_error:
            self.assertIsNone(read_file(os.path.join(self.test_dir, "nonexistent.txt")))
            mock_error.assert_called_once()
    
    def test_write_file(self):
        """Test writing files."""
        # Test writing to a new file
        new_file_path = os.path.join(self.test_dir, "new_file.txt")
        new_content = "New file content."
        self.assertTrue(write_file(new_file_path, new_content))
        
        # Verify the file was written
        with open(new_file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), new_content)
        
        # Test writing to an existing file
        updated_content = "Updated content."
        self.assertTrue(write_file(self.test_file_path, updated_content))
        
        # Verify the file was updated
        with open(self.test_file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), updated_content)
        
        # Test writing to a file in a non-existent directory
        nested_file_path = os.path.join(self.test_dir, "nested", "new_file.txt")
        self.assertTrue(write_file(nested_file_path, new_content))
        
        # Verify the file was written
        with open(nested_file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), new_content)
        
        # Test with error
        with patch("builtins.open", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(write_file(new_file_path, new_content))
                mock_error.assert_called_once()
    
    def test_read_json_file(self):
        """Test reading JSON files."""
        # Test with existing file
        data = read_json_file(self.test_json_path)
        self.assertEqual(data, self.test_json_data)
        
        # Test with non-existent file
        with patch("logging.Logger.error") as mock_error:
            self.assertIsNone(read_json_file(os.path.join(self.test_dir, "nonexistent.json")))
            mock_error.assert_called_once()
        
        # Test with invalid JSON
        invalid_json_path = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_json_path, "w", encoding="utf-8") as f:
            f.write("Invalid JSON")
        
        with patch("logging.Logger.error") as mock_error:
            self.assertIsNone(read_json_file(invalid_json_path))
            mock_error.assert_called_once()
    
    def test_write_json_file(self):
        """Test writing JSON files."""
        # Test writing to a new file
        new_json_path = os.path.join(self.test_dir, "new_file.json")
        new_data = {"name": "New", "value": 100}
        self.assertTrue(write_json_file(new_json_path, new_data))
        
        # Verify the file was written
        with open(new_json_path, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), new_data)
        
        # Test writing to an existing file
        updated_data = {"name": "Updated", "value": 200}
        self.assertTrue(write_json_file(self.test_json_path, updated_data))
        
        # Verify the file was updated
        with open(self.test_json_path, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), updated_data)
        
        # Test writing to a file in a non-existent directory
        nested_json_path = os.path.join(self.test_dir, "nested", "new_file.json")
        self.assertTrue(write_json_file(nested_json_path, new_data))
        
        # Verify the file was written
        with open(nested_json_path, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), new_data)
        
        # Test with datetime objects
        import datetime
        date_data = {"date": datetime.datetime(2023, 1, 1, 12, 0, 0)}
        self.assertTrue(write_json_file(new_json_path, date_data))
        
        # Verify the file was written
        with open(new_json_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            self.assertEqual(loaded_data["date"], "2023-01-01T12:00:00")
        
        # Test with error
        with patch("builtins.open", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(write_json_file(new_json_path, new_data))
                mock_error.assert_called_once()
    
    def test_delete_file(self):
        """Test deleting files."""
        # Test with existing file
        self.assertTrue(delete_file(self.test_file_path))
        self.assertFalse(os.path.exists(self.test_file_path))
        
        # Test with non-existent file
        self.assertTrue(delete_file(os.path.join(self.test_dir, "nonexistent.txt")))
        
        # Test with error
        with patch("os.remove", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(delete_file(self.test_json_path))
                mock_error.assert_called_once()
    
    def test_copy_file(self):
        """Test copying files."""
        # Test copying to a new file
        dest_path = os.path.join(self.test_dir, "copy.txt")
        self.assertTrue(copy_file(self.test_file_path, dest_path))
        
        # Verify the file was copied
        self.assertTrue(os.path.exists(dest_path))
        with open(dest_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), self.test_content)
        
        # Test copying to a file in a non-existent directory
        nested_dest_path = os.path.join(self.test_dir, "nested", "copy.txt")
        self.assertTrue(copy_file(self.test_file_path, nested_dest_path))
        
        # Verify the file was copied
        self.assertTrue(os.path.exists(nested_dest_path))
        
        # Test with error
        with patch("shutil.copy2", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(copy_file(self.test_file_path, dest_path))
                mock_error.assert_called_once()
    
    def test_list_files(self):
        """Test listing files."""
        # Test listing files in a directory
        files = list_files(self.test_dir)
        self.assertIn(self.test_file_path, files)
        self.assertIn(self.test_json_path, files)
        self.assertIn(self.test_binary_path, files)
        self.assertIn(self.test_pickle_path, files)
        
        # Test with pattern
        txt_files = list_files(self.test_dir, "*.txt")
        self.assertIn(self.test_file_path, txt_files)
        self.assertNotIn(self.test_json_path, txt_files)
        
        # Test with recursive
        all_files = list_files(self.test_dir, recursive=True)
        self.assertTrue(len(all_files) > len(files))  # Should include files in subdirectory
        
        # Test with pattern and recursive
        all_txt_files = list_files(self.test_dir, "*.txt", recursive=True)
        self.assertIn(self.test_file_path, all_txt_files)
        self.assertIn(os.path.join(self.test_subdir, "file0.txt"), all_txt_files)
        
        # Test with non-existent directory
        self.assertEqual(list_files(os.path.join(self.test_dir, "nonexistent")), [])
        
        # Test with error
        with patch("os.listdir", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertEqual(list_files(self.test_dir), [])
                mock_error.assert_called_once()
    
    def test_read_text_file(self):
        """Test reading text files."""
        # This is just an alias for read_file
        self.assertEqual(read_text_file(self.test_file_path), self.test_content)
    
    def test_write_text_file(self):
        """Test writing text files."""
        # This is just an alias for write_file
        new_file_path = os.path.join(self.test_dir, "new_text_file.txt")
        new_content = "New text file content."
        self.assertTrue(write_text_file(new_file_path, new_content))
        
        # Verify the file was written
        with open(new_file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), new_content)
    
    def test_read_binary_file(self):
        """Test reading binary files."""
        # Test with existing file
        self.assertEqual(read_binary_file(self.test_binary_path), self.test_binary_data)
        
        # Test with non-existent file
        with patch("logging.Logger.error") as mock_error:
            self.assertIsNone(read_binary_file(os.path.join(self.test_dir, "nonexistent.bin")))
            mock_error.assert_called_once()
    
    def test_write_binary_file(self):
        """Test writing binary files."""
        # Test writing to a new file
        new_binary_path = os.path.join(self.test_dir, "new_file.bin")
        new_binary_data = b"New binary data"
        self.assertTrue(write_binary_file(new_binary_path, new_binary_data))
        
        # Verify the file was written
        with open(new_binary_path, "rb") as f:
            self.assertEqual(f.read(), new_binary_data)
        
        # Test writing to an existing file
        updated_binary_data = b"Updated binary data"
        self.assertTrue(write_binary_file(self.test_binary_path, updated_binary_data))
        
        # Verify the file was updated
        with open(self.test_binary_path, "rb") as f:
            self.assertEqual(f.read(), updated_binary_data)
        
        # Test writing to a file in a non-existent directory
        nested_binary_path = os.path.join(self.test_dir, "nested", "new_file.bin")
        self.assertTrue(write_binary_file(nested_binary_path, new_binary_data))
        
        # Verify the file was written
        with open(nested_binary_path, "rb") as f:
            self.assertEqual(f.read(), new_binary_data)
        
        # Test with error
        with patch("builtins.open", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(write_binary_file(new_binary_path, new_binary_data))
                mock_error.assert_called_once()
    
    def test_read_pickle_file(self):
        """Test reading pickle files."""
        # Test with existing file
        data = read_pickle_file(self.test_pickle_path)
        self.assertEqual(data, self.test_pickle_data)
        
        # Test with non-existent file
        with patch("logging.Logger.error") as mock_error:
            self.assertIsNone(read_pickle_file(os.path.join(self.test_dir, "nonexistent.pkl")))
            mock_error.assert_called_once()
        
        # Test with invalid pickle
        invalid_pickle_path = os.path.join(self.test_dir, "invalid.pkl")
        with open(invalid_pickle_path, "wb") as f:
            f.write(b"Invalid pickle data")
        
        with patch("logging.Logger.error") as mock_error:
            self.assertIsNone(read_pickle_file(invalid_pickle_path))
            mock_error.assert_called_once()
    
    def test_write_pickle_file(self):
        """Test writing pickle files."""
        # Test writing to a new file
        new_pickle_path = os.path.join(self.test_dir, "new_file.pkl")
        new_pickle_data = {"new": [4, 5, 6], "nested": {"c": 3, "d": 4}}
        self.assertTrue(write_pickle_file(new_pickle_path, new_pickle_data))
        
        # Verify the file was written
        with open(new_pickle_path, "rb") as f:
            self.assertEqual(pickle.load(f), new_pickle_data)
        
        # Test writing to an existing file
        updated_pickle_data = {"updated": True}
        self.assertTrue(write_pickle_file(self.test_pickle_path, updated_pickle_data))
        
        # Verify the file was updated
        with open(self.test_pickle_path, "rb") as f:
            self.assertEqual(pickle.load(f), updated_pickle_data)
        
        # Test writing to a file in a non-existent directory
        nested_pickle_path = os.path.join(self.test_dir, "nested", "new_file.pkl")
        self.assertTrue(write_pickle_file(nested_pickle_path, new_pickle_data))
        
        # Verify the file was written
        with open(nested_pickle_path, "rb") as f:
            self.assertEqual(pickle.load(f), new_pickle_data)
        
        # Test with error
        with patch("builtins.open", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(write_pickle_file(new_pickle_path, new_pickle_data))
                mock_error.assert_called_once()
    
    def test_move_file(self):
        """Test moving files."""
        # Test moving to a new file
        dest_path = os.path.join(self.test_dir, "moved.txt")
        self.assertTrue(move_file(self.test_file_path, dest_path))
        
        # Verify the file was moved
        self.assertFalse(os.path.exists(self.test_file_path))
        self.assertTrue(os.path.exists(dest_path))
        with open(dest_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), self.test_content)
        
        # Test moving to a file in a non-existent directory
        source_path = os.path.join(self.test_subdir, "file0.txt")
        nested_dest_path = os.path.join(self.test_dir, "nested", "moved.txt")
        self.assertTrue(move_file(source_path, nested_dest_path))
        
        # Verify the file was moved
        self.assertFalse(os.path.exists(source_path))
        self.assertTrue(os.path.exists(nested_dest_path))
        
        # Test with error
        with patch("shutil.move", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertFalse(move_file(dest_path, source_path))
                mock_error.assert_called_once()
    
    def test_create_temp_file(self):
        """Test creating temporary files."""
        # Test without content
        temp_path = create_temp_file()
        self.assertIsNotNone(temp_path)
        self.assertTrue(os.path.exists(temp_path))
        
        # Test with content
        content = "Temporary file content."
        temp_path_with_content = create_temp_file(content)
        self.assertIsNotNone(temp_path_with_content)
        with open(temp_path_with_content, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)
        
        # Test with suffix
        temp_path_with_suffix = create_temp_file(suffix=".txt")
        self.assertIsNotNone(temp_path_with_suffix)
        self.assertTrue(temp_path_with_suffix.endswith(".txt"))
        
        # Test with error
        with patch("tempfile.mkstemp", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertIsNone(create_temp_file())
                mock_error.assert_called_once()
        
        # Clean up
        os.remove(temp_path)
        os.remove(temp_path_with_content)
        os.remove(temp_path_with_suffix)
    
    def test_create_temp_directory(self):
        """Test creating temporary directories."""
        # Test creating a temporary directory
        temp_dir = create_temp_directory()
        self.assertIsNotNone(temp_dir)
        self.assertTrue(os.path.exists(temp_dir))
        self.assertTrue(os.path.isdir(temp_dir))
        
        # Test with error
        with patch("tempfile.mkdtemp", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertIsNone(create_temp_directory())
                mock_error.assert_called_once()
        
        # Clean up
        os.rmdir(temp_dir)
    
    def test_get_file_size(self):
        """Test getting file sizes."""
        # Test with existing file
        size = get_file_size(self.test_file_path)
        self.assertEqual(size, len(self.test_content))
        
        # Test with non-existent file
        self.assertIsNone(get_file_size(os.path.join(self.test_dir, "nonexistent.txt")))
        
        # Test with error
        with patch("os.path.getsize", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertIsNone(get_file_size(self.test_file_path))
                mock_error.assert_called_once()
    
    def test_get_file_modification_time(self):
        """Test getting file modification times."""
        # Test with existing file
        mtime = get_file_modification_time(self.test_file_path)
        self.assertIsNotNone(mtime)
        self.assertIsInstance(mtime, float)
        
        # Test with non-existent file
        self.assertIsNone(get_file_modification_time(os.path.join(self.test_dir, "nonexistent.txt")))
        
        # Test with error
        with patch("os.path.getmtime", side_effect=Exception("Test error")):
            with patch("logging.Logger.error") as mock_error:
                self.assertIsNone(get_file_modification_time(self.test_file_path))
                mock_error.assert_called_once()
    
    def test_directory_exists(self):
        """Test checking if directories exist."""
        # Test with existing directory
        self.assertTrue(directory_exists(self.test_dir))
        self.assertTrue(directory_exists(self.test_subdir))
        
        # Test with non-existent directory
        self.assertFalse(directory_exists(os.path.join(self.test_dir, "nonexistent")))
        
        # Test with file
        self.assertFalse(directory_exists(self.test_file_path))


# Pytest-style tests
class TestFileUtilsPytest:
    """Pytest-style tests for the file_utils module."""
    
    @pytest.fixture
    def setup(self, tmp_path):
        """Set up test fixtures."""
        # Create test files and directories
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        test_file_path = test_dir / "test_file.txt"
        test_content = "This is a test file."
        test_file_path.write_text(test_content)
        
        test_json_path = test_dir / "test_file.json"
        test_json_data = {"name": "Test", "value": 42}
        test_json_path.write_text(json.dumps(test_json_data))
        
        # Create a subdirectory
        test_subdir = test_dir / "subdir"
        test_subdir.mkdir()
        
        return {
            "test_dir": str(test_dir),
            "test_file_path": str(test_file_path),
            "test_content": test_content,
            "test_json_path": str(test_json_path),
            "test_json_data": test_json_data,
            "test_subdir": str(test_subdir)
        }
    
    def test_read_file_pytest(self, setup):
        """Test reading files using pytest style."""
        # Test with existing file
        assert read_file(setup["test_file_path"]) == setup["test_content"]
        
        # Test with non-existent file
        with patch("logging.Logger.error"):
            assert read_file(os.path.join(setup["test_dir"], "nonexistent.txt")) is None
    
    def test_write_file_pytest(self, setup):
        """Test writing files using pytest style."""
        # Test writing to a new file
        new_file_path = os.path.join(setup["test_dir"], "new_file.txt")
        new_content = "New file content."
        assert write_file(new_file_path, new_content) is True
        
        # Verify the file was written
        with open(new_file_path, "r", encoding="utf-8") as f:
            assert f.read() == new_content
    
    def test_list_files_pytest(self, setup):
        """Test listing files using pytest style."""
        # Test listing files in a directory
        files = list_files(setup["test_dir"])
        assert setup["test_file_path"] in files
        assert setup["test_json_path"] in files


if __name__ == '__main__':
    unittest.main()
