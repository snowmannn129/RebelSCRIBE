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
        content = f.read()
    
    # Print the problematic line for debugging
    lines = content.split('\n')
    print(f"Line 56: {repr(lines[55])}")
    
    # Replace the problematic line
    lines[55] = '        self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)'
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print("Fixed the document_manager.py file")
    
    # Verify the fix
    with open(document_manager_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        print(f"Verification - Line 56: {repr(lines[55])}")

if __name__ == "__main__":
    fix_line()
