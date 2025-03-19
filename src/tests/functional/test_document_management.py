#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functional tests for document management.
"""

import os
import unittest

from src.tests.functional.base_functional_test import BaseFunctionalTest
from src.backend.models.document import Document


class TestDocumentManagement(BaseFunctionalTest):
    """Test case for document management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test project
        self.project_path = self.create_test_project()
        self.project_manager.load_project(self.project_path)
    
    def test_create_and_load_document(self):
        """Test creating and loading a document."""
        # Create a document
        document_id = self.create_test_document(
            title="Test Document",
            content="This is a test document."
        )
        
        # Load the document
        document = self.load_test_document(document_id)
        
        # Verify the document
        self.assertIsNotNone(document)
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.content, "This is a test document.")
    
    def test_update_document(self):
        """Test updating a document."""
        # Create a document
        document_id = self.create_test_document()
        
        # Load the document
        document = self.load_test_document(document_id)
        
        # Update the document
        document.title = "Updated Title"
        document.content = "Updated content."
        self.document_manager.save_document(document)
        
        # Load the document again
        updated_document = self.load_test_document(document_id)
        
        # Verify the document was updated
        self.assertEqual(updated_document.title, "Updated Title")
        self.assertEqual(updated_document.content, "Updated content.")
    
    def test_delete_document(self):
        """Test deleting a document."""
        # Create a document
        document_id = self.create_test_document()
        
        # Delete the document
        self.document_manager.delete_document(document_id)
        
        # Try to load the document
        document = self.load_test_document(document_id)
        
        # Verify the document was deleted
        self.assertIsNone(document)
    
    def test_create_multiple_documents(self):
        """Test creating multiple documents."""
        # Create documents
        document_ids = []
        for i in range(5):
            document_id = self.create_test_document(
                title=f"Document {i+1}",
                content=f"Content for document {i+1}."
            )
            document_ids.append(document_id)
        
        # Get all documents
        documents = self.document_manager.get_all_documents()
        
        # Verify the documents
        self.assertEqual(len(documents), 5)
        document_titles = [doc.title for doc in documents]
        for i in range(5):
            self.assertIn(f"Document {i+1}", document_titles)
    
    def test_document_metadata(self):
        """Test document metadata."""
        # Create a document with metadata
        document = Document(
            title="Metadata Test",
            content="Testing metadata.",
            metadata={
                "author": "Test Author",
                "tags": ["test", "metadata"],
                "status": "draft"
            }
        )
        self.document_manager.add_document(document)
        
        # Load the document
        loaded_document = self.load_test_document(document.id)
        
        # Verify the metadata
        self.assertEqual(loaded_document.metadata["author"], "Test Author")
        self.assertEqual(loaded_document.metadata["tags"], ["test", "metadata"])
        self.assertEqual(loaded_document.metadata["status"], "draft")
    
    def test_document_versioning(self):
        """Test document versioning."""
        # Create a document
        document_id = self.create_test_document(
            title="Version Test",
            content="Initial version."
        )
        
        # Update the document multiple times
        document = self.load_test_document(document_id)
        document.content = "Second version."
        self.document_manager.save_document(document)
        
        document = self.load_test_document(document_id)
        document.content = "Third version."
        self.document_manager.save_document(document)
        
        # Get document versions
        versions = self.document_manager.get_document_versions(document_id)
        
        # Verify the versions
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].content, "Initial version.")
        self.assertEqual(versions[1].content, "Second version.")
        self.assertEqual(versions[2].content, "Third version.")
    
    def test_document_search(self):
        """Test searching for documents."""
        # Create documents with different content
        self.create_test_document(
            title="Apple Document",
            content="This document is about apples."
        )
        self.create_test_document(
            title="Banana Document",
            content="This document is about bananas."
        )
        self.create_test_document(
            title="Orange Document",
            content="This document is about oranges."
        )
        
        # Search for documents containing "apple"
        results = self.search_service.search_text("apple")
        
        # Verify the search results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Apple Document")
        
        # Search for documents containing "document"
        results = self.search_service.search_text("document")
        
        # Verify the search results
        self.assertEqual(len(results), 3)
    
    def test_document_export(self):
        """Test exporting a document."""
        # Create a document
        document_id = self.create_test_document(
            title="Export Test",
            content="This document will be exported."
        )
        
        # Export the document to a text file
        export_path = os.path.join(self.test_dir, "export_test.txt")
        self.export_service.export_document(
            document_id=document_id,
            export_path=export_path,
            format="txt"
        )
        
        # Verify the exported file
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("This document will be exported.", content)


if __name__ == "__main__":
    unittest.main()
