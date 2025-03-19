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
    
    # Replace the problematic line
    old_line = 'self.max_versions = self.config.get("documents" "max_versions" self.DEFAULT_MAX_VERSIONS)'
    new_line = 'self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)'
    
    # Print the content around the problematic line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "self.max_versions = self.config.get" in line:
            print(f"Found line {i+1}: {repr(line)}")
            print(f"Context:")
            for j in range(max(0, i-2), min(len(lines), i+3)):
                print(f"Line {j+1}: {lines[j]}")
    
    # Replace the line
    new_content = content.replace(old_line, new_line)
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.write(new_content)
    
    print("Fixed the document_manager.py file")
    
    # Verify the fix
    with open(document_manager_path, 'r') as f:
        content = f.read()
        if new_line in content:
            print(f"Verification - Line fixed successfully")
        else:
            print(f"Verification - Line not fixed")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager_simple.py")

if __name__ == "__main__":
    fix_line()
