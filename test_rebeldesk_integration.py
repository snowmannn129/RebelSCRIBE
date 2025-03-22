#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RebelDESK Integration for RebelSCRIBE.

This script tests the RebelDESK integration for RebelSCRIBE, which extracts documentation
from RebelDESK source code and generates documentation files.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.integrations.rebeldesk_integration import RebelDESKIntegration
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class TestRebelDESKIntegration(unittest.TestCase):
    """Test the RebelDESK integration."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test output
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize the integration
        self.integration = RebelDESKIntegration()
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_extract_documentation(self):
        """Test extracting documentation from RebelDESK source code."""
        # Extract documentation
        docs = self.integration.extract_documentation(self.temp_dir)
        
        # Check that documentation was extracted
        self.assertGreater(len(docs), 0, "No documentation was extracted")
        
        # Check that documentation files were generated
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "index.html")), "index.html was not generated")
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "search_index.json")), "search_index.json was not generated")
        
        # Check that at least one documentation file was generated
        doc_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".html") and f != "index.html"]
        self.assertGreater(len(doc_files), 0, "No documentation files were generated")
    
    def test_integrate_with_rebeldesk(self):
        """Test integrating with RebelDESK."""
        # Create a mock RebelDESK directory
        rebeldesk_dir = os.path.join(self.temp_dir, "RebelDESK")
        os.makedirs(os.path.join(rebeldesk_dir, "src", "integrations"), exist_ok=True)
        
        # Set the RebelDESK directory
        self.integration.rebeldesk_dir = rebeldesk_dir
        
        # Integrate with RebelDESK
        success = self.integration.integrate_with_rebeldesk()
        
        # Check that integration was successful
        self.assertTrue(success, "Integration failed")
        
        # Check that integration files were created
        integration_dir = os.path.join(rebeldesk_dir, "src", "integrations", "rebelscribe")
        self.assertTrue(os.path.exists(integration_dir), "Integration directory was not created")
        self.assertTrue(os.path.exists(os.path.join(integration_dir, "__init__.py")), "__init__.py was not created")
        
        # Check that integration modules were created
        self.assertTrue(os.path.exists(os.path.join(integration_dir, "documentation_manager.py")), "documentation_manager.py was not created")
        self.assertTrue(os.path.exists(os.path.join(integration_dir, "documentation_editor.py")), "documentation_editor.py was not created")
        self.assertTrue(os.path.exists(os.path.join(integration_dir, "documentation_browser.py")), "documentation_browser.py was not created")
        self.assertTrue(os.path.exists(os.path.join(integration_dir, "version_control.py")), "version_control.py was not created")

if __name__ == "__main__":
    unittest.main()
