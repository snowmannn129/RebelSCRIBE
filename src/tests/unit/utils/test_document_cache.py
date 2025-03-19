#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the document cache module.

This module contains tests for the document cache functionality,
which is used to improve performance by reducing disk I/O.
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from src.utils.document_cache import LRUCache, DocumentCache
from src.backend.models.document import Document


class TestLRUCache(unittest.TestCase):
    """Tests for the LRUCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = LRUCache(max_size=3, ttl=1)  # 1 second TTL for testing
    
    def test_put_and_get(self):
        """Test putting and getting items from the cache."""
        # Put items in cache
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        # Get items from cache
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertIsNone(self.cache.get("key3"))  # Not in cache
    
    def test_lru_eviction(self):
        """Test that least recently used items are evicted when cache is full."""
        # Fill cache
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        
        # Cache is now full (max_size=3)
        
        # Access key1 to make it most recently used
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Add another item, should evict key2 (least recently used)
        self.cache.put("key4", "value4")
        
        # Check what's in cache
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertIsNone(self.cache.get("key2"))  # Evicted
        self.assertEqual(self.cache.get("key3"), "value3")
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_ttl_expiration(self):
        """Test that items expire after TTL."""
        # Put item in cache
        self.cache.put("key1", "value1")
        
        # Item should be in cache initially
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Wait for TTL to expire
        time.sleep(1.1)  # Slightly more than TTL
        
        # Item should be expired now
        self.assertIsNone(self.cache.get("key1"))
    
    def test_remove(self):
        """Test removing items from the cache."""
        # Put items in cache
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        # Remove an item
        self.assertTrue(self.cache.remove("key1"))
        
        # Item should be gone
        self.assertIsNone(self.cache.get("key1"))
        self.assertEqual(self.cache.get("key2"), "value2")
        
        # Removing non-existent item should return False
        self.assertFalse(self.cache.remove("key3"))
    
    def test_clear(self):
        """Test clearing the cache."""
        # Put items in cache
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        # Clear cache
        self.cache.clear()
        
        # Cache should be empty
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
    
    def test_contains(self):
        """Test checking if an item is in the cache."""
        # Put item in cache
        self.cache.put("key1", "value1")
        
        # Item should be in cache
        self.assertTrue(self.cache.contains("key1"))
        self.assertFalse(self.cache.contains("key2"))
        
        # Wait for TTL to expire
        time.sleep(1.1)  # Slightly more than TTL
        
        # Item should be expired now
        self.assertFalse(self.cache.contains("key1"))
    
    def test_get_all_keys(self):
        """Test getting all keys from the cache."""
        # Put items in cache
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        # Get all keys
        keys = self.cache.get_all_keys()
        
        # Check keys
        self.assertEqual(len(keys), 2)
        self.assertIn("key1", keys)
        self.assertIn("key2", keys)
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        # Put items in cache
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        # Get item (hit)
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Get non-existent item (miss)
        self.assertIsNone(self.cache.get("key3"))
        
        # Get stats
        stats = self.cache.get_stats()
        
        # Check stats
        self.assertEqual(stats["size"], 2)
        self.assertEqual(stats["max_size"], 3)
        self.assertEqual(stats["ttl"], 1)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate"], 0.5)


class TestDocumentCache(unittest.TestCase):
    """Tests for the DocumentCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = DocumentCache(
            max_documents=3,
            max_content_size_mb=1,
            document_ttl=1,  # 1 second TTL for testing
            metadata_ttl=2   # 2 seconds TTL for testing
        )
        
        # Create test documents
        self.doc1 = Document(title="Document 1", content="Content 1")
        self.doc2 = Document(title="Document 2", content="Content 2")
        self.doc3 = Document(title="Document 3", content="Content 3")
    
    def test_document_cache(self):
        """Test document caching."""
        # Put documents in cache
        self.cache.put_document(self.doc1.id, self.doc1)
        self.cache.put_document(self.doc2.id, self.doc2)
        
        # Get documents from cache
        cached_doc1 = self.cache.get_document(self.doc1.id)
        cached_doc2 = self.cache.get_document(self.doc2.id)
        
        # Check documents
        self.assertEqual(cached_doc1.id, self.doc1.id)
        self.assertEqual(cached_doc1.title, self.doc1.title)
        self.assertEqual(cached_doc1.content, self.doc1.content)
        
        self.assertEqual(cached_doc2.id, self.doc2.id)
        self.assertEqual(cached_doc2.title, self.doc2.title)
        self.assertEqual(cached_doc2.content, self.doc2.content)
        
        # Non-existent document should return None
        self.assertIsNone(self.cache.get_document("non-existent"))
    
    def test_metadata_cache(self):
        """Test document metadata caching."""
        # Create metadata
        metadata1 = {"id": self.doc1.id, "title": self.doc1.title, "content": None}
        metadata2 = {"id": self.doc2.id, "title": self.doc2.title, "content": None}
        
        # Put metadata in cache
        self.cache.put_document_metadata(self.doc1.id, metadata1)
        self.cache.put_document_metadata(self.doc2.id, metadata2)
        
        # Get metadata from cache
        cached_metadata1 = self.cache.get_document_metadata(self.doc1.id)
        cached_metadata2 = self.cache.get_document_metadata(self.doc2.id)
        
        # Check metadata
        self.assertEqual(cached_metadata1["id"], self.doc1.id)
        self.assertEqual(cached_metadata1["title"], self.doc1.title)
        self.assertIsNone(cached_metadata1["content"])
        
        self.assertEqual(cached_metadata2["id"], self.doc2.id)
        self.assertEqual(cached_metadata2["title"], self.doc2.title)
        self.assertIsNone(cached_metadata2["content"])
        
        # Non-existent metadata should return None
        self.assertIsNone(self.cache.get_document_metadata("non-existent"))
    
    def test_content_cache(self):
        """Test document content caching."""
        # Put content in cache
        self.cache.put_document_content(self.doc1.id, self.doc1.content)
        self.cache.put_document_content(self.doc2.id, self.doc2.content)
        
        # Get content from cache
        cached_content1 = self.cache.get_document_content(self.doc1.id)
        cached_content2 = self.cache.get_document_content(self.doc2.id)
        
        # Check content
        self.assertEqual(cached_content1, self.doc1.content)
        self.assertEqual(cached_content2, self.doc2.content)
        
        # Non-existent content should return None
        self.assertIsNone(self.cache.get_document_content("non-existent"))
    
    def test_content_size_limit(self):
        """Test content size limit."""
        # Create a large document (500KB)
        large_content = "X" * 500000
        large_doc = Document(title="Large Document", content=large_content)
        
        # Put large document content in cache
        self.cache.put_document_content(large_doc.id, large_doc.content)
        
        # Create another large document (600KB)
        larger_content = "Y" * 600000
        larger_doc = Document(title="Larger Document", content=larger_content)
        
        # Put larger document content in cache
        # This should evict the first large document content
        self.cache.put_document_content(larger_doc.id, larger_doc.content)
        
        # First document content should be evicted
        self.assertIsNone(self.cache.get_document_content(large_doc.id))
        
        # Second document content should be in cache
        self.assertEqual(self.cache.get_document_content(larger_doc.id), larger_doc.content)
    
    def test_document_ttl(self):
        """Test document TTL."""
        # Put document in cache
        self.cache.put_document(self.doc1.id, self.doc1)
        
        # Document should be in cache initially
        self.assertIsNotNone(self.cache.get_document(self.doc1.id))
        
        # Wait for TTL to expire
        time.sleep(1.1)  # Slightly more than document TTL
        
        # Document should be expired now
        self.assertIsNone(self.cache.get_document(self.doc1.id))
    
    def test_metadata_ttl(self):
        """Test metadata TTL."""
        # Create metadata
        metadata = {"id": self.doc1.id, "title": self.doc1.title, "content": None}
        
        # Put metadata in cache
        self.cache.put_document_metadata(self.doc1.id, metadata)
        
        # Metadata should be in cache initially
        self.assertIsNotNone(self.cache.get_document_metadata(self.doc1.id))
        
        # Wait for document TTL to expire but not metadata TTL
        time.sleep(1.1)  # Slightly more than document TTL
        
        # Metadata should still be in cache
        self.assertIsNotNone(self.cache.get_document_metadata(self.doc1.id))
        
        # Wait for metadata TTL to expire
        time.sleep(1.0)  # Now we're past metadata TTL
        
        # Metadata should be expired now
        self.assertIsNone(self.cache.get_document_metadata(self.doc1.id))
    
    def test_remove_document(self):
        """Test removing a document from the cache."""
        # Put document, metadata, and content in cache
        self.cache.put_document(self.doc1.id, self.doc1)
        self.cache.put_document_metadata(self.doc1.id, {"id": self.doc1.id, "title": self.doc1.title})
        self.cache.put_document_content(self.doc1.id, self.doc1.content)
        
        # Remove document
        self.cache.remove_document(self.doc1.id)
        
        # Document, metadata, and content should be gone
        self.assertIsNone(self.cache.get_document(self.doc1.id))
        self.assertIsNone(self.cache.get_document_metadata(self.doc1.id))
        self.assertIsNone(self.cache.get_document_content(self.doc1.id))
    
    def test_clear(self):
        """Test clearing the cache."""
        # Put documents in cache
        self.cache.put_document(self.doc1.id, self.doc1)
        self.cache.put_document(self.doc2.id, self.doc2)
        
        # Clear cache
        self.cache.clear()
        
        # Cache should be empty
        self.assertIsNone(self.cache.get_document(self.doc1.id))
        self.assertIsNone(self.cache.get_document(self.doc2.id))
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        # Put documents in cache
        self.cache.put_document(self.doc1.id, self.doc1)
        self.cache.put_document_content(self.doc1.id, self.doc1.content)
        
        # Get stats
        stats = self.cache.get_stats()
        
        # Check stats
        self.assertIn("document_cache", stats)
        self.assertIn("metadata_cache", stats)
        self.assertIn("content_cache", stats)
        self.assertIn("content_size_bytes", stats)
        self.assertIn("max_content_size_bytes", stats)
        
        # Document cache should have one item
        self.assertEqual(stats["document_cache"]["size"], 1)
        
        # Content size should be the size of doc1's content
        self.assertEqual(stats["content_size_bytes"], len(self.doc1.content.encode('utf-8')))


if __name__ == '__main__':
    unittest.main()
