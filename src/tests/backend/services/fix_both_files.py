#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix both document_manager.py and test_document_manager.py files.
"""

import os

def fix_files():
    """Fix both document_manager.py and test_document_manager.py files."""
    # Fix document_manager.py
    document_manager_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        '..', '..', '..', 
        'backend', 'services', 'document_manager.py'
    ))
    
    print(f"Document manager path: {document_manager_path}")
    
    # Read the file
    with open(document_manager_path, 'r') as f:
        content = f.read()
    
    # Fix the get_config issue
    content = content.replace(
        "self.config = self.config_manager.get_config()",
        "self.config = self.config_manager"
    )
    
    # Fix the missing commas in self.config.get() calls
    content = content.replace(
        "self.max_versions = self.config.get(\"documents\" \"max_versions\" self.DEFAULT_MAX_VERSIONS)",
        "self.max_versions = self.config.get(\"documents\", \"max_versions\", self.DEFAULT_MAX_VERSIONS)"
    )
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.write(content)
    
    print("Fixed the document_manager.py file")
    
    # Fix test_document_manager.py
    test_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'test_document_manager.py.bak'
    ))
    
    # Check if the backup file exists
    if os.path.exists(test_file_path):
        print(f"Restoring test_document_manager.py from backup")
        
        # Copy the backup file to the original file
        with open(test_file_path, 'r') as f:
            content = f.read()
        
        with open(os.path.join(os.path.dirname(__file__), 'test_document_manager.py'), 'w') as f:
            f.write(content)
    else:
        print(f"Backup file not found, creating a backup")
        
        # Create a backup of the test file
        test_file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            'test_document_manager.py'
        ))
        
        with open(test_file_path, 'r') as f:
            content = f.read()
        
        with open(os.path.join(os.path.dirname(__file__), 'test_document_manager.py.bak'), 'w') as f:
            f.write(content)
    
    print("Fixed the test_document_manager.py file")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager_simple.py")

if __name__ == "__main__":
    fix_files()
