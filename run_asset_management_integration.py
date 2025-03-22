#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Asset Management Integration Test for RebelSCRIBE.

This script runs the asset management integration test for RebelSCRIBE,
which demonstrates the integration with the RebelSUITE Unified Asset Management System.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the asset management integration test."""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the path to the test script
        test_script = os.path.join(current_dir, 'test_asset_management_integration.py')
        
        # Check if the test script exists
        if not os.path.exists(test_script):
            logger.error(f"Test script not found: {test_script}")
            return 1
        
        # Run the test script
        logger.info(f"Running asset management integration test: {test_script}")
        result = subprocess.run([sys.executable, test_script], check=False)
        
        # Check the result
        if result.returncode == 0:
            logger.info("Asset management integration test completed successfully")
            return 0
        else:
            logger.error(f"Asset management integration test failed with return code: {result.returncode}")
            return result.returncode
    except Exception as e:
        logger.error(f"Error running asset management integration test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
