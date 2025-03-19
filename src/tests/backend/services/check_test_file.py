#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to check the test_document_manager.py file.
"""

import os

def check_test_file():
    """Check the test_document_manager.py file."""
    # Get the path to the test_document_manager.py file
    test_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'test_document_manager.py'
    ))
    
    print(f"Test file path: {test_file_path}")
    
    # Read the file
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Check the test_merge_documents method
    merge_start = content.find('def test_merge_documents')
    if merge_start == -1:
        print("test_merge_documents method not found")
        return
    
    # Find the next method
    merge_end = content.find('def ', merge_start + 1)
    if merge_end == -1:
        # If there's no next method, use the end of the file
        merge_method = content[merge_start:]
    else:
        merge_method = content[merge_start:merge_end]
    
    print("test_merge_documents method:")
    print(merge_method)
    
    # Check the test_split_document method
    split_start = content.find('def test_split_document')
    if split_start == -1:
        print("test_split_document method not found")
        return
    
    # Find the next method
    split_end = content.find('def ', split_start + 1)
    if split_end == -1:
        # If there's no next method, use the end of the file
        split_method = content[split_start:]
    else:
        split_method = content[split_start:split_end]
    
    print("\ntest_split_document method:")
    print(split_method)

if __name__ == "__main__":
    check_test_file()
