#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelCAD Integration Module for RebelSCRIBE.

This module provides functionality for extracting documentation from RebelCAD source code
and generating documentation using RebelSCRIBE.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Add parent directory to path to allow imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.backend.models.documentation import Documentation
from src.backend.services.documentation_manager import DocumentationManager
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class RebelCADIntegration:
    """
    Integration class for RebelCAD.
    
    This class provides functionality for extracting documentation from RebelCAD source code
    and generating documentation using RebelSCRIBE.
    """
    
    def __init__(self, rebelsuite_root: str = None):
        """
        Initialize the RebelCAD integration.
        
        Args:
            rebelsuite_root: The root directory of the RebelSUITE project.
                             If None, it will try to detect it automatically.
        """
        self.doc_manager = DocumentationManager()
        
        # Set RebelSUITE root directory
        if rebelsuite_root:
            self.rebelsuite_root = rebelsuite_root
        else:
            # Try to detect RebelSUITE root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.rebelsuite_root = self._find_rebelsuite_root(current_dir)
            if not self.rebelsuite_root:
                raise ValueError("Could not detect RebelSUITE root directory")
        
        # Set RebelCAD directory
        self.rebelcad_dir = os.path.join(self.rebelsuite_root, "RebelCAD")
        if not os.path.exists(self.rebelcad_dir):
            raise ValueError(f"RebelCAD directory not found: {self.rebelcad_dir}")
        
        logger.info(f"RebelCAD integration initialized with RebelSUITE root: {self.rebelsuite_root}")
    
    def _find_rebelsuite_root(self, start_dir: str) -> Optional[str]:
        """
        Find the RebelSUITE root directory by looking for specific markers.
        
        Args:
            start_dir: The directory to start the search from.
            
        Returns:
            The RebelSUITE root directory, or None if not found.
        """
        current_dir = start_dir
        max_levels = 5  # Maximum number of parent directories to check
        
        for _ in range(max_levels):
            # Check if this is the RebelSUITE root directory
            if os.path.exists(os.path.join(current_dir, "RebelCAD")) and \
               os.path.exists(os.path.join(current_dir, "RebelSCRIBE")) and \
               os.path.exists(os.path.join(current_dir, "RebelSUITE_Integration_Tracking.md")):
                return current_dir
            
            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached the root of the filesystem
                break
            current_dir = parent_dir
        
        return None
    
    def extract_documentation(self, output_dir: str = None) -> List[Documentation]:
        """
        Extract documentation from RebelCAD source code.
        
        Args:
            output_dir: The directory to output the documentation to.
                        If None, it will use the default RebelSCRIBE docs directory.
                        
        Returns:
            A list of Documentation objects.
        """
        logger.info("Extracting documentation from RebelCAD source code")
        
        # Set output directory
        if output_dir is None:
            output_dir = os.path.join(self.rebelsuite_root, "RebelSCRIBE", "docs", "rebelcad")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract documentation from source code
        include_dir = os.path.join(self.rebelcad_dir, "include")
        src_dir = os.path.join(self.rebelcad_dir, "src")
        
        # Extract documentation from header files
        header_docs = self._extract_from_directory(
            include_dir,
            Documentation.COMPONENT_CAD,
            Documentation.LANGUAGE_CPP
        )
        
        # Extract documentation from source files
        source_docs = self._extract_from_directory(
            src_dir,
            Documentation.COMPONENT_CAD,
            Documentation.LANGUAGE_CPP
        )
        
        # Combine documentation
        all_docs = header_docs + source_docs
        
        # Generate documentation files
        self._generate_documentation_files(all_docs, output_dir)
        
        logger.info(f"Extracted {len(all_docs)} documentation items from RebelCAD")
        return all_docs
    
    def _process_cpp_comment(self, doc: Documentation, comment_text: str) -> None:
        """
        Process a C++ comment to extract structured information.
        
        Args:
            doc: The Documentation object to update.
            comment_text: The comment text to process.
        """
        # Clean up the comment text by removing leading asterisks and spaces
        lines = comment_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove leading asterisks and spaces
            cleaned_line = re.sub(r'^\s*\*\s?', '', line)
            cleaned_lines.append(cleaned_line)
        
        # Join cleaned lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Extract class/brief description
        brief_match = re.search(r'@brief\s+(.*?)(?=\n\n|\n@|\Z)', cleaned_text, re.DOTALL)
        if brief_match:
            doc.content = brief_match.group(1).strip()
        
        # Extract detailed description (text between @brief and the next tag)
        detail_match = re.search(r'@brief\s+.*?\n\n(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if detail_match:
            detailed_desc = detail_match.group(1).strip()
            if doc.content:
                doc.content += '\n\n' + detailed_desc
            else:
                doc.content = detailed_desc
        
        # Extract parameters
        param_matches = re.finditer(r'@param\s+(\w+)\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in param_matches:
            param_name = match.group(1)
            param_desc = match.group(2).strip()
            doc.add_parameter(param_name, param_desc)
        
        # Extract return value
        return_match = re.search(r'@return(?:s)?\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if return_match:
            return_desc = return_match.group(1).strip()
            doc.set_returns(return_desc)
        
        # Extract throws/exceptions
        throws_matches = re.finditer(r'@throws\s+(\w+)\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in throws_matches:
            exc_type = match.group(1)
            exc_desc = match.group(2).strip()
            doc.add_exception(exc_type, exc_desc)
        
        # Extract deprecated
        deprecated_match = re.search(r'@deprecated\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if deprecated_match:
            reason = deprecated_match.group(1).strip()
            doc.set_deprecated(True, reason)
        
        # Extract since version
        since_match = re.search(r'@since\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        if since_match:
            since_version = since_match.group(1).strip()
            doc.set_since_version(since_version)
        
        # Extract authors
        author_matches = re.finditer(r'@author\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in author_matches:
            author = match.group(1).strip()
            doc.add_author(author)
        
        # Extract see also
        see_matches = re.finditer(r'@see\s+(.*?)(?=\n@|\Z)', cleaned_text, re.DOTALL)
        for match in see_matches:
            reference = match.group(1).strip()
            doc.add_see_also(reference)
    
    def _extract_from_directory(self, directory: str, component: str, language: str) -> List[Documentation]:
        """
        Extract documentation from all source files in a directory.
        
        Args:
            directory: The directory to extract documentation from.
            component: The component name.
            language: The programming language.
            
        Returns:
            A list of Documentation objects.
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return []
        
        docs = []
        
        # Walk through the directory
        for root, _, files in os.walk(directory):
            for file in files:
                # Check if this is a C++ file
                if file.endswith((".h", ".hpp", ".cpp", ".cc", ".c")):
                    file_path = os.path.join(root, file)
                    
                    # Read source code
                    with open(file_path, "r", encoding="utf-8") as f:
                        source_code = f.read()
                    
                    # Extract documentation blocks
                    doc_blocks = re.finditer(r'/\*\*\s*([\s\S]*?)\s*\*/', source_code)
                    
                    for block in doc_blocks:
                        comment_text = block.group(1)
                        block_end = block.end()
                        
                        # Get the next non-whitespace line after the comment block
                        next_line_match = re.search(r'\s*(.+)', source_code[block_end:])
                        if not next_line_match:
                            continue
                        
                        next_line = next_line_match.group(1)
                        
                        # Check if it's a class
                        class_match = re.match(r'class\s+(\w+)', next_line)
                        if class_match:
                            class_name = class_match.group(1)
                            
                            # Create documentation
                            doc = Documentation(
                                title=class_name,
                                type=Documentation.TYPE_CLASS,
                                content="",
                                source_code=source_code,
                                language=Documentation.LANGUAGE_CPP,
                                component=component,
                                api_version="1.0.0"
                            )
                            
                            # Process the comment text
                            self._process_cpp_comment(doc, comment_text)
                            
                            docs.append(doc)
                            continue
                        
                        # Check if it's an enum
                        enum_match = re.match(r'enum\s+(?:class\s+)?(\w+)', next_line)
                        if enum_match:
                            enum_name = enum_match.group(1)
                            
                            # Create documentation
                            doc = Documentation(
                                title=enum_name,
                                type=Documentation.TYPE_CLASS,  # Using CLASS type for enums
                                content="",
                                source_code=source_code,
                                language=Documentation.LANGUAGE_CPP,
                                component=component,
                                api_version="1.0.0"
                            )
                            
                            # Process the comment text
                            self._process_cpp_comment(doc, comment_text)
                            
                            docs.append(doc)
                            continue
                        
                        # Check if it's a struct
                        struct_match = re.match(r'struct\s+(\w+)', next_line)
                        if struct_match:
                            struct_name = struct_match.group(1)
                            
                            # Create documentation
                            doc = Documentation(
                                title=struct_name,
                                type=Documentation.TYPE_CLASS,  # Using CLASS type for structs
                                content="",
                                source_code=source_code,
                                language=Documentation.LANGUAGE_CPP,
                                component=component,
                                api_version="1.0.0"
                            )
                            
                            # Process the comment text
                            self._process_cpp_comment(doc, comment_text)
                            
                            docs.append(doc)
                            continue
                        
                        # Check if it's a function
                        func_match = re.match(r'(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?(?:\w+(?:::\w+)*\s+)?(\w+)\s*\(', next_line)
                        if func_match:
                            func_name = func_match.group(1)
                            
                            # Create documentation
                            doc = Documentation(
                                title=func_name,
                                type=Documentation.TYPE_FUNCTION,
                                content="",
                                source_code=source_code,
                                language=Documentation.LANGUAGE_CPP,
                                component=component,
                                api_version="1.0.0"
                            )
                            
                            # Process the comment text
                            self._process_cpp_comment(doc, comment_text)
                            
                            docs.append(doc)
                            continue
                    
                    # If no documentation was extracted, create a generic documentation for the file
                    if not docs:
                        file_name = os.path.basename(file_path)
                        doc = Documentation(
                            title=file_name,
                            type=Documentation.TYPE_CODE,
                            content="",
                            source_code=source_code,
                            language=Documentation.LANGUAGE_CPP,
                            component=component,
                            api_version="1.0.0"
                        )
                        
                        # Extract documentation from source code
                        success = doc.extract_documentation_from_code()
                        if not success:
                            logger.warning(f"Failed to extract documentation from: {file_path}")
                        
                        if doc:
                            docs.append(doc)
        
        return docs
    
    def _generate_documentation_files(self, docs: List[Documentation], output_dir: str) -> None:
        """
        Generate documentation files from Documentation objects.
        
        Args:
            docs: A list of Documentation objects.
            output_dir: The directory to output the documentation to.
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate index.html
        index_html = self._generate_index_html(docs)
        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)
        
        # Generate documentation files
        for doc in docs:
            # Generate HTML
            html = doc.generate_html()
            
            # Write to file
            file_path = os.path.join(output_dir, f"{doc.id}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            # Generate Markdown
            markdown = doc.generate_markdown()
            
            # Write to file
            file_path = os.path.join(output_dir, f"{doc.id}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown)
    
    def _generate_index_html(self, docs: List[Documentation]) -> str:
        """
        Generate an index.html file for the documentation.
        
        Args:
            docs: A list of Documentation objects.
            
        Returns:
            The generated HTML.
        """
        html = """<!DOCTYPE html>
<html>
<head>
    <title>RebelCAD Documentation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        
        h2 {
            color: #3498db;
            margin-top: 20px;
        }
        
        .category {
            margin-bottom: 30px;
        }
        
        ul {
            list-style-type: none;
            padding: 0;
        }
        
        li {
            margin-bottom: 5px;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .search {
            margin-bottom: 20px;
        }
        
        #search-input {
            padding: 8px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>RebelCAD Documentation</h1>
    
    <div class="search">
        <input type="text" id="search-input" placeholder="Search documentation...">
    </div>
"""
        
        # Group documentation by type
        docs_by_type = {}
        for doc in docs:
            if doc.type not in docs_by_type:
                docs_by_type[doc.type] = []
            docs_by_type[doc.type].append(doc)
        
        # Add documentation by type
        for doc_type, type_docs in docs_by_type.items():
            # Skip empty categories
            if not type_docs:
                continue
            
            # Get human-readable type name
            type_name = doc_type.capitalize()
            if doc_type == Documentation.TYPE_CLASS:
                type_name = "Classes"
            elif doc_type == Documentation.TYPE_FUNCTION:
                type_name = "Functions"
            elif doc_type == Documentation.TYPE_MODULE:
                type_name = "Modules"
            elif doc_type == Documentation.TYPE_PACKAGE:
                type_name = "Packages"
            elif doc_type == Documentation.TYPE_INTERFACE:
                type_name = "Interfaces"
            elif doc_type == Documentation.TYPE_API:
                type_name = "API Reference"
            elif doc_type == Documentation.TYPE_GUIDE:
                type_name = "Guides"
            elif doc_type == Documentation.TYPE_TUTORIAL:
                type_name = "Tutorials"
            elif doc_type == Documentation.TYPE_REFERENCE:
                type_name = "Reference"
            elif doc_type == Documentation.TYPE_CODE:
                type_name = "Code Documentation"
            
            html += f"""
    <div class="category">
        <h2>{type_name}</h2>
        <ul>
"""
            
            # Sort documentation by title
            type_docs.sort(key=lambda d: d.title)
            
            # Add documentation to HTML
            for doc in type_docs:
                html += f'            <li><a href="{doc.id}.html">{doc.title}</a></li>\n'
            
            html += """        </ul>
    </div>
"""
        
        html += """
    <script>
        // Simple search functionality
        document.getElementById('search-input').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const items = document.querySelectorAll('li');
            
            items.forEach(function(item) {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Show/hide categories based on visible items
            const categories = document.querySelectorAll('.category');
            categories.forEach(function(category) {
                const visibleItems = category.querySelectorAll('li:not([style="display: none;"])');
                if (visibleItems.length === 0) {
                    category.style.display = 'none';
                } else {
                    category.style.display = '';
                }
            });
        });
    </script>
</body>
</html>
"""
        
        return html

def main():
    """Main function."""
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="RebelCAD Integration for RebelSCRIBE")
    parser.add_argument("--rebelsuite-root", help="RebelSUITE root directory")
    parser.add_argument("--output-dir", help="Output directory for documentation")
    args = parser.parse_args()
    
    try:
        # Create integration
        integration = RebelCADIntegration(args.rebelsuite_root)
        
        # Extract documentation
        integration.extract_documentation(args.output_dir)
        
        print("Documentation extraction completed successfully")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
