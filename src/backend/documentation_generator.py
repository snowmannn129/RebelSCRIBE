#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation Generator for RebelSCRIBE.

This module provides functionality for generating documentation from source code files.
It uses the code parsers to extract documentation from source code files and generates
HTML or Markdown documentation.
"""

import os
import re
import logging
import argparse
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from src.utils.logging_utils import get_logger
from src.backend.parsers import (
    CodeParser, CodeNode, PythonParser, CppParser, TypeScriptParser
)

logger = get_logger(__name__)

class DocumentationGenerator:
    """
    Documentation generator for source code files.
    
    This class provides functionality for generating documentation from source code files.
    It uses the code parsers to extract documentation from source code files and generates
    HTML or Markdown documentation.
    """
    
    def __init__(self):
        """
        Initialize the DocumentationGenerator.
        """
        # Initialize parsers
        self.parsers = {
            '.py': PythonParser(),
            '.pyw': PythonParser(),
            '.pyi': PythonParser(),
            '.cpp': CppParser(),
            '.cc': CppParser(),
            '.cxx': CppParser(),
            '.c++': CppParser(),
            '.hpp': CppParser(),
            '.hh': CppParser(),
            '.hxx': CppParser(),
            '.h++': CppParser(),
            '.h': CppParser(),
            '.ts': TypeScriptParser(),
            '.tsx': TypeScriptParser(),
            '.js': TypeScriptParser(),
            '.jsx': TypeScriptParser(),
        }
    
    def generate_documentation(self, input_path: str, output_path: str, 
                              format: str = 'html', recursive: bool = True) -> None:
        """
        Generate documentation for source code files.
        
        Args:
            input_path: The input path (file or directory).
            output_path: The output path (file or directory).
            format: The output format ('html' or 'markdown').
            recursive: Whether to process directories recursively.
        """
        try:
            # Check if input path exists
            if not os.path.exists(input_path):
                logger.error(f"Input path '{input_path}' does not exist")
                return
            
            # Check if input path is a file or directory
            if os.path.isfile(input_path):
                # Process single file
                self._process_file(input_path, output_path, format)
            else:
                # Process directory
                self._process_directory(input_path, output_path, format, recursive)
        except Exception as e:
            logger.error(f"Failed to generate documentation: {e}")
    
    def _process_file(self, input_file: str, output_file: str, format: str) -> None:
        """
        Process a single file.
        
        Args:
            input_file: The input file path.
            output_file: The output file path.
            format: The output format ('html' or 'markdown').
        """
        try:
            # Get file extension
            _, ext = os.path.splitext(input_file)
            
            # Check if we have a parser for this file type
            if ext.lower() not in self.parsers:
                logger.warning(f"No parser available for file type '{ext}'")
                return
            
            # Get parser
            parser = self.parsers[ext.lower()]
            
            # Parse file
            code_node = parser.parse_file(input_file)
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Generate documentation
            if format.lower() == 'html':
                # Generate HTML documentation
                html = code_node.to_html()
                
                # Add HTML header and footer
                html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation for {os.path.basename(input_file)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #0066cc;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .code-file {{
            margin-bottom: 40px;
        }}
        .code-class, .code-function, .code-namespace, .code-interface, .code-enum {{
            margin-bottom: 30px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .class-name, .function-name, .namespace-name, .interface-name, .enum-name {{
            font-weight: bold;
        }}
        .inheritance, .extends {{
            font-style: italic;
            color: #666;
        }}
        .parameter, .return-type, .var-type, .param-type {{
            color: #0066cc;
        }}
        .code-parameter, .code-return, .code-exception, .code-decorator {{
            margin-left: 20px;
            margin-bottom: 10px;
        }}
        .code-variable, .code-property {{
            margin-bottom: 10px;
        }}
        .code-comment {{
            color: #666;
            font-style: italic;
        }}
        .code-import, .code-export {{
            color: #666;
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <h1>Documentation for {os.path.basename(input_file)}</h1>
    {html}
</body>
</html>"""
                
                # Write HTML to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html)
            else:
                # Generate Markdown documentation
                markdown = code_node.to_markdown()
                
                # Add Markdown header
                markdown = f"# Documentation for {os.path.basename(input_file)}\n\n{markdown}"
                
                # Write Markdown to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown)
            
            logger.info(f"Generated documentation for '{input_file}' to '{output_file}'")
        except Exception as e:
            logger.error(f"Failed to process file '{input_file}': {e}")
    
    def _process_directory(self, input_dir: str, output_dir: str, format: str, recursive: bool) -> None:
        """
        Process a directory.
        
        Args:
            input_dir: The input directory path.
            output_dir: The output directory path.
            format: The output format ('html' or 'markdown').
            recursive: Whether to process subdirectories recursively.
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Get list of files in directory
            for item in os.listdir(input_dir):
                input_path = os.path.join(input_dir, item)
                
                # Skip hidden files and directories
                if item.startswith('.'):
                    continue
                
                if os.path.isfile(input_path):
                    # Process file
                    _, ext = os.path.splitext(input_path)
                    
                    # Skip files without a parser
                    if ext.lower() not in self.parsers:
                        continue
                    
                    # Generate output file path
                    output_file = os.path.join(output_dir, f"{item}.{'html' if format.lower() == 'html' else 'md'}")
                    
                    # Process file
                    self._process_file(input_path, output_file, format)
                elif os.path.isdir(input_path) and recursive:
                    # Process subdirectory
                    output_subdir = os.path.join(output_dir, item)
                    self._process_directory(input_path, output_subdir, format, recursive)
        except Exception as e:
            logger.error(f"Failed to process directory '{input_dir}': {e}")

def main():
    """
    Main function.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate documentation from source code files.')
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('output', help='Output file or directory')
    parser.add_argument('--format', choices=['html', 'markdown'], default='html', help='Output format')
    parser.add_argument('--recursive', action='store_true', help='Process directories recursively')
    args = parser.parse_args()
    
    # Create documentation generator
    generator = DocumentationGenerator()
    
    # Generate documentation
    generator.generate_documentation(args.input, args.output, args.format, args.recursive)

if __name__ == '__main__':
    main()
