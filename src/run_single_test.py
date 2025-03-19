import unittest
import sys
import traceback

from tests.backend.services.test_statistics_service import TestStatisticsService

if __name__ == "__main__":
    print("Starting test execution...")
    
    try:
        # Create an instance of the test class
        test_instance = TestStatisticsService("test_update_goal_progress")
        
        # Run the test
        test_instance.setUp()
        test_instance.test_update_goal_progress()
        test_instance.tearDown()
        
        print("Test passed!")
        sys.exit(0)
    except Exception as e:
        print(f"Test failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)
