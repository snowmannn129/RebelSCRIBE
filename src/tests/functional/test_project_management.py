#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functional tests for project management.
"""

import os
import unittest
import json
from pathlib import Path

from src.tests.functional.base_functional_test import BaseFunctionalTest
from src.backend.models.project import Project


class TestProjectManagement(BaseFunctionalTest):
    """Test case for project management functionality."""
    
    def test_create_project(self):
        """Test creating a project."""
        # Create a project
        project_path = self.create_test_project(
            title="Test Project Creation",
            author="Test Author"
        )
        
        # Verify the project file exists
        self.assertTrue(os.path.exists(project_path))
        
        # Load the project
        project = self.project_manager.load_project(project_path)
        
        # Verify the project
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project Creation")
        self.assertEqual(project.author, "Test Author")
    
    def test_create_project_with_template(self):
        """Test creating a project with different templates."""
        # Test each template type
        templates = ["novel", "short_story", "screenplay", "empty"]
        
        for template in templates:
            # Create a project with the template
            project_path = os.path.join(self.test_dir, f"{template}_project.rebelscribe")
            project = self.project_manager.create_project(
                title=f"{template.capitalize()} Project",
                author="Test Author",
                template=template,
                path=project_path
            )
            
            # Verify the project was created
            self.assertIsNotNone(project)
            self.assertEqual(project.title, f"{template.capitalize()} Project")
            
            # Load the project
            self.project_manager.load_project(project_path)
            
            # Verify the document structure based on template
            document_tree = self.project_manager.get_document_tree()
            
            if template == "empty":
                self.assertEqual(len(document_tree), 0)
            else:
                self.assertGreater(len(document_tree), 0)
                
                # Check specific structure for each template
                if template == "novel":
                    folder_titles = [node["title"] for node in document_tree]
                    self.assertIn("Manuscript", folder_titles)
                    self.assertIn("Characters", folder_titles)
                    self.assertIn("Locations", folder_titles)
                    self.assertIn("Research", folder_titles)
                    self.assertIn("Notes", folder_titles)
                elif template == "short_story":
                    folder_titles = [node["title"] for node in document_tree]
                    self.assertIn("Story", folder_titles)
                    self.assertIn("Characters", folder_titles)
                    self.assertIn("Notes", folder_titles)
                elif template == "screenplay":
                    folder_titles = [node["title"] for node in document_tree]
                    self.assertIn("Screenplay", folder_titles)
                    self.assertIn("Characters", folder_titles)
                    self.assertIn("Scenes", folder_titles)
                    self.assertIn("Notes", folder_titles)
    
    def test_load_project(self):
        """Test loading a project."""
        # Create a project
        project_path = self.create_test_project()
        
        # Close the project
        self.project_manager.close_project()
        
        # Load the project
        project = self.project_manager.load_project(project_path)
        
        # Verify the project
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.author, "Test Author")
        
        # Verify the project is set as current project
        self.assertEqual(self.project_manager.current_project, project)
    
    def test_save_project(self):
        """Test saving a project."""
        # Create a project
        project_path = self.create_test_project()
        
        # Modify the project
        self.project_manager.current_project.title = "Updated Title"
        self.project_manager.current_project.author = "Updated Author"
        self.project_manager.modified = True
        
        # Save the project
        success = self.project_manager.save_project()
        
        # Verify the save was successful
        self.assertTrue(success)
        self.assertFalse(self.project_manager.modified)
        
        # Close and reload the project to verify changes were saved
        self.project_manager.close_project()
        project = self.project_manager.load_project(project_path)
        
        # Verify the changes were saved
        self.assertEqual(project.title, "Updated Title")
        self.assertEqual(project.author, "Updated Author")
    
    def test_project_metadata(self):
        """Test project metadata."""
        # Create a project with metadata
        project_path = os.path.join(self.test_dir, "metadata_project.rebelscribe")
        project = self.project_manager.create_project(
            title="Metadata Project",
            author="Test Author",
            description="Test description",
            path=project_path
        )
        
        # Add custom metadata
        project.metadata = {
            "genre": "Science Fiction",
            "target_word_count": 80000,
            "status": "In Progress",
            "tags": ["sci-fi", "adventure", "space"]
        }
        
        # Save the project
        self.project_manager.save_project()
        
        # Close and reload the project
        self.project_manager.close_project()
        loaded_project = self.project_manager.load_project(project_path)
        
        # Verify the metadata
        self.assertEqual(loaded_project.description, "Test description")
        self.assertEqual(loaded_project.metadata["genre"], "Science Fiction")
        self.assertEqual(loaded_project.metadata["target_word_count"], 80000)
        self.assertEqual(loaded_project.metadata["status"], "In Progress")
        self.assertEqual(loaded_project.metadata["tags"], ["sci-fi", "adventure", "space"])
    
    def test_project_document_structure(self):
        """Test project document structure."""
        # Create a project
        project_path = self.create_test_project()
        
        # Create document structure
        manuscript = self.project_manager.create_document(
            title="Manuscript",
            doc_type="folder"
        )
        
        chapter1 = self.project_manager.create_document(
            title="Chapter 1",
            doc_type="folder",
            parent_id=manuscript.id
        )
        
        scene1 = self.project_manager.create_document(
            title="Scene 1",
            doc_type="scene",
            parent_id=chapter1.id,
            content="This is scene 1 content."
        )
        
        scene2 = self.project_manager.create_document(
            title="Scene 2",
            doc_type="scene",
            parent_id=chapter1.id,
            content="This is scene 2 content."
        )
        
        chapter2 = self.project_manager.create_document(
            title="Chapter 2",
            doc_type="folder",
            parent_id=manuscript.id
        )
        
        scene3 = self.project_manager.create_document(
            title="Scene 3",
            doc_type="scene",
            parent_id=chapter2.id,
            content="This is scene 3 content."
        )
        
        # Save the project
        self.project_manager.save_project()
        
        # Get document tree
        document_tree = self.project_manager.get_document_tree()
        
        # Verify the document structure
        self.assertEqual(len(document_tree), 1)  # One root document (Manuscript)
        
        # Find the manuscript node
        manuscript_node = document_tree[0]
        self.assertEqual(manuscript_node["title"], "Manuscript")
        self.assertEqual(len(manuscript_node["children"]), 2)  # Two chapters
        
        # Find chapter nodes
        chapter_nodes = manuscript_node["children"]
        chapter1_node = next((node for node in chapter_nodes if node["title"] == "Chapter 1"), None)
        chapter2_node = next((node for node in chapter_nodes if node["title"] == "Chapter 2"), None)
        
        self.assertIsNotNone(chapter1_node)
        self.assertIsNotNone(chapter2_node)
        
        # Verify chapter 1 has two scenes
        self.assertEqual(len(chapter1_node["children"]), 2)
        
        # Verify chapter 2 has one scene
        self.assertEqual(len(chapter2_node["children"]), 1)
        
        # Verify scene titles
        scene_titles_ch1 = [node["title"] for node in chapter1_node["children"]]
        self.assertIn("Scene 1", scene_titles_ch1)
        self.assertIn("Scene 2", scene_titles_ch1)
        
        scene_titles_ch2 = [node["title"] for node in chapter2_node["children"]]
        self.assertIn("Scene 3", scene_titles_ch2)
    
    def test_project_backup_and_restore(self):
        """Test project backup and restore."""
        # Create a project
        project_path = self.create_test_project(title="Backup Test Project")
        
        # Add some documents
        manuscript = self.project_manager.create_document(
            title="Manuscript",
            doc_type="folder"
        )
        
        chapter1 = self.project_manager.create_document(
            title="Chapter 1",
            doc_type="folder",
            parent_id=manuscript.id
        )
        
        scene1 = self.project_manager.create_document(
            title="Scene 1",
            doc_type="scene",
            parent_id=chapter1.id,
            content="This is scene 1 content."
        )
        
        # Save the project
        self.project_manager.save_project()
        
        # Create a backup
        backup_path = self.backup_service.create_backup(project_path, manual=True)
        
        # Verify the backup was created
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        # Modify the project
        self.project_manager.current_project.title = "Modified Project"
        scene1_doc = self.project_manager.get_document(scene1.id)
        scene1_doc.content = "Modified content"
        self.project_manager.save_document(scene1_doc)
        self.project_manager.save_project()
        
        # Close the project
        self.project_manager.close_project()
        
        # Create a restore directory
        restore_dir = os.path.join(self.test_dir, "restored_project")
        os.makedirs(restore_dir, exist_ok=True)
        
        # Restore from backup
        success = self.backup_service.restore_from_backup(backup_path, restore_dir)
        
        # Verify the restore was successful
        self.assertTrue(success)
        
        # Load the restored project
        restored_project_path = os.path.join(restore_dir, "project.json")
        self.assertTrue(os.path.exists(restored_project_path))
        
        restored_project = self.project_manager.load_project(restored_project_path)
        
        # Verify the restored project
        self.assertIsNotNone(restored_project)
        self.assertEqual(restored_project.title, "Backup Test Project")  # Original title, not "Modified Project"
        
        # Verify the document structure was restored
        document_tree = self.project_manager.get_document_tree()
        self.assertEqual(len(document_tree), 1)  # One root document (Manuscript)
        
        # Find the manuscript node
        manuscript_node = document_tree[0]
        self.assertEqual(manuscript_node["title"], "Manuscript")
        
        # Find chapter 1
        chapter1_node = manuscript_node["children"][0]
        self.assertEqual(chapter1_node["title"], "Chapter 1")
        
        # Find scene 1
        scene1_node = chapter1_node["children"][0]
        self.assertEqual(scene1_node["title"], "Scene 1")
        
        # Verify scene content was restored to original
        scene1_id = scene1_node["id"]
        scene1_doc = self.project_manager.get_document(scene1_id)
        self.assertEqual(scene1_doc.content, "This is scene 1 content.")  # Original content, not "Modified content"
    
    def test_project_template_export_and_use(self):
        """Test exporting a project as a template and using it."""
        # Create a project with a specific structure
        project_path = self.create_test_project(title="Template Source Project")
        
        # Add some documents
        manuscript = self.project_manager.create_document(
            title="Custom Manuscript",
            doc_type="folder"
        )
        
        characters = self.project_manager.create_document(
            title="Custom Characters",
            doc_type="folder"
        )
        
        worldbuilding = self.project_manager.create_document(
            title="Custom Worldbuilding",
            doc_type="folder"
        )
        
        # Save the project
        self.project_manager.save_project()
        
        # Export as template
        template_path = self.project_manager.export_project_template(
            template_name="Custom Template",
            template_description="A custom project template"
        )
        
        # Verify the template was created
        self.assertIsNotNone(template_path)
        self.assertTrue(os.path.exists(template_path))
        
        # Close the current project
        self.project_manager.close_project()
        
        # Create a new project from the template
        new_project_path = os.path.join(self.test_dir, "template_based_project.rebelscribe")
        new_project = self.project_manager.create_project_from_template(
            template_path=template_path,
            title="Template Based Project",
            author="Test Author",
            path=new_project_path
        )
        
        # Verify the new project was created
        self.assertIsNotNone(new_project)
        self.assertEqual(new_project.title, "Template Based Project")
        
        # Verify the document structure matches the template
        document_tree = self.project_manager.get_document_tree()
        folder_titles = [node["title"] for node in document_tree]
        
        self.assertIn("Custom Manuscript", folder_titles)
        self.assertIn("Custom Characters", folder_titles)
        self.assertIn("Custom Worldbuilding", folder_titles)
    
    def test_project_list(self):
        """Test getting a list of projects."""
        # Create multiple projects
        project1_path = self.create_test_project(title="Project 1")
        self.project_manager.close_project()
        
        project2_path = self.create_test_project(title="Project 2")
        self.project_manager.close_project()
        
        project3_path = self.create_test_project(title="Project 3")
        self.project_manager.close_project()
        
        # Get project list
        project_list = self.project_manager.get_project_list()
        
        # Verify the projects are in the list
        self.assertGreaterEqual(len(project_list), 3)
        
        project_titles = [project["title"] for project in project_list]
        self.assertIn("Project 1", project_titles)
        self.assertIn("Project 2", project_titles)
        self.assertIn("Project 3", project_titles)


if __name__ == "__main__":
    unittest.main()
