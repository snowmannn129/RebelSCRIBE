#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to extract the merge_documents and split_document methods from document_manager.py.
"""

import os

def extract_methods():
    """Extract the merge_documents and split_document methods."""
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
    
    # Find the merge_documents method
    merge_start = content.find('def merge_documents')
    if merge_start == -1:
        print("merge_documents method not found")
        return
    
    # Find the next method
    merge_end = content.find('def ', merge_start + 1)
    if merge_end == -1:
        # If there's no next method, use the end of the file
        merge_method = content[merge_start:]
    else:
        merge_method = content[merge_start:merge_end]
    
    print("merge_documents method:")
    print(merge_method)
    
    # Find the split_document method
    split_start = content.find('def split_document')
    if split_start == -1:
        print("split_document method not found")
        return
    
    # Find the next method
    split_end = content.find('def ', split_start + 1)
    if split_end == -1:
        # If there's no next method, use the end of the file
        split_method = content[split_start:]
    else:
        split_method = content[split_start:split_end]
    
    print("\nsplit_document method:")
    print(split_method)
    
    # Also extract the test methods
    test_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'test_document_manager.py'
    ))
    
    print(f"\nTest file path: {test_file_path}")
    
    # Read the file
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Find the test_merge_documents method
    test_merge_start = content.find('def test_merge_documents')
    if test_merge_start == -1:
        print("test_merge_documents method not found")
        return
    
    # Find the next method
    test_merge_end = content.find('def ', test_merge_start + 1)
    if test_merge_end == -1:
        # If there's no next method, use the end of the file
        test_merge_method = content[test_merge_start:]
    else:
        test_merge_method = content[test_merge_start:test_merge_end]
    
    print("\ntest_merge_documents method:")
    print(test_merge_method)
    
    # Find the test_split_document method
    test_split_start = content.find('def test_split_document')
    if test_split_start == -1:
        print("test_split_document method not found")
        return
    
    # Find the next method
    test_split_end = content.find('def ', test_split_start + 1)
    if test_split_end == -1:
        # If there's no next method, use the end of the file
        test_split_method = content[test_split_start:]
    else:
        test_split_method = content[test_split_start:test_split_end]
    
    print("\ntest_split_document method:")
    print(test_split_method)

if __name__ == "__main__":
    extract_methods()
