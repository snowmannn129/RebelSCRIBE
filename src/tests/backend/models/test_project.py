#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Project model.
"""

import os
import pytest
import datetime
from unittest.mock import patch
from typing import Dict, Any

from src.backend.models.project import Project


class TestProject:
    """Test suite for the Project model."""

    def test_init_default_values(self):
        """Test that a project is initialized with default values."""
        project = Project()
        
        assert project.title == ""
        assert project.description == ""
        assert project.author == ""
        assert isinstance(project.created_at, datetime.datetime)
        assert isinstance(project.updated_at, datetime.datetime)
        assert project.word_count_goal is None
        assert project.deadline is None
        assert project.genre == ""
        assert project.tags == []
        assert project.path is None
        assert project.version == "1.0.0"
        assert project.language == "en"
        assert project.status == "In Progress"
        assert project.metadata == {}

    def test_init_with_values(self):
        """Test that a project is initialized with provided values."""
        title = "Test Project"
        description = "This is a test project."
        author = "Test Author"
        
        project = Project(
            title=title,
            description=description,
            author=author
        )
        
        assert project.title == title
        assert project.description == description
        assert project.author == author

    def test_filename_property_with_path(self):
        """Test the filename property when path is set."""
        project = Project(title="Test Project")
        
        # Set path
        test_path = "/path/to/test_project.rebelscribe"
        project.set_path(test_path)
        
        assert project.filename == "test_project.rebelscribe"

    def test_filename_property_without_path(self):
        """Test the filename property when path is not set."""
        project = Project(title="Test Project")
        
        # Path is not set
        assert project.path is None
        
        # Filename should be derived from title
        assert project.filename == "Test_Project.rebelscribe"

    def test_filename_property_with_special_chars(self):
        """Test the filename property with special characters in title."""
        project = Project(title="Test Project: A Special & Unique Title!")
        
        # Filename should replace special characters
        assert project.filename == "Test_Project__A_Special___Unique_Title_.rebelscribe"

    def test_directory_property_with_path(self):
        """Test the directory property when path is set."""
        project = Project(title="Test Project")
        
        # Set path - use a Windows-style path since we're on Windows
        test_path = "C:\\path\\to\\test_project.rebelscribe"
        project.set_path(test_path)
        
        # Use Path to get the expected directory in a platform-independent way
        from pathlib import Path
        expected_dir = str(Path(test_path).parent)
        
        assert project.directory == expected_dir

    def test_directory_property_without_path(self):
        """Test the directory property when path is not set."""
        project = Project(title="Test Project")
        
        # Path is not set
        assert project.path is None
        
        # Directory should be None
        assert project.directory is None

    def test_set_path(self):
        """Test setting the project path."""
        project = Project(title="Test Project")
        
        # Set path
        test_path = "/path/to/test_project.rebelscribe"
        project.set_path(test_path)
        
        # Path should be absolute
        assert project.path == os.path.abspath(test_path)

    def test_add_tag(self):
        """Test adding a tag to the project."""
        project = Project()
        tag = "test-tag"
        
        project.add_tag(tag)
        assert tag in project.tags
        
        # Adding the same tag again should not duplicate
        project.add_tag(tag)
        assert project.tags.count(tag) == 1

    def test_remove_tag(self):
        """Test removing a tag from the project."""
        project = Project()
        tag = "test-tag"
        
        # Add tag
        project.add_tag(tag)
        assert tag in project.tags
        
        # Remove tag
        project.remove_tag(tag)
        assert tag not in project.tags
        
        # Removing a non-existent tag should not error
        project.remove_tag("nonexistent")

    def test_metadata_operations(self):
        """Test metadata operations."""
        project = Project()
        
        # Set metadata
        project.set_metadata("key1", "value1")
        assert project.metadata["key1"] == "value1"
        
        # Get metadata
        assert project.get_metadata("key1") == "value1"
        assert project.get_metadata("nonexistent") is None
        assert project.get_metadata("nonexistent", "default") == "default"
        
        # Update metadata
        project.set_metadata("key1", "updated")
        assert project.get_metadata("key1") == "updated"
        
        # Remove metadata
        project.remove_metadata("key1")
        assert "key1" not in project.metadata
        
        # Removing non-existent metadata should not error
        project.remove_metadata("nonexistent")

    def test_update_word_count_goal(self):
        """Test updating the word count goal."""
        project = Project()
        
        # Set goal
        goal = 50000
        project.update_word_count_goal(goal)
        assert project.word_count_goal == goal
        
        # Remove goal
        project.update_word_count_goal(None)
        assert project.word_count_goal is None

    def test_update_deadline(self):
        """Test updating the deadline."""
        project = Project()
        
        # Set deadline
        deadline = datetime.datetime(2025, 12, 31)
        project.update_deadline(deadline)
        assert project.deadline == deadline
        
        # Remove deadline
        project.update_deadline(None)
        assert project.deadline is None

    def test_update_status_valid(self):
        """Test updating the status with a valid status."""
        project = Project()
        
        # Default status
        assert project.status == "In Progress"
        
        # Update to valid status
        project.update_status("Completed")
        assert project.status == "Completed"
        
        project.update_status("On Hold")
        assert project.status == "On Hold"
        
        project.update_status("Abandoned")
        assert project.status == "Abandoned"
        
        project.update_status("In Progress")
        assert project.status == "In Progress"

    def test_update_status_invalid(self):
        """Test updating the status with an invalid status."""
        project = Project()
        
        # Set to a valid status first
        project.update_status("Completed")
        assert project.status == "Completed"
        
        # Update to invalid status should default to "In Progress"
        project.update_status("Invalid Status")
        assert project.status == "In Progress"

    def test_str_representation(self):
        """Test the string representation of a project."""
        project = Project(title="Test Project", author="Test Author", status="Completed")
        
        expected = "Project(title='Test Project', author='Test Author', status='Completed')"
        assert str(project) == expected

    def test_to_dict(self):
        """Test converting a project to a dictionary."""
        project = Project(
            title="Test Project",
            description="This is a test project.",
            author="Test Author"
        )
        
        project_dict = project.to_dict()
        
        assert project_dict["title"] == "Test Project"
        assert project_dict["description"] == "This is a test project."
        assert project_dict["author"] == "Test Author"
        assert "id" in project_dict
        assert "created_at" in project_dict
        assert "updated_at" in project_dict

    def test_from_dict(self):
        """Test creating a project from a dictionary."""
        data: Dict[str, Any] = {
            "title": "Test Project",
            "description": "This is a test project.",
            "author": "Test Author",
            "tags": ["test", "project"],
            "status": "Completed"
        }
        
        project = Project.from_dict(data)
        
        assert project.title == "Test Project"
        assert project.description == "This is a test project."
        assert project.author == "Test Author"
        assert project.tags == ["test", "project"]
        assert project.status == "Completed"

    def test_to_json_from_json(self):
        """Test JSON serialization and deserialization."""
        original = Project(
            title="Test Project",
            description="This is a test project.",
            author="Test Author",
            tags=["test", "project"],
            status="Completed"
        )
        
        # Convert to JSON
        json_str = original.to_json()
        
        # Convert back from JSON
        restored = Project.from_json(json_str)
        
        # Check that the restored project has the same properties
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.author == original.author
        assert restored.tags == original.tags
        assert restored.status == original.status
