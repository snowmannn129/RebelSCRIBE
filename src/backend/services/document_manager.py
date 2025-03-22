#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document Manager Service for RebelSCRIBE.

This module provides functionality for creating, loading, saving, and managing documents.
"""

import os
import json
import logging
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from src.utils.logging_utils import get_logger
from src.utils import file_utils
from src.utils.document_cache import DocumentCache
from ..models.document import Document

logger = get_logger(__name__)

class DocumentManager:
    """
    Manages documents in RebelSCRIBE.
    
    This class provides functionality for creating, loading, saving, and managing documents.
    """
    
    # Document file extension
    DOCUMENT_FILE_EXTENSION = ".rsdoc"
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize the DocumentManager.
        
        Args:
            project_path: The path to the project directory. If None, documents will be
                          managed independently of a project.
        """
        # Set project path
        self.project_path = project_path
        
        # Initialize document storage
        self.documents: Dict[str, Document] = {}
        self.modified_documents: Set[str] = set()
        
        # Initialize document cache
        self.cache = DocumentCache()
        
        # Initialize document indexes
        self._document_type_index: Dict[str, Set[str]] = {}
        self._document_tag_index: Dict[str, Set[str]] = {}
        self._document_parent_index: Dict[str, Set[str]] = {}
    
    def create_document(self, title: str, doc_type: str = Document.TYPE_SCENE,
                      parent_id: Optional[str] = None, content: str = "",
                      **kwargs) -> Optional[Document]:
        """
        Create a new document.
        
        Args:
            title: The document title.
            doc_type: The document type.
            parent_id: The parent document ID, or None for a root document.
            content: The document content.
            **kwargs: Additional document attributes.
            
        Returns:
            The created document, or None if creation failed.
        """
        try:
            # Create document
            document = Document(
                title=title,
                type=doc_type,
                content=content,
                parent_id=parent_id,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                **kwargs
            )
            
            # Add to documents
            self.documents[document.id] = document
            self.modified_documents.add(document.id)
            
            # Add to cache
            self.cache.put_document(document.id, document)
            
            # Update indexes
            self._update_document_indexes(document)
            
            # Add to parent's children if parent exists
            if parent_id and parent_id in self.documents:
                parent = self.documents[parent_id]
                parent.add_child(document.id)
                self.modified_documents.add(parent_id)
            
            logger.info(f"Created document: {title}")
            return document
        
        except Exception as e:
            logger.error(f"Error creating document: {e}", exc_info=True)
            return None
    
    def _update_document_indexes(self, document: Document) -> None:
        """
        Update document indexes.
        
        Args:
            document: The document to index.
        """
        try:
            # Update type index
            if document.type:
                if document.type not in self._document_type_index:
                    self._document_type_index[document.type] = set()
                self._document_type_index[document.type].add(document.id)
            
            # Update tag index
            for tag in document.tags:
                if tag not in self._document_tag_index:
                    self._document_tag_index[tag] = set()
                self._document_tag_index[tag].add(document.id)
            
            # Update parent index
            if document.parent_id:
                if document.parent_id not in self._document_parent_index:
                    self._document_parent_index[document.parent_id] = set()
                self._document_parent_index[document.parent_id].add(document.id)
        
        except Exception as e:
            logger.error(f"Error updating document indexes: {e}", exc_info=True)
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The document, or None if not found.
        """
        try:
            # Check cache first
            document = self.cache.get_document(document_id)
            if document:
                return document
            
            # Check documents
            if document_id in self.documents:
                document = self.documents[document_id]
                
                # Add to cache
                self.cache.put_document(document_id, document)
                
                return document
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting document: {e}", exc_info=True)
            return None
    
    def get_documents_by_type(self, doc_type: str) -> List[Document]:
        """
        Get all documents of a specific type.
        
        Args:
            doc_type: The document type.
            
        Returns:
            A list of documents of the specified type.
        """
        # Use index for faster lookup
        if doc_type in self._document_type_index:
            return [self.get_document(doc_id) for doc_id in self._document_type_index[doc_type]
                   if self.get_document(doc_id) is not None]
        return []
    
    def get_documents_by_tag(self, tag: str) -> List[Document]:
        """
        Get all documents with a specific tag.
        
        Args:
            tag: The tag.
            
        Returns:
            A list of documents with the specified tag.
        """
        # Use index for faster lookup
        if tag in self._document_tag_index:
            return [self.get_document(doc_id) for doc_id in self._document_tag_index[tag]
                   if self.get_document(doc_id) is not None]
        return []
    
    def get_child_documents(self, parent_id: str) -> List[Document]:
        """
        Get all child documents of a parent document.
        
        Args:
            parent_id: The parent document ID.
            
        Returns:
            A list of child documents.
        """
        # Use index for faster lookup
        if parent_id in self._document_parent_index:
            return [self.get_document(doc_id) for doc_id in self._document_parent_index[parent_id]
                   if self.get_document(doc_id) is not None]
        return []
    
    def update_document(self, document_id: str, **kwargs) -> bool:
        """
        Update a document.
        
        Args:
            document_id: The document ID.
            **kwargs: Document attributes to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Get document
            document = self.get_document(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return False
            
            # Update attributes
            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            # Update timestamp
            document.updated_at = datetime.datetime.now()
            
            # Mark as modified
            self.modified_documents.add(document_id)
            
            # Update cache
            self.cache.put_document(document_id, document)
            
            logger.info(f"Updated document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating document: {e}", exc_info=True)
            return False
    
    def delete_document(self, document_id: str, delete_children: bool = False) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: The document ID.
            delete_children: Whether to delete child documents.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Get document
            document = self.get_document(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return False
            
            # Delete children if requested
            if delete_children:
                for child_id in document.children_ids:
                    self.delete_document(child_id, delete_children)
            else:
                # Update parent of children
                for child_id in document.children_ids:
                    child = self.get_document(child_id)
                    if child:
                        child.set_parent(document.parent_id)
                        self.modified_documents.add(child_id)
            
            # Remove from parent's children
            if document.parent_id:
                parent = self.get_document(document.parent_id)
                if parent:
                    parent.remove_child(document_id)
                    self.modified_documents.add(parent.id)
            
            # Remove from indexes
            if document.type in self._document_type_index:
                self._document_type_index[document.type].discard(document_id)
            
            for tag in document.tags:
                if tag in self._document_tag_index:
                    self._document_tag_index[tag].discard(document_id)
            
            if document.parent_id in self._document_parent_index:
                self._document_parent_index[document.parent_id].discard(document_id)
            
            # Remove from cache
            self.cache.remove_document(document_id)
            
            # Remove from documents
            if document_id in self.documents:
                del self.documents[document_id]
            
            # Remove from modified documents
            self.modified_documents.discard(document_id)
            
            logger.info(f"Deleted document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document: {e}", exc_info=True)
            return False
    
    def save_document(self, document_id: str) -> bool:
        """
        Save a document to disk.
        
        Args:
            document_id: The document ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Get document
            document = self.get_document(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return False
            
            # Check if project path is set
            if not self.project_path:
                logger.error("Project path not set")
                return False
            
            # Create documents directory if it doesn't exist
            documents_dir = os.path.join(self.project_path, "documents")
            file_utils.ensure_directory(documents_dir)
            
            # Create document file path
            file_path = os.path.join(documents_dir, f"{document_id}{self.DOCUMENT_FILE_EXTENSION}")
            
            # Convert document to dictionary
            document_dict = document.to_dict()
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(document_dict, f, indent=2, default=str)
            
            # Remove from modified documents
            self.modified_documents.discard(document_id)
            
            logger.info(f"Saved document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving document: {e}", exc_info=True)
            return False
    
    def load_document(self, file_path: str) -> Optional[Document]:
        """
        Load a document from disk.
        
        Args:
            file_path: The path to the document file.
            
        Returns:
            The loaded document, or None if loading failed.
        """
        try:
            # Check if file exists
            if not file_utils.file_exists(file_path):
                logger.error(f"Document file not found: {file_path}")
                return None
            
            # Read file
            with open(file_path, "r", encoding="utf-8") as f:
                document_dict = json.load(f)
            
            # Create document from dictionary
            document = Document.from_dict(document_dict)
            
            # Add to documents
            self.documents[document.id] = document
            
            # Add to cache
            self.cache.put_document(document.id, document)
            
            # Update indexes
            self._update_document_indexes(document)
            
            logger.info(f"Loaded document: {document.title}")
            return document
        
        except Exception as e:
            logger.error(f"Error loading document: {e}", exc_info=True)
            return None
    
    def load_documents(self, directory_path: Optional[str] = None) -> int:
        """
        Load all documents from a directory.
        
        Args:
            directory_path: The directory path, or None to use the project path.
            
        Returns:
            The number of documents loaded.
        """
        try:
            # Use project path if directory path not provided
            if not directory_path:
                if not self.project_path:
                    logger.error("Project path not set")
                    return 0
                directory_path = os.path.join(self.project_path, "documents")
            
            # Check if directory exists
            if not file_utils.directory_exists(directory_path):
                logger.error(f"Documents directory not found: {directory_path}")
                return 0
            
            # Find all document files
            document_files = []
            for file in os.listdir(directory_path):
                if file.endswith(self.DOCUMENT_FILE_EXTENSION):
                    document_files.append(os.path.join(directory_path, file))
            
            # Load each document
            loaded_count = 0
            for file_path in document_files:
                document = self.load_document(file_path)
                if document:
                    loaded_count += 1
            
            logger.info(f"Loaded {loaded_count} documents from: {directory_path}")
            return loaded_count
        
        except Exception as e:
            logger.error(f"Error loading documents: {e}", exc_info=True)
            return 0
    
    def save_all_documents(self) -> int:
        """
        Save all modified documents.
        
        Returns:
            The number of documents saved.
        """
        try:
            # Check if project path is set
            if not self.project_path:
                logger.error("Project path not set")
                return 0
            
            # Save each modified document
            saved_count = 0
            for document_id in list(self.modified_documents):
                if self.save_document(document_id):
                    saved_count += 1
            
            logger.info(f"Saved {saved_count} documents")
            return saved_count
        
        except Exception as e:
            logger.error(f"Error saving all documents: {e}", exc_info=True)
            return 0
    
    def create_backup(self, backup_dir: Optional[str] = None) -> bool:
        """
        Create a backup of all documents.
        
        Args:
            backup_dir: The backup directory, or None to use the default.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if project path is set
            if not self.project_path:
                logger.error("Project path not set")
                return False
            
            # Use default backup directory if not provided
            if not backup_dir:
                backup_dir = os.path.join(self.project_path, "backups")
            
            # Create backup directory if it doesn't exist
            file_utils.ensure_directory(backup_dir)
            
            # Create timestamp for backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
            file_utils.ensure_directory(backup_path)
            
            # Save all documents to backup directory
            documents_dir = os.path.join(self.project_path, "documents")
            if file_utils.directory_exists(documents_dir):
                for file in os.listdir(documents_dir):
                    if file.endswith(self.DOCUMENT_FILE_EXTENSION):
                        source_path = os.path.join(documents_dir, file)
                        dest_path = os.path.join(backup_path, file)
                        shutil.copy2(source_path, dest_path)
            
            logger.info(f"Created backup: {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return False
    
    def search_documents(self, query: str, case_sensitive: bool = False,
                       doc_types: Optional[List[str]] = None,
                       tags: Optional[List[str]] = None) -> List[Document]:
        """
        Search for documents matching a query.
        
        Args:
            query: The search query.
            case_sensitive: Whether the search is case-sensitive.
            doc_types: The document types to search, or None for all types.
            tags: The tags to search, or None for all tags.
            
        Returns:
            A list of matching documents.
        """
        try:
            # Prepare query
            if not case_sensitive:
                query = query.lower()
            
            # Get documents to search
            documents_to_search = []
            
            # Filter by type if specified
            if doc_types:
                for doc_type in doc_types:
                    documents_to_search.extend(self.get_documents_by_type(doc_type))
            # Filter by tag if specified
            elif tags:
                for tag in tags:
                    documents_to_search.extend(self.get_documents_by_tag(tag))
            # Otherwise search all documents
            else:
                documents_to_search = list(self.documents.values())
            
            # Search documents
            matching_documents = []
            for document in documents_to_search:
                # Search in title
                title = document.title if case_sensitive else document.title.lower()
                if query in title:
                    matching_documents.append(document)
                    continue
                
                # Search in content
                content = document.content if case_sensitive else document.content.lower()
                if query in content:
                    matching_documents.append(document)
                    continue
            
            logger.info(f"Found {len(matching_documents)} documents matching query: {query}")
            return matching_documents
        
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the documents.
        
        Returns:
            A dictionary with document statistics.
        """
        try:
            stats = {
                "total_documents": len(self.documents),
                "modified_documents": len(self.modified_documents),
                "document_types": {},
                "total_words": 0,
                "total_characters": 0,
                "tags": {}
            }
            
            # Count document types
            for doc_type, doc_ids in self._document_type_index.items():
                stats["document_types"][doc_type] = len(doc_ids)
            
            # Count words and characters
            for document in self.documents.values():
                stats["total_words"] += document.word_count
                stats["total_characters"] += document.character_count
            
            # Count tags
            for tag, doc_ids in self._document_tag_index.items():
                stats["tags"][tag] = len(doc_ids)
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting document stats: {e}", exc_info=True)
            return {}
