#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the line in document_manager.py.
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
    
    # Replace the problematic line
    old_line = 'self.max_versions = self.config.get("documents" "max_versions" self.DEFAULT_MAX_VERSIONS)'
    new_line = 'self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)'
    
    if old_line in content:
        print(f"Found problematic line: {old_line}")
        content = content.replace(old_line, new_line)
        print(f"Replaced with: {new_line}")
        
        # Write the fixed content back to the file
        with open(document_manager_path, 'w') as f:
            f.write(content)
        
        print("Fixed the document_manager.py file")
    else:
        print(f"Problematic line not found: {old_line}")
        
        # Print the actual line for debugging
        with open(document_manager_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "self.max_versions = self.config.get" in line:
                    print(f"Actual line {i+1}: {line.strip()}")

if __name__ == "__main__":
    fix_line()
