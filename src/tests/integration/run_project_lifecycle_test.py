import unittest
import sys
from test_project_lifecycle import TestProjectLifecycle

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProjectLifecycle)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("All tests passed successfully!")
        sys.exit(0)
    else:
        print("Tests failed!")
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(error[1])
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(failure[1])
        sys.exit(1)
