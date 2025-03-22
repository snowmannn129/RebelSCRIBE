#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document cache for RebelSCRIBE.

This module provides caching functionality for documents.
"""

import time
from typing import Dict, List, Optional, Any, Set
import logging

logger = logging.getLogger(__name__)

class DocumentCache:
    """
    Cache for documents.
    
    This class provides caching functionality for documents, including content and metadata caching.
    """
    
    def __init__(self, max_documents: int = 50, max_content_size_mb: int = 100,
                document_ttl: int = 3600, metadata_ttl: int = 7200):
        """
        Initialize the DocumentCache.
        
        Args:
            max_documents: The maximum number of documents to cache.
            max_content_size_mb: The maximum content cache size in MB.
            document_ttl: The document time-to-live in seconds.
            metadata_ttl: The metadata time-to-live in seconds.
        """
        self.max_documents = max_documents
        self.max_content_size_bytes = max_content_size_mb * 1024 * 1024
        self.document_ttl = document_ttl
        self.metadata_ttl = metadata_ttl
        
        # Cache dictionaries
        self.document_cache: Dict[str, Dict[str, Any]] = {}
        self.content_cache: Dict[str, Dict[str, Any]] = {}
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}
        
        # Cache statistics
        self.document_cache_hits = 0
        self.document_cache_misses = 0
        self.content_cache_hits = 0
        self.content_cache_misses = 0
        self.metadata_cache_hits = 0
        self.metadata_cache_misses = 0
        
        # Current cache size
        self.current_content_size_bytes = 0
    
    def put_document(self, document_id: str, document: Any) -> None:
        """
        Put a document in the cache.
        
        Args:
            document_id: The document ID.
            document: The document to cache.
        """
        try:
            # Check if we need to evict documents
            if len(self.document_cache) >= self.max_documents:
                self._evict_documents()
            
            # Add to document cache
            self.document_cache[document_id] = {
                "document": document,
                "timestamp": time.time()
            }
            
            # Add content to content cache if available
            if hasattr(document, "content") and document.content:
                self.put_document_content(document_id, document.content)
            
            # Add metadata to metadata cache
            if hasattr(document, "to_dict"):
                metadata = document.to_dict()
                if "content" in metadata:
                    metadata["content"] = None  # Don't store content in metadata cache
                self.put_document_metadata(document_id, metadata)
            
            logger.debug(f"Added document to cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error putting document in cache: {e}", exc_info=True)
    
    def get_document(self, document_id: str) -> Optional[Any]:
        """
        Get a document from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document, or None if not found or expired.
        """
        try:
            # Check if document is in cache
            if document_id in self.document_cache:
                cache_entry = self.document_cache[document_id]
                
                # Check if document has expired
                if time.time() - cache_entry["timestamp"] > self.document_ttl:
                    # Remove expired document
                    del self.document_cache[document_id]
                    self.document_cache_misses += 1
                    logger.debug(f"Document cache miss (expired): {document_id}")
                    return None
                
                # Update timestamp
                cache_entry["timestamp"] = time.time()
                
                self.document_cache_hits += 1
                logger.debug(f"Document cache hit: {document_id}")
                return cache_entry["document"]
            
            self.document_cache_misses += 1
            logger.debug(f"Document cache miss: {document_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting document from cache: {e}", exc_info=True)
            self.document_cache_misses += 1
            return None
    
    def put_document_content(self, document_id: str, content: str) -> None:
        """
        Put document content in the cache.
        
        Args:
            document_id: The document ID.
            content: The document content.
        """
        try:
            # Calculate content size
            content_size = len(content.encode("utf-8"))
            
            # Check if we need to evict content
            if self.current_content_size_bytes + content_size > self.max_content_size_bytes:
                self._evict_content(content_size)
            
            # Add to content cache
            self.content_cache[document_id] = {
                "content": content,
                "size": content_size,
                "timestamp": time.time()
            }
            
            # Update current content size
            self.current_content_size_bytes += content_size
            
            logger.debug(f"Added document content to cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error putting document content in cache: {e}", exc_info=True)
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """
        Get document content from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document content, or None if not found or expired.
        """
        try:
            # Check if content is in cache
            if document_id in self.content_cache:
                cache_entry = self.content_cache[document_id]
                
                # Check if content has expired
                if time.time() - cache_entry["timestamp"] > self.document_ttl:
                    # Remove expired content
                    self._remove_content(document_id)
                    self.content_cache_misses += 1
                    logger.debug(f"Content cache miss (expired): {document_id}")
                    return None
                
                # Update timestamp
                cache_entry["timestamp"] = time.time()
                
                self.content_cache_hits += 1
                logger.debug(f"Content cache hit: {document_id}")
                return cache_entry["content"]
            
            self.content_cache_misses += 1
            logger.debug(f"Content cache miss: {document_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting document content from cache: {e}", exc_info=True)
            self.content_cache_misses += 1
            return None
    
    def put_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> None:
        """
        Put document metadata in the cache.
        
        Args:
            document_id: The document ID.
            metadata: The document metadata.
        """
        try:
            # Add to metadata cache
            self.metadata_cache[document_id] = {
                "metadata": metadata,
                "timestamp": time.time()
            }
            
            logger.debug(f"Added document metadata to cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error putting document metadata in cache: {e}", exc_info=True)
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata from the cache.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The cached document metadata, or None if not found or expired.
        """
        try:
            # Check if metadata is in cache
            if document_id in self.metadata_cache:
                cache_entry = self.metadata_cache[document_id]
                
                # Check if metadata has expired
                if time.time() - cache_entry["timestamp"] > self.metadata_ttl:
                    # Remove expired metadata
                    del self.metadata_cache[document_id]
                    self.metadata_cache_misses += 1
                    logger.debug(f"Metadata cache miss (expired): {document_id}")
                    return None
                
                # Update timestamp
                cache_entry["timestamp"] = time.time()
                
                self.metadata_cache_hits += 1
                logger.debug(f"Metadata cache hit: {document_id}")
                return cache_entry["metadata"]
            
            self.metadata_cache_misses += 1
            logger.debug(f"Metadata cache miss: {document_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting document metadata from cache: {e}", exc_info=True)
            self.metadata_cache_misses += 1
            return None
    
    def remove_document(self, document_id: str) -> None:
        """
        Remove a document from the cache.
        
        Args:
            document_id: The document ID.
        """
        try:
            # Remove from document cache
            if document_id in self.document_cache:
                del self.document_cache[document_id]
            
            # Remove from content cache
            self._remove_content(document_id)
            
            # Remove from metadata cache
            if document_id in self.metadata_cache:
                del self.metadata_cache[document_id]
            
            logger.debug(f"Removed document from cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error removing document from cache: {e}", exc_info=True)
    
    def _remove_content(self, document_id: str) -> None:
        """
        Remove document content from the cache.
        
        Args:
            document_id: The document ID.
        """
        try:
            # Check if content is in cache
            if document_id in self.content_cache:
                # Update current content size
                self.current_content_size_bytes -= self.content_cache[document_id]["size"]
                
                # Remove from content cache
                del self.content_cache[document_id]
        
        except Exception as e:
            logger.error(f"Error removing document content from cache: {e}", exc_info=True)
    
    def _evict_documents(self) -> None:
        """
        Evict documents from the cache based on LRU policy.
        """
        try:
            # Sort documents by timestamp
            sorted_documents = sorted(
                self.document_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Remove oldest documents
            num_to_remove = max(1, len(self.document_cache) // 4)  # Remove at least 1, up to 25%
            for i in range(min(num_to_remove, len(sorted_documents))):
                document_id = sorted_documents[i][0]
                self.remove_document(document_id)
                logger.debug(f"Evicted document from cache: {document_id}")
        
        except Exception as e:
            logger.error(f"Error evicting documents from cache: {e}", exc_info=True)
    
    def _evict_content(self, required_size: int) -> None:
        """
        Evict document content from the cache based on LRU policy.
        
        Args:
            required_size: The required size in bytes.
        """
        try:
            # Sort content by timestamp
            sorted_content = sorted(
                self.content_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Remove oldest content until we have enough space
            for document_id, _ in sorted_content:
                self._remove_content(document_id)
                logger.debug(f"Evicted document content from cache: {document_id}")
                
                # Check if we have enough space
                if self.current_content_size_bytes + required_size <= self.max_content_size_bytes:
                    break
        
        except Exception as e:
            logger.error(f"Error evicting content from cache: {e}", exc_info=True)
    
    def clear(self) -> None:
        """
        Clear the cache.
        """
        try:
            self.document_cache = {}
            self.content_cache = {}
            self.metadata_cache = {}
            self.current_content_size_bytes = 0
            
            logger.debug("Cleared cache")
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary with cache statistics.
        """
        try:
            return {
                "document_cache_size": len(self.document_cache),
                "content_cache_size": len(self.content_cache),
                "metadata_cache_size": len(self.metadata_cache),
                "content_cache_size_bytes": self.current_content_size_bytes,
                "content_cache_size_mb": self.current_content_size_bytes / (1024 * 1024),
                "document_cache_hits": self.document_cache_hits,
                "document_cache_misses": self.document_cache_misses,
                "content_cache_hits": self.content_cache_hits,
                "content_cache_misses": self.content_cache_misses,
                "metadata_cache_hits": self.metadata_cache_hits,
                "metadata_cache_misses": self.metadata_cache_misses
            }
        
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}", exc_info=True)
            return {}
