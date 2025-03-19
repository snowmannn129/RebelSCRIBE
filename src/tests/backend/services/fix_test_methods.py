#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the test_document_manager.py file.
"""

import os

def fix_test_methods():
    """Fix the test_document_manager.py file."""
    # Get the path to the test_document_manager.py file
    test_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'test_document_manager.py'
    ))
    
    print(f"Test file path: {test_file_path}")
    
    # Read the file
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Fix the test_merge_documents method
    content = content.replace(
        'doc2 = self.document_manager.create_document(\n            title="Document 2"\n            doc_type=Document.TYPE_SCENE\n        )',
        'doc2 = self.document_manager.create_document(\n            title="Document 2",\n            doc_type=Document.TYPE_SCENE,\n            content="Content 2"\n        )'
    )
    
    # Fix the missing commas in the test_merge_documents method
    content = content.replace(
        '[doc1.id doc2.id]',
        '[doc1.id, doc2.id]'
    )
    
    content = content.replace(
        'self.assertEqual(merged.content "Content 1\\n\\nContent 2")',
        'self.assertEqual(merged.content, "Content 1\\n\\nContent 2")'
    )
    
    # Fix the missing commas in the test_split_document method
    content = content.replace(
        'split_points = [\n            (19 "Second Part")  # After "First part content."\n            (41 "Third Part")    # After "Second part content."\n        ]',
        'split_points = [\n            (19, "Second Part"),  # After "First part content."\n            (41, "Third Part")    # After "Second part content."\n        ]'
    )
    
    content = content.replace(
        'result_docs = self.document_manager.split_document(document.id split_points)',
        'result_docs = self.document_manager.split_document(document.id, split_points)'
    )
    
    content = content.replace(
        'self.assertEqual(len(result_docs) 3)',
        'self.assertEqual(len(result_docs), 3)'
    )
    
    # Write the fixed content back to the file
    with open(test_file_path, 'w') as f:
        f.write(content)
    
    print("Fixed the test_document_manager.py file")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager.py")

if __name__ == "__main__":
    fix_test_methods()
