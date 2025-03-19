import sys
import os
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("Starting test debugging...")

try:
    # Import the test class
    print("Importing TestStatisticsService...")
    from src.tests.backend.services.test_statistics_service import TestStatisticsService
    print("Successfully imported TestStatisticsService")
    
    # Create an instance of the test class
    print("Creating test instance...")
    test_instance = TestStatisticsService("test_update_goal_progress")
    print("Successfully created test instance")
    
    # Run setUp
    print("Running setUp...")
    test_instance.setUp()
    print("Successfully ran setUp")
    
    # Run the test method
    print("Running test_update_goal_progress...")
    test_instance.test_update_goal_progress()
    print("Successfully ran test_update_goal_progress")
    
    # Run tearDown
    print("Running tearDown...")
    test_instance.tearDown()
    print("Successfully ran tearDown")
    
    print("Test passed!")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    print("Test failed!")
    sys.exit(1)

print("Test debugging complete")
sys.exit(0)
