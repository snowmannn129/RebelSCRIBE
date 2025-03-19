#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to extract the test_split_document method from test_document_manager.py.
"""

import os

def extract_test():
    """Extract the test_split_document method."""
    # Get the path to the test_document_manager.py file
    test_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'test_document_manager.py'
    ))
    
    print(f"Test file path: {test_file_path}")
    
    # Read the file
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Find the test_split_document method
    start_index = content.find('def test_split_document')
    if start_index == -1:
        print("test_split_document method not found")
        return
    
    # Find the next method
    next_method_index = content.find('def ', start_index + 1)
    if next_method_index == -1:
        # If there's no next method, use the end of the file
        test_method = content[start_index:]
    else:
        test_method = content[start_index:next_method_index]
    
    print("test_split_document method:")
    print(test_method)
    
    # Also extract the split_document method from document_manager.py
    document_manager_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        '..', '..', '..', 
        'backend', 'services', 'document_manager.py'
    ))
    
    print(f"\nDocument manager path: {document_manager_path}")
    
    # Read the file
    with open(document_manager_path, 'r') as f:
        content = f.read()
    
    # Find the split_document method
    start_index = content.find('def split_document')
    if start_index == -1:
        print("split_document method not found")
        return
    
    # Find the next method
    next_method_index = content.find('def ', start_index + 1)
    if next_method_index == -1:
        # If there's no next method, use the end of the file
        split_method = content[start_index:]
    else:
        split_method = content[start_index:next_method_index]
    
    print("\nsplit_document method:")
    print(split_method)

if __name__ == "__main__":
    extract_test()
