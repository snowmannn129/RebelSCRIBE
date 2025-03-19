#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the DocumentManager class.
"""

import os

def fix_document_manager():
    """Fix the DocumentManager class."""
    # Get the path to the document_manager.py file
    document_manager_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        '..', '..', '..', 
        'backend', 'services', 'document_manager.py'
    ))
    
    print(f"Document manager path: {document_manager_path}")
    
    # Read the file
    with open(document_manager_path, 'r') as f:
        content = f.read()
    
    # Fix the specific line with missing commas
    content = content.replace(
        'self.max_versions = self.config.get("documents" "max_versions" self.DEFAULT_MAX_VERSIONS)',
        'self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)'
    )
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.write(content)
    
    print("Fixed the document_manager.py file")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager.py")

if __name__ == "__main__":
    fix_document_manager()
