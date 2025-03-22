#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for document versioning in RebelSCRIBE.

This script tests the document versioning functionality in the Document class.
"""

import os
import sys
import unittest
from pathlib import Path
import datetime

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(parent_dir))

from src.backend.models.document import Document
from src.backend.models.document_version import DocumentVersion

class TestDocumentVersioning(unittest.TestCase):
    """Test case for document versioning."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a test document
        self.document = Document(
            title="Test Document",
            content="Initial content."
        )
    
    def test_create_version(self):
        """Test creating a version."""
        # Create a version
        version = self.document.create_version(
            created_by="Test User",
            comment="Initial version"
        )
        
        # Check version properties
        self.assertEqual(version.document_id, self.document.id)
        self.assertEqual(version.title, "Test Document")
        self.assertEqual(version.content, "Initial content.")
        self.assertEqual(version.created_by, "Test User")
        self.assertEqual(version.comment, "Initial version")
        self.assertEqual(version.version_number, 2)  # First version is 2 (initial state is 1)
        
        # Check document properties
        self.assertEqual(self.document.current_version, 2)
        self.assertEqual(len(self.document.versions), 1)
    
    def test_set_content_with_versioning(self):
        """Test setting content with versioning."""
        # Set content with versioning
        self.document.set_content(
            "New content.",
            created_by="Test User",
            comment="Updated content"
        )
        
        # Check document properties
        self.assertEqual(self.document.content, "New content.")
        self.assertEqual(self.document.current_version, 2)
        self.assertEqual(len(self.document.versions), 1)
        
        # Check version properties
        version = self.document.get_version(2)
        self.assertIsNotNone(version)
        self.assertEqual(version.content, "Initial content.")  # Original content
        self.assertEqual(version.created_by, "Test User")
        self.assertEqual(version.comment, "Updated content")
    
    def test_set_content_without_versioning(self):
        """Test setting content without versioning."""
        # Set content without versioning
        self.document.set_content(
            "New content.",
            create_version=False
        )
        
        # Check document properties
        self.assertEqual(self.document.content, "New content.")
        self.assertEqual(self.document.current_version, 1)  # Still at initial version
        self.assertEqual(len(self.document.versions), 0)  # No versions created
    
    def test_append_content_with_versioning(self):
        """Test appending content with versioning."""
        # Append content with versioning
        self.document.append_content(
            " Appended content.",
            created_by="Test User",
            comment="Appended content"
        )
        
        # Check document properties
        self.assertEqual(self.document.content, "Initial content. Appended content.")
        self.assertEqual(self.document.current_version, 2)
        self.assertEqual(len(self.document.versions), 1)
        
        # Check version properties
        version = self.document.get_version(2)
        self.assertIsNotNone(version)
        self.assertEqual(version.content, "Initial content.")  # Original content
        self.assertEqual(version.created_by, "Test User")
        self.assertEqual(version.comment, "Appended content")
    
    def test_append_content_without_versioning(self):
        """Test appending content without versioning."""
        # Append content without versioning
        self.document.append_content(
            " Appended content.",
            create_version=False
        )
        
        # Check document properties
        self.assertEqual(self.document.content, "Initial content. Appended content.")
        self.assertEqual(self.document.current_version, 1)  # Still at initial version
        self.assertEqual(len(self.document.versions), 0)  # No versions created
    
    def test_get_version(self):
        """Test getting a version."""
        # Create multiple versions
        self.document.set_content("Version 2 content.", comment="Version 2")
        self.document.set_content("Version 3 content.", comment="Version 3")
        
        # Get a specific version
        version = self.document.get_version(2)
        
        # Check version properties
        self.assertIsNotNone(version)
        self.assertEqual(version.content, "Initial content.")
        self.assertEqual(version.comment, "Version 2")
        self.assertEqual(version.version_number, 2)
    
    def test_get_versions(self):
        """Test getting all versions."""
        # Create multiple versions
        self.document.set_content("Version 2 content.", comment="Version 2")
        self.document.set_content("Version 3 content.", comment="Version 3")
        
        # Get all versions
        versions = self.document.get_versions()
        
        # Check versions
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version_number, 2)
        self.assertEqual(versions[0].content, "Initial content.")
        self.assertEqual(versions[1].version_number, 3)
        self.assertEqual(versions[1].content, "Version 2 content.")
    
    def test_restore_version(self):
        """Test restoring a version."""
        # Create multiple versions
        self.document.set_content("Version 2 content.", comment="Version 2")
        self.document.set_content("Version 3 content.", comment="Version 3")
        
        # Restore a version
        result = self.document.restore_version(2, comment="Restoring version 2")
        
        # Check result
        self.assertTrue(result)
        
        # Check document properties
        self.assertEqual(self.document.content, "Initial content.")
        self.assertEqual(self.document.current_version, 4)  # New version created before restoring
        self.assertEqual(len(self.document.versions), 3)
        
        # Check version properties
        version = self.document.get_version(4)
        self.assertIsNotNone(version)
        self.assertEqual(version.content, "Version 3 content.")  # Content before restoring
        self.assertEqual(version.comment, "Restoring version 2")
    
    def test_restore_version_without_creating_version(self):
        """Test restoring a version without creating a new version."""
        # Create multiple versions
        self.document.set_content("Version 2 content.", comment="Version 2")
        self.document.set_content("Version 3 content.", comment="Version 3")
        
        # Restore a version without creating a new version
        result = self.document.restore_version(2, create_version=False)
        
        # Check result
        self.assertTrue(result)
        
        # Check document properties
        self.assertEqual(self.document.content, "Initial content.")
        self.assertEqual(self.document.current_version, 3)  # No new version created
        self.assertEqual(len(self.document.versions), 2)
    
    def test_restore_nonexistent_version(self):
        """Test restoring a nonexistent version."""
        # Attempt to restore a nonexistent version
        result = self.document.restore_version(999)
        
        # Check result
        self.assertFalse(result)
        
        # Check document properties (unchanged)
        self.assertEqual(self.document.content, "Initial content.")
        self.assertEqual(self.document.current_version, 1)
        self.assertEqual(len(self.document.versions), 0)
    
    def test_max_versions(self):
        """Test maximum number of versions."""
        # Set max versions to 3
        self.document.set_max_versions(3)
        
        # Create 5 versions
        for i in range(5):
            self.document.set_content(f"Version {i+2} content.", comment=f"Version {i+2}")
        
        # Check document properties
        self.assertEqual(self.document.current_version, 6)
        self.assertEqual(len(self.document.versions), 3)  # Only the last 3 versions are kept
        
        # Check available versions
        versions = self.document.get_versions()
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].version_number, 4)
        self.assertEqual(versions[1].version_number, 5)
        self.assertEqual(versions[2].version_number, 6)
    
    def test_set_max_versions(self):
        """Test setting maximum number of versions."""
        # Create 5 versions
        for i in range(5):
            self.document.set_content(f"Version {i+2} content.", comment=f"Version {i+2}")
        
        # Set max versions to 2
        self.document.set_max_versions(2)
        
        # Check document properties
        self.assertEqual(len(self.document.versions), 2)  # Only the last 2 versions are kept
        
        # Check available versions
        versions = self.document.get_versions()
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version_number, 5)
        self.assertEqual(versions[1].version_number, 6)
    
    def test_serialization(self):
        """Test serialization of document with versions."""
        # Create versions
        self.document.set_content("Version 2 content.", comment="Version 2")
        self.document.set_content("Version 3 content.", comment="Version 3")
        
        # Serialize to dictionary
        data = self.document.to_dict()
        
        # Check serialized data
        self.assertEqual(data["title"], "Test Document")
        self.assertEqual(data["content"], "Version 3 content.")
        self.assertEqual(data["current_version"], 3)
        self.assertEqual(len(data["versions"]), 2)
        
        # Deserialize from dictionary
        new_document = Document.from_dict(data)
        
        # Check deserialized document
        self.assertEqual(new_document.title, "Test Document")
        self.assertEqual(new_document.content, "Version 3 content.")
        self.assertEqual(new_document.current_version, 3)
        self.assertEqual(len(new_document.versions), 2)
        
        # Check deserialized versions
        versions = new_document.get_versions()
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version_number, 2)
        self.assertEqual(versions[0].content, "Initial content.")
        self.assertEqual(versions[1].version_number, 3)
        self.assertEqual(versions[1].content, "Version 2 content.")

def main():
    """Run the tests."""
    unittest.main()

if __name__ == "__main__":
    main()
