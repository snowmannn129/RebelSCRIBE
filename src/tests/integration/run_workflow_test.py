#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run the workflow integration tests.
"""

import os
import sys
import unittest
import logging
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import the test module
from src.tests.integration.test_workflow import TestEndToEndWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

if __name__ == '__main__':
    # Create a test suite with the workflow tests
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestEndToEndWorkflow)
    
    # Run the tests
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Print a summary of the test results
    print(f"Tests run: {test_result.testsRun}")
    print(f"Errors: {len(test_result.errors)}")
    print(f"Failures: {len(test_result.failures)}")
    print(f"Skipped: {len(test_result.skipped)}")
    
    # Print detailed error information if there are any errors or failures
    if test_result.errors:
        print("\nERRORS:")
        for test, error in test_result.errors:
            print(f"ERROR: {test}")
            print(error)
    
    if test_result.failures:
        print("\nFAILURES:")
        for test, failure in test_result.failures:
            print(f"FAILURE: {test}")
            print(failure)
    
    # Print a final status message
    if test_result.wasSuccessful():
        print("All tests passed successfully!")
    else:
        print("Tests failed!")
    
    # Exit with an appropriate status code
    sys.exit(not test_result.wasSuccessful())
