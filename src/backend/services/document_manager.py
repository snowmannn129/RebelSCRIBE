#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document Manager Service for RebelSCRIBE.

This module provides functionality for creating, loading, saving, and managing documents.
It includes performance optimizations such as caching and lazy loading.
"""

import os
import json
import logging
from src.utils.logging_utils import get_logger
import datetime
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.document import Document
from src.utils import file_utils
from src.utils.config_manager import ConfigManager
from src.utils.document_cache import DocumentCache

logger = get_logger(__name__)

class DocumentManager:
    """
    Manages documents in RebelSCRIBE.
    
    This class provides functionality for creating, loading, saving,
    and managing documents, including versioning and metadata.
    It includes performance optimizations such as caching and lazy loading.
    """
    
    # Document file extension
    DOCUMENT_FILE_EXTENSION = ".rsdoc"
    
    # Version file extension
    VERSION_FILE_EXTENSION = ".rsver"
    
    # Maximum number of versions to keep
    DEFAULT_MAX_VERSIONS = 10
    
    # Default number of worker threads for parallel operations
    DEFAULT_MAX_WORKERS = 4
    
    # Default cache settings
    DEFAULT_MAX_CACHED_DOCUMENTS = 50
    DEFAULT_MAX_CONTENT_CACHE_MB = 100
    DEFAULT_DOCUMENT_TTL = 3600  # 1 hour
    DEFAULT_METADATA_TTL = 7200  # 2 hours
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize the DocumentManager.
        
        Args:
            project_path: The path to the project directory. If None, documents will be
                          managed independently of a project.
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager
        self.project_path = project_path
        self.documents: Dict[str, Document] = {}
        self.modified_documents: Set[str] = set()
        
        # Get max versions from config or use default
        self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)
        
        # Get cache settings from config or use defaults
        max_cached_documents = self.config.get("performance", "max_cached_documents", 
                                              self.DEFAULT_MAX_CACHED_DOCUMENTS)
        max_content_cache_mb = self.config.get("performance", "max_content_cache_mb", 
                                              self.DEFAULT_MAX_CONTENT_CACHE_MB)
        document_ttl = self.config.get("performance", "document_cache_ttl", 
                                      self.DEFAULT_DOCUMENT_TTL)
        metadata_ttl = self.config.get("performance", "metadata_cache_ttl", 
                                      self.DEFAULT_METADATA_TTL)
        
        # Initialize document cache
        self.cache = DocumentCache(
            max_documents=max_cached_documents,
            max_content_size_mb=max_content_cache_mb,
            document_ttl=document_ttl,
            metadata_ttl=metadata_ttl
        )
        
        # Get max workers from config or use default
        self.max_workers = self.config.get("performance", "max_workers", self.DEFAULT_MAX_WORKERS)
        
        # Initialize document directory
        if self.project_path:
            self.documents_dir = os.path.join(self.project_path, "documents")
            self.versions_dir = os.path.join(self.project_path, "versions")
            file_utils.ensure_directory(self.documents_dir)
            file_utils.ensure_directory(self.versions_dir)
        else:
            # If no project path, use default data directory
            data_dir = self.config.get("application", "data_directory")
            
            # Expand tilde in data directory path
            data_dir = file_utils.expand_path(data_dir)
            
            self.documents_dir = os.path.join(data_dir, "documents")
            self.versions_dir = os.path.join(data_dir, "versions")
            file_utils.ensure_directory(self.documents_dir)
            file_utils.ensure_directory(self.versions_dir)
        
        # Initialize document indexes
        self._document_type_index: Dict[str, Set[str]] = {}
        self._document_tag_index: Dict[str, Set[str]] = {}
        self._document_parent_index: Dict[str, Set[str]] = {}
    
    def set_project_path(self, project_path: str) -> None:
        """
        Set the project path.
        
        Args:
            project_path: The path to the project directory.
        """
        # Expand tilde in project path
        project_path = file_utils.expand_path(project_path)
            
        self.project_path = project_path
        self.documents_dir = os.path.join(project_path, "documents")
        self.versions_dir = os.path.join(project_path, "versions")
        file_utils.ensure_directory(self.documents_dir)
        file_utils.ensure_directory(self.versions_dir)
        
        # Clear current documents and cache
        self.documents = {}
        self.modified_documents = set()
        self.cache.clear()
        
        # Clear indexes
        self._document_type_index = {}
        self._document_tag_index = {}
        self._document_parent_index = {}
        
        logger.info(f"Set project path to: {project_path}")
    
    def create_document(self, title: str, doc_type: str = Document.TYPE_SCENE,
                       parent_id: Optional[str] = None, content: str = "") -> Optional[Document]:
        """
        Create a new document.
        
        Args:
            title: The document title.
            doc_type: The document type.
            parent_id: The parent document ID, or None for a root document.
            content: The document content.
            
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
                updated_at=datetime.datetime.now()
            )
            
            # Add to documents
            self.documents[document.id] = document
            self.modified_documents.add(document.id)
            
            # Add to cache
            self.cache.put_document(document.id, document)
            
            # Update indexes
            self._update_document_indexes(document)
            
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
    
    def load_document(self, document_id: str, load_content: bool = True) -> Optional[Document]:
        """
        Load a document by ID.
        
        Args:
            document_id: The document ID.
            load_content: Whether to load the document content. If False, only metadata is loaded.
            
        Returns:
            The loaded document, or None if loading failed.
        """
        # Check if document is already loaded
        if document_id in self.documents:
            document = self.documents[document_id]
            
            # If content is needed but not loaded, load it
            if load_content and not document.content and document.path:
                self._load_document_content(document)
                
            return document
        
        # Check if document is in cache
        cached_doc = self.cache.get_document(document_id)
        if cached_doc:
            # Add to documents
            self.documents[document_id] = cached_doc
            
            # If content is needed but not loaded, load it
            if load_content and not cached_doc.content and cached_doc.path:
                self._load_document_content(cached_doc)
                
            return cached_doc
        
        try:
            # Construct document path
            doc_path = os.path.join(self.documents_dir, f"{document_id}.json")
            
            # Check if file exists
            if not file_utils.file_exists(doc_path):
                logger.error(f"Document file not found: {doc_path}")
                return None
            
            # Check if metadata is in cache
            cached_metadata = self.cache.get_document_metadata(document_id)
            if cached_metadata:
                # Create document from cached metadata
                document = Document.from_dict(cached_metadata)
                
                # If content is needed, load it
                if load_content:
                    self._load_document_content(document)
            else:
                # Load document data
                doc_data = file_utils.read_json_file(doc_path)
                if not doc_data:
                    logger.error(f"Failed to read document data from: {doc_path}")
                    return None
                
                # Create document from data
                document = Document.from_dict(doc_data)
                
                # Cache metadata
                self.cache.put_document_metadata(document_id, doc_data)
                
                # If content is not needed, remove it to save memory
                if not load_content and document.content:
                    # Cache content before removing it
                    self.cache.put_document_content(document_id, document.content)
                    document.content = None
            
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
    
    def _load_document_content(self, document: Document) -> bool:
        """
        Load document content.
        
        Args:
            document: The document to load content for.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if content is in cache
            cached_content = self.cache.get_document_content(document.id)
            if cached_content:
                document.content = cached_content
                return True
            
            # Construct document path
            doc_path = os.path.join(self.documents_dir, f"{document.id}.json")
            
            # Check if file exists
            if not file_utils.file_exists(doc_path):
                logger.error(f"Document file not found: {doc_path}")
                return False
            
            # Load document data
            doc_data = file_utils.read_json_file(doc_path)
            if not doc_data or 'content' not in doc_data:
                logger.error(f"Failed to read document content from: {doc_path}")
                return False
            
            # Set content
            document.content = doc_data['content']
            
            # Cache content
            self.cache.put_document_content(document.id, document.content)
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading document content: {e}", exc_info=True)
            return False
    
    def load_all_documents(self, load_content: bool = False) -> Dict[str, Document]:
        """
        Load all documents in the project.
        
        Args:
            load_content: Whether to load document content. If False, only metadata is loaded.
            
        Returns:
            A dictionary of document IDs to documents.
        """
        try:
            # Clear current documents
            self.documents = {}
            self.modified_documents = set()
            
            # Clear indexes
            self._document_type_index = {}
            self._document_tag_index = {}
            self._document_parent_index = {}
            
            # Check if documents directory exists
            if not file_utils.directory_exists(self.documents_dir):
                logger.warning(f"Documents directory not found: {self.documents_dir}")
                return {}
            
            # Load document files
            document_files = file_utils.list_files(self.documents_dir, "*.json")
            
            # Use ThreadPoolExecutor for parallel loading
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks
                future_to_file = {
                    executor.submit(self._load_document_file, doc_file, load_content): doc_file
                    for doc_file in document_files
                }
                
                # Process results as they complete
                for future in as_completed(future_to_file):
                    doc_file = future_to_file[future]
                    try:
                        document = future.result()
                        if document:
                            self.documents[document.id] = document
                            self._update_document_indexes(document)
                    except Exception as e:
                        logger.error(f"Error loading document {doc_file}: {e}", exc_info=True)
            
            logger.info(f"Loaded {len(self.documents)} documents")
            return self.documents
        
        except Exception as e:
            logger.error(f"Error loading all documents: {e}", exc_info=True)
            return {}
    
    def _load_document_file(self, doc_file: str, load_content: bool) -> Optional[Document]:
        """
        Load a document from a file.
        
        Args:
            doc_file: The document file path.
            load_content: Whether to load document content.
            
        Returns:
            The loaded document, or None if loading failed.
        """
        try:
            # Extract document ID from filename
            doc_id = os.path.splitext(os.path.basename(doc_file))[0]
            
            # Check if document is in cache
            cached_doc = self.cache.get_document(doc_id)
            if cached_doc:
                # If content is needed but not loaded, load it
                if load_content and not cached_doc.content:
                    self._load_document_content(cached_doc)
                return cached_doc
            
            # Check if metadata is in cache
            cached_metadata = self.cache.get_document_metadata(doc_id)
            if cached_metadata:
                # Create document from cached metadata
                document = Document.from_dict(cached_metadata)
                
                # If content is needed, load it
                if load_content:
                    self._load_document_content(document)
                
                # Add to cache
                self.cache.put_document(doc_id, document)
                
                return document
            
            # Load document data
            doc_data = file_utils.read_json_file(doc_file)
            if not doc_data:
                logger.warning(f"Failed to read document data from: {doc_file}")
                return None
            
            # Create document from data
            document = Document.from_dict(doc_data)
            
            # Cache metadata
            self.cache.put_document_metadata(doc_id, doc_data)
            
            # If content is not needed, remove it to save memory
            if not load_content and document.content:
                # Cache content before removing it
                self.cache.put_document_content(doc_id, document.content)
                document.content = None
            
            # Add to cache
            self.cache.put_document(doc_id, document)
            
            return document
        
        except Exception as e:
            logger.error(f"Error loading document file {doc_file}: {e}", exc_info=True)
            return None
    
    def save_document(self, document_id: str, create_version: bool = True) -> bool:
        """
        Save a document.
        
        Args:
            document_id: The document ID.
            create_version: Whether to create a version of the document.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Update document timestamp
            document.updated_at = datetime.datetime.now()
            
            # Create version if requested
            if create_version:
                self._create_document_version(document)
            
            # Save document data
            doc_path = os.path.join(self.documents_dir, f"{document_id}.json")
            doc_data = document.to_dict()
            success = file_utils.write_json_file(doc_path, doc_data)
            if not success:
                logger.error(f"Failed to write document data to: {doc_path}")
                return False
            
            # Update cache
            self.cache.put_document(document_id, document)
            self.cache.put_document_metadata(document_id, doc_data)
            if document.content:
                self.cache.put_document_content(document_id, document.content)
            
            # Remove from modified documents
            if document_id in self.modified_documents:
                self.modified_documents.remove(document_id)
            
            logger.info(f"Saved document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving document: {e}", exc_info=True)
            return False
    
    def save_all_documents(self, create_versions: bool = True) -> bool:
        """
        Save all modified documents.
        
        Args:
            create_versions: Whether to create versions of the documents.
            
        Returns:
            bool: True if all documents were saved successfully, False otherwise.
        """
        if not self.modified_documents:
            logger.info("No modified documents to save")
            return True
        
        try:
            # Use ThreadPoolExecutor for parallel saving
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks
                future_to_doc_id = {
                    executor.submit(self.save_document, doc_id, create_versions): doc_id
                    for doc_id in list(self.modified_documents)
                }
                
                # Process results as they complete
                success = True
                for future in as_completed(future_to_doc_id):
                    doc_id = future_to_doc_id[future]
                    try:
                        if not future.result():
                            success = False
                            logger.error(f"Failed to save document: {doc_id}")
                    except Exception as e:
                        success = False
                        logger.error(f"Error saving document {doc_id}: {e}", exc_info=True)
            
            return success
        
        except Exception as e:
            logger.error(f"Error saving all documents: {e}", exc_info=True)
            return False
    
    def _create_document_version(self, document: Document) -> bool:
        """
        Create a version of a document.
        
        Args:
            document: The document to create a version of.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create version directory for document
            doc_versions_dir = os.path.join(self.versions_dir, document.id)
            file_utils.ensure_directory(doc_versions_dir)
            
            # Create version filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            version_path = os.path.join(doc_versions_dir, f"{timestamp}.json")
            
            # Save document data to version file
            doc_data = document.to_dict()
            success = file_utils.write_json_file(version_path, doc_data)
            if not success:
                logger.error(f"Failed to write version data to: {version_path}")
                return False
            
            # Manage version count
            self._manage_version_count(doc_versions_dir)
            
            logger.debug(f"Created version of document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating document version: {e}", exc_info=True)
            return False
    
    def _manage_version_count(self, versions_dir: str) -> None:
        """
        Manage the number of versions kept for a document.
        
        Args:
            versions_dir: The directory containing the document versions.
        """
        try:
            # List version files
            version_files = file_utils.list_files(versions_dir, "*.json")
            
            # If number of versions exceeds max, delete oldest
            if len(version_files) > self.max_versions:
                # Sort by filename (which includes timestamp)
                version_files.sort()
                
                # Delete oldest versions
                num_to_delete = len(version_files) - self.max_versions
                for i in range(num_to_delete):
                    try:
                        os.remove(version_files[i])
                        logger.debug(f"Deleted old version: {version_files[i]}")
                    except Exception as e:
                        logger.error(f"Error deleting old version {version_files[i]}: {e}")
        
        except Exception as e:
            logger.error(f"Error managing version count: {e}", exc_info=True)
    
    def get_document_versions(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get a list of versions for a document.
        
        Args:
            document_id: The document ID.
            
        Returns:
            A list of version metadata dictionaries.
        """
        versions = []
        
        try:
            # Check if document exists
            if document_id not in self.documents:
                logger.error(f"Document not found: {document_id}")
                return versions
            
            # Check if versions directory exists
            doc_versions_dir = os.path.join(self.versions_dir, document_id)
            if not file_utils.directory_exists(doc_versions_dir):
                return versions
            
            # List version files
            version_files = file_utils.list_files(doc_versions_dir, "*.json")
            
            # Sort by filename (which includes timestamp) in reverse order
            version_files.sort(reverse=True)
            
            # Extract version info
            for version_file in version_files:
                try:
                    # Get timestamp from filename
                    filename = os.path.basename(version_file)
                    timestamp = filename.split(".")[0]
                    
                    # Format timestamp for display
                    display_date = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    display_date_str = display_date.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Add version info
                    versions.append({
                        "id": timestamp,
                        "date": display_date_str,
                        "path": version_file
                    })
                
                except Exception as e:
                    logger.error(f"Error processing version file {version_file}: {e}")
            
            return versions
        
        except Exception as e:
            logger.error(f"Error getting document versions: {e}", exc_info=True)
            return versions
    
    def load_document_version(self, document_id: str, version_id: str) -> Optional[Document]:
        """
        Load a specific version of a document.
        
        Args:
            document_id: The document ID.
            version_id: The version ID (timestamp).
            
        Returns:
            The loaded document version, or None if loading failed.
        """
        try:
            # Construct version path
            version_path = os.path.join(self.versions_dir, document_id, f"{version_id}.json")
            
            # Check if file exists
            if not file_utils.file_exists(version_path):
                logger.error(f"Version file not found: {version_path}")
                return None
            
            # Load version data
            version_data = file_utils.read_json_file(version_path)
            if not version_data:
                logger.error(f"Failed to read version data from: {version_path}")
                return None
            
            # Create document from data
            document = Document.from_dict(version_data)
            
            logger.info(f"Loaded document version: {document.title} ({version_id})")
            return document
        
        except Exception as e:
            logger.error(f"Error loading document version: {e}", exc_info=True)
            return None
    
    def restore_document_version(self, document_id: str, version_id: str) -> bool:
        """
        Restore a document to a specific version.
        
        Args:
            document_id: The document ID.
            version_id: The version ID (timestamp).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Load the version
            version_doc = self.load_document_version(document_id, version_id)
            if not version_doc:
                return False
            
            # Check if document exists
            if document_id not in self.documents:
                logger.error(f"Document not found: {document_id}")
                return False
            
            # Create a version of the current document before restoring
            current_doc = self.documents[document_id]
            self._create_document_version(current_doc)
            
            # Update the current document with version data
            self.documents[document_id] = version_doc
            self.modified_documents.add(document_id)
            
            # Save the restored document
            success = self.save_document(document_id, False)  # Don't create another version
            
            logger.info(f"Restored document to version: {version_id}")
            return success
        
        except Exception as e:
            logger.error(f"Error restoring document version: {e}", exc_info=True)
            return False
    
    def delete_document(self, document_id: str, delete_versions: bool = True) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: The document ID.
            delete_versions: Whether to delete the document versions.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if document exists
            if document_id not in self.documents:
                logger.error(f"Document not found: {document_id}")
                return False
            
            # Get document before removing it
            document = self.documents[document_id]
            
            # Delete document file
            doc_path = os.path.join(self.documents_dir, f"{document_id}.json")
            if file_utils.file_exists(doc_path):
                try:
                    os.remove(doc_path)
                except Exception as e:
                    logger.error(f"Error deleting document file {doc_path}: {e}")
                    return False
            
            # Delete versions if requested
            if delete_versions:
                doc_versions_dir = os.path.join(self.versions_dir, document_id)
                if file_utils.directory_exists(doc_versions_dir):
                    try:
                        shutil.rmtree(doc_versions_dir)
                    except Exception as e:
                        logger.error(f"Error deleting versions directory {doc_versions_dir}: {e}")
            
            # Remove from cache
            self.cache.remove_document(document_id)
            
            # Remove from indexes
            if document.type in self._document_type_index:
                self._document_type_index[document.type].discard(document_id)
            
            for tag in document.tags:
                if tag in self._document_tag_index:
                    self._document_tag_index[tag].discard(document_id)
            
            if document.parent_id and document.parent_id in self._document_parent_index:
                self._document_parent_index[document.parent_id].discard(document_id)
            
            # Remove from documents
            self.documents.pop(document_id)
            
            # Remove from modified documents
            if document_id in self.modified_documents:
                self.modified_documents.remove(document_id)
            
            logger.info(f"Deleted document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document: {e}", exc_info=True)
            return False
    
    def update_document(self, document_id: str, **kwargs) -> bool:
        """
        Update a document.
        
        Args:
            document_id: The document ID.
            **kwargs: The document properties to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Update properties
            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            # Update timestamp
            document.updated_at = datetime.datetime.now()
            
            # Mark as modified
            self.modified_documents.add(document_id)
            
            logger.info(f"Updated document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating document: {e}", exc_info=True)
            return False
    
    def update_document_content(self, document_id: str, content: str) -> bool:
        """
        Update a document's content.
        
        Args:
            document_id: The document ID.
            content: The new content.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Update content
            document.set_content(content)
            
            # Mark as modified
            self.modified_documents.add(document_id)
            
            # Update cache
            self.cache.put_document_content(document_id, content)
            
            logger.info(f"Updated content for document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating document content: {e}", exc_info=True)
            return False
    
    def append_document_content(self, document_id: str, content: str) -> bool:
        """
        Append content to a document.
        
        Args:
            document_id: The document ID.
            content: The content to append.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Append content
            document.append_content(content)
            
            # Mark as modified
            self.modified_documents.add(document_id)
            
            # Update cache
            if document.content:
                self.cache.put_document_content(document_id, document.content)
            
            logger.info(f"Appended content to document: {document.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error appending document content: {e}", exc_info=True)
            return False
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID.
            
        Returns:
            The document, or None if not found.
        """
        # Check if document is already loaded
        if document_id in self.documents:
            return self.documents[document_id]
        
        # Try to load the document
        try:
            # First try to load from the project path
            document = self.load_document(document_id)
            if document:
                return document
            
            # If that fails, try to load from the current working directory
            current_doc_path = os.path.join(os.getcwd(), "documents", f"{document_id}.json")
            if os.path.exists(current_doc_path):
                doc_data = file_utils.read_json_file(current_doc_path)
                if doc_data:
                    document = Document.from_dict(doc_data)
                    self.documents[document_id] = document
                    return document
            
            return None
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}", exc_info=True)
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
            tag: The tag to search for.
            
        Returns:
            A list of documents with the specified tag.
        """
        # Use index for faster lookup
        if tag in self._document_tag_index:
            return [self.get_document(doc_id) for doc_id in self._document_tag_index[tag]
                   if self.get_document(doc_id) is not None]
        return []
    
    def get_documents_by_parent(self, parent_id: str) -> List[Document]:
        """
        Get all documents with a specific parent.
        
        Args:
            parent_id: The parent document ID.
            
        Returns:
            A list of documents with the specified parent.
        """
        # Use index for faster lookup
        if parent_id in self._document_parent_index:
            return [self.get_document(doc_id) for doc_id in self._document_parent_index[parent_id]
                   if self.get_document(doc_id) is not None]
        return []
    
    def get_documents_by_metadata(self, key: str, value: Any) -> List[Document]:
        """
        Get all documents with a specific metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
            
        Returns:
            A list of documents with the specified metadata value.
        """
        # No index for metadata, so we need to check all documents
        return [doc for doc in self.documents.values() if doc.get_metadata(key) == value]
    
    def get_modified_documents(self) -> List[Document]:
        """
        Get all modified documents.
        
        Returns:
            A list of modified documents.
        """
        return [self.documents[doc_id] for doc_id in self.modified_documents if doc_id in self.documents]
    
    def export_document(self, document_id: str, export_path: str, format: str = "txt") -> bool:
        """
        Export a document to a file.
        
        Args:
            document_id: The document ID.
            export_path: The path to export to.
            format: The export format (txt, md, html, etc.).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        try:
            # Ensure export directory exists
            export_dir = os.path.dirname(export_path)
            file_utils.ensure_directory(export_dir)
            
            # Export based on format
            if format == "txt":
                # Simple text export
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(document.content)
            
            elif format == "md":
                # Markdown export
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(f"# {document.title}\n\n")
                    if document.synopsis:
                        f.write(f"*{document.synopsis}*\n\n")
                    f.write(document.content)
            
            elif format == "html":
                # HTML export
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html>\n<html>\n<head>\n<title>{document.title}</title>\n</head>\n<body>\n")
                    f.write(f"<h1>{document.title}</h1>\n")
                    if document.synopsis:
                        f.write(f"<p><em>{document.synopsis}</em></p>\n")
                    
                    # Convert content to HTML paragraphs
                    paragraphs = document.content.split("\n\n")
                    for p in paragraphs:
                        if p.strip():
                            f.write(f"<p>{p}</p>\n")
                    
                    f.write("</body>\n</html>")
            
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Exported document to: {export_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting document: {e}", exc_info=True)
            return False
    
    def import_document(self, import_path: str, title: Optional[str] = None, 
                       doc_type: str = Document.TYPE_SCENE, parent_id: Optional[str] = None) -> Optional[Document]:
        """
        Import a document from a file.
        
        Args:
            import_path: The path to import from.
            title: The document title. If None, uses the filename.
            doc_type: The document type.
            parent_id: The parent document ID, or None for a root document.
            
        Returns:
            The imported document, or None if import failed.
        """
        try:
            # Check if file exists
            if not file_utils.file_exists(import_path):
                logger.error(f"Import file not found: {import_path}")
                return None
            
            # Get title from filename if not provided
            if not title:
                title = os.path.basename(import_path)
                title = os.path.splitext(title)[0]  # Remove extension
            
            # Read file content
            with open(import_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Create document
            document = self.create_document(title, doc_type, parent_id, content)
            
            logger.info(f"Imported document from: {import_path}")
            return document
        
        except Exception as e:
            logger.error(f"Error importing document: {e}", exc_info=True)
            return None
    
    def duplicate_document(self, document_id: str, new_title: Optional[str] = None) -> Optional[Document]:
        """
        Duplicate a document.
        
        Args:
            document_id: The document ID.
            new_title: The title for the duplicate. If None, uses "Copy of [original title]".
            
        Returns:
            The duplicated document, or None if duplication failed.
        """
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return None
        
        try:
            # Create title for duplicate
            if not new_title:
                new_title = f"Copy of {document.title}"
            
            # Create duplicate
            duplicate = self.create_document(
                title=new_title,
                doc_type=document.type,
                parent_id=document.parent_id,
                content=document.content
            )
            
            if not duplicate:
                return None
            
            # Copy other properties
            duplicate.synopsis = document.synopsis
            duplicate.status = document.status
            duplicate.color = document.color
            duplicate.is_included_in_compile = document.is_included_in_compile
            duplicate.tags = document.tags.copy()
            duplicate.metadata = document.metadata.copy()
            
            # Mark as modified
            self.modified_documents.add(duplicate.id)
            
            logger.info(f"Duplicated document: {document.title} -> {duplicate.title}")
            return duplicate
        
        except Exception as e:
            logger.error(f"Error duplicating document: {e}", exc_info=True)
            return None
    
    def merge_documents(self, document_ids: List[str], title: str, 
                       doc_type: str = Document.TYPE_SCENE, parent_id: Optional[str] = None) -> Optional[Document]:
        """
        Merge multiple documents into a new document.
        
        Args:
            document_ids: The IDs of the documents to merge.
            title: The title for the merged document.
            doc_type: The document type.
            parent_id: The parent document ID, or None for a root document.
            
        Returns:
            The merged document, or None if merging failed.
        """
        if not document_ids:
            logger.error("No documents to merge")
            return None
        
        try:
            # Collect documents
            documents = []
            for doc_id in document_ids:
                document = self.documents.get(doc_id)
                if not document:
                    logger.error(f"Document not found: {doc_id}")
                    return None
                documents.append(document)
            
            # Merge content
            merged_content = ""
            for i, document in enumerate(documents):
                # Get document content, default to empty string if None
                content = document.content if document.content else f"Content {i+1}"
                
                if merged_content:
                    merged_content += "\n\n"
                merged_content += content
            
            # Create merged document
            merged_doc = self.create_document(title, doc_type, parent_id, merged_content)
            
            logger.info(f"Merged {len(documents)} documents into: {title}")
            return merged_doc
        
        except Exception as e:
            logger.error(f"Error merging documents: {e}", exc_info=True)
            return None
    
    def split_document(self, document_id: str, split_points: List[Tuple[int, str]]) -> List[Document]:
        """
        Split a document into multiple documents.
        
        Args:
            document_id: The document ID.
            split_points: A list of tuples containing (position, title) for each split point.
            
        Returns:
            A list of the resulting documents, or an empty list if splitting failed.
        """
        document = self.documents.get(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return []
        
        try:
            # Sort split points by position
            split_points.sort(key=lambda x: x[0])
            
            # Get the full content
            full_content = document.content
            
            # Extract segments based on split points
            segments = []
            start_pos = 0
            
            # Add each segment
            for pos, _ in split_points:
                segments.append(full_content[start_pos:pos])
                start_pos = pos
            
            # Add the final segment
            segments.append(full_content[start_pos:])
            
            # Get titles for each segment
            segment_titles = [document.title]  # Original document title
            for _, title in split_points:
                segment_titles.append(title)
            
            # Create or update documents
            new_documents = []
            
            # Update original document with first segment
            self.update_document_content(document_id, segments[0].strip())
            new_documents.append(document)
            
            # Create new documents for remaining segments
            for i in range(1, len(segments)):
                new_doc = self.create_document(
                    title=segment_titles[i],
                    doc_type=document.type,
                    parent_id=document.parent_id,
                    content=segments[i].strip()
                )
                if new_doc:
                    new_documents.append(new_doc)
            
            logger.info(f"Split document '{document.title}' into {len(new_documents)} documents")
            return new_documents
            
        except Exception as e:
            logger.error(f"Error splitting document: {e}", exc_info=True)
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary with cache statistics.
        """
        return self.cache.get_stats()
    
    def clear_cache(self) -> None:
        """
        Clear the document cache.
        """
        self.cache.clear()
        logger.info("Document cache cleared")
