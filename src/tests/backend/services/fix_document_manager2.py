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
        lines = f.readlines()
    
    # Fix the get_config issue
    for i, line in enumerate(lines):
        if "self.config = self.config_manager.get_config()" in line:
            lines[i] = line.replace("self.config = self.config_manager.get_config()", "self.config = self.config_manager")
            print(f"Fixed line {i+1}: {lines[i].strip()}")
    
    # Fix the missing commas in self.config.get() calls
    for i, line in enumerate(lines):
        if "self.max_versions = self.config.get(\"documents\"" in line and "," not in line:
            lines[i] = line.replace(
                "self.max_versions = self.config.get(\"documents\" \"max_versions\" self.DEFAULT_MAX_VERSIONS)",
                "self.max_versions = self.config.get(\"documents\", \"max_versions\", self.DEFAULT_MAX_VERSIONS)"
            )
            print(f"Fixed line {i+1}: {lines[i].strip()}")
        
        if "data_dir = self.config.get(\"application\"" in line and "," not in line:
            lines[i] = line.replace(
                "data_dir = self.config.get(\"application\" \"data_directory\")",
                "data_dir = self.config.get(\"application\", \"data_directory\")"
            )
            print(f"Fixed line {i+1}: {lines[i].strip()}")
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.writelines(lines)
    
    print("Fixed the document_manager.py file")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager_simple.py")

if __name__ == "__main__":
    fix_document_manager()
