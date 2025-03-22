#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag Manager for RebelSCRIBE.

This module provides functionality for managing tags and categories for content organization.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime
import uuid

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class Tag:
    """
    Represents a tag in the content organization system.
    
    This class provides functionality for managing a tag, including its metadata and relationships.
    """
    
    def __init__(self, tag_id: str, name: str, color: Optional[str] = None,
               parent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a Tag.
        
        Args:
            tag_id: The unique identifier for the tag.
            name: The name of the tag.
            color: The color of the tag, or None for default.
            parent_id: The ID of the parent tag, or None for a root tag.
            metadata: Additional metadata for the tag.
        """
        self.id = tag_id
        self.name = name
        self.color = color
        self.parent_id = parent_id
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tag to a dictionary representation.
        
        Returns:
            A dictionary representation of the tag.
        """
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'parent_id': self.parent_id,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """
        Create a tag from a dictionary representation.
        
        Args:
            data: The dictionary representation of the tag.
            
        Returns:
            A Tag instance.
        """
        tag = cls(
            tag_id=data['id'],
            name=data['name'],
            color=data.get('color'),
            parent_id=data.get('parent_id'),
            metadata=data.get('metadata', {})
        )
        
        tag.created_at = data.get('created_at', tag.created_at)
        tag.updated_at = data.get('updated_at', tag.updated_at)
        
        return tag


class TagManager:
    """
    Manages tags and categories for content organization.
    
    This class provides functionality for creating, updating, and organizing tags and categories.
    """
    
    def __init__(self):
        """Initialize the TagManager."""
        self.tags: Dict[str, Tag] = {}
        self.root_tags: Dict[str, Tag] = {}
        self.document_tags: Dict[str, Set[str]] = {}  # Maps document IDs to tag IDs
        self.tag_documents: Dict[str, Set[str]] = {}  # Maps tag IDs to document IDs
    
    def create_tag(self, name: str, color: Optional[str] = None,
                 parent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Tag:
        """
        Create a new tag.
        
        Args:
            name: The name of the tag.
            color: The color of the tag, or None for default.
            parent_id: The ID of the parent tag, or None for a root tag.
            metadata: Additional metadata for the tag.
            
        Returns:
            The created tag.
        """
        # Generate a unique ID
        tag_id = str(uuid.uuid4())
        
        # Create the tag
        tag = Tag(
            tag_id=tag_id,
            name=name,
            color=color,
            parent_id=parent_id,
            metadata=metadata
        )
        
        # Add to tags
        self.tags[tag_id] = tag
        
        # Add to root tags if it's a root tag
        if parent_id is None:
            self.root_tags[tag_id] = tag
        
        # Initialize tag documents
        self.tag_documents[tag_id] = set()
        
        return tag
    
    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """
        Get a tag by ID.
        
        Args:
            tag_id: The ID of the tag to get.
            
        Returns:
            The tag, or None if not found.
        """
        return self.tags.get(tag_id)
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        Get a tag by name.
        
        Args:
            name: The name of the tag to get.
            
        Returns:
            The tag, or None if not found.
        """
        for tag in self.tags.values():
            if tag.name.lower() == name.lower():
                return tag
        return None
    
    def get_or_create_tag(self, name: str, color: Optional[str] = None,
                        parent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Tag:
        """
        Get a tag by name, or create it if it doesn't exist.
        
        Args:
            name: The name of the tag.
            color: The color of the tag, or None for default.
            parent_id: The ID of the parent tag, or None for a root tag.
            metadata: Additional metadata for the tag.
            
        Returns:
            The tag.
        """
        tag = self.get_tag_by_name(name)
        if tag:
            return tag
        
        return self.create_tag(name, color, parent_id, metadata)
    
    def update_tag(self, tag_id: str, name: Optional[str] = None, color: Optional[str] = None,
                 parent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a tag.
        
        Args:
            tag_id: The ID of the tag to update.
            name: The new name for the tag, or None to keep the current name.
            color: The new color for the tag, or None to keep the current color.
            parent_id: The new parent ID for the tag, or None to keep the current parent ID.
            metadata: Additional metadata for the tag, or None to keep the current metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        tag = self.get_tag(tag_id)
        if not tag:
            logger.warning(f"Tag not found: {tag_id}")
            return False
        
        # Update name
        if name is not None:
            tag.name = name
        
        # Update color
        if color is not None:
            tag.color = color
        
        # Update parent ID
        if parent_id is not None:
            # Check if parent exists
            if parent_id and parent_id not in self.tags:
                logger.warning(f"Parent tag not found: {parent_id}")
                return False
            
            # Update parent ID
            old_parent_id = tag.parent_id
            tag.parent_id = parent_id
            
            # Update root tags
            if old_parent_id is None and parent_id is not None:
                # No longer a root tag
                if tag_id in self.root_tags:
                    del self.root_tags[tag_id]
            elif old_parent_id is not None and parent_id is None:
                # Now a root tag
                self.root_tags[tag_id] = tag
        
        # Update metadata
        if metadata is not None:
            tag.metadata.update(metadata)
        
        # Update timestamp
        tag.updated_at = datetime.now().isoformat()
        
        return True
    
    def delete_tag(self, tag_id: str, recursive: bool = False) -> bool:
        """
        Delete a tag.
        
        Args:
            tag_id: The ID of the tag to delete.
            recursive: Whether to delete child tags recursively.
            
        Returns:
            True if successful, False otherwise.
        """
        tag = self.get_tag(tag_id)
        if not tag:
            logger.warning(f"Tag not found: {tag_id}")
            return False
        
        # Check if tag has children
        children = self.get_child_tags(tag_id)
        if children and not recursive:
            logger.warning(f"Tag has children and recursive is False: {tag_id}")
            return False
        
        # Delete children recursively if requested
        if recursive:
            for child in children:
                self.delete_tag(child.id, recursive=True)
        
        # Remove from document tags
        for document_id in list(self.tag_documents.get(tag_id, set())):
            if document_id in self.document_tags:
                self.document_tags[document_id].discard(tag_id)
        
        # Remove from tag documents
        if tag_id in self.tag_documents:
            del self.tag_documents[tag_id]
        
        # Remove from root tags if it's a root tag
        if tag.parent_id is None and tag_id in self.root_tags:
            del self.root_tags[tag_id]
        
        # Remove from tags
        del self.tags[tag_id]
        
        return True
    
    def get_root_tags(self) -> List[Tag]:
        """
        Get all root tags.
        
        Returns:
            A list of root tags.
        """
        return list(self.root_tags.values())
    
    def get_child_tags(self, parent_id: str) -> List[Tag]:
        """
        Get all child tags of a parent tag.
        
        Args:
            parent_id: The ID of the parent tag.
            
        Returns:
            A list of child tags.
        """
        return [tag for tag in self.tags.values() if tag.parent_id == parent_id]
    
    def get_descendant_tags(self, parent_id: str) -> List[Tag]:
        """
        Get all descendant tags of a parent tag.
        
        Args:
            parent_id: The ID of the parent tag.
            
        Returns:
            A list of descendant tags.
        """
        descendants = []
        
        def collect_descendants(tag_id: str):
            children = self.get_child_tags(tag_id)
            descendants.extend(children)
            for child in children:
                collect_descendants(child.id)
        
        collect_descendants(parent_id)
        
        return descendants
    
    def get_ancestor_tags(self, tag_id: str) -> List[Tag]:
        """
        Get all ancestor tags of a tag.
        
        Args:
            tag_id: The ID of the tag.
            
        Returns:
            A list of ancestor tags.
        """
        ancestors = []
        current_id = tag_id
        
        while True:
            tag = self.get_tag(current_id)
            if not tag or not tag.parent_id:
                break
            
            parent = self.get_tag(tag.parent_id)
            if not parent:
                break
            
            ancestors.append(parent)
            current_id = parent.id
        
        return ancestors
    
    def get_tag_path(self, tag_id: str) -> List[Tag]:
        """
        Get the path to a tag.
        
        Args:
            tag_id: The ID of the tag.
            
        Returns:
            A list of tags from the root to the specified tag.
        """
        tag = self.get_tag(tag_id)
        if not tag:
            return []
        
        path = [tag]
        current_id = tag_id
        
        while True:
            current_tag = self.get_tag(current_id)
            if not current_tag or not current_tag.parent_id:
                break
            
            parent = self.get_tag(current_tag.parent_id)
            if not parent:
                break
            
            path.insert(0, parent)
            current_id = parent.id
        
        return path
    
    def add_document_tag(self, document_id: str, tag_id: str) -> bool:
        """
        Add a tag to a document.
        
        Args:
            document_id: The ID of the document.
            tag_id: The ID of the tag.
            
        Returns:
            True if successful, False otherwise.
        """
        # Check if tag exists
        if tag_id not in self.tags:
            logger.warning(f"Tag not found: {tag_id}")
            return False
        
        # Initialize document tags if needed
        if document_id not in self.document_tags:
            self.document_tags[document_id] = set()
        
        # Add tag to document
        self.document_tags[document_id].add(tag_id)
        
        # Add document to tag
        if tag_id not in self.tag_documents:
            self.tag_documents[tag_id] = set()
        
        self.tag_documents[tag_id].add(document_id)
        
        return True
    
    def remove_document_tag(self, document_id: str, tag_id: str) -> bool:
        """
        Remove a tag from a document.
        
        Args:
            document_id: The ID of the document.
            tag_id: The ID of the tag.
            
        Returns:
            True if successful, False otherwise.
        """
        # Check if document has tags
        if document_id not in self.document_tags:
            logger.warning(f"Document has no tags: {document_id}")
            return False
        
        # Check if document has the tag
        if tag_id not in self.document_tags[document_id]:
            logger.warning(f"Document does not have tag: {tag_id}")
            return False
        
        # Remove tag from document
        self.document_tags[document_id].remove(tag_id)
        
        # Remove document from tag
        if tag_id in self.tag_documents:
            self.tag_documents[tag_id].discard(document_id)
        
        return True
    
    def get_document_tags(self, document_id: str) -> List[Tag]:
        """
        Get all tags for a document.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            A list of tags.
        """
        if document_id not in self.document_tags:
            return []
        
        return [self.tags[tag_id] for tag_id in self.document_tags[document_id]
                if tag_id in self.tags]
    
    def get_documents_with_tag(self, tag_id: str, include_descendants: bool = False) -> Set[str]:
        """
        Get all documents with a tag.
        
        Args:
            tag_id: The ID of the tag.
            include_descendants: Whether to include documents with descendant tags.
            
        Returns:
            A set of document IDs.
        """
        if tag_id not in self.tag_documents:
            return set()
        
        documents = set(self.tag_documents[tag_id])
        
        if include_descendants:
            for descendant in self.get_descendant_tags(tag_id):
                if descendant.id in self.tag_documents:
                    documents.update(self.tag_documents[descendant.id])
        
        return documents
    
    def get_documents_with_tags(self, tag_ids: List[str], match_all: bool = False) -> Set[str]:
        """
        Get all documents with the specified tags.
        
        Args:
            tag_ids: The IDs of the tags.
            match_all: Whether to match all tags (AND) or any tag (OR).
            
        Returns:
            A set of document IDs.
        """
        if not tag_ids:
            return set()
        
        if match_all:
            # Match all tags (AND)
            result = None
            for tag_id in tag_ids:
                documents = self.get_documents_with_tag(tag_id)
                if result is None:
                    result = documents
                else:
                    result = result.intersection(documents)
            
            return result or set()
        else:
            # Match any tag (OR)
            result = set()
            for tag_id in tag_ids:
                result.update(self.get_documents_with_tag(tag_id))
            
            return result
    
    def search_tags(self, query: str) -> List[Tag]:
        """
        Search for tags matching a query.
        
        Args:
            query: The search query.
            
        Returns:
            A list of matching tags.
        """
        return [tag for tag in self.tags.values()
                if query.lower() in tag.name.lower()]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tag manager to a dictionary representation.
        
        Returns:
            A dictionary representation of the tag manager.
        """
        return {
            'tags': [tag.to_dict() for tag in self.tags.values()],
            'document_tags': {doc_id: list(tag_ids) for doc_id, tag_ids in self.document_tags.items()}
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load the tag manager from a dictionary representation.
        
        Args:
            data: The dictionary representation of the tag manager.
        """
        # Clear existing data
        self.tags = {}
        self.root_tags = {}
        self.document_tags = {}
        self.tag_documents = {}
        
        # Load tags
        for tag_data in data.get('tags', []):
            tag = Tag.from_dict(tag_data)
            self.tags[tag.id] = tag
            
            # Add to root tags if it's a root tag
            if tag.parent_id is None:
                self.root_tags[tag.id] = tag
            
            # Initialize tag documents
            self.tag_documents[tag.id] = set()
        
        # Load document tags
        for doc_id, tag_ids in data.get('document_tags', {}).items():
            self.document_tags[doc_id] = set(tag_ids)
            
            # Update tag documents
            for tag_id in tag_ids:
                if tag_id in self.tags:
                    if tag_id not in self.tag_documents:
                        self.tag_documents[tag_id] = set()
                    
                    self.tag_documents[tag_id].add(doc_id)
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Save the tag manager to a file.
        
        Args:
            file_path: The path to save the tag manager to.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert to dictionary
            data = self.to_dict()
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving tag manager to file: {e}", exc_info=True)
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load the tag manager from a file.
        
        Args:
            file_path: The path to load the tag manager from.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Tag manager file not found: {file_path}")
                return False
            
            # Read from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load from dictionary
            self.from_dict(data)
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading tag manager from file: {e}", exc_info=True)
            return False
