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
        lines = f.readlines()
    
    # Find the problematic line
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

if __name__ == "__main__":
    fix_line()
