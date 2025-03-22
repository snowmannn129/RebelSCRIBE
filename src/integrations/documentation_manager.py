#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE Documentation Manager for RebelDESK.

This module provides functionality for managing RebelSCRIBE documentation within RebelDESK.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Union

# Add RebelSCRIBE to path
rebelsuite_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
rebelscribe_dir = os.path.join(rebelsuite_root, "RebelSCRIBE")
if rebelscribe_dir not in sys.path:
    sys.path.insert(0, rebelscribe_dir)

# Import RebelSCRIBE modules
from src.backend.models.documentation import Documentation
from src.backend.services.documentation_manager import DocumentationManager
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class RebelSCRIBEManager:
    """
    RebelSCRIBE Documentation Manager for RebelDESK.
    
    This class provides functionality for managing RebelSCRIBE documentation within RebelDESK,
    including loading, saving, and searching documentation.
    """
    
    def __init__(self, rebelsuite_root: str = None):
        """
        Initialize the RebelSCRIBE Manager.
        
        Args:
            rebelsuite_root: The root directory of the RebelSUITE project.
                             If None, it will try to detect it automatically.
        """
        # Set RebelSUITE root directory
        if rebelsuite_root:
            self.rebelsuite_root = rebelsuite_root
        else:
            # Try to detect RebelSUITE root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.rebelsuite_root = self._find_rebelsuite_root(current_dir)
            if not self.rebelsuite_root:
                raise ValueError("Could not detect RebelSUITE root directory")
        
        # Set RebelSCRIBE directory
        self.rebelscribe_dir = os.path.join(self.rebelsuite_root, "RebelSCRIBE")
        if not os.path.exists(self.rebelscribe_dir):
            raise ValueError(f"RebelSCRIBE directory not found: {self.rebelscribe_dir}")
        
        # Create documentation manager
        self.doc_manager = DocumentationManager(self.rebelscribe_dir)
        
        logger.info(f"RebelSCRIBE Manager initialized with RebelSUITE root: {self.rebelsuite_root}")
    
    def _find_rebelsuite_root(self, start_dir: str) -> Optional[str]:
        """
        Find the RebelSUITE root directory by looking for specific markers.
        
        Args:
            start_dir: The directory to start the search from.
            
        Returns:
            The RebelSUITE root directory, or None if not found.
        """
        current_dir = start_dir
        max_levels = 5  # Maximum number of parent directories to check
        
        for _ in range(max_levels):
            # Check if this is the RebelSUITE root directory
            if os.path.exists(os.path.join(current_dir, "RebelCAD")) and \
               os.path.exists(os.path.join(current_dir, "RebelSCRIBE")) and \
               os.path.exists(os.path.join(current_dir, "RebelSUITE_Integration_Tracking.md")):
                return current_dir
            
            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached the root of the filesystem
                break
            current_dir = parent_dir
        
        return None
    
    def get_documentation(self, doc_id: str) -> Optional[Documentation]:
        """
        Get a documentation document by ID.
        
        Args:
            doc_id: The document ID.
            
        Returns:
            The documentation, or None if not found.
        """
        return self.doc_manager.get_documentation(doc_id)
    
    def get_all_documentation(self) -> List[Documentation]:
        """
        Get all documentation documents.
        
        Returns:
            A list of all documentation documents.
        """
        return self.doc_manager.get_all_documents()
    
    def search_documentation(self, query: str) -> List[Documentation]:
        """
        Search for documentation documents.
        
        Args:
            query: The search query.
            
        Returns:
            A list of matching documentation documents.
        """
        return self.doc_manager.search_documents(query)
    
    def create_documentation(self, title: str, doc_type: str, content: str, **kwargs) -> Optional[Documentation]:
        """
        Create a new documentation document.
        
        Args:
            title: The document title.
            doc_type: The document type.
            content: The document content.
            **kwargs: Additional document attributes.
            
        Returns:
            The created documentation, or None if creation failed.
        """
        return self.doc_manager.create_documentation(title, doc_type, content=content, **kwargs)
    
    def update_documentation(self, doc_id: str, **kwargs) -> bool:
        """
        Update a documentation document.
        
        Args:
            doc_id: The document ID.
            **kwargs: The document attributes to update.
            
        Returns:
            True if successful, False otherwise.
        """
        doc = self.doc_manager.get_documentation(doc_id)
        if not doc:
            logger.error(f"Documentation not found: {doc_id}")
            return False
        
        # Update document attributes
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        
        # Save document
        return self.doc_manager.save_document(doc_id)
    
    def delete_documentation(self, doc_id: str) -> bool:
        """
        Delete a documentation document.
        
        Args:
            doc_id: The document ID.
            
        Returns:
            True if successful, False otherwise.
        """
        return self.doc_manager.delete_document(doc_id)
    
    def export_documentation(self, doc_id: str, format: str, output_path: str) -> bool:
        """
        Export a documentation document to a file.
        
        Args:
            doc_id: The document ID.
            format: The export format ("html" or "markdown").
            output_path: The output file path.
            
        Returns:
            True if successful, False otherwise.
        """
        if format.lower() == "html":
            return self.doc_manager.export_html_documentation(doc_id, output_path)
        elif format.lower() in ["markdown", "md"]:
            return self.doc_manager.export_markdown_documentation(doc_id, output_path)
        else:
            logger.error(f"Unsupported export format: {format}")
            return False
    
    def generate_static_site(self, output_dir: str, doc_ids: List[str] = None) -> bool:
        """
        Generate a static documentation site.
        
        Args:
            output_dir: The output directory.
            doc_ids: A list of document IDs to include, or None for all documents.
            
        Returns:
            True if successful, False otherwise.
        """
        return self.doc_manager.generate_static_site(output_dir, doc_ids)
