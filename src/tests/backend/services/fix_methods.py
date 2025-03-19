#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the merge_documents and split_document methods in document_manager.py.
"""

import os

def fix_methods():
    """Fix the merge_documents and split_document methods."""
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
    
    # Fix the merge_documents method
    content = content.replace(
        'merged_doc = self.create_document(title doc_type parent_id merged_content)',
        'merged_doc = self.create_document(title, doc_type, parent_id, merged_content)'
    )
    
    # Fix the split_document method
    content = content.replace(
        'split_positions = [pos for pos _ in split_points] + [content_length]',
        'split_positions = [pos for pos, _ in split_points] + [content_length]'
    )
    
    content = content.replace(
        'for i (end_pos title) in enumerate(zip(split_positions [title for _ title in split_points] + [""])):',
        'for i, (end_pos, title) in enumerate(zip(split_positions, [title for _, title in split_points] + [""])):',
    )
    
    content = content.replace(
        'title=title\n                        doc_type=document.type\n                        parent_id=document.parent_id\n                        content=segment',
        'title=title,\n                        doc_type=document.type,\n                        parent_id=document.parent_id,\n                        content=segment'
    )
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.write(content)
    
    print("Fixed the document_manager.py file")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager.py")

if __name__ == "__main__":
    fix_methods()
