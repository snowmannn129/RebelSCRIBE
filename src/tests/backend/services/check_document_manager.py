#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to check the document_manager.py file.
"""

import os
import re
import ast

def check_document_manager():
    """Check the document_manager.py file."""
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
    
    # Print the line containing the max_versions assignment
    for i, line in enumerate(content.split('\n')):
        if "self.max_versions = self.config.get" in line:
            print(f"Line {i+1}: {line}")
            # Check if the line has commas
            if ',' in line:
                print("Line has commas")
            else:
                print("Line does not have commas")
            
            # Try to parse the line as Python code
            try:
                ast.parse(line)
                print("Line is valid Python syntax")
            except SyntaxError as e:
                print(f"Line has syntax error: {e}")
    
    # Try to fix the line if needed
    if "self.max_versions = self.config.get(\"documents\" \"max_versions\" self.DEFAULT_MAX_VERSIONS)" in content:
        print("Found problematic line without commas")
        # Fix the line
        fixed_content = content.replace(
            "self.max_versions = self.config.get(\"documents\" \"max_versions\" self.DEFAULT_MAX_VERSIONS)",
            "self.max_versions = self.config.get(\"documents\", \"max_versions\", self.DEFAULT_MAX_VERSIONS)"
        )
        
        # Write the fixed content back to the file
        with open(document_manager_path, 'w') as f:
            f.write(fixed_content)
        
        print("Fixed the document_manager.py file")
    else:
        print("Did not find exact problematic line")

if __name__ == "__main__":
    check_document_manager()
