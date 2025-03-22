#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE Documentation Browser for RebelDESK.

This module provides functionality for browsing and searching RebelSCRIBE documentation within RebelDESK.
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
from src.utils.logging_utils import get_logger

# Import RebelDESK modules
# These would be imported from RebelDESK, but we're just defining the interface here
# from rebeldesk.ui import BrowserWidget

logger = get_logger(__name__)

class RebelSCRIBEBrowser:
    """
    RebelSCRIBE Documentation Browser for RebelDESK.
    
    This class provides functionality for browsing and searching RebelSCRIBE documentation within RebelDESK,
    including a tree view, search functionality, and filtering.
    """
    
    def __init__(self, rebelsuite_root: str = None):
        """
        Initialize the RebelSCRIBE Browser.
        
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
        
        # Initialize browser components
        self.documents = []
        self.search_index = {}
        
        logger.info(f"RebelSCRIBE Browser initialized with RebelSUITE root: {self.rebelsuite_root}")
    
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
    
    def create_browser_widget(self):
        """
        Create a browser widget for RebelDESK.
        
        Returns:
            A browser widget that can be embedded in RebelDESK.
        """
        # This would create a PyQt widget that can be embedded in RebelDESK
        # For now, we'll just return a placeholder
        return {
            "type": "browser_widget",
            "name": "RebelSCRIBE Documentation Browser"
        }
    
    def load_documents(self, documents: List[Documentation]) -> bool:
        """
        Load documents into the browser.
        
        Args:
            documents: The documents to load.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.documents = documents
            self._build_search_index()
            logger.info(f"Loaded {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error loading documents: {e}", exc_info=True)
            return False
    
    def _build_search_index(self) -> None:
        """
        Build a search index for the loaded documents.
        """
        self.search_index = {}
        
        for i, doc in enumerate(self.documents):
            # Add terms to index
            terms = set()
            
            # Add title terms
            title_terms = re.findall(r'\w+', doc.title.lower())
            terms.update(title_terms)
            
            # Add content terms
            if doc.content:
                content_terms = re.findall(r'\w+', doc.content.lower())
                terms.update(content_terms)
            
            # Add parameter terms
            for param in doc.parameters:
                param_terms = re.findall(r'\w+', param["name"].lower())
                terms.update(param_terms)
                
                if param["description"]:
                    param_desc_terms = re.findall(r'\w+', param["description"].lower())
                    terms.update(param_desc_terms)
            
            # Add return terms
            if doc.returns:
                return_terms = re.findall(r'\w+', doc.returns.lower())
                terms.update(return_terms)
            
            # Add exception terms
            for exc in doc.exceptions:
                exc_terms = re.findall(r'\w+', exc["type"].lower())
                terms.update(exc_terms)
                
                if exc["description"]:
                    exc_desc_terms = re.findall(r'\w+', exc["description"].lower())
                    terms.update(exc_desc_terms)
            
            # Add terms to index
            for term in terms:
                if term not in self.search_index:
                    self.search_index[term] = []
                
                if i not in self.search_index[term]:
                    self.search_index[term].append(i)
    
    def search(self, query: str) -> List[Documentation]:
        """
        Search for documents.
        
        Args:
            query: The search query.
            
        Returns:
            A list of matching documents.
        """
        if not query:
            return self.documents
        
        # Split query into terms
        query_terms = re.findall(r'\w+', query.lower())
        
        # Find matching documents
        matching_indices = set()
        for term in query_terms:
            if term in self.search_index:
                if not matching_indices:
                    matching_indices = set(self.search_index[term])
                else:
                    matching_indices &= set(self.search_index[term])
        
        # Return matching documents
        return [self.documents[i] for i in matching_indices]
    
    def filter_by_type(self, doc_type: str) -> List[Documentation]:
        """
        Filter documents by type.
        
        Args:
            doc_type: The document type.
            
        Returns:
            A list of matching documents.
        """
        return [doc for doc in self.documents if doc.type == doc_type]
    
    def filter_by_component(self, component: str) -> List[Documentation]:
        """
        Filter documents by component.
        
        Args:
            component: The component name.
            
        Returns:
            A list of matching documents.
        """
        return [doc for doc in self.documents if doc.component == component]
    
    def get_document_by_id(self, doc_id: str) -> Optional[Documentation]:
        """
        Get a document by ID.
        
        Args:
            doc_id: The document ID.
            
        Returns:
            The document, or None if not found.
        """
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def get_document_by_title(self, title: str) -> Optional[Documentation]:
        """
        Get a document by title.
        
        Args:
            title: The document title.
            
        Returns:
            The document, or None if not found.
        """
        for doc in self.documents:
            if doc.title == title:
                return doc
        return None
