#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to directly fix the document_manager.py file.
"""

import os

def direct_fix():
    """Directly fix the document_manager.py file."""
    # Get the path to the document_manager.py file
    document_manager_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        '..', '..', '..', 
        'backend', 'services', 'document_manager.py'
    ))
    
    print(f"Document manager path: {document_manager_path}")
    
    # Create a backup of the file
    backup_path = document_manager_path + '.bak'
    with open(document_manager_path, 'r') as src, open(backup_path, 'w') as dst:
        dst.write(src.read())
    print(f"Created backup at {backup_path}")
    
    # Read the file line by line
    with open(document_manager_path, 'r') as f:
        lines = f.readlines()
    
    # Find and fix the problematic line
    for i, line in enumerate(lines):
        if "self.max_versions = self.config.get" in line:
            print(f"Found line {i+1}: {line.strip()}")
            # Replace the line with the correct version
            lines[i] = "        self.max_versions = self.config.get(\"documents\", \"max_versions\", self.DEFAULT_MAX_VERSIONS)\n"
            print(f"Replaced with: {lines[i].strip()}")
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.writelines(lines)
    
    print("Fixed the document_manager.py file")

if __name__ == "__main__":
    direct_fix()
