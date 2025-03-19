#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document Cache for RebelSCRIBE.

This module provides a caching system for documents to improve performance
by reducing disk I/O and speeding up document access.
"""

import time
import logging
from typing import Dict, Optional, Any, List, Tuple, Set
from collections import OrderedDict
from threading import RLock

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.
    
    This class provides a thread-safe LRU cache with configurable size limits
    and expiration times.
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Initialize the LRU cache.
        
        Args:
            max_size: Maximum number of items to store in the cache.
            ttl: Time to live in seconds for cache items (0 for no expiration).
        """
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = RLock()
        self._timestamps: Dict[Any, float] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: Any) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            The cached item, or None if not found or expired.
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            # Check if item has expired
            if self._ttl > 0:
                timestamp = self._timestamps.get(key, 0)
                if timestamp + self._ttl < time.time():
                    # Item has expired
                    self._remove_item(key)
                    self._misses += 1
                    return None
            
            # Move item to the end (most recently used)
            value = self._cache.pop(key)
            self._cache[key] = value
            self._hits += 1
            return value
    
    def put(self, key: Any, value: Any) -> None:
        """
        Add or update an item in the cache.
        
        Args:
            key: The cache key.
            value: The value to cache.
        """
        with self._lock:
            # Remove existing item if present
            if key in self._cache:
                self._remove_item(key)
            
            # Add new item
            self._cache[key] = value
            self._timestamps[key] = time.time()
            
            # Remove oldest item if cache is full
            if len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                self._remove_item(oldest_key)
    
    def remove(self, key: Any) -> bool:
        """
        Remove an item from the cache.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the item was removed, False if it wasn't in the cache.
        """
        with self._lock:
            if key in self._cache:
                self._remove_item(key)
                return True
            return False
    
    def _remove_item(self, key: Any) -> None:
        """
        Remove an item from the cache and timestamps.
        
        Args:
            key: The cache key.
        """
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def contains(self, key: Any) -> bool:
        """
        Check if an item is in the cache and not expired.
        
        Args:
            key: The cache key.
            
        Returns:
            True if the item is in the cache and not expired, False otherwise.
        """
        with self._lock:
            if key not in self._cache:
                return False
            
            # Check if item has expired
            if self._ttl > 0:
                timestamp = self._timestamps.get(key, 0)
                if timestamp + self._ttl < time.time():
                    # Item has expired
                    self._remove_item(key)
                    return False
            
            return True
    
    def get_all_keys(self) -> List[Any]:
        """
        Get all keys in the cache.
        
        Returns:
            A list of all keys in the cache.
        """
        with self._lock:
            return list(self._cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary with cache statistics.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "ttl": self._ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate
            }


class DocumentCache:
    """
    Cache for document objects and metadata.
    
    This class provides a caching system for documents to improve performance
    by reducing disk I/O and speeding up document access.
    """
    
    def __init__(self, max_documents: int = 50, max_content_size_mb: int = 100,
                document_ttl: int = 3600, metadata_ttl: int = 7200):
        """
        Initialize the document cache.
        
        Args:
            max_documents: Maximum number of documents to cache.
            max_content_size_mb: Maximum size of document content cache in MB.
            document_ttl: Time to live in seconds for document cache items.
            metadata_ttl: Time to live in seconds for metadata cache items.
        """
        self._document_cache = LRUCache(max_documents, document_ttl)
        self._metadata_cache = LRUCache(max_documents * 2, metadata_ttl)
        self._content_cache = LRUCache(max_documents, document_ttl)
        
        # Convert max content size to bytes
        self._max_content_size = max_content_size_mb * 1024 * 1024
        self._current_content_size = 0
        self._content_sizes: Dict[str, int] = {}
        self._lock = RLock()
    
    def get_document(self, document_id: str) -> Optional[Any]:
        """
        Get a document from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document, or None if not found.
        """
        return self._document_cache.get(document_id)
    
    def put_document(self, document_id: str, document: Any) -> None:
        """
        Add or update a document in the cache.
        
        Args:
            document_id: The document ID.
            document: The document object.
        """
        self._document_cache.put(document_id, document)
        
        # Cache document metadata separately
        if hasattr(document, 'to_dict'):
            # Don't include content in metadata
            metadata = document.to_dict()
            if 'content' in metadata:
                metadata['content'] = None
            self._metadata_cache.put(document_id, metadata)
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document metadata, or None if not found.
        """
        return self._metadata_cache.get(document_id)
    
    def put_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> None:
        """
        Add or update document metadata in the cache.
        
        Args:
            document_id: The document ID.
            metadata: The document metadata.
        """
        self._metadata_cache.put(document_id, metadata)
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """
        Get document content from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document content, or None if not found.
        """
        return self._content_cache.get(document_id)
    
    def put_document_content(self, document_id: str, content: str) -> None:
        """
        Add or update document content in the cache.
        
        Args:
            document_id: The document ID.
            content: The document content.
        """
        with self._lock:
            # Check if content is already cached
            old_size = self._content_sizes.get(document_id, 0)
            new_size = len(content.encode('utf-8'))
            
            # Update content size tracking
            size_diff = new_size - old_size
            new_total_size = self._current_content_size + size_diff
            
            # If adding this content would exceed the max size, remove items until it fits
            if new_total_size > self._max_content_size and size_diff > 0:
                self._make_room_for_content(size_diff)
            
            # Update cache
            self._content_cache.put(document_id, content)
            self._content_sizes[document_id] = new_size
            self._current_content_size += size_diff
    
    def _make_room_for_content(self, needed_size: int) -> None:
        """
        Remove items from the content cache to make room for new content.
        
        Args:
            needed_size: The amount of space needed in bytes.
        """
        # Get all keys in reverse order (oldest first)
        keys = self._content_cache.get_all_keys()
        keys.reverse()
        
        # Remove items until we have enough space
        for key in keys:
            if self._current_content_size + needed_size <= self._max_content_size:
                break
            
            # Remove this item
            size = self._content_sizes.get(key, 0)
            self._content_cache.remove(key)
            self._content_sizes.pop(key, None)
            self._current_content_size -= size
    
    def remove_document(self, document_id: str) -> None:
        """
        Remove a document and its metadata from the cache.
        
        Args:
            document_id: The document ID.
        """
        with self._lock:
            self._document_cache.remove(document_id)
            self._metadata_cache.remove(document_id)
            
            # Update content size tracking if content was cached
            if document_id in self._content_sizes:
                self._current_content_size -= self._content_sizes[document_id]
                self._content_sizes.pop(document_id)
            
            self._content_cache.remove(document_id)
    
    def clear(self) -> None:
        """Clear all caches."""
        with self._lock:
            self._document_cache.clear()
            self._metadata_cache.clear()
            self._content_cache.clear()
            self._content_sizes.clear()
            self._current_content_size = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary with cache statistics.
        """
        document_stats = self._document_cache.get_stats()
        metadata_stats = self._metadata_cache.get_stats()
        content_stats = self._content_cache.get_stats()
        
        return {
            "document_cache": document_stats,
            "metadata_cache": metadata_stats,
            "content_cache": content_stats,
            "content_size_bytes": self._current_content_size,
            "max_content_size_bytes": self._max_content_size
        }
