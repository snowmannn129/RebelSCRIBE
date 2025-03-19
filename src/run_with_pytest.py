import sys
import os
import subprocess

# Get the absolute path to the test file
test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests/backend/services/test_statistics_service.py'))

# Run pytest with the test file
print(f"Running pytest on {test_file}")
result = subprocess.run(['python', '-m', 'pytest', test_file, '-v'], capture_output=True, text=True)

# Print the output
print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)

# Exit with the same status code as pytest
sys.exit(result.returncode)
