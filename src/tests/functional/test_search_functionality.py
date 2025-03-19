#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functional tests for search functionality.
"""

import os
import unittest

from src.tests.functional.base_functional_test import BaseFunctionalTest
from src.backend.models.document import Document


class TestSearchFunctionality(BaseFunctionalTest):
    """Test case for search functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test project
        self.project_path = self.create_test_project()
        self.project_manager.load_project(self.project_path)
        
        # Create test documents with different content
        self.doc1_id = self.create_test_document(
            title="Apple Document",
            content="This document is about apples. Apples are fruits that grow on trees."
        )
        
        self.doc2_id = self.create_test_document(
            title="Banana Document",
            content="This document is about bananas. Bananas are yellow fruits."
        )
        
        self.doc3_id = self.create_test_document(
            title="Orange Document",
            content="This document is about oranges. Oranges are citrus fruits."
        )
        
        self.doc4_id = self.create_test_document(
            title="Fruit Comparison",
            content="Apples, bananas, and oranges are all fruits. Apples are usually red or green. "
                    "Bananas are yellow. Oranges are orange."
        )
        
        # Create a document with metadata
        doc5 = Document(
            title="Fruit Study",
            content="A scientific study of various fruits.",
            metadata={
                "tags": ["fruit", "research", "science"],
                "status": "draft",
                "author": "Dr. Botanist"
            }
        )
        self.document_manager.add_document(doc5)
        self.doc5_id = doc5.id
    
    def test_basic_text_search(self):
        """Test basic text search functionality."""
        # Search for documents containing "apple"
        results = self.search_service.search_text("apple")
        
        # Verify the search results
        self.assertEqual(len(results), 2)
        result_titles = [doc.title for doc in results]
        self.assertIn("Apple Document", result_titles)
        self.assertIn("Fruit Comparison", result_titles)
    
    def test_case_insensitive_search(self):
        """Test case-insensitive search."""
        # Search for documents containing "BANANA" (uppercase)
        results = self.search_service.search_text("BANANA")
        
        # Verify the search results
        self.assertEqual(len(results), 2)
        result_titles = [doc.title for doc in results]
        self.assertIn("Banana Document", result_titles)
        self.assertIn("Fruit Comparison", result_titles)
    
    def test_multiple_term_search(self):
        """Test searching for multiple terms."""
        # Search for documents containing both "apple" and "banana"
        results = self.search_service.search_text("apple banana")
        
        # Verify the search results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Fruit Comparison")
    
    def test_phrase_search(self):
        """Test searching for exact phrases."""
        # Search for the exact phrase "about oranges"
        results = self.search_service.search_phrase("about oranges")
        
        # Verify the search results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Orange Document")
    
    def test_wildcard_search(self):
        """Test wildcard search functionality."""
        # Search for documents containing words starting with "app"
        results = self.search_service.search_pattern("app*")
        
        # Verify the search results
        self.assertEqual(len(results), 2)
        result_titles = [doc.title for doc in results]
        self.assertIn("Apple Document", result_titles)
        self.assertIn("Fruit Comparison", result_titles)
    
    def test_regex_search(self):
        """Test regex search functionality."""
        # Search for documents containing words matching the pattern "or[a-z]nge"
        results = self.search_service.search_regex("or[a-z]nge")
        
        # Verify the search results
        self.assertEqual(len(results), 2)
        result_titles = [doc.title for doc in results]
        self.assertIn("Orange Document", result_titles)
        self.assertIn("Fruit Comparison", result_titles)
    
    def test_metadata_search(self):
        """Test searching in document metadata."""
        # Search for documents with the tag "research"
        results = self.search_service.search_metadata("tags", "research")
        
        # Verify the search results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Fruit Study")
    
    def test_combined_search(self):
        """Test combining text and metadata search."""
        # Search for documents containing "fruit" and having the "draft" status
        text_results = self.search_service.search_text("fruit")
        metadata_results = self.search_service.search_metadata("status", "draft")
        
        # Combine results (documents that match both criteria)
        combined_results = [doc for doc in text_results if doc in metadata_results]
        
        # Verify the combined search results
        self.assertEqual(len(combined_results), 1)
        self.assertEqual(combined_results[0].title, "Fruit Study")
    
    def test_search_with_filters(self):
        """Test search with filters."""
        # Search for documents containing "fruit" with title filter
        results = self.search_service.search_text("fruit", title_filter="Study")
        
        # Verify the search results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Fruit Study")
    
    def test_search_with_sorting(self):
        """Test search with sorting."""
        # Search for documents containing "fruit" and sort by title
        results = self.search_service.search_text("fruit", sort_by="title")
        
        # Verify the search results are sorted by title
        self.assertGreaterEqual(len(results), 2)
        titles = [doc.title for doc in results]
        sorted_titles = sorted(titles)
        self.assertEqual(titles, sorted_titles)
    
    def test_search_highlighting(self):
        """Test search result highlighting."""
        # Search for documents containing "apple" with highlighting
        results = self.search_service.search_text("apple", highlight=True)
        
        # Verify the search results contain highlighting information
        self.assertGreaterEqual(len(results), 1)
        
        # Check that the first result has highlighting data
        first_result = results[0]
        self.assertTrue(hasattr(first_result, 'highlights') or 'highlights' in first_result.__dict__)
        
        # If the search service returns highlights as a separate structure,
        # adjust this test accordingly
        if hasattr(first_result, 'highlights'):
            self.assertGreaterEqual(len(first_result.highlights), 1)
    
    def test_search_with_pagination(self):
        """Test search with pagination."""
        # Create more documents to ensure pagination
        for i in range(10):
            self.create_test_document(
                title=f"Pagination Test {i}",
                content=f"This is document {i} for pagination testing. It contains the word fruit."
            )
        
        # Search for documents containing "fruit" with pagination
        page1_results = self.search_service.search_text("fruit", page=1, page_size=5)
        page2_results = self.search_service.search_text("fruit", page=2, page_size=5)
        
        # Verify pagination works correctly
        self.assertEqual(len(page1_results), 5)
        self.assertGreaterEqual(len(page2_results), 1)
        
        # Verify the results on different pages are different
        page1_ids = [doc.id for doc in page1_results]
        page2_ids = [doc.id for doc in page2_results]
        
        # Check that there's no overlap between pages
        self.assertEqual(len(set(page1_ids).intersection(set(page2_ids))), 0)
    
    def test_empty_search_results(self):
        """Test search with no matching results."""
        # Search for a term that doesn't exist in any document
        results = self.search_service.search_text("xylophone")
        
        # Verify the search returns an empty list
        self.assertEqual(len(results), 0)
    
    def test_search_in_specific_document_types(self):
        """Test searching in specific document types."""
        # Create documents of different types
        note_doc = Document(
            title="Fruit Note",
            content="Notes about various fruits.",
            doc_type="note"
        )
        self.document_manager.add_document(note_doc)
        
        character_doc = Document(
            title="Fruit Vendor Character",
            content="A character who sells fruits.",
            doc_type="character"
        )
        self.document_manager.add_document(character_doc)
        
        # Search for "fruit" only in notes
        results = self.search_service.search_text("fruit", doc_type_filter="note")
        
        # Verify the search results only include notes
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Fruit Note")
    
    def test_search_performance(self):
        """Test search performance with a large number of documents."""
        # Skip this test if not running performance tests
        if not getattr(self, 'run_performance_tests', False):
            self.skipTest("Skipping performance test")
        
        # Create a large number of documents
        for i in range(100):
            content = f"Document {i} content. " * 100  # ~2KB per document
            self.create_test_document(
                title=f"Performance Test {i}",
                content=content
            )
        
        # Add the search term to a few documents
        for i in range(90, 100):
            content = f"Document {i} content with searchterm123. " * 100
            self.create_test_document(
                title=f"Performance Test {i} with Term",
                content=content
            )
        
        # Measure search time
        import time
        start_time = time.time()
        
        # Search for a specific term
        results = self.search_service.search_text("searchterm123")
        
        end_time = time.time()
        search_time = end_time - start_time
        
        # Verify search returns correct results
        self.assertEqual(len(results), 10)
        
        # Verify search completes within a reasonable time (adjust threshold as needed)
        self.assertLess(search_time, 1.0)  # Should complete in less than 1 second


if __name__ == "__main__":
    unittest.main()
