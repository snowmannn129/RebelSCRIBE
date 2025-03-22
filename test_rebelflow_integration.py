#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for RebelFLOW integration with RebelSCRIBE.

This script tests the RebelFLOW integration module to ensure it correctly extracts
documentation from RebelFLOW source code and generates documentation.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(parent_dir))

from src.integrations.rebelflow_integration import RebelFLOWIntegration

class TestRebelFLOWIntegration(unittest.TestCase):
    """Test case for RebelFLOW integration."""
    
    def setUp(self):
        """Set up the test case."""
        # Get RebelSUITE root directory
        self.rebelsuite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up test output directory
        self.test_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "rebelflow")
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # Create integration instance
        self.integration = RebelFLOWIntegration(self.rebelsuite_root)
    
    def test_initialization(self):
        """Test initialization of RebelFLOWIntegration."""
        self.assertIsNotNone(self.integration)
        self.assertEqual(self.integration.rebelsuite_root, self.rebelsuite_root)
        self.assertEqual(self.integration.rebelflow_dir, os.path.join(self.rebelsuite_root, "RebelFLOW"))
        self.assertTrue(os.path.exists(self.integration.rebelflow_dir))
    
    def test_extract_documentation(self):
        """Test extraction of documentation from RebelFLOW source code."""
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
        src_dir = os.path.join(self.integration.rebelflow_dir, "src")
        docs = self.integration._extract_from_directory(
            src_dir,
            "RebelFLOW",
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
        self.assertIn("<title>RebelFLOW Documentation</title>", index_html)
        
        # Print summary
        print(f"Generated index.html with {len(index_html)} characters")
    
    def test_node_specific_features(self):
        """Test node-specific features of RebelFLOW integration."""
        # Extract documentation
        docs = self.integration.extract_documentation(self.test_output_dir)
        
        # Check for node-specific metadata
        node_docs = [doc for doc in docs if doc.type == "node"]
        
        # Print summary
        print(f"Found {len(node_docs)} node documentation items")
        
        # Check node categories
        node_categories = set()
        for doc in node_docs:
            if doc.metadata and "nodeCategory" in doc.metadata:
                node_categories.add(doc.metadata["nodeCategory"])
        
        print(f"Found {len(node_categories)} node categories: {', '.join(node_categories)}")
        
        # Check node inputs and outputs
        nodes_with_inputs = 0
        nodes_with_outputs = 0
        
        for doc in node_docs:
            if doc.metadata and "nodeInputs" in doc.metadata:
                nodes_with_inputs += 1
            
            if doc.metadata and "nodeOutputs" in doc.metadata:
                nodes_with_outputs += 1
        
        print(f"Found {nodes_with_inputs} nodes with inputs")
        print(f"Found {nodes_with_outputs} nodes with outputs")

def main():
    """Run the tests."""
    unittest.main()

if __name__ == "__main__":
    main()
