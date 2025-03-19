#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RebelSCRIBE - UI Test Runner

This script runs the UI tests for RebelSCRIBE.
"""

import os
import sys
import unittest
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
sys.path.insert(0, project_root)

# Import test utilities
from src.utils.logging_utils import get_logger, setup_logging

# Set up logging
logger = get_logger(__name__)
setup_logging(log_level=logging.DEBUG)

def discover_tests(test_pattern=None, test_dir=None):
    """
    Discover tests based on the given pattern and directory.
    
    Args:
        test_pattern: Pattern to match test files (default: "test_*.py")
        test_dir: Directory to search for tests (default: current directory)
    
    Returns:
        TestSuite: A test suite containing the discovered tests
    """
    if test_dir is None:
        test_dir = os.path.dirname(os.path.abspath(__file__))
    
    if test_pattern is None:
        test_pattern = "test_*.py"
    
    logger.info(f"Discovering tests in {test_dir} with pattern {test_pattern}")
    
    return unittest.defaultTestLoader.discover(
        start_dir=test_dir,
        pattern=test_pattern,
        top_level_dir=os.path.abspath(os.path.join(test_dir, '..', '..'))
    )

def run_tests(test_suite, output_file=None):
    """
    Run the given test suite.
    
    Args:
        test_suite: TestSuite to run
        output_file: File to write test results to (default: None)
    
    Returns:
        TestResult: The result of running the test suite
    """
    if output_file:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Run tests with output to file
        with open(output_file, 'w') as f:
            runner = unittest.TextTestRunner(
                stream=f,
                verbosity=2,
                failfast=False
            )
            result = runner.run(test_suite)
    else:
        # Run tests with output to console
        runner = unittest.TextTestRunner(
            verbosity=2,
            failfast=False
        )
        result = runner.run(test_suite)
    
    return result

def generate_report(result, output_file=None):
    """
    Generate a report of the test results.
    
    Args:
        result: TestResult to generate report for
        output_file: File to write report to (default: None)
    """
    # Create report content
    report = []
    report.append("=" * 80)
    report.append(f"RebelSCRIBE UI Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")
    
    # Test summary
    report.append("Test Summary:")
    report.append(f"  Tests run: {result.testsRun}")
    report.append(f"  Errors: {len(result.errors)}")
    report.append(f"  Failures: {len(result.failures)}")
    report.append(f"  Skipped: {len(result.skipped)}")
    report.append(f"  Success rate: {(result.testsRun - len(result.errors) - len(result.failures)) / result.testsRun * 100:.2f}%")
    report.append("")
    
    # Errors
    if result.errors:
        report.append("Errors:")
        for i, (test, error) in enumerate(result.errors, 1):
            report.append(f"  {i}. {test}")
            report.append(f"     {error}")
            report.append("")
    
    # Failures
    if result.failures:
        report.append("Failures:")
        for i, (test, failure) in enumerate(result.failures, 1):
            report.append(f"  {i}. {test}")
            report.append(f"     {failure}")
            report.append("")
    
    # Skipped
    if result.skipped:
        report.append("Skipped:")
        for i, (test, reason) in enumerate(result.skipped, 1):
            report.append(f"  {i}. {test}")
            report.append(f"     Reason: {reason}")
            report.append("")
    
    # Join report lines
    report_text = "\n".join(report)
    
    # Write report to file or print to console
    if output_file:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        logger.info(f"Test report written to {output_file}")
    else:
        print(report_text)

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run RebelSCRIBE UI tests")
    parser.add_argument(
        "--pattern", "-p",
        help="Pattern to match test files (default: test_*.py)",
        default="test_*.py"
    )
    parser.add_argument(
        "--dir", "-d",
        help="Directory to search for tests (default: current directory)",
        default=None
    )
    parser.add_argument(
        "--output", "-o",
        help="File to write test results to (default: None)",
        default=None
    )
    parser.add_argument(
        "--report", "-r",
        help="File to write test report to (default: None)",
        default=None
    )
    parser.add_argument(
        "--component", "-c",
        help="Specific UI component to test (e.g., event_bus, state_manager)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Set test directory
    test_dir = args.dir or os.path.dirname(os.path.abspath(__file__))
    
    # Set test pattern
    if args.component:
        test_pattern = f"test_{args.component}.py"
    else:
        test_pattern = args.pattern
    
    # Set output file
    if args.output:
        output_file = args.output
    else:
        # Create a timestamped output file in the test_results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(project_root, "test_results")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"ui_tests_{timestamp}.txt")
    
    # Set report file
    if args.report:
        report_file = args.report
    else:
        # Create a timestamped report file in the test_results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(project_root, "test_results")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"ui_test_report_{timestamp}.txt")
    
    # Discover tests
    test_suite = discover_tests(test_pattern, test_dir)
    
    # Run tests
    start_time = time.time()
    result = run_tests(test_suite, output_file)
    end_time = time.time()
    
    # Generate report
    generate_report(result, report_file)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success rate: {(result.testsRun - len(result.errors) - len(result.failures)) / result.testsRun * 100:.2f}%")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    # Return exit code
    return 0 if len(result.errors) == 0 and len(result.failures) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
