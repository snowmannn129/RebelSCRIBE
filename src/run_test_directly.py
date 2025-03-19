import sys
import os
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the test module
from src.tests.backend.services.test_statistics_service import TestStatisticsService

if __name__ == "__main__":
    # Create a test suite with all tests from TestStatisticsService
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStatisticsService)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful())
