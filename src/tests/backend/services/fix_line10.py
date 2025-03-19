#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix the line in document_manager.py by directly editing the file.
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
    
    # Find the problematic line
    pattern = r'self\.max_versions\s*=\s*self\.config\.get\("documents"\s+"max_versions"\s+self\.DEFAULT_MAX_VERSIONS\)'
    match = re.search(pattern, content)
    if match:
        print(f"Found match: {match.group(0)}")
        
        # Replace the line
        fixed_content = content.replace(
            match.group(0),
            'self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)'
        )
        
        # Write the fixed content back to the file
        with open(document_manager_path, 'w') as f:
            f.write(fixed_content)
        
        print("Fixed the document_manager.py file")
    else:
        print("No match found")
        
        # Try a more direct approach
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "self.max_versions = self.config.get" in line:
                print(f"Found line {i+1}: {repr(line)}")
                lines[i] = '        self.max_versions = self.config.get("documents", "max_versions", self.DEFAULT_MAX_VERSIONS)'
                print(f"Replaced with: {repr(lines[i])}")
                
                # Write the fixed content back to the file
                with open(document_manager_path, 'w') as f:
                    f.write('\n'.join(lines))
                
                print("Fixed the document_manager.py file")
                break

if __name__ == "__main__":
    fix_line()
