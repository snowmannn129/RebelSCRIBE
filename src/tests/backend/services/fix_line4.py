#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the line in document_manager.py using regular expressions.
"""

import os
import re

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
    
    # Use regular expression to find and replace the problematic line
    pattern = r'self\.max_versions\s*=\s*self\.config\.get\("documents"\s*"max_versions"\s*self\.DEFAULT_MAX_VERSIONS\)'
    replacement = 'self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)'
    
    # Print the match for debugging
    match = re.search(pattern, content)
    if match:
        print(f"Found match: {match.group(0)}")
        
        # Replace the line
        new_content = re.sub(pattern, replacement, content)
        
        # Write the fixed content back to the file
        with open(document_manager_path, 'w') as f:
            f.write(new_content)
        
        print("Fixed the document_manager.py file")
    else:
        print("No match found")
        
        # Print the line for debugging
        with open(document_manager_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "self.max_versions = self.config.get" in line:
                    print(f"Line {i+1}: {repr(line)}")

if __name__ == "__main__":
    fix_line()
