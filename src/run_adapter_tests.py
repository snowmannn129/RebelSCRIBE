#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run adapter support tests.

This script provides a flexible way to run tests for the adapter support module.
It supports various command-line options for controlling which tests to run,
how they are run, and where the output is directed.

Examples:
    # Run all adapter tests
    python src/run_adapter_tests.py

    # Run only TestAdapterInfo tests
    python src/run_adapter_tests.py --test-class TestAdapterInfo

    # Run a specific test method
    python src/run_adapter_tests.py --test-method test_init

    # Run tests with high verbosity
    python src/run_adapter_tests.py --verbose 2

    # Run tests and save output to a file
    python src/run_adapter_tests.py --output test_results.txt

    # Run tests multiple times for stability testing
    python src/run_adapter_tests.py --repeat 3

    # Stop on first failure for quicker debugging
    python src/run_adapter_tests.py --fail-fast
"""

import unittest
import sys
import os
import argparse
import time
from typing import List, Optional, TextIO

# Add the parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run adapter support tests")
    
    parser.add_argument(
        "--test-class",
        type=str,
        help="Run only tests from the specified class (TestAdapterInfo or TestAdapterManager)"
    )
    
    parser.add_argument(
        "--test-method",
        type=str,
        help="Run only the specified test method"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="Verbosity level (0=quiet, 1=normal, 2=verbose)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="File to write test output to"
    )
    
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat the tests"
    )
    
    parser.add_argument(
        "--fail-fast", "-f",
        action="store_true",
        help="Stop on first failure"
    )
    
    return parser.parse_args()


def create_test_suite(test_class: Optional[str] = None, test_method: Optional[str] = None) -> unittest.TestSuite:
    """
    Create a test suite with the specified tests.
    
    Args:
        test_class: Name of the test class to run (optional)
        test_method: Name of the test method to run (optional)
    
    Returns:
        A test suite containing the specified tests
    """
    print("Importing test modules...")
    
    # Import the test module
    from tests.ai.test_adapter_support import TestAdapterInfo, TestAdapterManager
    
    print("Test modules imported successfully.")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Determine which test classes to include
    test_classes = []
    if test_class:
        if test_class == "TestAdapterInfo":
            test_classes = [TestAdapterInfo]
        elif test_class == "TestAdapterManager":
            test_classes = [TestAdapterManager]
        else:
            print(f"Warning: Unknown test class '{test_class}'. Using all test classes.")
            test_classes = [TestAdapterInfo, TestAdapterManager]
    else:
        test_classes = [TestAdapterInfo, TestAdapterManager]
    
    # Add tests to the suite
    for cls in test_classes:
        if test_method:
            # Add only the specified test method if it exists
            if hasattr(cls, test_method) and callable(getattr(cls, test_method)):
                suite.addTest(cls(test_method))
            else:
                print(f"Warning: Test method '{test_method}' not found in {cls.__name__}")
        else:
            # Add all test methods from the class
            for method_name in dir(cls):
                if method_name.startswith('test_'):
                    suite.addTest(cls(method_name))
    
    return suite


def run_tests(suite: unittest.TestSuite, verbosity: int = 2, 
              output_file: Optional[TextIO] = None, fail_fast: bool = False) -> unittest.TestResult:
    """
    Run the tests in the suite.
    
    Args:
        suite: The test suite to run
        verbosity: Verbosity level (0=quiet, 1=normal, 2=verbose)
        output_file: File to write test output to (optional)
        fail_fast: Whether to stop on first failure
    
    Returns:
        The test result
    """
    # Create a test runner
    if output_file:
        # Use a custom test runner that writes to the output file
        from unittest import TextTestRunner
        runner = TextTestRunner(stream=output_file, verbosity=verbosity, failfast=fail_fast)
    else:
        # Use the standard test runner
        runner = unittest.TextTestRunner(verbosity=verbosity, failfast=fail_fast)
    
    # Run the tests
    return runner.run(suite)


def print_result_summary(result: unittest.TestResult, run_time: float, output_file: Optional[TextIO] = None):
    """
    Print a summary of the test results.
    
    Args:
        result: The test result
        run_time: The time taken to run the tests
        output_file: File to write the summary to (optional)
    """
    # Determine where to print the summary
    out = output_file if output_file else sys.stdout
    
    # Print the summary
    print(f"\nTests run: {result.testsRun}", file=out)
    print(f"Time taken: {run_time:.2f} seconds", file=out)
    print(f"Errors: {len(result.errors)}", file=out)
    print(f"Failures: {len(result.failures)}", file=out)
    
    # Print errors
    if result.errors:
        print("\nErrors:", file=out)
        for test, error in result.errors:
            print(f"{test}: {error}", file=out)
    
    # Print failures
    if result.failures:
        print("\nFailures:", file=out)
        for test, failure in result.failures:
            print(f"{test}: {failure}", file=out)


def main():
    """Main function."""
    print("Starting adapter tests...")
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Open output file if specified
    output_file = None
    if args.output:
        try:
            output_file = open(args.output, 'w')
            print(f"Writing test output to {args.output}")
        except IOError as e:
            print(f"Error opening output file: {e}")
            return 1
    
    # Create test suite
    suite = create_test_suite(args.test_class, args.test_method)
    
    # Run tests the specified number of times
    all_passed = True
    for i in range(args.repeat):
        if args.repeat > 1:
            print(f"\nRun {i+1}/{args.repeat}:")
        
        # Run the tests and measure the time taken
        start_time = time.time()
        result = run_tests(suite, args.verbose, output_file, args.fail_fast)
        run_time = time.time() - start_time
        
        # Print result summary
        print_result_summary(result, run_time, output_file)
        
        # Update overall result
        all_passed = all_passed and result.wasSuccessful()
        
        # Stop if tests failed and fail-fast is enabled
        if not result.wasSuccessful() and args.fail_fast:
            break
    
    # Close output file if opened
    if output_file:
        output_file.close()
    
    # Return appropriate exit code
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
