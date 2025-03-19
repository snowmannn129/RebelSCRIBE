#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run a single test method from a specified test class.

This script provides a flexible way to run a single test method from any test class.
It supports command-line arguments for specifying the test file, test class, and test method.

Examples:
    # Run a specific test method
    python src/run_single_test_method.py --test-file src/tests/ui/test_adapter_training_integration.py --test-class TestAdapterTrainingIntegration --test-method test_start_training_integration
"""

import sys
import os
import unittest
import argparse
import importlib.util
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run a single test method")
    
    parser.add_argument(
        "--test-file",
        type=str,
        required=True,
        help="Path to the test file"
    )
    
    parser.add_argument(
        "--test-class",
        type=str,
        required=True,
        help="Name of the test class"
    )
    
    parser.add_argument(
        "--test-method",
        type=str,
        required=True,
        help="Name of the test method"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Increase verbosity"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="File to write test output to"
    )
    
    return parser.parse_args()


def load_test_class(test_file, test_class_name):
    """
    Load a test class from a file.
    
    Args:
        test_file: Path to the test file
        test_class_name: Name of the test class
    
    Returns:
        The test class
    """
    # Convert file path to module name
    if test_file.endswith('.py'):
        test_file = test_file[:-3]
    
    # Replace path separators with dots
    module_name = test_file.replace('/', '.').replace('\\', '.')
    
    # Remove leading dots
    if module_name.startswith('.'):
        module_name = module_name[1:]
    
    try:
        # Import the module
        module = __import__(module_name, fromlist=[test_class_name])
        
        # Get the test class
        if hasattr(module, test_class_name):
            return getattr(module, test_class_name)
        else:
            print(f"Error: Test class '{test_class_name}' not found in {module_name}")
            sys.exit(1)
    except ImportError as e:
        print(f"Error importing module {module_name}: {e}")
        sys.exit(1)


def run_test(test_class, test_method_name, verbose=False, output_file=None):
    """
    Run a single test method.
    
    Args:
        test_class: The test class
        test_method_name: Name of the test method
        verbose: Whether to increase verbosity
        output_file: File to write test output to
    
    Returns:
        The test result
    """
    # Create a test suite with the specified test method
    suite = unittest.TestSuite()
    
    # Check if the test method exists
    if hasattr(test_class, test_method_name) and callable(getattr(test_class, test_method_name)):
        suite.addTest(test_class(test_method_name))
    else:
        print(f"Error: Test method '{test_method_name}' not found in {test_class.__name__}")
        sys.exit(1)
    
    # Create a test runner
    verbosity = 2 if verbose else 1
    if output_file:
        with open(output_file, 'w') as f:
            runner = unittest.TextTestRunner(stream=f, verbosity=verbosity)
            return runner.run(suite)
    else:
        runner = unittest.TextTestRunner(verbosity=verbosity)
        return runner.run(suite)


def main():
    """Main function."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load the test class
    test_class = load_test_class(args.test_file, args.test_class)
    
    # Run the test
    print(f"Running test: {args.test_class}.{args.test_method} from {args.test_file}")
    
    # Start the timer
    start_time = time.time()
    
    # Run the test
    result = run_test(test_class, args.test_method, args.verbose, args.output)
    
    # Stop the timer
    run_time = time.time() - start_time
    
    # Print the result
    print(f"\nTest run completed in {run_time:.2f} seconds")
    
    if result.wasSuccessful():
        print("Test passed!")
        return 0
    else:
        print("Test failed!")
        
        # Print failures
        for failure in result.failures:
            print(f"\nFailure: {failure[0]}")
            print(f"{failure[1]}")
        
        # Print errors
        for error in result.errors:
            print(f"\nError: {error[0]}")
            print(f"{error[1]}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
