# Run comprehensive UI tests for RebelSCRIBE
# This script runs the comprehensive UI tests to ensure all UI components are present and functional

# Set the Python executable path
$pythonExe = "python"

# Set the test file path
$testFile = "src/tests/ui/test_comprehensive_ui.py"

# Check if the test file exists
if (-not (Test-Path $testFile)) {
    Write-Error "Test file not found: $testFile"
    exit 1
}

# Run the tests with verbose output
Write-Host "Running comprehensive UI tests..." -ForegroundColor Green
& $pythonExe -m unittest $testFile -v 2>&1 | Tee-Object -Variable testOutput

# Print the test output
Write-Host $testOutput

# Check the exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed. Please check the output above for details." -ForegroundColor Red
}
