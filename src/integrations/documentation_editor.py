#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE Documentation Editor for RebelDESK.

This module provides functionality for editing RebelSCRIBE documentation within RebelDESK.
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
# from rebeldesk.editor import Editor
# from rebeldesk.ui import EditorWidget

logger = get_logger(__name__)

class RebelSCRIBEEditor:
    """
    RebelSCRIBE Documentation Editor for RebelDESK.
    
    This class provides functionality for editing RebelSCRIBE documentation within RebelDESK,
    including a WYSIWYG editor, markdown preview, and syntax highlighting.
    """
    
    def __init__(self, rebelsuite_root: str = None):
        """
        Initialize the RebelSCRIBE Editor.
        
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
        
        # Initialize editor components
        self.current_document = None
        self.is_modified = False
        
        logger.info(f"RebelSCRIBE Editor initialized with RebelSUITE root: {self.rebelsuite_root}")
    
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
    
    def create_editor_widget(self):
        """
        Create an editor widget for RebelDESK.
        
        Returns:
            An editor widget that can be embedded in RebelDESK.
        """
        # This would create a PyQt widget that can be embedded in RebelDESK
        # For now, we'll just return a placeholder
        return {
            "type": "editor_widget",
            "name": "RebelSCRIBE Documentation Editor"
        }
    
    def load_document(self, document: Documentation) -> bool:
        """
        Load a document into the editor.
        
        Args:
            document: The document to load.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.current_document = document
            self.is_modified = False
            logger.info(f"Loaded document: {document.title}")
            return True
        except Exception as e:
            logger.error(f"Error loading document: {e}", exc_info=True)
            return False
    
    def get_content(self) -> str:
        """
        Get the current content of the editor.
        
        Returns:
            The current content.
        """
        if self.current_document:
            return self.current_document.content
        return ""
    
    def set_content(self, content: str) -> bool:
        """
        Set the content of the editor.
        
        Args:
            content: The new content.
            
        Returns:
            True if successful, False otherwise.
        """
        if self.current_document:
            self.current_document.content = content
            self.is_modified = True
            return True
        return False
    
    def save_document(self) -> bool:
        """
        Save the current document.
        
        Returns:
            True if successful, False otherwise.
        """
        if self.current_document and self.is_modified:
            # This would save the document to the RebelSCRIBE database
            # For now, we'll just log it
            logger.info(f"Saved document: {self.current_document.title}")
            self.is_modified = False
            return True
        return False
    
    def preview_document(self) -> str:
        """
        Generate a preview of the current document.
        
        Returns:
            The HTML preview of the document.
        """
        if self.current_document:
            return self.current_document.generate_html()
        return ""
    
    def export_document(self, format: str, output_path: str) -> bool:
        """
        Export the current document to a file.
        
        Args:
            format: The export format ("html" or "markdown").
            output_path: The output file path.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.current_document:
            logger.error("No document loaded")
            return False
        
        try:
            if format.lower() == "html":
                html = self.current_document.generate_html()
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)
            elif format.lower() in ["markdown", "md"]:
                markdown = self.current_document.generate_markdown()
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Exported document to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting document: {e}", exc_info=True)
            return False
