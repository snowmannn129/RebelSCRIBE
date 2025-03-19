#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to check if the ConfigManager mock is working properly.
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import shutil

def check_mock():
    """Check if the ConfigManager mock is working properly."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    try:
        # Mock the ConfigManager
        with patch('src.backend.services.document_manager.ConfigManager') as mock_config:
            # Set up the mock
            mock_config_instance = MagicMock()
            mock_config_instance.get_config.return_value = {
                'application': {
                    'data_directory': temp_dir
                },
                'documents': {
                    'max_versions': 5
                }
            }
            mock_config.return_value = mock_config_instance
            
            # Import the DocumentManager
            from src.backend.services.document_manager import DocumentManager
            
            # Create a document manager instance
            project_path = os.path.join(temp_dir, "test_project")
            os.makedirs(project_path, exist_ok=True)
            document_manager = DocumentManager(project_path)
            
            # Check if the document manager was created successfully
            print(f"DocumentManager created successfully")
            print(f"project_path: {document_manager.project_path}")
            print(f"documents_dir: {document_manager.documents_dir}")
            print(f"versions_dir: {document_manager.versions_dir}")
            print(f"max_versions: {document_manager.max_versions}")
            
            # Check if the mock was called correctly
            print(f"get_config called: {mock_config_instance.get_config.called}")
            
            # Create a document to test
            document = document_manager.create_document(
                title="Test Document",
                content="Test content"
            )
            
            print(f"Document created: {document.title}")
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"Removed temporary directory: {temp_dir}")

if __name__ == "__main__":
    check_mock()
