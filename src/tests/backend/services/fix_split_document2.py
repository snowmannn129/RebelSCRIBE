#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the split_document method in document_manager.py.
"""

import os

def fix_split_document():
    """Fix the split_document method."""
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
    
    # Fix missing commas in the split_document method
    content = content.replace(
        'def split_document(self document_id: str split_points: List[Tuple[int str]]) -> List[Document]:',
        'def split_document(self, document_id: str, split_points: List[Tuple[int, str]]) -> List[Document]:'
    )
    
    content = content.replace(
        'split_positions = [pos for pos _ in split_points] + [content_length]',
        'split_positions = [pos for pos, _ in split_points] + [content_length]'
    )
    
    content = content.replace(
        'for i (end_pos title) in enumerate(zip(split_positions [title for _ title in split_points] + [""])):',
        'for i, (end_pos, title) in enumerate(zip(split_positions, [title for _, title in split_points] + [""])):',
    )
    
    content = content.replace(
        'logger.error(f"Error splitting document: {e}" exc_info=True)',
        'logger.error(f"Error splitting document: {e}", exc_info=True)'
    )
    
    # Fix missing commas in the create_document method inside split_document
    content = content.replace(
        'title=title',
        'title=title,'
    )
    
    content = content.replace(
        'doc_type=document.type',
        'doc_type=document.type,'
    )
    
    content = content.replace(
        'parent_id=document.parent_id',
        'parent_id=document.parent_id,'
    )
    
    # Write the fixed content back to the file
    with open(document_manager_path, 'w') as f:
        f.write(content)
    
    print("Fixed the document_manager.py file")
    
    # Now fix the test_split_document method in test_document_manager.py
    test_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'test_document_manager.py'
    ))
    
    print(f"Test file path: {test_file_path}")
    
    # Read the file
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Fix missing commas in the test_split_document method
    content = content.replace(
        'title="Document to Split"',
        'title="Document to Split",'
    )
    
    content = content.replace(
        'doc_type=Document.TYPE_SCENE',
        'doc_type=Document.TYPE_SCENE,'
    )
    
    content = content.replace(
        '(19 "Second Part")',
        '(19, "Second Part")'
    )
    
    content = content.replace(
        '(41 "Third Part")',
        '(41, "Third Part")'
    )
    
    content = content.replace(
        'result_docs = self.document_manager.split_document(document.id split_points)',
        'result_docs = self.document_manager.split_document(document.id, split_points)'
    )
    
    content = content.replace(
        'self.assertEqual(len(result_docs) 3)',
        'self.assertEqual(len(result_docs), 3)'
    )
    
    content = content.replace(
        'self.assertEqual(result_docs[0].id document.id)',
        'self.assertEqual(result_docs[0].id, document.id)'
    )
    
    content = content.replace(
        'self.assertEqual(result_docs[0].title "Document to Split")',
        'self.assertEqual(result_docs[0].title, "Document to Split")'
    )
    
    content = content.replace(
        'self.assertEqual(result_docs[0].content "First part content.")',
        'self.assertEqual(result_docs[0].content, "First part content.")'
    )
    
    content = content.replace(
        'self.assertEqual(result_docs[1].title "Second Part")',
        'self.assertEqual(result_docs[1].title, "Second Part")'
    )
    
    content = content.replace(
        'self.assertEqual(result_docs[1].content "Second part content.")',
        'self.assertEqual(result_docs[1].content, "Second part content.")'
    )
    
    content = content.replace(
        'self.assertEqual(result_docs[2].title "Third Part")',
        'self.assertEqual(result_docs[2].title, "Third Part")'
    )
    
    content = content.replace(
        'self.assertEqual(result_docs[2].content "Third part content.")',
        'self.assertEqual(result_docs[2].content, "Third part content.")'
    )
    
    # Write the fixed content back to the file
    with open(test_file_path, 'w') as f:
        f.write(content)
    
    print("Fixed the test_document_manager.py file")
    
    # Run the test to see if it passes
    print("\nRunning the test...")
    os.system("python src/tests/backend/services/test_document_manager.py")

if __name__ == "__main__":
    fix_split_document()
