#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for RebelCODE integration with RebelSCRIBE.

This script tests the RebelCODE integration module to ensure it correctly extracts
documentation from RebelCODE source code and generates documentation.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(parent_dir))

from src.integrations.rebelcode_integration import RebelCODEIntegration

class TestRebelCODEIntegration(unittest.TestCase):
    """Test case for RebelCODE integration."""
    
    def setUp(self):
        """Set up the test case."""
        # Get RebelSUITE root directory
        self.rebelsuite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up test output directory
        self.test_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "rebelcode")
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # Create integration instance
        self.integration = RebelCODEIntegration(self.rebelsuite_root)
    
    def test_initialization(self):
        """Test initialization of RebelCODEIntegration."""
        self.assertIsNotNone(self.integration)
        self.assertEqual(self.integration.rebelsuite_root, self.rebelsuite_root)
        self.assertEqual(self.integration.rebelcode_dir, os.path.join(self.rebelsuite_root, "RebelCODE"))
        self.assertTrue(os.path.exists(self.integration.rebelcode_dir))
    
    def test_extract_documentation(self):
        """Test extraction of documentation from RebelCODE source code."""
        # Extract documentation
        docs = self.integration.extract_documentation(self.test_output_dir)
        
        # Check that documentation was extracted
        self.assertIsNotNone(docs)
        self.assertGreater(len(docs), 0)
        
        # Check that output files were created
        self.assertTrue(os.path.exists(os.path.join(self.test_output_dir, "index.html")))
        
        # Check that at least one documentation file was created
        doc_files = [f for f in os.listdir(self.test_output_dir) if f.endswith(".html") and f != "index.html"]
        self.assertGreater(len(doc_files), 0)
        
        # Check that at least one markdown file was created
        md_files = [f for f in os.listdir(self.test_output_dir) if f.endswith(".md")]
        self.assertGreater(len(md_files), 0)
        
        # Print summary
        print(f"Extracted {len(docs)} documentation items")
        print(f"Generated {len(doc_files)} HTML files")
        print(f"Generated {len(md_files)} Markdown files")
    
    def test_extract_from_directory(self):
        """Test extraction of documentation from a directory."""
        # Extract documentation from src directory
        src_dir = os.path.join(self.integration.rebelcode_dir, "src")
        docs = self.integration._extract_from_directory(
            src_dir,
            "RebelCODE",
            "typescript"
        )
        
        # Check that documentation was extracted
        self.assertIsNotNone(docs)
        self.assertGreater(len(docs), 0)
        
        # Print summary
        print(f"Extracted {len(docs)} documentation items from src directory")
    
    def test_generate_index_html(self):
        """Test generation of index.html."""
        # Extract documentation
        docs = self.integration.extract_documentation(self.test_output_dir)
        
        # Generate index.html
        index_html = self.integration._generate_index_html(docs)
        
        # Check that index.html was generated
        self.assertIsNotNone(index_html)
        self.assertGreater(len(index_html), 0)
        self.assertIn("<!DOCTYPE html>", index_html)
        self.assertIn("<title>RebelCODE Documentation</title>", index_html)
        
        # Print summary
        print(f"Generated index.html with {len(index_html)} characters")

def main():
    """Run the tests."""
    unittest.main()

if __name__ == "__main__":
    main()
