import sys
import os
import unittest
import io
import contextlib

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the test module
from src.tests.backend.services.test_statistics_service import TestStatisticsService

if __name__ == "__main__":
    # Create a string buffer to capture output
    output_buffer = io.StringIO()
    
    # Capture both stdout and stderr
    with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
        # Create a test suite with all tests from TestStatisticsService
        suite = unittest.TestLoader().loadTestsFromTestCase(TestStatisticsService)
        
        # Run the tests
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Get the captured output
    output = output_buffer.getvalue()
    
    # Write the output to a file
    with open("test_output.txt", "w") as f:
        f.write(output)
    
    print(f"Test output written to test_output.txt")
    print(f"Tests passed: {result.wasSuccessful()}")
    
    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful())
