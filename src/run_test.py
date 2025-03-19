import unittest
import sys
import traceback
import io
import contextlib

from tests.backend.services.test_statistics_service import TestStatisticsService

def run_test_with_output_capture():
    # Create a string buffer to capture output
    output_buffer = io.StringIO()
    
    # Capture both stdout and stderr
    with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
        try:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestStatisticsService)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            success = result.wasSuccessful()
        except Exception as e:
            print(f"Exception during test execution: {e}")
            traceback.print_exc()
            success = False
    
    # Get the captured output
    output = output_buffer.getvalue()
    return success, output

if __name__ == "__main__":
    try:
        print("Starting test execution...")
        success, output = run_test_with_output_capture()
        
        print("\n--- Test Output ---")
        print(output)
        print("--- End Test Output ---\n")
        
        if success:
            print("All tests passed!")
            sys.exit(0)
        else:
            print("Some tests failed. See output above for details.")
            sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        traceback.print_exc()
        sys.exit(1)
