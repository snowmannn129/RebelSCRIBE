#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content Organization System for RebelSCRIBE.

This module provides the main class for the content organization system, which integrates
the metadata extractor, content hierarchy, tag manager, and search index.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime
import uuid

from src.utils.logging_utils import get_logger
from src.backend.models.document import Document
from src.backend.organization.metadata_extractor import MetadataExtractor
from src.backend.organization.content_hierarchy import ContentHierarchy
from src.backend.organization.tag_manager import TagManager
from src.backend.organization.search_index import SearchIndex, SearchResult

logger = get_logger(__name__)

class ContentOrganizationSystem:
    """
    Main class for the content organization system.
    
    This class integrates the metadata extractor, content hierarchy, tag manager, and search index
    to provide a comprehensive content organization system.
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize the ContentOrganizationSystem.
        
        Args:
            project_path: The path to the project directory, or None if not associated with a project.
        """
        self.project_path = project_path
        self.metadata_extractor = MetadataExtractor()
        self.content_hierarchy = ContentHierarchy()
        self.tag_manager = TagManager()
        self.search_index = SearchIndex()
        
        # Load data if project path is provided
        if project_path:
            self.load_data()
    
    def set_project_path(self, project_path: str) -> None:
        """
        Set the project path.
        
        Args:
            project_path: The path to the project directory.
        """
        self.project_path = project_path
        
        # Load data from the new project path
        self.load_data()
    
    def load_data(self) -> bool:
        """
        Load data from the project directory.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self.project_path:
            logger.warning("Project path not set")
            return False
        
        try:
            # Create organization directory if it doesn't exist
            organization_dir = os.path.join(self.project_path, "organization")
            os.makedirs(organization_dir, exist_ok=True)
            
            # Load content hierarchy
            hierarchy_path = os.path.join(organization_dir, "hierarchy.json")
            if os.path.exists(hierarchy_path):
                self.content_hierarchy.load_from_file(hierarchy_path)
            
            # Load tag manager
            tags_path = os.path.join(organization_dir, "tags.json")
            if os.path.exists(tags_path):
                self.tag_manager.load_from_file(tags_path)
            
            # Load search index
            index_path = os.path.join(organization_dir, "search_index.json")
            if os.path.exists(index_path):
                self.search_index.load_from_file(index_path)
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            return False
    
    def save_data(self) -> bool:
        """
        Save data to the project directory.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self.project_path:
            logger.warning("Project path not set")
            return False
        
        try:
            # Create organization directory if it doesn't exist
            organization_dir = os.path.join(self.project_path, "organization")
            os.makedirs(organization_dir, exist_ok=True)
            
            # Save content hierarchy
            hierarchy_path = os.path.join(organization_dir, "hierarchy.json")
            self.content_hierarchy.save_to_file(hierarchy_path)
            
            # Save tag manager
            tags_path = os.path.join(organization_dir, "tags.json")
            self.tag_manager.save_to_file(tags_path)
            
            # Save search index
            index_path = os.path.join(organization_dir, "search_index.json")
            self.search_index.save_to_file(index_path)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving data: {e}", exc_info=True)
            return False
    
    def create_backup(self) -> bool:
        """
        Create a backup of the organization data.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self.project_path:
            logger.warning("Project path not set")
            return False
        
        try:
            # Create backups directory if it doesn't exist
            backups_dir = os.path.join(self.project_path, "backups", "organization")
            os.makedirs(backups_dir, exist_ok=True)
            
            # Create timestamp for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save content hierarchy
            hierarchy_path = os.path.join(backups_dir, f"hierarchy_{timestamp}.json")
            self.content_hierarchy.save_to_file(hierarchy_path)
            
            # Save tag manager
            tags_path = os.path.join(backups_dir, f"tags_{timestamp}.json")
            self.tag_manager.save_to_file(tags_path)
            
            # Save search index
            index_path = os.path.join(backups_dir, f"search_index_{timestamp}.json")
            self.search_index.save_to_file(index_path)
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return False
    
    def process_document(self, document: Document) -> bool:
        """
        Process a document to extract metadata, update hierarchy, and index content.
        
        Args:
            document: The document to process.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Extract metadata
            metadata = self.metadata_extractor.extract_from_markdown(document.content)
            
            # Normalize metadata
            metadata = self.metadata_extractor.normalize_metadata(metadata)
            
            # Add document metadata
            metadata['document_id'] = document.id
            metadata['title'] = document.title
            metadata['type'] = document.type
            metadata['created_at'] = document.created_at
            metadata['updated_at'] = document.updated_at
            metadata['content'] = document.content
            
            # Update document with metadata
            if not hasattr(document, 'metadata'):
                document.metadata = {}
            
            document.metadata.update(metadata)
            
            # Update hierarchy
            node = self.content_hierarchy.get_node_by_document_id(document.id)
            if node:
                # Update existing node
                self.content_hierarchy.update_node_metadata(node.id, metadata)
            else:
                # Create new node
                self.content_hierarchy.create_node(
                    name=document.title,
                    node_type=document.type,
                    parent_id=document.parent_id,
                    document_id=document.id,
                    metadata=metadata
                )
            
            # Index document
            self.search_index.index_document(document.id, document.content, metadata)
            
            # Process tags
            if 'tags' in metadata and isinstance(metadata['tags'], list):
                for tag_name in metadata['tags']:
                    # Get or create tag
                    tag = self.tag_manager.get_or_create_tag(tag_name)
                    
                    # Add tag to document
                    self.tag_manager.add_document_tag(document.id, tag.id)
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            return False
    
    def process_documents(self, documents: List[Document]) -> int:
        """
        Process multiple documents.
        
        Args:
            documents: The list of documents to process.
            
        Returns:
            The number of documents processed successfully.
        """
        success_count = 0
        
        for document in documents:
            if self.process_document(document):
                success_count += 1
        
        return success_count
    
    def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the organization system.
        
        Args:
            document_id: The ID of the document to remove.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Remove from hierarchy
            node = self.content_hierarchy.get_node_by_document_id(document_id)
            if node:
                self.content_hierarchy.delete_node(node.id)
            
            # Remove from search index
            self.search_index.remove_document(document_id)
            
            # Remove from tag manager
            tags = self.tag_manager.get_document_tags(document_id)
            for tag in tags:
                self.tag_manager.remove_document_tag(document_id, tag.id)
            
            return True
        
        except Exception as e:
            logger.error(f"Error removing document: {e}", exc_info=True)
            return False
    
    def search(self, query: str, max_results: int = 10, metadata_filter: Optional[Dict[str, Any]] = None,
             tag_ids: Optional[List[str]] = None, match_all_tags: bool = False) -> List[SearchResult]:
        """
        Search for documents matching a query.
        
        Args:
            query: The search query.
            max_results: The maximum number of results to return.
            metadata_filter: A dictionary of metadata key-value pairs to filter by.
            tag_ids: A list of tag IDs to filter by.
            match_all_tags: Whether to match all tags (AND) or any tag (OR).
            
        Returns:
            A list of search results.
        """
        try:
            # Get documents with tags
            document_ids = None
            if tag_ids:
                document_ids = self.tag_manager.get_documents_with_tags(tag_ids, match_all_tags)
                
                # If no documents match the tags, return empty results
                if not document_ids:
                    return []
            
            # Update metadata filter with document IDs
            if document_ids is not None:
                if metadata_filter is None:
                    metadata_filter = {}
                
                metadata_filter['document_id'] = list(document_ids)
            
            # Search for documents
            results = self.search_index.search(query, max_results, metadata_filter)
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            return []
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a document.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            The document metadata, or None if not found.
        """
        return self.search_index.get_document_metadata(document_id)
    
    def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a document.
        
        Args:
            document_id: The ID of the document.
            metadata: The new metadata for the document.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Update search index
            self.search_index.update_document_metadata(document_id, metadata)
            
            # Update hierarchy
            node = self.content_hierarchy.get_node_by_document_id(document_id)
            if node:
                self.content_hierarchy.update_node_metadata(node.id, metadata)
            
            # Update tags
            if 'tags' in metadata and isinstance(metadata['tags'], list):
                # Remove existing tags
                existing_tags = self.tag_manager.get_document_tags(document_id)
                for tag in existing_tags:
                    self.tag_manager.remove_document_tag(document_id, tag.id)
                
                # Add new tags
                for tag_name in metadata['tags']:
                    tag = self.tag_manager.get_or_create_tag(tag_name)
                    self.tag_manager.add_document_tag(document_id, tag.id)
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating document metadata: {e}", exc_info=True)
            return False
    
    def get_document_tags(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get tags for a document.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            A list of tag dictionaries.
        """
        try:
            tags = self.tag_manager.get_document_tags(document_id)
            return [tag.to_dict() for tag in tags]
        
        except Exception as e:
            logger.error(f"Error getting document tags: {e}", exc_info=True)
            return []
    
    def add_document_tag(self, document_id: str, tag_name: str) -> bool:
        """
        Add a tag to a document.
        
        Args:
            document_id: The ID of the document.
            tag_name: The name of the tag.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get or create tag
            tag = self.tag_manager.get_or_create_tag(tag_name)
            
            # Add tag to document
            success = self.tag_manager.add_document_tag(document_id, tag.id)
            
            # Update document metadata
            if success:
                metadata = self.search_index.get_document_metadata(document_id)
                if metadata:
                    if 'tags' not in metadata:
                        metadata['tags'] = []
                    
                    if tag_name not in metadata['tags']:
                        metadata['tags'].append(tag_name)
                        self.search_index.update_document_metadata(document_id, metadata)
            
            return success
        
        except Exception as e:
            logger.error(f"Error adding document tag: {e}", exc_info=True)
            return False
    
    def remove_document_tag(self, document_id: str, tag_name: str) -> bool:
        """
        Remove a tag from a document.
        
        Args:
            document_id: The ID of the document.
            tag_name: The name of the tag.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get tag by name
            tag = self.tag_manager.get_tag_by_name(tag_name)
            if not tag:
                logger.warning(f"Tag not found: {tag_name}")
                return False
            
            # Remove tag from document
            success = self.tag_manager.remove_document_tag(document_id, tag.id)
            
            # Update document metadata
            if success:
                metadata = self.search_index.get_document_metadata(document_id)
                if metadata and 'tags' in metadata:
                    if tag_name in metadata['tags']:
                        metadata['tags'].remove(tag_name)
                        self.search_index.update_document_metadata(document_id, metadata)
            
            return success
        
        except Exception as e:
            logger.error(f"Error removing document tag: {e}", exc_info=True)
            return False
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags.
        
        Returns:
            A list of tag dictionaries.
        """
        try:
            return [tag.to_dict() for tag in self.tag_manager.tags.values()]
        
        except Exception as e:
            logger.error(f"Error getting all tags: {e}", exc_info=True)
            return []
    
    def get_tag_by_name(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tag by name.
        
        Args:
            tag_name: The name of the tag.
            
        Returns:
            The tag dictionary, or None if not found.
        """
        try:
            tag = self.tag_manager.get_tag_by_name(tag_name)
            if tag:
                return tag.to_dict()
            return None
        
        except Exception as e:
            logger.error(f"Error getting tag by name: {e}", exc_info=True)
            return None
    
    def create_tag(self, tag_name: str, color: Optional[str] = None,
                 parent_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new tag.
        
        Args:
            tag_name: The name of the tag.
            color: The color of the tag, or None for default.
            parent_name: The name of the parent tag, or None for a root tag.
            metadata: Additional metadata for the tag.
            
        Returns:
            The tag dictionary, or None if creation failed.
        """
        try:
            # Check if tag already exists
            existing_tag = self.tag_manager.get_tag_by_name(tag_name)
            if existing_tag:
                logger.warning(f"Tag already exists: {tag_name}")
                return existing_tag.to_dict()
            
            # Get parent tag ID
            parent_id = None
            if parent_name:
                parent_tag = self.tag_manager.get_tag_by_name(parent_name)
                if parent_tag:
                    parent_id = parent_tag.id
                else:
                    logger.warning(f"Parent tag not found: {parent_name}")
            
            # Create tag
            tag = self.tag_manager.create_tag(tag_name, color, parent_id, metadata)
            
            return tag.to_dict()
        
        except Exception as e:
            logger.error(f"Error creating tag: {e}", exc_info=True)
            return None
    
    def update_tag(self, tag_name: str, new_name: Optional[str] = None, color: Optional[str] = None,
                 parent_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a tag.
        
        Args:
            tag_name: The name of the tag to update.
            new_name: The new name for the tag, or None to keep the current name.
            color: The new color for the tag, or None to keep the current color.
            parent_name: The name of the new parent tag, or None to keep the current parent.
            metadata: Additional metadata for the tag, or None to keep the current metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get tag by name
            tag = self.tag_manager.get_tag_by_name(tag_name)
            if not tag:
                logger.warning(f"Tag not found: {tag_name}")
                return False
            
            # Get parent tag ID
            parent_id = None
            if parent_name:
                parent_tag = self.tag_manager.get_tag_by_name(parent_name)
                if parent_tag:
                    parent_id = parent_tag.id
                else:
                    logger.warning(f"Parent tag not found: {parent_name}")
            
            # Update tag
            success = self.tag_manager.update_tag(tag.id, new_name, color, parent_id, metadata)
            
            # Update document metadata
            if success and new_name and new_name != tag_name:
                # Get documents with this tag
                document_ids = self.tag_manager.get_documents_with_tag(tag.id)
                
                # Update metadata for each document
                for document_id in document_ids:
                    metadata = self.search_index.get_document_metadata(document_id)
                    if metadata and 'tags' in metadata:
                        if tag_name in metadata['tags']:
                            metadata['tags'].remove(tag_name)
                            metadata['tags'].append(new_name)
                            self.search_index.update_document_metadata(document_id, metadata)
            
            return success
        
        except Exception as e:
            logger.error(f"Error updating tag: {e}", exc_info=True)
            return False
    
    def delete_tag(self, tag_name: str, recursive: bool = False) -> bool:
        """
        Delete a tag.
        
        Args:
            tag_name: The name of the tag to delete.
            recursive: Whether to delete child tags recursively.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get tag by name
            tag = self.tag_manager.get_tag_by_name(tag_name)
            if not tag:
                logger.warning(f"Tag not found: {tag_name}")
                return False
            
            # Get documents with this tag
            document_ids = self.tag_manager.get_documents_with_tag(tag.id)
            
            # Delete tag
            success = self.tag_manager.delete_tag(tag.id, recursive)
            
            # Update document metadata
            if success:
                for document_id in document_ids:
                    metadata = self.search_index.get_document_metadata(document_id)
                    if metadata and 'tags' in metadata:
                        if tag_name in metadata['tags']:
                            metadata['tags'].remove(tag_name)
                            self.search_index.update_document_metadata(document_id, metadata)
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting tag: {e}", exc_info=True)
            return False
    
    def get_hierarchy_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a hierarchy node by ID.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            The node dictionary, or None if not found.
        """
        try:
            node = self.content_hierarchy.get_node(node_id)
            if node:
                return node.to_dict()
            return None
        
        except Exception as e:
            logger.error(f"Error getting hierarchy node: {e}", exc_info=True)
            return None
    
    def get_hierarchy_node_by_document_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a hierarchy node by document ID.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            The node dictionary, or None if not found.
        """
        try:
            node = self.content_hierarchy.get_node_by_document_id(document_id)
            if node:
                return node.to_dict()
            return None
        
        except Exception as e:
            logger.error(f"Error getting hierarchy node by document ID: {e}", exc_info=True)
            return None
    
    def get_hierarchy_root_nodes(self) -> List[Dict[str, Any]]:
        """
        Get all root nodes in the hierarchy.
        
        Returns:
            A list of node dictionaries.
        """
        try:
            return [node.to_dict() for node in self.content_hierarchy.get_root_nodes()]
        
        except Exception as e:
            logger.error(f"Error getting hierarchy root nodes: {e}", exc_info=True)
            return []
    
    def create_hierarchy_node(self, name: str, node_type: str = "folder",
                            parent_id: Optional[str] = None, document_id: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new hierarchy node.
        
        Args:
            name: The name of the node.
            node_type: The type of the node (folder, document, etc.).
            parent_id: The ID of the parent node, or None for a root node.
            document_id: The ID of the associated document, or None if not associated.
            metadata: Additional metadata for the node.
            
        Returns:
            The node dictionary, or None if creation failed.
        """
        try:
            # Create node
            node = self.content_hierarchy.create_node(name, node_type, parent_id, document_id, metadata)
            
            return node.to_dict()
        
        except Exception as e:
            logger.error(f"Error creating hierarchy node: {e}", exc_info=True)
            return None
    
    def update_hierarchy_node(self, node_id: str, name: Optional[str] = None,
                            parent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a hierarchy node.
        
        Args:
            node_id: The ID of the node to update.
            name: The new name for the node, or None to keep the current name.
            parent_id: The ID of the new parent node, or None to keep the current parent.
            metadata: Additional metadata for the node, or None to keep the current metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get node
            node = self.content_hierarchy.get_node(node_id)
            if not node:
                logger.warning(f"Node not found: {node_id}")
                return False
            
            # Update name
            if name is not None:
                self.content_hierarchy.rename_node(node_id, name)
            
            # Update parent
            if parent_id is not None:
                self.content_hierarchy.move_node(node_id, parent_id)
            
            # Update metadata
            if metadata is not None:
                self.content_hierarchy.update_node_metadata(node_id, metadata)
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating hierarchy node: {e}", exc_info=True)
            return False
    
    def delete_hierarchy_node(self, node_id: str, recursive: bool = False) -> bool:
        """
        Delete a hierarchy node.
        
        Args:
            node_id: The ID of the node to delete.
            recursive: Whether to delete child nodes recursively.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            return self.content_hierarchy.delete_node(node_id, recursive)
        
        except Exception as e:
            logger.error(f"Error deleting hierarchy node: {e}", exc_info=True)
            return False
    
    def get_similar_documents(self, document_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get documents similar to a document.
        
        Args:
            document_id: The ID of the document.
            max_results: The maximum number of results to return.
            
        Returns:
            A list of document dictionaries.
        """
        try:
            # Get similar documents
            similar_docs = self.search_index.get_similar_documents(document_id, max_results)
            
            # Create result list
            results = []
            for doc_id, similarity in similar_docs:
                # Get document metadata
                metadata = self.search_index.get_document_metadata(doc_id)
                if metadata:
                    # Create result
                    result = {
                        'document_id': doc_id,
                        'similarity': similarity,
                        'title': metadata.get('title', doc_id),
                        'metadata': metadata
                    }
                    
                    results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting similar documents: {e}", exc_info=True)
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the content organization system.
        
        Returns:
            A dictionary of statistics.
        """
        try:
            stats = {
                'document_count': self.search_index.document_count,
                'term_count': self.search_index.term_count,
                'tag_count': len(self.tag_manager.tags),
                'hierarchy_node_count': len(self.content_hierarchy.nodes),
                'root_node_count': len(self.content_hierarchy.root_nodes),
                'average_document_length': 0,
                'average_tags_per_document': 0,
                'most_common_tags': [],
                'most_similar_documents': []
            }
            
            # Calculate average document length
            if stats['document_count'] > 0:
                total_length = sum(self.search_index.document_lengths.values())
                stats['average_document_length'] = total_length / stats['document_count']
            
            # Calculate average tags per document
            if stats['document_count'] > 0:
                total_tags = sum(len(tags) for tags in self.tag_manager.document_tags.values())
                stats['average_tags_per_document'] = total_tags / stats['document_count']
            
            # Get most common tags
            tag_counts = {}
            for tag_id, doc_ids in self.tag_manager.tag_documents.items():
                tag = self.tag_manager.get_tag(tag_id)
                if tag:
                    tag_counts[tag.name] = len(doc_ids)
            
            # Sort by count
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Limit to top 10
            stats['most_common_tags'] = sorted_tags[:10]
            
            # Get most similar document pairs
            document_pairs = []
            for doc_id in self.search_index.document_metadata:
                similar_docs = self.search_index.get_similar_documents(doc_id, 1)
                if similar_docs:
                    similar_id, similarity = similar_docs[0]
                    if similarity > 0:
                        # Create pair
                        pair = {
                            'document1_id': doc_id,
                            'document2_id': similar_id,
                            'similarity': similarity
                        }
                        
                        document_pairs.append(pair)
            
            # Sort by similarity
            sorted_pairs = sorted(document_pairs, key=lambda x: x['similarity'], reverse=True)
            
            # Limit to top 10
            stats['most_similar_documents'] = sorted_pairs[:10]
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)
            return {}
