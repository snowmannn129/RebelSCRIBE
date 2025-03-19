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
    
    # Create a new file with the fixed content
    fixed_file_path = document_manager_path + ".fixed"
    
    with open(document_manager_path, 'r') as src, open(fixed_file_path, 'w') as dst:
        for i, line in enumerate(src):
            if i == 55:  # Line 56 (0-indexed)
                print(f"Found line {i+1}: {repr(line)}")
                # Write the fixed line with commas
                fixed_line = '        self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)\n'
                dst.write(fixed_line)
                print(f"Replaced with: {repr(fixed_line)}")
            else:
                dst.write(line)
    
    # Replace the original file with the fixed file
    os.replace(fixed_file_path, document_manager_path)
    
    print("Fixed the document_manager.py file")
    
    # Verify the fix
    with open(document_manager_path, 'r') as f:
        lines = f.readlines()
        print(f"Verification - Line 56: {repr(lines[55])}")

if __name__ == "__main__":
    fix_line()
