#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance tests for document operations.

This module contains performance tests for document-related operations
to ensure they meet performance requirements.
"""

import os
import tempfile
import time
import json
import pytest
from unittest.mock import patch, MagicMock

from src.backend.models.document import Document
from src.backend.services.document_manager import DocumentManager
from src.backend.services.project_manager import ProjectManager
from src.utils.config_manager import ConfigManager


class TestDocumentPerformance:
    """Performance tests for document operations."""
    
    @pytest.fixture
    def setup(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test configuration
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.config = ConfigManager(self.config_path)
        
        # Set up the project manager
        self.project_manager = ProjectManager(self.config)
        
        # Set up the document manager
        self.document_manager = DocumentManager(None)
        
        # Create a project
        self.project_path = os.path.join(self.test_dir, "perf_test_project.rebelscribe")
        self.project = self.project_manager.create_project(
            title="Performance Test Project",
            author="Test Author",
            path=self.project_path
        )
        
        # Set project path for document manager
        self.document_manager.set_project_path(os.path.dirname(self.project_path))
        
        yield
        
        # Clean up
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_document_creation_performance(self, setup, benchmark):
        """Test document creation performance."""
        def create_document():
            return self.document_manager.create_document(
                title="Performance Test Document",
                content="This is a test document for performance testing."
            )
        
        # Benchmark document creation
        result = benchmark(create_document)
        
        # Verify the document was created
        assert result is not None
        assert result.title == "Performance Test Document"
    
    def test_document_save_performance(self, setup, benchmark):
        """Test document saving performance."""
        # Create a document
        doc = self.document_manager.create_document(
            title="Save Performance Test",
            content="This is a test document for save performance testing."
        )
        
        def save_document():
            return self.document_manager.save_document(doc)
        
        # Benchmark document saving
        benchmark(save_document)
    
    def test_document_load_performance(self, setup, benchmark):
        """Test document loading performance."""
        # Create a document
        doc = self.document_manager.create_document(
            title="Load Performance Test",
            content="This is a test document for load performance testing."
        )
        
        # Save the document to get its path
        self.document_manager.save_document(doc)
        doc_path = doc.path
        
        def load_document():
            return self.document_manager.load_document(doc_path)
        
        # Benchmark document loading
        result = benchmark(load_document)
        
        # Verify the document was loaded
        assert result is not None
        assert result.title == "Load Performance Test"
    
    def test_large_document_performance(self, setup, benchmark):
        """Test performance with large documents."""
        # Create a large document (100KB of text)
        large_content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 1000
        
        # Create the document
        doc = Document(title="Large Document", content=large_content)
        
        # Save the document
        doc_path = os.path.join(self.test_dir, "large_doc.json")
        with open(doc_path, 'w') as f:
            json.dump(doc.to_dict(), f)
        
        def load_large_document():
            with open(doc_path, 'r') as f:
                data = json.load(f)
            return Document.from_dict(data)
        
        # Benchmark large document loading
        result = benchmark(load_large_document)
        
        # Verify the document was loaded
        assert result is not None
        assert result.title == "Large Document"
        assert len(result.content) == len(large_content)
    
    def test_multiple_document_operations(self, setup, benchmark):
        """Test performance of multiple document operations."""
        def create_and_save_multiple_documents():
            docs = []
            for i in range(10):
                doc = self.document_manager.create_document(
                    title=f"Document {i}",
                    content=f"Content for document {i}"
                )
                self.document_manager.save_document(doc)
                docs.append(doc)
            return docs
        
        # Benchmark multiple document operations
        results = benchmark(create_and_save_multiple_documents)
        
        # Verify the documents were created and saved
        assert len(results) == 10
        for i, doc in enumerate(results):
            assert doc.title == f"Document {i}"
    
    def test_document_search_performance(self, setup, benchmark):
        """Test document search performance."""
        # Create multiple documents with searchable content
        docs = []
        for i in range(20):
            content = f"Document {i} content with searchable terms like apple, banana, and cherry."
            if i % 5 == 0:
                content += " This document contains the special term 'performance'."
            
            doc = self.document_manager.create_document(
                title=f"Search Document {i}",
                content=content
            )
            self.document_manager.save_document(doc)
            docs.append(doc)
        
        # Mock the search service
        mock_search_service = MagicMock()
        mock_search_service.search_documents.return_value = [
            doc for doc in docs if "performance" in doc.content
        ]
        
        def search_documents():
            return mock_search_service.search_documents(
                project=self.project,
                query="performance",
                case_sensitive=False,
                whole_word=False
            )
        
        # Benchmark document search
        results = benchmark(search_documents)
        
        # Verify the search results
        assert len(results) == 4  # Every 5th document contains 'performance'
    
    def test_document_update_performance(self, setup, benchmark):
        """Test document update performance."""
        # Create a document
        doc = self.document_manager.create_document(
            title="Update Performance Test",
            content="Original content for update performance testing."
        )
        
        # Save the document
        self.document_manager.save_document(doc)
        
        def update_document():
            doc.content = "Updated content for performance testing."
            return self.document_manager.save_document(doc)
        
        # Benchmark document updating
        benchmark(update_document)
        
        # Verify the document was updated
        updated_doc = self.document_manager.load_document(doc.path)
        assert updated_doc.content == "Updated content for performance testing."
    
    def test_document_versioning_performance(self, setup, benchmark):
        """Test document versioning performance."""
        # Create a document
        doc = self.document_manager.create_document(
            title="Versioning Performance Test",
            content="Original content for versioning performance testing."
        )
        
        # Save the document
        self.document_manager.save_document(doc)
        
        # Mock the versioning method
        original_create_version = self.document_manager.create_version
        self.document_manager.create_version = MagicMock()
        self.document_manager.create_version.return_value = "version1"
        
        def create_document_version():
            return self.document_manager.create_version(doc)
        
        try:
            # Benchmark document versioning
            version_id = benchmark(create_document_version)
            
            # Verify the version was created
            assert version_id == "version1"
            assert self.document_manager.create_version.call_count > 0
        finally:
            # Restore original method
            self.document_manager.create_version = original_create_version


if __name__ == '__main__':
    pytest.main(['-v', __file__])
