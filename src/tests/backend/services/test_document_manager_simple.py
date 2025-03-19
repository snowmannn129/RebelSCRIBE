#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for DocumentManager.
"""

import inspect
import os

def test_document_manager():
    """Test creating a DocumentManager instance."""
    try:
        # Get the path to the document_manager.py file
        import src.backend.services.document_manager as dm_module
        dm_file_path = inspect.getfile(dm_module)
        print(f"DocumentManager module file path: {dm_file_path}")

        # Read the file and print the relevant line
        with open(dm_file_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "self.max_versions = self.config.get" in line:
                    print(f"Line {i+1}: {line.strip()}")
                    # Print a few lines before and after for context
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    print("\nContext:")
                    for j in range(start, end):
                        print(f"Line {j+1}: {lines[j].strip()}")

        # Now try to import and create an instance
        from src.backend.services.document_manager import DocumentManager
        document_manager = DocumentManager()
        print("\nDocumentManager instance created successfully.")
    except Exception as e:
        print(f"\nError creating DocumentManager instance: {e}")

if __name__ == "__main__":
    test_document_manager()
