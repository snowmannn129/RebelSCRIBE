#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the SearchService.

This module contains tests for the SearchService class, which provides
functionality for searching through documents in a project.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.backend.services.search_service import SearchService, SearchResult
from src.backend.models.document import Document


class TestSearchService(unittest.TestCase):
    """Test cases for the SearchService class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the config
        self.config_patcher = patch('src.backend.services.search_service.get_config')
        self.mock_config = self.config_patcher.start()
        # Make sure the mock returns a dictionary with the expected structure
        self.mock_config.return_value = {
            'search': {
                'context_size': 30,
                'max_results': 50
            }
        }
        
        # Create test documents
        self.documents = {}
        
        # Document 1: Scene with specific content
        self.doc1 = Document(
            id="doc1",
            title="Chapter 1: Introduction",
            type=Document.TYPE_SCENE,
            content="This is the first chapter of the novel. It introduces the main character John Smith, who lives in New York City."
        )
        self.doc1.add_tag("chapter")
        self.doc1.add_tag("introduction")
        self.doc1.set_metadata("pov_character", "John Smith")
        self.doc1.set_metadata("location", "New York")
        self.documents[self.doc1.id] = self.doc1
        
        # Document 2: Scene with different content
        self.doc2 = Document(
            id="doc2",
            title="Chapter 2: The Journey",
            type=Document.TYPE_SCENE,
            content="John Smith embarks on a journey to find his long-lost sister. He travels to Boston by train."
        )
        self.doc2.add_tag("chapter")
        self.doc2.add_tag("journey")
        self.doc2.set_metadata("pov_character", "John Smith")
        self.doc2.set_metadata("location", "Boston")
        self.documents[self.doc2.id] = self.doc2
        
        # Document 3: Character profile
        self.doc3 = Document(
            id="doc3",
            title="Character: John Smith",
            type=Document.TYPE_CHARACTER,
            content="John Smith is a 35-year-old detective from New York. He has a sister named Mary who disappeared 10 years ago."
        )
        self.doc3.add_tag("character")
        self.doc3.add_tag("protagonist")
        self.doc3.set_metadata("age", 35)
        self.doc3.set_metadata("occupation", "detective")
        self.documents[self.doc3.id] = self.doc3
        
        # Document 4: Location profile
        self.doc4 = Document(
            id="doc4",
            title="Location: New York",
            type=Document.TYPE_LOCATION,
            content="New York City is where John Smith lives and works. It's a bustling metropolis with millions of people."
        )
        self.doc4.add_tag("location")
        self.doc4.add_tag("city")
        self.doc4.set_metadata("population", "8.4 million")
        self.doc4.set_metadata("country", "USA")
        self.documents[self.doc4.id] = self.doc4
        
        # Create the search service
        self.search_service = SearchService(self.documents)

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Stop the config patcher
        self.config_patcher.stop()

    def test_init(self):
        """Test initialization of SearchService."""
        # Test with documents
        self.assertEqual(self.search_service.documents, self.documents)
        self.assertEqual(self.search_service.context_size, 30)
        self.assertEqual(self.search_service.max_results, 50)
        
        # Test without documents
        search_service_no_docs = SearchService()
        self.assertEqual(search_service_no_docs.documents, {})
        self.assertEqual(search_service_no_docs.context_size, 30)
        self.assertEqual(search_service_no_docs.max_results, 50)

    def test_set_documents(self):
        """Test setting documents."""
        # Create a new search service without documents
        search_service = SearchService()
        self.assertEqual(search_service.documents, {})
        
        # Set documents
        search_service.set_documents(self.documents)
        self.assertEqual(search_service.documents, self.documents)
        
        # Set different documents
        new_documents = {"new_doc": Document(id="new_doc", title="New Document")}
        search_service.set_documents(new_documents)
        self.assertEqual(search_service.documents, new_documents)

    def test_search_text_basic(self):
        """Test basic text search functionality."""
        # Search for a term that appears in multiple documents
        results = self.search_service.search_text("John Smith")
        
        # Should find matches in all documents
        self.assertEqual(len(results), 4)
        
        # Verify result properties
        for result in results:
            self.assertIsInstance(result, SearchResult)
            self.assertIn(result.document_id, self.documents)
            self.assertEqual(result.document_title, self.documents[result.document_id].title)
            self.assertEqual(result.document_type, self.documents[result.document_id].type)
            self.assertEqual(result.match_text, "John Smith")
            self.assertFalse(result.metadata_match)
            self.assertFalse(result.tag_match)
            
        # Search for a term that appears in only one document
        results = self.search_service.search_text("long-lost sister")
        
        # Should find match in doc2 only
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc2")
        self.assertEqual(results[0].match_text, "long-lost sister")

    def test_search_text_case_sensitive(self):
        """Test case-sensitive text search."""
        # Case-insensitive search (default)
        results_insensitive = self.search_service.search_text("john smith")
        self.assertEqual(len(results_insensitive), 4)
        
        # Case-sensitive search
        results_sensitive = self.search_service.search_text("john smith", case_sensitive=True)
        self.assertEqual(len(results_sensitive), 0)
        
        results_sensitive = self.search_service.search_text("John Smith", case_sensitive=True)
        self.assertEqual(len(results_sensitive), 4)

    def test_search_text_whole_word(self):
        """Test whole word text search."""
        # Partial word search (default)
        results_partial = self.search_service.search_text("York")
        self.assertEqual(len(results_partial), 3)
        
        # Whole word search
        results_whole = self.search_service.search_text("York", whole_word=True)
        self.assertEqual(len(results_whole), 0)
        
        results_whole = self.search_service.search_text("New York", whole_word=True)
        self.assertEqual(len(results_whole), 2)

    def test_search_text_document_types(self):
        """Test text search with document type filtering."""
        # Search in all document types (default)
        results_all = self.search_service.search_text("John Smith")
        self.assertEqual(len(results_all), 4)
        
        # Search only in scenes
        results_scenes = self.search_service.search_text(
            "John Smith", 
            document_types=[Document.TYPE_SCENE]
        )
        self.assertEqual(len(results_scenes), 2)
        for result in results_scenes:
            self.assertEqual(result.document_type, Document.TYPE_SCENE)
        
        # Search in character and location documents
        results_char_loc = self.search_service.search_text(
            "John Smith", 
            document_types=[Document.TYPE_CHARACTER, Document.TYPE_LOCATION]
        )
        self.assertEqual(len(results_char_loc), 2)
        for result in results_char_loc:
            self.assertIn(result.document_type, [Document.TYPE_CHARACTER, Document.TYPE_LOCATION])

    def test_search_text_max_results(self):
        """Test text search with maximum results limit."""
        # Create a search service with a low max_results
        with patch('src.backend.services.search_service.get_config') as mock_config:
            mock_config.return_value = {
                'search': {
                    'context_size': 30,
                    'max_results': 2
                }
            }
            limited_search_service = SearchService(self.documents)
        
        # Search for a term that appears in all documents
        results = limited_search_service.search_text("John Smith")
        
        # Should be limited to max_results
        self.assertEqual(len(results), 2)

    def test_search_metadata(self):
        """Test metadata search functionality."""
        # Search for documents with a specific metadata value
        results = self.search_service.search_metadata("location", "New York")
        
        # Should find doc1
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc1")
        self.assertTrue(results[0].metadata_match)
        
        # Search for documents with a numeric metadata value
        results = self.search_service.search_metadata("age", 35)
        
        # Should find doc3
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc3")
        self.assertTrue(results[0].metadata_match)
        
        # Search for a metadata key that multiple documents have
        results = self.search_service.search_metadata("pov_character", "John Smith")
        
        # Should find doc1 and doc2
        self.assertEqual(len(results), 2)
        doc_ids = [result.document_id for result in results]
        self.assertIn("doc1", doc_ids)
        self.assertIn("doc2", doc_ids)
        
        # Search for a non-existent metadata key
        results = self.search_service.search_metadata("non_existent", "value")
        self.assertEqual(len(results), 0)

    def test_search_tags(self):
        """Test tag search functionality."""
        # Search for documents with a specific tag
        results = self.search_service.search_tags(["chapter"])
        
        # Should find doc1 and doc2
        self.assertEqual(len(results), 2)
        doc_ids = [result.document_id for result in results]
        self.assertIn("doc1", doc_ids)
        self.assertIn("doc2", doc_ids)
        for result in results:
            self.assertTrue(result.tag_match)
        
        # Search for documents with multiple tags (any match)
        results = self.search_service.search_tags(["introduction", "journey"])
        
        # Should find doc1 and doc2
        self.assertEqual(len(results), 2)
        doc_ids = [result.document_id for result in results]
        self.assertIn("doc1", doc_ids)
        self.assertIn("doc2", doc_ids)
        
        # Search for documents with multiple tags (all must match)
        results = self.search_service.search_tags(["chapter", "introduction"], match_all=True)
        
        # Should find only doc1
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc1")
        
        # Search for a non-existent tag
        results = self.search_service.search_tags(["non_existent"])
        self.assertEqual(len(results), 0)
        
        # Test case insensitivity
        results = self.search_service.search_tags(["CHAPTER"])
        self.assertEqual(len(results), 2)

    def test_advanced_search(self):
        """Test advanced search functionality."""
        # Search with text query only
        results = self.search_service.advanced_search(
            text_query="John Smith",
            case_sensitive=False,
            whole_word=False
        )
        self.assertEqual(len(results), 4)
        
        # Search with metadata filters only
        results = self.search_service.advanced_search(
            metadata_filters={"location": "New York"}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc1")
        
        # Search with tags only
        results = self.search_service.advanced_search(
            tags=["chapter"],
            match_all_tags=False
        )
        self.assertEqual(len(results), 2)
        
        # Search with document types only
        results = self.search_service.advanced_search(
            document_types=[Document.TYPE_SCENE]
        )
        self.assertEqual(len(results), 2)
        
        # Search with combined criteria
        results = self.search_service.advanced_search(
            text_query="John",
            metadata_filters={"pov_character": "John Smith"},
            tags=["chapter"],
            document_types=[Document.TYPE_SCENE],
            case_sensitive=False,
            whole_word=False
        )
        self.assertEqual(len(results), 2)
        doc_ids = [result.document_id for result in results]
        self.assertIn("doc1", doc_ids)
        self.assertIn("doc2", doc_ids)
        
        # More specific combined search
        results = self.search_service.advanced_search(
            text_query="New York",
            metadata_filters={"pov_character": "John Smith"},
            tags=["introduction"],
            document_types=[Document.TYPE_SCENE]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc1")

    def test_highlight_matches(self):
        """Test highlighting matches in text."""
        # Test basic highlighting
        text = "This is a test text with the word test appearing twice."
        highlighted = self.search_service.highlight_matches(text, "test")
        expected = "This is a **test** text with the word **test** appearing twice."
        self.assertEqual(highlighted, expected)
        
        # Test case-sensitive highlighting
        text = "Test test TEST"
        highlighted = self.search_service.highlight_matches(text, "test", case_sensitive=False)
        expected = "**Test** **test** **TEST**"
        self.assertEqual(highlighted, expected)
        
        highlighted = self.search_service.highlight_matches(text, "test", case_sensitive=True)
        expected = "Test **test** TEST"
        self.assertEqual(highlighted, expected)
        
        # Test whole word highlighting
        text = "testing test tests"
        highlighted = self.search_service.highlight_matches(text, "test", whole_word=False)
        expected = "**test**ing **test** **test**s"
        self.assertEqual(highlighted, expected)
        
        highlighted = self.search_service.highlight_matches(text, "test", whole_word=True)
        expected = "testing **test** tests"
        self.assertEqual(highlighted, expected)
        
        # Test custom highlight markers
        text = "This is a test."
        highlighted = self.search_service.highlight_matches(
            text, "test", highlight_prefix="<mark>", highlight_suffix="</mark>"
        )
        expected = "This is a <mark>test</mark>."
        self.assertEqual(highlighted, expected)
        
        # Test with no matches
        text = "This is a sample text."
        highlighted = self.search_service.highlight_matches(text, "nonexistent")
        self.assertEqual(highlighted, text)
        
        # Test with empty text or query
        self.assertEqual(self.search_service.highlight_matches("", "test"), "")
        self.assertEqual(self.search_service.highlight_matches("text", ""), "text")

    def test_get_search_suggestions(self):
        """Test getting search suggestions based on a partial query."""
        # Test suggestions for document titles
        suggestions = self.search_service.get_search_suggestions("Cha")
        self.assertIn("Chapter 1: Introduction", suggestions)
        self.assertIn("Chapter 2: The Journey", suggestions)
        self.assertIn("Character: John Smith", suggestions)
        
        # Test suggestions for tags
        suggestions = self.search_service.get_search_suggestions("ch")
        self.assertIn("chapter", suggestions)
        self.assertIn("character", suggestions)
        
        # Test suggestions for metadata keys
        suggestions = self.search_service.get_search_suggestions("loc")
        self.assertIn("location", suggestions)
        
        # Test with no matches
        suggestions = self.search_service.get_search_suggestions("xyz")
        self.assertEqual(len(suggestions), 0)
        
        # Test with empty query
        suggestions = self.search_service.get_search_suggestions("")
        self.assertEqual(len(suggestions), 0)
        
        # Test max suggestions limit
        with patch('src.backend.services.search_service.get_config') as mock_config:
            mock_config.return_value = {
                'search': {
                    'context_size': 30,
                    'max_results': 50
                }
            }
            limited_search_service = SearchService(self.documents)
        
        # Should be limited to max_suggestions
        suggestions = limited_search_service.get_search_suggestions("ch", max_suggestions=2)
        self.assertEqual(len(suggestions), 2)

    def test_edge_cases(self):
        """Test edge cases."""
        # Empty query
        results = self.search_service.search_text("")
        self.assertEqual(len(results), 0)
        
        # No documents
        empty_search_service = SearchService()
        results = empty_search_service.search_text("test")
        self.assertEqual(len(results), 0)
        
        # Empty tags list
        results = self.search_service.search_tags([])
        self.assertEqual(len(results), 0)
        
        # Advanced search with no criteria
        results = self.search_service.advanced_search()
        self.assertEqual(len(results), 4)  # Should return all documents
        
        # Search with non-existent document types
        results = self.search_service.search_text("John", document_types=["non_existent_type"])
        self.assertEqual(len(results), 0)

    def test_error_handling(self):
        """Test error handling."""
        # Test with invalid regex pattern
        with patch('re.compile', side_effect=Exception("Invalid regex")):
            results = self.search_service.search_text("test[")
            self.assertEqual(len(results), 0)
        
        # Test with exception in _search_in_document
        with patch.object(self.search_service, '_search_in_document', side_effect=Exception("Search error")):
            results = self.search_service.search_text("test")
            self.assertEqual(len(results), 0)
        
        # Test with exception in search_metadata
        with patch.object(Document, 'get_metadata', side_effect=Exception("Metadata error")):
            results = self.search_service.search_metadata("key", "value")
            self.assertEqual(len(results), 0)
        
        # Test with exception in highlight_matches
        with patch('re.compile', side_effect=Exception("Invalid regex")):
            highlighted = self.search_service.highlight_matches("text", "test[")
            self.assertEqual(highlighted, "text")
        
        # Test with exception in get_search_suggestions
        with patch('src.backend.services.search_service.getattr', side_effect=Exception("Title error")):
            suggestions = self.search_service.get_search_suggestions("test")
            self.assertEqual(len(suggestions), 0)


if __name__ == '__main__':
    unittest.main()
