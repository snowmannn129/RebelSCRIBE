#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functional tests for export functionality.
"""

import os
import unittest
import tempfile
import shutil

from src.tests.functional.base_functional_test import BaseFunctionalTest
from src.backend.models.document import Document
from src.utils.export_formats import get_additional_available_formats


class TestExportFunctionality(BaseFunctionalTest):
    """Test case for export functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test project
        self.project_path = self.create_test_project(
            title="Export Test Project",
            author="Test Author"
        )
        self.project_manager.load_project(self.project_path)
        
        # Create a temporary directory for exports
        self.export_dir = os.path.join(self.test_dir, "exports")
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Create test documents
        self.create_test_document_structure()
    
    def create_test_document_structure(self):
        """Create a test document structure for export testing."""
        # Create a manuscript folder
        self.manuscript = self.project_manager.create_document(
            title="Manuscript",
            doc_type="folder"
        )
        
        # Create chapters
        self.chapter1 = self.project_manager.create_document(
            title="Chapter 1: Introduction",
            doc_type="folder",
            parent_id=self.manuscript.id
        )
        
        self.chapter2 = self.project_manager.create_document(
            title="Chapter 2: Development",
            doc_type="folder",
            parent_id=self.manuscript.id
        )
        
        self.chapter3 = self.project_manager.create_document(
            title="Chapter 3: Conclusion",
            doc_type="folder",
            parent_id=self.manuscript.id
        )
        
        # Create scenes for Chapter 1
        self.scene1_1 = self.project_manager.create_document(
            title="Scene 1.1",
            doc_type="scene",
            parent_id=self.chapter1.id,
            content="# Introduction\n\nThis is the first scene of the first chapter. "
                    "It introduces the main characters and setting.\n\n"
                    "\"Hello,\" said John, looking around the room.\n\n"
                    "Mary smiled. \"Welcome to our new home.\""
        )
        
        self.scene1_2 = self.project_manager.create_document(
            title="Scene 1.2",
            doc_type="scene",
            parent_id=self.chapter1.id,
            content="The next day, they began unpacking their belongings.\n\n"
                    "\"Where should I put these books?\" John asked.\n\n"
                    "\"On the shelf in the study,\" Mary replied."
        )
        
        # Create scenes for Chapter 2
        self.scene2_1 = self.project_manager.create_document(
            title="Scene 2.1",
            doc_type="scene",
            parent_id=self.chapter2.id,
            content="# Development\n\nWeeks passed as they settled into their new routine.\n\n"
                    "John found a job at the local newspaper, while Mary continued her research."
        )
        
        self.scene2_2 = self.project_manager.create_document(
            title="Scene 2.2",
            doc_type="scene",
            parent_id=self.chapter2.id,
            content="One evening, John came home with exciting news.\n\n"
                    "\"I've been promoted to editor!\" he announced.\n\n"
                    "Mary hugged him. \"That's wonderful!\""
        )
        
        # Create scenes for Chapter 3
        self.scene3_1 = self.project_manager.create_document(
            title="Scene 3.1",
            doc_type="scene",
            parent_id=self.chapter3.id,
            content="# Conclusion\n\nA year later, they hosted a housewarming party.\n\n"
                    "\"I can't believe how much has changed,\" John said, raising his glass.\n\n"
                    "\"To new beginnings,\" Mary toasted."
        )
        
        # Create character documents
        self.characters_folder = self.project_manager.create_document(
            title="Characters",
            doc_type="folder"
        )
        
        self.john_character = self.project_manager.create_document(
            title="John Smith",
            doc_type="character",
            parent_id=self.characters_folder.id,
            content="# John Smith\n\nAge: 35\nOccupation: Journalist\n\n"
                    "John is ambitious and hardworking, with a passion for uncovering the truth."
        )
        
        self.mary_character = self.project_manager.create_document(
            title="Mary Smith",
            doc_type="character",
            parent_id=self.characters_folder.id,
            content="# Mary Smith\n\nAge: 32\nOccupation: Researcher\n\n"
                    "Mary is intelligent and methodical, with a keen eye for detail."
        )
        
        # Create notes
        self.notes_folder = self.project_manager.create_document(
            title="Notes",
            doc_type="folder"
        )
        
        self.setting_note = self.project_manager.create_document(
            title="Setting",
            doc_type="note",
            parent_id=self.notes_folder.id,
            content="# Setting\n\nThe story takes place in a small coastal town in New England.\n\n"
                    "The town has a rich history and a close-knit community."
        )
        
        self.theme_note = self.project_manager.create_document(
            title="Themes",
            doc_type="note",
            parent_id=self.notes_folder.id,
            content="# Themes\n\n- New beginnings\n- Adaptation to change\n- Building a life together"
        )
        
        # Save all documents
        self.project_manager.save_project()
        self.document_manager.save_all_documents()
    
    def test_export_single_document_to_txt(self):
        """Test exporting a single document to TXT format."""
        # Export path
        export_path = os.path.join(self.export_dir, "scene1_1.txt")
        
        # Export the document
        success = self.export_service.export_document(
            document_id=self.scene1_1.id,
            export_path=export_path,
            format="txt"
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the content matches the original document
        self.assertIn("Introduction", content)
        self.assertIn("This is the first scene of the first chapter.", content)
        self.assertIn("\"Hello,\" said John", content)
    
    def test_export_single_document_to_html(self):
        """Test exporting a single document to HTML format."""
        # Export path
        export_path = os.path.join(self.export_dir, "scene1_1.html")
        
        # Export the document
        success = self.export_service.export_document(
            document_id=self.scene1_1.id,
            export_path=export_path,
            format="html"
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the content is properly formatted as HTML
        self.assertIn("<html", content.lower())
        self.assertIn("<body", content.lower())
        self.assertIn("<h1>Introduction</h1>", content)
        self.assertIn("<p>This is the first scene of the first chapter.", content)
        self.assertIn("\"Hello,\" said John", content)
    
    def test_export_single_document_to_markdown(self):
        """Test exporting a single document to Markdown format."""
        # Export path
        export_path = os.path.join(self.export_dir, "scene1_1.md")
        
        # Export the document
        success = self.export_service.export_document(
            document_id=self.scene1_1.id,
            export_path=export_path,
            format="markdown"
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the content is properly formatted as Markdown
        self.assertIn("# Introduction", content)
        self.assertIn("This is the first scene of the first chapter.", content)
        self.assertIn("\"Hello,\" said John", content)
    
    def test_export_chapter_to_txt(self):
        """Test exporting a chapter (folder with scenes) to TXT format."""
        # Export path
        export_path = os.path.join(self.export_dir, "chapter1.txt")
        
        # Export the chapter
        success = self.export_service.export_document(
            document_id=self.chapter1.id,
            export_path=export_path,
            format="txt",
            include_children=True
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the content includes all scenes from the chapter
        self.assertIn("Introduction", content)
        self.assertIn("This is the first scene of the first chapter.", content)
        self.assertIn("\"Hello,\" said John", content)
        self.assertIn("The next day, they began unpacking", content)
        self.assertIn("\"Where should I put these books?\"", content)
    
    def test_export_manuscript_to_txt(self):
        """Test exporting the entire manuscript to TXT format."""
        # Export path
        export_path = os.path.join(self.export_dir, "manuscript.txt")
        
        # Export the manuscript
        success = self.export_service.export_document(
            document_id=self.manuscript.id,
            export_path=export_path,
            format="txt",
            include_children=True,
            recursive=True
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the content includes all chapters and scenes
        self.assertIn("Introduction", content)
        self.assertIn("This is the first scene of the first chapter.", content)
        self.assertIn("Development", content)
        self.assertIn("Weeks passed as they settled into their new routine.", content)
        self.assertIn("Conclusion", content)
        self.assertIn("A year later, they hosted a housewarming party.", content)
    
    def test_export_project_to_pdf(self):
        """Test exporting the entire project to PDF format."""
        # Skip if PDF export is not available
        available_formats = get_additional_available_formats()
        if "pdf" not in available_formats:
            self.skipTest("PDF export not available")
        
        # Export path
        export_path = os.path.join(self.export_dir, "project.pdf")
        
        # Export the project
        success = self.export_service.export_project(
            export_path=export_path,
            format="pdf",
            include_front_matter=True,
            include_notes=False,
            include_characters=False
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify file size (PDF should have some content)
        file_size = os.path.getsize(export_path)
        self.assertGreater(file_size, 1000)  # PDF should be at least 1KB
    
    def test_export_project_to_epub(self):
        """Test exporting the entire project to EPUB format."""
        # Skip if EPUB export is not available
        available_formats = get_additional_available_formats()
        if "epub" not in available_formats:
            self.skipTest("EPUB export not available")
        
        # Export path
        export_path = os.path.join(self.export_dir, "project.epub")
        
        # Export the project
        success = self.export_service.export_project(
            export_path=export_path,
            format="epub",
            include_front_matter=True,
            include_notes=False,
            include_characters=False
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify file size (EPUB should have some content)
        file_size = os.path.getsize(export_path)
        self.assertGreater(file_size, 1000)  # EPUB should be at least 1KB
    
    def test_export_project_to_docx(self):
        """Test exporting the entire project to DOCX format."""
        # Skip if DOCX export is not available
        available_formats = get_additional_available_formats()
        if "docx" not in available_formats:
            self.skipTest("DOCX export not available")
        
        # Export path
        export_path = os.path.join(self.export_dir, "project.docx")
        
        # Export the project
        success = self.export_service.export_project(
            export_path=export_path,
            format="docx",
            include_front_matter=True,
            include_notes=False,
            include_characters=False
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify file size (DOCX should have some content)
        file_size = os.path.getsize(export_path)
        self.assertGreater(file_size, 1000)  # DOCX should be at least 1KB
    
    def test_export_with_custom_options(self):
        """Test exporting with custom options."""
        # Export path
        export_path = os.path.join(self.export_dir, "custom_export.txt")
        
        # Export with custom options
        success = self.export_service.export_project(
            export_path=export_path,
            format="txt",
            include_front_matter=True,
            include_notes=True,
            include_characters=True,
            title_page_template="# {title}\n\nBy {author}\n\n{date}",
            scene_separator="\n\n* * *\n\n",
            chapter_template="## {title}\n\n"
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that custom options were applied
        self.assertIn(f"# {self.project_manager.current_project.title}", content)
        self.assertIn(f"By {self.project_manager.current_project.author}", content)
        self.assertIn("* * *", content)
        self.assertIn("## Chapter 1: Introduction", content)
    
    def test_export_with_filtering(self):
        """Test exporting with document filtering."""
        # Export path
        export_path = os.path.join(self.export_dir, "filtered_export.txt")
        
        # Export with filtering (only Chapter 1 and 3)
        success = self.export_service.export_project(
            export_path=export_path,
            format="txt",
            include_front_matter=False,
            document_filter=[self.chapter1.id, self.chapter3.id]
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that filtering was applied
        self.assertIn("Introduction", content)
        self.assertIn("Conclusion", content)
        self.assertNotIn("Development", content)
    
    def test_export_with_metadata(self):
        """Test exporting with metadata."""
        # Export path
        export_path = os.path.join(self.export_dir, "metadata_export.txt")
        
        # Set project metadata
        self.project_manager.current_project.metadata = {
            "genre": "Fiction",
            "word_count_goal": 50000,
            "status": "Draft"
        }
        
        # Export with metadata
        success = self.export_service.export_project(
            export_path=export_path,
            format="txt",
            include_front_matter=True,
            include_metadata=True
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that metadata was included
        self.assertIn("Genre: Fiction", content)
        self.assertIn("Status: Draft", content)
    
    def test_export_with_custom_stylesheet(self):
        """Test exporting with a custom stylesheet."""
        # Skip if HTML export is not available
        available_formats = get_additional_available_formats()
        if "html" not in available_formats:
            self.skipTest("HTML export not available")
        
        # Export path
        export_path = os.path.join(self.export_dir, "styled_export.html")
        
        # Create a custom stylesheet
        stylesheet = """
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 2em;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
        }
        p {
            margin-bottom: 1.2em;
        }
        """
        
        # Export with custom stylesheet
        success = self.export_service.export_project(
            export_path=export_path,
            format="html",
            include_front_matter=True,
            custom_stylesheet=stylesheet
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the stylesheet was included
        self.assertIn("font-family: Arial, sans-serif", content)
        self.assertIn("color: #2c3e50", content)
    
    def test_export_with_table_of_contents(self):
        """Test exporting with a table of contents."""
        # Export path
        export_path = os.path.join(self.export_dir, "toc_export.txt")
        
        # Export with table of contents
        success = self.export_service.export_project(
            export_path=export_path,
            format="txt",
            include_front_matter=True,
            include_table_of_contents=True
        )
        
        # Verify export was successful
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the table of contents was included
        self.assertIn("Table of Contents", content)
        self.assertIn("Chapter 1: Introduction", content)
        self.assertIn("Chapter 2: Development", content)
        self.assertIn("Chapter 3: Conclusion", content)
    
    def test_export_with_invalid_format(self):
        """Test exporting with an invalid format."""
        # Export path
        export_path = os.path.join(self.export_dir, "invalid_export.xyz")
        
        # Try to export with an invalid format
        with self.assertRaises(ValueError):
            self.export_service.export_project(
                export_path=export_path,
                format="xyz"  # Invalid format
            )
    
    def test_export_nonexistent_document(self):
        """Test exporting a nonexistent document."""
        # Export path
        export_path = os.path.join(self.export_dir, "nonexistent.txt")
        
        # Try to export a nonexistent document
        success = self.export_service.export_document(
            document_id="nonexistent_id",
            export_path=export_path,
            format="txt"
        )
        
        # Verify export failed
        self.assertFalse(success)
        self.assertFalse(os.path.exists(export_path))
    
    def test_export_to_invalid_path(self):
        """Test exporting to an invalid path."""
        # Invalid export path (directory doesn't exist)
        export_path = os.path.join("/nonexistent/directory", "export.txt")
        
        # Try to export to an invalid path
        success = self.export_service.export_document(
            document_id=self.scene1_1.id,
            export_path=export_path,
            format="txt"
        )
        
        # Verify export failed
        self.assertFalse(success)
    
    def test_export_all_formats(self):
        """Test exporting to all available formats."""
        # Get all available export formats
        available_formats = get_additional_available_formats()
        
        for format_name in available_formats:
            # Skip formats that require special handling
            if format_name in ["custom"]:
                continue
                
            # Export path
            export_path = os.path.join(self.export_dir, f"all_formats.{format_name}")
            
            # Export to this format
            success = self.export_service.export_document(
                document_id=self.scene1_1.id,
                export_path=export_path,
                format=format_name
            )
            
            # Verify export was successful
            self.assertTrue(success, f"Export to {format_name} format failed")
            self.assertTrue(os.path.exists(export_path), f"Export file for {format_name} format not found")
            
            # Verify file size
            file_size = os.path.getsize(export_path)
            self.assertGreater(file_size, 0, f"Export file for {format_name} format is empty")


if __name__ == "__main__":
    unittest.main()
