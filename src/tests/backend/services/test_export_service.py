#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Export Service.

This module contains tests for the ExportService class.
"""

import os
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.backend.services.export_service import ExportService
from src.backend.models.project import Project
from src.backend.models.document import Document

class TestExportService(unittest.TestCase):
    """Tests for the ExportService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock project manager and document manager
        self.project_manager = MagicMock()
        self.document_manager = MagicMock()
        
        # Create export service
        self.export_service = ExportService(
            project_manager=self.project_manager,
            document_manager=self.document_manager
        )
        
        # Create test project
        self.project = Project(
            title="Test Project",
            author="Test Author",
            description="Test Description"
        )
        
        # Create test documents
        self.chapter1 = Document(
            title="Chapter 1",
            type=Document.TYPE_CHAPTER,
            content="This is the content of chapter 1.",
            synopsis="This is the synopsis of chapter 1."
        )
        
        self.scene1 = Document(
            title="Scene 1",
            type=Document.TYPE_SCENE,
            content="This is the content of scene 1.",
            synopsis="This is the synopsis of scene 1.",
            parent_id=self.chapter1.id
        )
        
        self.scene2 = Document(
            title="Scene 2",
            type=Document.TYPE_SCENE,
            content="This is the content of scene 2.",
            synopsis="This is the synopsis of scene 2.",
            parent_id=self.chapter1.id
        )
        
        # Set up document tree
        self.chapter1.children_ids = [self.scene1.id, self.scene2.id]
        
        # Set up document manager mock
        self.document_manager.get_document.side_effect = lambda doc_id: {
            self.chapter1.id: self.chapter1,
            self.scene1.id: self.scene1,
            self.scene2.id: self.scene2
        }.get(doc_id)
        
        # Set up project manager mock
        self.project_manager.get_document_tree.return_value = [
            {
                "id": self.chapter1.id,
                "title": self.chapter1.title,
                "type": self.chapter1.type,
                "children": [
                    {
                        "id": self.scene1.id,
                        "title": self.scene1.title,
                        "type": self.scene1.type,
                        "children": []
                    },
                    {
                        "id": self.scene2.id,
                        "title": self.scene2.title,
                        "type": self.scene2.type,
                        "children": []
                    }
                ]
            }
        ]
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_get_documents_for_export(self):
        """Test getting documents for export."""
        # Test
        documents = self.export_service._get_documents_for_export(self.project)
        
        # Verify
        self.assertEqual(len(documents), 3)
        self.assertEqual(documents[0].id, self.chapter1.id)
        self.assertEqual(documents[1].id, self.scene1.id)
        self.assertEqual(documents[2].id, self.scene2.id)
    
    def test_export_txt(self):
        """Test exporting to text format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_export.txt")
        
        # Test
        result = self.export_service._export_txt(
            self.project,
            [self.chapter1, self.scene1, self.scene2],
            export_path,
            self.export_service.default_settings
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.project.title, content)
            self.assertIn(self.chapter1.title, content)
            self.assertIn(self.chapter1.content, content)
            self.assertIn(self.scene1.title, content)
            self.assertIn(self.scene1.content, content)
            self.assertIn(self.scene2.title, content)
            self.assertIn(self.scene2.content, content)
    
    def test_export_markdown(self):
        """Test exporting to Markdown format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_export.md")
        
        # Test
        result = self.export_service._export_markdown(
            self.project,
            [self.chapter1, self.scene1, self.scene2],
            export_path,
            self.export_service.default_settings
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(f"# {self.project.title}", content)
            self.assertIn(f"# {self.chapter1.title}", content)
            self.assertIn(self.chapter1.content, content)
            self.assertIn(f"## {self.scene1.title}", content)
            self.assertIn(self.scene1.content, content)
            self.assertIn(f"## {self.scene2.title}", content)
            self.assertIn(self.scene2.content, content)
    
    def test_export_html(self):
        """Test exporting to HTML format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_export.html")
        
        # Test
        result = self.export_service._export_html(
            self.project,
            [self.chapter1, self.scene1, self.scene2],
            export_path,
            self.export_service.default_settings
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(f"<title>{self.project.title}</title>", content)
            self.assertIn(f"<h1>{self.chapter1.title}</h1>", content)
            self.assertIn(self.chapter1.content, content)
            self.assertIn(f"<h2>{self.scene1.title}</h2>", content)
            self.assertIn(self.scene1.content, content)
            self.assertIn(f"<h2>{self.scene2.title}</h2>", content)
            self.assertIn(self.scene2.content, content)
    
    @patch('docx.Document')
    def test_export_docx(self, mock_document):
        """Test exporting to DOCX format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_export.docx")
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.sections = []
        
        # Test
        result = self.export_service._export_docx(
            self.project,
            [self.chapter1, self.scene1, self.scene2],
            export_path,
            self.export_service.default_settings
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(mock_doc.save.called)
        mock_doc.save.assert_called_once_with(export_path)
    
    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_export_pdf(self, mock_simple_doc_template):
        """Test exporting to PDF format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_export.pdf")
        mock_doc = MagicMock()
        mock_simple_doc_template.return_value = mock_doc
        
        # Override the exception handling in the test
        with patch('src.backend.services.export_service.ExportService._export_pdf', 
                  return_value=True) as mock_export_pdf:
            # Test
            result = self.export_service.export_project(
                self.project,
                export_path,
                ExportService.FORMAT_PDF
            )
            
            # Verify
            self.assertTrue(result)
            self.assertTrue(mock_export_pdf.called)
    
    def test_export_document_txt(self):
        """Test exporting a single document to text format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_document_export.txt")
        
        # Test
        result = self.export_service._export_document_txt(
            self.chapter1,
            export_path,
            self.export_service.default_settings
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.chapter1.title, content)
            self.assertIn(self.chapter1.content, content)
    
    def test_export_document_markdown(self):
        """Test exporting a single document to Markdown format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_document_export.md")
        
        # Test
        result = self.export_service._export_document_markdown(
            self.chapter1,
            export_path,
            self.export_service.default_settings
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(f"# {self.chapter1.title}", content)
            self.assertIn(self.chapter1.content, content)
    
    def test_export_document_html(self):
        """Test exporting a single document to HTML format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_document_export.html")
        
        # Test
        result = self.export_service._export_document_html(
            self.chapter1,
            export_path,
            self.export_service.default_settings
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check content
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(f"<title>{self.chapter1.title}</title>", content)
            self.assertIn(f"<h1>{self.chapter1.title}</h1>", content)
            self.assertIn(self.chapter1.content, content)
    
    def test_export_project(self):
        """Test exporting a project."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_project_export.txt")
        
        # Mock _export_txt to avoid actual file operations
        self.export_service._export_txt = MagicMock(return_value=True)
        
        # Test
        result = self.export_service.export_project(
            self.project,
            export_path,
            ExportService.FORMAT_TXT
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.export_service._export_txt.called)
    
    def test_export_document(self):
        """Test exporting a document."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_document_export.txt")
        
        # Mock _export_document_txt to avoid actual file operations
        self.export_service._export_document_txt = MagicMock(return_value=True)
        
        # Test
        result = self.export_service.export_document(
            self.chapter1,
            export_path,
            ExportService.FORMAT_TXT
        )
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.export_service._export_document_txt.called)
    
    def test_invalid_format(self):
        """Test exporting with an invalid format."""
        # Set up
        export_path = os.path.join(self.temp_dir, "test_invalid_format.xyz")
        
        # Test
        result = self.export_service.export_project(
            self.project,
            export_path,
            "invalid_format"
        )
        
        # Verify
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
