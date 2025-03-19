#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the test_document_manager.py file.
"""

import os

def fix_test_document_manager():
    """Fix the test_document_manager.py file."""
    # Get the path to the test_document_manager.py file
    test_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'test_document_manager.py'
    ))
    
    print(f"Test file path: {test_file_path}")
    
    # Read the file
    with open(test_file_path, 'r') as f:
        lines = f.readlines()
    
    # Print the lines around line 112
    print("Lines around line 112:")
    for i in range(max(0, 112-5), min(len(lines), 112+5)):
        print(f"Line {i+1}: {lines[i].strip()}")
    
    # Fix the syntax error
    for i, line in enumerate(lines):
        if i == 111 and "doc_type=Document.TYPE_SCENE" in line and "," not in line:
            lines[i] = line.replace("doc_type=Document.TYPE_SCENE", "doc_type=Document.TYPE_SCENE,")
            print(f"Fixed line {i+1}: {lines[i].strip()}")
    
    # Write the fixed content back to the file
    with open(test_file_path, 'w') as f:
        f.writelines(lines)
    
    print("Fixed the test_document_manager.py file")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager.py")

if __name__ == "__main__":
    fix_test_document_manager()
