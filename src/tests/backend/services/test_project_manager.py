#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the ProjectManager service.

This module contains tests for the ProjectManager class, which is responsible
for creating, loading, saving, and managing writing projects.
"""

import unittest
import os
import tempfile
import shutil
import json
import datetime
from unittest.mock import patch, MagicMock, mock_open

from src.backend.services.project_manager import ProjectManager
from src.backend.models.project import Project
from src.backend.models.document import Document


class TestProjectManager(unittest.TestCase):
    """Test cases for the ProjectManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the config to use the temporary directory
        self.config_patcher = patch('src.backend.services.project_manager.ConfigManager')
        self.mock_config = self.config_patcher.start()
        mock_config_instance = MagicMock()
        mock_config_instance.get.side_effect = lambda section, key=None, default=None: {
            'application': {'data_directory': self.temp_dir}
        }.get(section, {}).get(key, default)
        self.mock_config.return_value = mock_config_instance
        
        # Create the project manager instance
        self.project_manager = ProjectManager()
        
        # Ensure the project manager's data directory is set to our temp directory
        self.project_manager.data_directory = self.temp_dir

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Stop the config patcher
        self.config_patcher.stop()
        
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)

    @patch('src.backend.services.project_manager.file_utils')
    def test_create_project(self, mock_file_utils):
        """Test creating a new project."""
        # Mock file_utils methods
        mock_file_utils.ensure_directory.return_value = True
        mock_file_utils.write_json_file.return_value = True
        
        # Create a project
        project = self.project_manager.create_project(
            title="Test Project",
            author="Test Author",
            description="Test Description",
            template="novel"
        )
        
        # Assertions
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.author, "Test Author")
        self.assertEqual(project.description, "Test Description")
        # Note: modified is set to False after saving in save_project
        self.assertEqual(self.project_manager.current_project, project)
        
        # Verify file_utils methods were called
        mock_file_utils.ensure_directory.assert_called()
        mock_file_utils.write_json_file.assert_called()
        
        # Verify documents were created from template
        self.assertTrue(len(self.project_manager.documents) > 0)
        self.assertTrue(len(self.project_manager.root_document_ids) > 0)

    @patch('src.backend.services.project_manager.file_utils')
    def test_load_project(self, mock_file_utils):
        """Test loading a project from a file."""
        # Mock file_utils methods
        mock_file_utils.file_exists.return_value = True
        mock_file_utils.directory_exists.return_value = False
        
        # Create a mock project data
        project_data = {
            "id": "test-id",
            "title": "Test Project",
            "author": "Test Author",
            "description": "Test Description",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Mock read_json_file to return our project data
        mock_file_utils.read_json_file.return_value = project_data
        
        # Mock list_files to return an empty list (no documents)
        mock_file_utils.list_files.return_value = []
        
        # Load the project
        project = self.project_manager.load_project("test_project.rebelscribe")
        
        # Assertions
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.author, "Test Author")
        self.assertEqual(project.description, "Test Description")
        self.assertFalse(self.project_manager.modified)
        self.assertEqual(self.project_manager.current_project, project)
        
        # Verify file_utils methods were called
        mock_file_utils.file_exists.assert_called_with("test_project.rebelscribe")
        mock_file_utils.read_json_file.assert_called_with("test_project.rebelscribe")

    @patch('src.backend.services.project_manager.file_utils')
    def test_save_project(self, mock_file_utils):
        """Test saving a project."""
        # Mock file_utils methods
        mock_file_utils.ensure_directory.return_value = True
        mock_file_utils.write_json_file.return_value = True
        
        # Create a project to save
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        project.set_path(os.path.join(self.temp_dir, "test_project.rebelscribe"))
        
        # Set as current project
        self.project_manager.current_project = project
        self.project_manager.modified = True
        
        # Save the project
        result = self.project_manager.save_project()
        
        # Assertions
        self.assertTrue(result)
        self.assertFalse(self.project_manager.modified)
        
        # Verify file_utils methods were called
        mock_file_utils.ensure_directory.assert_called()
        mock_file_utils.write_json_file.assert_called()

    @patch('src.backend.services.project_manager.file_utils')
    def test_close_project(self, mock_file_utils):
        """Test closing a project."""
        # Mock file_utils methods
        mock_file_utils.ensure_directory.return_value = True
        mock_file_utils.write_json_file.return_value = True
        
        # Create a project to close
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        project.set_path(os.path.join(self.temp_dir, "test_project.rebelscribe"))
        
        # Set as current project
        self.project_manager.current_project = project
        self.project_manager.modified = True
        
        # Close the project
        result = self.project_manager.close_project()
        
        # Assertions
        self.assertTrue(result)
        self.assertIsNone(self.project_manager.current_project)
        self.assertEqual(self.project_manager.documents, {})
        self.assertEqual(self.project_manager.root_document_ids, [])
        self.assertFalse(self.project_manager.modified)

    @patch('src.backend.services.project_manager.file_utils')
    def test_get_project_list(self, mock_file_utils):
        """Test getting a list of available projects."""
        # Mock file_utils methods
        mock_file_utils.directory_exists.return_value = True
        
        # Create mock project files
        project_files = [
            os.path.join(self.temp_dir, "project1.rebelscribe"),
            os.path.join(self.temp_dir, "project2.rebelscribe")
        ]
        
        # Mock list_files to return our project files
        mock_file_utils.list_files.return_value = project_files
        
        # Create mock project data
        project1_data = {
            "title": "Project 1",
            "author": "Author 1",
            "description": "Description 1",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        project2_data = {
            "title": "Project 2",
            "author": "Author 2",
            "description": "Description 2",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Mock read_json_file to return our project data
        mock_file_utils.read_json_file.side_effect = [project1_data, project2_data]
        
        # Get the project list
        projects = self.project_manager.get_project_list()
        
        # Assertions
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]["title"], "Project 1")
        self.assertEqual(projects[1]["title"], "Project 2")
        
        # Verify file_utils methods were called
        mock_file_utils.directory_exists.assert_called_with(self.temp_dir)
        mock_file_utils.list_files.assert_called_with(self.temp_dir, "*.rebelscribe")

    def test_create_document(self):
        """Test creating a new document."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create a document
        document = self.project_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            content="Test content"
        )
        
        # Assertions
        self.assertIsNotNone(document)
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.type, Document.TYPE_SCENE)
        self.assertEqual(document.content, "Test content")
        self.assertIsNone(document.parent_id)
        self.assertTrue(self.project_manager.modified)
        self.assertIn(document.id, self.project_manager.documents)
        self.assertIn(document.id, self.project_manager.root_document_ids)

    def test_create_document_with_parent(self):
        """Test creating a new document with a parent."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create a parent document
        parent = self.project_manager.create_document(
            title="Parent Document",
            doc_type=Document.TYPE_FOLDER
        )
        
        # Create a child document
        child = self.project_manager.create_document(
            title="Child Document",
            doc_type=Document.TYPE_SCENE,
            parent_id=parent.id
        )
        
        # Assertions
        self.assertIsNotNone(child)
        self.assertEqual(child.title, "Child Document")
        self.assertEqual(child.parent_id, parent.id)
        self.assertIn(child.id, parent.children_ids)
        self.assertIn(child.id, self.project_manager.documents)
        self.assertNotIn(child.id, self.project_manager.root_document_ids)

    def test_get_document(self):
        """Test getting a document by ID."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create a document
        document = self.project_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE
        )
        
        # Get the document
        retrieved_document = self.project_manager.get_document(document.id)
        
        # Assertions
        self.assertEqual(retrieved_document, document)

    def test_update_document(self):
        """Test updating a document."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create a document
        document = self.project_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE
        )
        
        # Update the document
        result = self.project_manager.update_document(
            document.id,
            title="Updated Title",
            content="Updated content"
        )
        
        # Assertions
        self.assertTrue(result)
        self.assertTrue(self.project_manager.modified)
        self.assertEqual(document.title, "Updated Title")
        self.assertEqual(document.content, "Updated content")

    def test_delete_document(self):
        """Test deleting a document."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create a document
        document = self.project_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE
        )
        
        # Delete the document
        result = self.project_manager.delete_document(document.id)
        
        # Assertions
        self.assertTrue(result)
        self.assertTrue(self.project_manager.modified)
        self.assertNotIn(document.id, self.project_manager.documents)
        self.assertNotIn(document.id, self.project_manager.root_document_ids)

    def test_delete_document_recursive(self):
        """Test deleting a document with children recursively."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create a parent document
        parent = self.project_manager.create_document(
            title="Parent Document",
            doc_type=Document.TYPE_FOLDER
        )
        
        # Create a child document
        child = self.project_manager.create_document(
            title="Child Document",
            doc_type=Document.TYPE_SCENE,
            parent_id=parent.id
        )
        
        # Delete the parent document
        result = self.project_manager.delete_document(parent.id, recursive=True)
        
        # Assertions
        self.assertTrue(result)
        self.assertTrue(self.project_manager.modified)
        self.assertNotIn(parent.id, self.project_manager.documents)
        self.assertNotIn(parent.id, self.project_manager.root_document_ids)
        self.assertNotIn(child.id, self.project_manager.documents)

    def test_move_document(self):
        """Test moving a document to a new parent."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create folders
        folder1 = self.project_manager.create_document(
            title="Folder 1",
            doc_type=Document.TYPE_FOLDER
        )
        
        folder2 = self.project_manager.create_document(
            title="Folder 2",
            doc_type=Document.TYPE_FOLDER
        )
        
        # Create a document in folder1
        document = self.project_manager.create_document(
            title="Test Document",
            doc_type=Document.TYPE_SCENE,
            parent_id=folder1.id
        )
        
        # Move the document to folder2
        result = self.project_manager.move_document(document.id, folder2.id)
        
        # Assertions
        self.assertTrue(result)
        self.assertTrue(self.project_manager.modified)
        self.assertEqual(document.parent_id, folder2.id)
        self.assertIn(document.id, folder2.children_ids)
        self.assertNotIn(document.id, folder1.children_ids)

    def test_get_document_tree(self):
        """Test getting the document tree."""
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create a folder
        folder = self.project_manager.create_document(
            title="Folder",
            doc_type=Document.TYPE_FOLDER
        )
        
        # Create documents in the folder
        doc1 = self.project_manager.create_document(
            title="Document 1",
            doc_type=Document.TYPE_SCENE,
            parent_id=folder.id
        )
        
        doc2 = self.project_manager.create_document(
            title="Document 2",
            doc_type=Document.TYPE_SCENE,
            parent_id=folder.id
        )
        
        # Get the document tree
        tree = self.project_manager.get_document_tree()
        
        # Assertions
        self.assertEqual(len(tree), 1)  # One root document (the folder)
        self.assertEqual(tree[0]["id"], folder.id)
        self.assertEqual(tree[0]["title"], "Folder")
        self.assertEqual(len(tree[0]["children"]), 2)  # Two children
        
        # Check children
        child_ids = [child["id"] for child in tree[0]["children"]]
        self.assertIn(doc1.id, child_ids)
        self.assertIn(doc2.id, child_ids)

    @patch('src.backend.services.project_manager.file_utils')
    def test_create_project_from_template(self, mock_file_utils):
        """Test creating a project from a template file."""
        # Mock file_utils methods
        mock_file_utils.file_exists.return_value = True
        mock_file_utils.ensure_directory.return_value = True
        mock_file_utils.write_json_file.return_value = True
        
        # Create a mock template data
        template_data = {
            "name": "Test Template",
            "description": "Test Template Description",
            "structure": [
                {
                    "title": "Folder 1",
                    "type": Document.TYPE_FOLDER,
                    "children": [
                        {
                            "title": "Document 1",
                            "type": Document.TYPE_SCENE,
                            "content": "Content 1"
                        }
                    ]
                },
                {
                    "title": "Folder 2",
                    "type": Document.TYPE_FOLDER
                }
            ]
        }
        
        # Mock read_json_file to return our template data
        mock_file_utils.read_json_file.return_value = template_data
        
        # Create a project from the template
        project = self.project_manager.create_project_from_template(
            template_path="test_template.json",
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Assertions
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.author, "Test Author")
        self.assertEqual(project.description, "Test Description")
        # Note: modified is set to False after saving in save_project
        self.assertEqual(self.project_manager.current_project, project)
        
        # Verify file_utils methods were called
        mock_file_utils.file_exists.assert_called_with("test_template.json")
        mock_file_utils.read_json_file.assert_called_with("test_template.json")
        mock_file_utils.ensure_directory.assert_called()
        mock_file_utils.write_json_file.assert_called()

    @patch('src.backend.services.project_manager.file_utils')
    def test_export_project_template(self, mock_file_utils):
        """Test exporting a project as a template."""
        # Mock file_utils methods
        mock_file_utils.ensure_directory.return_value = True
        mock_file_utils.write_json_file.return_value = True
        
        # Create a project
        project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Set as current project
        self.project_manager.current_project = project
        
        # Create some documents
        folder = self.project_manager.create_document(
            title="Folder",
            doc_type=Document.TYPE_FOLDER
        )
        
        self.project_manager.create_document(
            title="Document",
            doc_type=Document.TYPE_SCENE,
            parent_id=folder.id,
            content="Test content"
        )
        
        # Export the project as a template
        template_path = self.project_manager.export_project_template(
            template_name="Test Template",
            template_description="Test Template Description"
        )
        
        # Assertions
        self.assertIsNotNone(template_path)
        
        # Verify file_utils methods were called
        mock_file_utils.ensure_directory.assert_called()
        mock_file_utils.write_json_file.assert_called()

    @patch('src.backend.services.project_manager.file_utils')
    def test_get_template_list(self, mock_file_utils):
        """Test getting a list of available templates."""
        # Mock file_utils methods
        mock_file_utils.directory_exists.return_value = True
        
        # Create mock template files
        template_files = [
            os.path.join(self.temp_dir, "templates", "template1.template.json"),
            os.path.join(self.temp_dir, "templates", "template2.template.json")
        ]
        
        # Mock list_files to return our template files
        mock_file_utils.list_files.return_value = template_files
        
        # Create mock template data
        template1_data = {
            "name": "Template 1",
            "description": "Description 1",
            "created_at": datetime.datetime.now().isoformat()
        }
        
        template2_data = {
            "name": "Template 2",
            "description": "Description 2",
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # Mock read_json_file to return our template data
        mock_file_utils.read_json_file.side_effect = [template1_data, template2_data]
        
        # Get the template list
        templates = self.project_manager.get_template_list()
        
        # Assertions
        # Should include built-in templates plus our custom templates
        self.assertEqual(len(templates), len(self.project_manager.DEFAULT_TEMPLATES) + 2)
        
        # Check custom templates
        custom_templates = [t for t in templates if not t["built_in"]]
        self.assertEqual(len(custom_templates), 2)
        self.assertEqual(custom_templates[0]["name"], "Template 1")
        self.assertEqual(custom_templates[1]["name"], "Template 2")
        
        # Verify file_utils methods were called
        mock_file_utils.directory_exists.assert_called()
        mock_file_utils.list_files.assert_called()


if __name__ == '__main__':
    unittest.main()
