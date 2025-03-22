#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content Hierarchy for RebelSCRIBE.

This module provides functionality for managing the hierarchical organization of content.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime
import uuid

from src.utils.logging_utils import get_logger
from src.backend.models.document import Document

logger = get_logger(__name__)

class HierarchyNode:
    """
    Represents a node in the content hierarchy.
    
    This class provides functionality for managing a node in the content hierarchy,
    including its children and metadata.
    """
    
    def __init__(self, node_id: str, name: str, node_type: str = "folder",
                parent_id: Optional[str] = None, document_id: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a HierarchyNode.
        
        Args:
            node_id: The unique identifier for the node.
            name: The name of the node.
            node_type: The type of the node (folder, document, etc.).
            parent_id: The ID of the parent node, or None for a root node.
            document_id: The ID of the associated document, or None if not associated.
            metadata: Additional metadata for the node.
        """
        self.id = node_id
        self.name = name
        self.type = node_type
        self.parent_id = parent_id
        self.document_id = document_id
        self.metadata = metadata or {}
        self.children: Dict[str, 'HierarchyNode'] = {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def add_child(self, child: 'HierarchyNode') -> None:
        """
        Add a child node to this node.
        
        Args:
            child: The child node to add.
        """
        self.children[child.id] = child
        child.parent_id = self.id
        self.updated_at = datetime.now().isoformat()
    
    def remove_child(self, child_id: str) -> Optional['HierarchyNode']:
        """
        Remove a child node from this node.
        
        Args:
            child_id: The ID of the child node to remove.
            
        Returns:
            The removed child node, or None if not found.
        """
        if child_id in self.children:
            child = self.children[child_id]
            del self.children[child_id]
            self.updated_at = datetime.now().isoformat()
            return child
        return None
    
    def get_child(self, child_id: str) -> Optional['HierarchyNode']:
        """
        Get a child node by ID.
        
        Args:
            child_id: The ID of the child node to get.
            
        Returns:
            The child node, or None if not found.
        """
        return self.children.get(child_id)
    
    def get_children(self) -> List['HierarchyNode']:
        """
        Get all child nodes.
        
        Returns:
            A list of child nodes.
        """
        return list(self.children.values())
    
    def get_child_count(self) -> int:
        """
        Get the number of child nodes.
        
        Returns:
            The number of child nodes.
        """
        return len(self.children)
    
    def has_children(self) -> bool:
        """
        Check if this node has any children.
        
        Returns:
            True if this node has children, False otherwise.
        """
        return len(self.children) > 0
    
    def is_leaf(self) -> bool:
        """
        Check if this node is a leaf node (has no children).
        
        Returns:
            True if this node is a leaf node, False otherwise.
        """
        return len(self.children) == 0
    
    def is_root(self) -> bool:
        """
        Check if this node is a root node (has no parent).
        
        Returns:
            True if this node is a root node, False otherwise.
        """
        return self.parent_id is None
    
    def get_path(self) -> List[str]:
        """
        Get the path to this node.
        
        Returns:
            A list of node IDs from the root to this node.
        """
        if self.parent_id is None:
            return [self.id]
        
        # This will be filled in by the ContentHierarchy class
        return [self.id]
    
    def get_depth(self) -> int:
        """
        Get the depth of this node in the hierarchy.
        
        Returns:
            The depth of this node (0 for root nodes).
        """
        if self.parent_id is None:
            return 0
        
        # This will be filled in by the ContentHierarchy class
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node to a dictionary representation.
        
        Returns:
            A dictionary representation of the node.
        """
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'parent_id': self.parent_id,
            'document_id': self.document_id,
            'metadata': self.metadata,
            'children': [child.to_dict() for child in self.children.values()],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HierarchyNode':
        """
        Create a node from a dictionary representation.
        
        Args:
            data: The dictionary representation of the node.
            
        Returns:
            A HierarchyNode instance.
        """
        node = cls(
            node_id=data['id'],
            name=data['name'],
            node_type=data['type'],
            parent_id=data.get('parent_id'),
            document_id=data.get('document_id'),
            metadata=data.get('metadata', {})
        )
        
        node.created_at = data.get('created_at', node.created_at)
        node.updated_at = data.get('updated_at', node.updated_at)
        
        # Add children
        for child_data in data.get('children', []):
            child = cls.from_dict(child_data)
            node.add_child(child)
        
        return node


class ContentHierarchy:
    """
    Manages the hierarchical organization of content.
    
    This class provides functionality for managing the hierarchical organization of content,
    including creating, updating, and navigating the hierarchy.
    """
    
    def __init__(self):
        """Initialize the ContentHierarchy."""
        self.nodes: Dict[str, HierarchyNode] = {}
        self.root_nodes: Dict[str, HierarchyNode] = {}
        self.document_map: Dict[str, str] = {}  # Maps document IDs to node IDs
    
    def create_node(self, name: str, node_type: str = "folder",
                  parent_id: Optional[str] = None, document_id: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> HierarchyNode:
        """
        Create a new node in the hierarchy.
        
        Args:
            name: The name of the node.
            node_type: The type of the node (folder, document, etc.).
            parent_id: The ID of the parent node, or None for a root node.
            document_id: The ID of the associated document, or None if not associated.
            metadata: Additional metadata for the node.
            
        Returns:
            The created node.
        """
        # Generate a unique ID
        node_id = str(uuid.uuid4())
        
        # Create the node
        node = HierarchyNode(
            node_id=node_id,
            name=name,
            node_type=node_type,
            parent_id=parent_id,
            document_id=document_id,
            metadata=metadata
        )
        
        # Add to nodes
        self.nodes[node_id] = node
        
        # Add to document map if associated with a document
        if document_id:
            self.document_map[document_id] = node_id
        
        # Add to parent if specified
        if parent_id:
            parent = self.get_node(parent_id)
            if parent:
                parent.add_child(node)
            else:
                logger.warning(f"Parent node not found: {parent_id}")
                # Make it a root node
                self.root_nodes[node_id] = node
        else:
            # Add to root nodes
            self.root_nodes[node_id] = node
        
        return node
    
    def get_node(self, node_id: str) -> Optional[HierarchyNode]:
        """
        Get a node by ID.
        
        Args:
            node_id: The ID of the node to get.
            
        Returns:
            The node, or None if not found.
        """
        return self.nodes.get(node_id)
    
    def get_node_by_document_id(self, document_id: str) -> Optional[HierarchyNode]:
        """
        Get a node by document ID.
        
        Args:
            document_id: The ID of the document.
            
        Returns:
            The node associated with the document, or None if not found.
        """
        node_id = self.document_map.get(document_id)
        if node_id:
            return self.get_node(node_id)
        return None
    
    def get_root_nodes(self) -> List[HierarchyNode]:
        """
        Get all root nodes.
        
        Returns:
            A list of root nodes.
        """
        return list(self.root_nodes.values())
    
    def get_node_path(self, node_id: str) -> List[HierarchyNode]:
        """
        Get the path to a node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A list of nodes from the root to the specified node.
        """
        node = self.get_node(node_id)
        if not node:
            return []
        
        path = [node]
        current = node
        
        while current.parent_id:
            parent = self.get_node(current.parent_id)
            if not parent:
                break
            path.insert(0, parent)
            current = parent
        
        return path
    
    def get_node_depth(self, node_id: str) -> int:
        """
        Get the depth of a node in the hierarchy.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            The depth of the node (0 for root nodes).
        """
        path = self.get_node_path(node_id)
        return len(path) - 1
    
    def move_node(self, node_id: str, new_parent_id: Optional[str] = None) -> bool:
        """
        Move a node to a new parent.
        
        Args:
            node_id: The ID of the node to move.
            new_parent_id: The ID of the new parent node, or None to make it a root node.
            
        Returns:
            True if successful, False otherwise.
        """
        node = self.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return False
        
        # Remove from current parent
        if node.parent_id:
            parent = self.get_node(node.parent_id)
            if parent:
                parent.remove_child(node_id)
            
            # Remove from root nodes if it was a root node
            if node_id in self.root_nodes:
                del self.root_nodes[node_id]
        
        # Add to new parent
        if new_parent_id:
            new_parent = self.get_node(new_parent_id)
            if not new_parent:
                logger.warning(f"New parent node not found: {new_parent_id}")
                # Make it a root node
                node.parent_id = None
                self.root_nodes[node_id] = node
                return False
            
            new_parent.add_child(node)
            
            # Remove from root nodes if it was a root node
            if node_id in self.root_nodes:
                del self.root_nodes[node_id]
        else:
            # Make it a root node
            node.parent_id = None
            self.root_nodes[node_id] = node
        
        return True
    
    def delete_node(self, node_id: str, recursive: bool = False) -> bool:
        """
        Delete a node from the hierarchy.
        
        Args:
            node_id: The ID of the node to delete.
            recursive: Whether to delete child nodes recursively.
            
        Returns:
            True if successful, False otherwise.
        """
        node = self.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return False
        
        # Check if node has children
        if node.has_children() and not recursive:
            logger.warning(f"Node has children and recursive is False: {node_id}")
            return False
        
        # Delete children recursively if requested
        if recursive:
            for child_id in list(node.children.keys()):
                self.delete_node(child_id, recursive=True)
        
        # Remove from parent
        if node.parent_id:
            parent = self.get_node(node.parent_id)
            if parent:
                parent.remove_child(node_id)
        
        # Remove from root nodes if it was a root node
        if node_id in self.root_nodes:
            del self.root_nodes[node_id]
        
        # Remove from document map if associated with a document
        if node.document_id and node.document_id in self.document_map:
            del self.document_map[node.document_id]
        
        # Remove from nodes
        del self.nodes[node_id]
        
        return True
    
    def rename_node(self, node_id: str, new_name: str) -> bool:
        """
        Rename a node.
        
        Args:
            node_id: The ID of the node to rename.
            new_name: The new name for the node.
            
        Returns:
            True if successful, False otherwise.
        """
        node = self.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return False
        
        node.name = new_name
        node.updated_at = datetime.now().isoformat()
        
        return True
    
    def update_node_metadata(self, node_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update a node's metadata.
        
        Args:
            node_id: The ID of the node to update.
            metadata: The new metadata for the node.
            
        Returns:
            True if successful, False otherwise.
        """
        node = self.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return False
        
        node.metadata.update(metadata)
        node.updated_at = datetime.now().isoformat()
        
        return True
    
    def get_node_children(self, node_id: str) -> List[HierarchyNode]:
        """
        Get a node's children.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A list of child nodes.
        """
        node = self.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return []
        
        return node.get_children()
    
    def get_node_descendants(self, node_id: str) -> List[HierarchyNode]:
        """
        Get all descendants of a node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A list of descendant nodes.
        """
        node = self.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return []
        
        descendants = []
        
        def collect_descendants(n: HierarchyNode):
            for child in n.get_children():
                descendants.append(child)
                collect_descendants(child)
        
        collect_descendants(node)
        
        return descendants
    
    def get_node_ancestors(self, node_id: str) -> List[HierarchyNode]:
        """
        Get all ancestors of a node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A list of ancestor nodes.
        """
        path = self.get_node_path(node_id)
        if not path:
            return []
        
        # Remove the node itself from the path
        return path[:-1]
    
    def get_node_siblings(self, node_id: str) -> List[HierarchyNode]:
        """
        Get all siblings of a node.
        
        Args:
            node_id: The ID of the node.
            
        Returns:
            A list of sibling nodes.
        """
        node = self.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return []
        
        if node.parent_id is None:
            # Root node, return other root nodes
            return [n for n in self.root_nodes.values() if n.id != node_id]
        
        parent = self.get_node(node.parent_id)
        if not parent:
            logger.warning(f"Parent node not found: {node.parent_id}")
            return []
        
        return [n for n in parent.get_children() if n.id != node_id]
    
    def search_nodes(self, query: str, node_type: Optional[str] = None,
                   metadata_filter: Optional[Dict[str, Any]] = None) -> List[HierarchyNode]:
        """
        Search for nodes matching a query.
        
        Args:
            query: The search query.
            node_type: The type of nodes to search for, or None for all types.
            metadata_filter: A dictionary of metadata key-value pairs to filter by.
            
        Returns:
            A list of matching nodes.
        """
        results = []
        
        for node in self.nodes.values():
            # Check node type
            if node_type and node.type != node_type:
                continue
            
            # Check metadata filter
            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    if key not in node.metadata or node.metadata[key] != value:
                        match = False
                        break
                
                if not match:
                    continue
            
            # Check query
            if query.lower() in node.name.lower():
                results.append(node)
                continue
            
            # Check metadata
            for key, value in node.metadata.items():
                if isinstance(value, str) and query.lower() in value.lower():
                    results.append(node)
                    break
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the hierarchy to a dictionary representation.
        
        Returns:
            A dictionary representation of the hierarchy.
        """
        return {
            'root_nodes': [node.to_dict() for node in self.root_nodes.values()],
            'document_map': self.document_map
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load the hierarchy from a dictionary representation.
        
        Args:
            data: The dictionary representation of the hierarchy.
        """
        # Clear existing data
        self.nodes = {}
        self.root_nodes = {}
        self.document_map = {}
        
        # Load document map
        self.document_map = data.get('document_map', {})
        
        # Load root nodes
        for node_data in data.get('root_nodes', []):
            node = HierarchyNode.from_dict(node_data)
            self.root_nodes[node.id] = node
            self._add_node_recursive(node)
    
    def _add_node_recursive(self, node: HierarchyNode) -> None:
        """
        Add a node and its children to the hierarchy recursively.
        
        Args:
            node: The node to add.
        """
        self.nodes[node.id] = node
        
        for child in node.get_children():
            self._add_node_recursive(child)
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Save the hierarchy to a file.
        
        Args:
            file_path: The path to save the hierarchy to.
            
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
            logger.error(f"Error saving hierarchy to file: {e}", exc_info=True)
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load the hierarchy from a file.
        
        Args:
            file_path: The path to load the hierarchy from.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Hierarchy file not found: {file_path}")
                return False
            
            # Read from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load from dictionary
            self.from_dict(data)
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading hierarchy from file: {e}", exc_info=True)
            return False
    
    def create_from_documents(self, documents: List[Document]) -> None:
        """
        Create a hierarchy from a list of documents.
        
        Args:
            documents: The list of documents to create the hierarchy from.
        """
        # Clear existing data
        self.nodes = {}
        self.root_nodes = {}
        self.document_map = {}
        
        # Create a map of document IDs to documents
        document_map = {doc.id: doc for doc in documents}
        
        # Create nodes for each document
        for doc in documents:
            # Create node
            node = self.create_node(
                name=doc.title,
                node_type="document",
                parent_id=doc.parent_id,
                document_id=doc.id,
                metadata=doc.metadata if hasattr(doc, 'metadata') else {}
            )
            
            # Add to document map
            self.document_map[doc.id] = node.id
        
        # Update parent-child relationships
        for doc in documents:
            if doc.parent_id:
                # Get parent node
                parent_node_id = self.document_map.get(doc.parent_id)
                if parent_node_id:
                    # Get child node
                    child_node_id = self.document_map.get(doc.id)
                    if child_node_id:
                        # Move child to parent
                        self.move_node(child_node_id, parent_node_id)
