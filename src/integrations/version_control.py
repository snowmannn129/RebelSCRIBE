#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE Version Control for RebelDESK.

This module provides functionality for version control of RebelSCRIBE documentation within RebelDESK.
"""

import os
import sys
import json
import logging
import datetime
from typing import List, Dict, Any, Optional, Union

# Add RebelSCRIBE to path
rebelsuite_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
rebelscribe_dir = os.path.join(rebelsuite_root, "RebelSCRIBE")
if rebelscribe_dir not in sys.path:
    sys.path.insert(0, rebelscribe_dir)

# Import RebelSCRIBE modules
from src.backend.models.documentation import Documentation
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class DocumentVersion:
    """
    Represents a version of a document.
    """
    
    def __init__(self, doc_id: str, version: int, content: str, timestamp: datetime.datetime = None, author: str = None):
        """
        Initialize a new document version.
        
        Args:
            doc_id: The document ID.
            version: The version number.
            content: The document content.
            timestamp: The timestamp of the version.
            author: The author of the version.
        """
        self.doc_id = doc_id
        self.version = version
        self.content = content
        self.timestamp = timestamp or datetime.datetime.now()
        self.author = author or "Unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the version to a dictionary.
        
        Returns:
            A dictionary representation of the version.
        """
        return {
            "doc_id": self.doc_id,
            "version": self.version,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "author": self.author
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentVersion':
        """
        Create a version from a dictionary.
        
        Args:
            data: The dictionary containing the version data.
            
        Returns:
            The created version.
        """
        return cls(
            doc_id=data["doc_id"],
            version=data["version"],
            content=data["content"],
            timestamp=datetime.datetime.fromisoformat(data["timestamp"]),
            author=data["author"]
        )

class RebelSCRIBEVersionControl:
    """
    RebelSCRIBE Version Control for RebelDESK.
    
    This class provides functionality for version control of RebelSCRIBE documentation within RebelDESK,
    including versioning, history tracking, and diffing.
    """
    
    def __init__(self, rebelsuite_root: str = None):
        """
        Initialize the RebelSCRIBE Version Control.
        
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
        
        # Set versions directory
        self.versions_dir = os.path.join(self.rebelscribe_dir, "versions")
        os.makedirs(self.versions_dir, exist_ok=True)
        
        logger.info(f"RebelSCRIBE Version Control initialized with RebelSUITE root: {self.rebelsuite_root}")
    
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
    
    def create_version(self, doc: Documentation, author: str = None) -> bool:
        """
        Create a new version of a document.
        
        Args:
            doc: The document to version.
            author: The author of the version.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get the next version number
            versions = self.get_versions(doc.id)
            next_version = len(versions) + 1
            
            # Create the version
            version = DocumentVersion(
                doc_id=doc.id,
                version=next_version,
                content=doc.content,
                author=author
            )
            
            # Save the version
            self._save_version(version)
            
            logger.info(f"Created version {next_version} of document {doc.id}")
            return True
        except Exception as e:
            logger.error(f"Error creating version: {e}", exc_info=True)
            return False
    
    def _save_version(self, version: DocumentVersion) -> None:
        """
        Save a version to disk.
        
        Args:
            version: The version to save.
        """
        # Create the document directory
        doc_dir = os.path.join(self.versions_dir, version.doc_id)
        os.makedirs(doc_dir, exist_ok=True)
        
        # Save the version
        version_path = os.path.join(doc_dir, f"{version.version}.json")
        with open(version_path, "w", encoding="utf-8") as f:
            json.dump(version.to_dict(), f, indent=2)
    
    def get_versions(self, doc_id: str) -> List[DocumentVersion]:
        """
        Get all versions of a document.
        
        Args:
            doc_id: The document ID.
            
        Returns:
            A list of document versions.
        """
        versions = []
        
        # Get the document directory
        doc_dir = os.path.join(self.versions_dir, doc_id)
        if not os.path.exists(doc_dir):
            return versions
        
        # Get all version files
        version_files = [f for f in os.listdir(doc_dir) if f.endswith(".json")]
        
        # Load each version
        for version_file in version_files:
            version_path = os.path.join(doc_dir, version_file)
            with open(version_path, "r", encoding="utf-8") as f:
                version_data = json.load(f)
                versions.append(DocumentVersion.from_dict(version_data))
        
        # Sort by version number
        versions.sort(key=lambda v: v.version)
        
        return versions
    
    def get_version(self, doc_id: str, version: int) -> Optional[DocumentVersion]:
        """
        Get a specific version of a document.
        
        Args:
            doc_id: The document ID.
            version: The version number.
            
        Returns:
            The document version, or None if not found.
        """
        # Get the document directory
        doc_dir = os.path.join(self.versions_dir, doc_id)
        if not os.path.exists(doc_dir):
            return None
        
        # Get the version file
        version_path = os.path.join(doc_dir, f"{version}.json")
        if not os.path.exists(version_path):
            return None
        
        # Load the version
        with open(version_path, "r", encoding="utf-8") as f:
            version_data = json.load(f)
            return DocumentVersion.from_dict(version_data)
    
    def restore_version(self, doc: Documentation, version: int) -> bool:
        """
        Restore a document to a specific version.
        
        Args:
            doc: The document to restore.
            version: The version number to restore to.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get the version
            doc_version = self.get_version(doc.id, version)
            if not doc_version:
                logger.error(f"Version {version} of document {doc.id} not found")
                return False
            
            # Restore the content
            doc.content = doc_version.content
            
            logger.info(f"Restored document {doc.id} to version {version}")
            return True
        except Exception as e:
            logger.error(f"Error restoring version: {e}", exc_info=True)
            return False
    
    def diff_versions(self, doc_id: str, version1: int, version2: int) -> List[Dict[str, Any]]:
        """
        Get the differences between two versions of a document.
        
        Args:
            doc_id: The document ID.
            version1: The first version number.
            version2: The second version number.
            
        Returns:
            A list of differences between the versions.
        """
        try:
            # Get the versions
            v1 = self.get_version(doc_id, version1)
            v2 = self.get_version(doc_id, version2)
            
            if not v1 or not v2:
                logger.error(f"Versions {version1} and/or {version2} of document {doc_id} not found")
                return []
            
            # Compute the diff
            import difflib
            
            # Split the content into lines
            v1_lines = v1.content.splitlines()
            v2_lines = v2.content.splitlines()
            
            # Compute the diff
            diff = difflib.unified_diff(
                v1_lines,
                v2_lines,
                lineterm="",
                n=3
            )
            
            # Convert the diff to a list of dictionaries
            result = []
            for line in diff:
                if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                    continue
                
                if line.startswith("+"):
                    result.append({
                        "type": "add",
                        "content": line[1:]
                    })
                elif line.startswith("-"):
                    result.append({
                        "type": "remove",
                        "content": line[1:]
                    })
                else:
                    result.append({
                        "type": "context",
                        "content": line
                    })
            
            return result
        except Exception as e:
            logger.error(f"Error computing diff: {e}", exc_info=True)
            return []
