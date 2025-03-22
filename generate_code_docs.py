#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Code Documentation Script for RebelSCRIBE.

This script provides a command-line interface for generating documentation from source code files.
It uses the DocumentationGenerator class to extract documentation from source code files and
generate HTML or Markdown documentation.

Usage:
    python generate_code_docs.py input_path output_path [--format {html,markdown}] [--recursive]

Examples:
    # Generate HTML documentation for a single file
    python generate_code_docs.py src/main.py docs/main.html

    # Generate Markdown documentation for a single file
    python generate_code_docs.py src/main.py docs/main.md --format markdown

    # Generate HTML documentation for a directory
    python generate_code_docs.py src docs --recursive

    # Generate Markdown documentation for a directory
    python generate_code_docs.py src docs --format markdown --recursive
"""

import os
import sys
import argparse
from typing import Dict, List, Optional, Any

# Add the RebelSCRIBE directory to the Python path
rebelsuite_path = os.path.abspath(os.path.dirname(__file__))
if rebelsuite_path not in sys.path:
    sys.path.append(rebelsuite_path)

from src.backend.documentation_generator import DocumentationGenerator

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
    
    print(f"Documentation generation {'completed' if os.path.exists(args.output) else 'failed'}")

if __name__ == '__main__':
    main()
