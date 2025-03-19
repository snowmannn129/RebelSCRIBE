#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the line in document_manager.py by directly editing the file.
"""

import os

def fix_line():
    """Fix the line in document_manager.py."""
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
    
    # Find and fix the problematic line
    for i, line in enumerate(lines):
        if "self.max_versions = self.config.get" in line:
            print(f"Found line {i+1}: {repr(line)}")
            # Replace the line with the correct version
            lines[i] = '        self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)\n'
            print(f"Replaced with: {repr(lines[i])}")
            break
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.writelines(lines)
    
    print("Fixed the document_manager.py file")
    
    # Verify the fix
    with open(document_manager_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "self.max_versions = self.config.get" in line:
                print(f"Verification - Line {i+1}: {repr(line)}")
                
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager.py")

if __name__ == "__main__":
    fix_line()
