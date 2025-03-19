#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run script for advanced AI tests.

This script runs the advanced tests for the AI module,
focusing on edge cases, error handling, and advanced features.
"""

import os
import sys
import unittest
import pytest
import argparse

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run advanced AI tests")
    
    # Main options
    parser.add_argument("--pytest", action="store_true", help="Use pytest runner instead of unittest")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("--cov", action="store_true", help="Generate coverage report (pytest only)")
    parser.add_argument("--cov-report", choices=["term", "html", "xml", "all"], default="term",
                        help="Coverage report format (pytest only)")
    
    # Test selection
    parser.add_argument("--test-file", help="Run specific test file (e.g., test_llama_support.py)")
    parser.add_argument("--test-class", help="Run specific test class (e.g., TestLlamaSupport)")
    parser.add_argument("--test-method", help="Run specific test method (e.g., test_load_model)")
    parser.add_argument("--model", choices=["local", "llama", "mistral", "phi", "falcon", "mpt", "adapter", "progress", "gguf", "registry", "benchmark", "visualization", "all"], default="all",
                        help="Run tests for specific model")
    
    # Additional options
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat tests multiple times")
    parser.add_argument("--output", help="Save test output to file")
    
    return parser.parse_args()

def get_test_files(args):
    """Get the test files to run based on arguments."""
    if args.test_file:
        # If a specific file is provided, use it
        return [f"src/tests/ai/{args.test_file}"]
    
    if args.model != "all":
        # If a specific model is selected
        model_map = {
            "local": ["test_local_models_advanced.py"],
            "llama": ["test_llama_support.py"],
            "mistral": ["test_mistral_support.py"],
            "phi": ["test_phi_support.py"],
            "falcon": ["test_falcon_support.py"],
            "mpt": ["test_mpt_support.py"],
            "adapter": ["test_adapter_support.py"],
            "progress": ["test_progress_callbacks.py"],
            "gguf": ["test_gguf_support.py"],
            "registry": ["test_model_registry.py"],
            "benchmark": ["test_model_benchmarking.py"],
            "visualization": ["test_benchmark_visualization.py"]
        }
        return [f"src/tests/ai/{file}" for file in model_map[args.model]]
    
    # Default: all test files
    return [
        "src/tests/ai/test_local_models_advanced.py",
        "src/tests/ai/test_llama_support.py",
        "src/tests/ai/test_mistral_support.py",
        "src/tests/ai/test_phi_support.py",
        "src/tests/ai/test_falcon_support.py",
        "src/tests/ai/test_mpt_support.py",
        "src/tests/ai/test_adapter_support.py",
        "src/tests/ai/test_progress_callbacks.py",
        "src/tests/ai/test_gguf_support.py",
        "src/tests/ai/test_model_registry.py",
        "src/tests/ai/test_model_benchmarking.py",
        "src/tests/ai/test_benchmark_visualization.py"
    ]

def run_with_pytest(args, test_files):
    """Run tests using pytest."""
    print("Using pytest runner")
    
    # Start with basic arguments
    pytest_args = []
    
    # Add test files
    pytest_args.extend(test_files)
    
    # Add verbosity
    if args.verbose:
        pytest_args.append("-v")
    
    # Add coverage if requested
    if args.cov:
        pytest_args.append("--cov=src/ai")
        if args.cov_report == "all":
            pytest_args.extend(["--cov-report=term", "--cov-report=html", "--cov-report=xml"])
        else:
            pytest_args.append(f"--cov-report={args.cov_report}")
    
    # Add fail-fast if requested
    if args.fail_fast:
        pytest_args.append("-x")
    
    # Add repeat if requested
    if args.repeat > 1:
        pytest_args.append(f"--count={args.repeat}")
    
    # Add specific test class or method if provided
    if args.test_class:
        class_filter = f"::{args.test_class}"
        if args.test_method:
            class_filter += f"::{args.test_method}"
        
        # Apply the filter to all test files
        for i, file in enumerate(pytest_args):
            if file.startswith("src/tests/ai/test_"):
                pytest_args[i] = f"{file}{class_filter}"
    elif args.test_method:
        # If only method is provided, we need to search for it in all files
        method_filter = f"::*::{args.test_method}"
        for i, file in enumerate(pytest_args):
            if file.startswith("src/tests/ai/test_"):
                pytest_args[i] = f"{file}{method_filter}"
    
    # Print the command
    print(f"Running: pytest {' '.join(pytest_args)}")
    
    # Run pytest
    exit_code = pytest.main(pytest_args)
    return exit_code

def run_with_unittest(args, test_files):
    """Run tests using unittest."""
    print("Using unittest runner")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Process test files
    for test_file in test_files:
        # Convert file path to module name
        module_name = test_file.replace("/", ".").replace(".py", "")
        
        if args.test_class:
            # If a specific class is provided
            if args.test_method:
                # If a specific method is also provided
                suite.addTest(loader.loadTestsFromName(f"{module_name}.{args.test_class}.{args.test_method}"))
            else:
                # Just the class
                suite.addTest(loader.loadTestsFromName(f"{module_name}.{args.test_class}"))
        else:
            # Load all tests from the module
            try:
                suite.addTests(loader.loadTestsFromName(module_name))
            except (ImportError, AttributeError) as e:
                print(f"Error loading tests from {module_name}: {e}")
    
    # Set up the test runner
    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, failfast=args.fail_fast)
    
    # Run tests
    result = runner.run(suite)
    
    # Return appropriate exit code
    return not result.wasSuccessful()

def main():
    """Main function to run the tests."""
    args = parse_arguments()
    
    print("Running advanced AI tests...")
    
    # Get test files to run
    test_files = get_test_files(args)
    
    # Redirect output if requested
    if args.output:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        with open(args.output, 'w') as f:
            sys.stdout = f
            sys.stderr = f
            
            # Run tests with appropriate runner
            if args.pytest:
                exit_code = run_with_pytest(args, test_files)
            else:
                exit_code = run_with_unittest(args, test_files)
            
            # Restore stdout and stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
            print(f"Test output saved to {args.output}")
    else:
        # Run tests with appropriate runner
        if args.pytest:
            exit_code = run_with_pytest(args, test_files)
        else:
            exit_code = run_with_unittest(args, test_files)
    
    # Exit with appropriate code
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
