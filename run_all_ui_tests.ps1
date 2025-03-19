# RebelSCRIBE - Run All UI Tests
# This script runs all UI tests for RebelSCRIBE

# Set error action preference
$ErrorActionPreference = "Stop"

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set the project root directory
$projectRoot = $scriptDir

# Create timestamp for output files
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Create output directories if they don't exist
$testResultsDir = Join-Path -Path $projectRoot -ChildPath "test_results"
if (-not (Test-Path -Path $testResultsDir)) {
    New-Item -ItemType Directory -Path $testResultsDir | Out-Null
}

# Set output files
$outputFile = Join-Path -Path $testResultsDir -ChildPath "ui_tests_$timestamp.txt"
$reportFile = Join-Path -Path $testResultsDir -ChildPath "ui_test_report_$timestamp.txt"

# Display header
Write-Host "========================================================"
Write-Host "RebelSCRIBE UI Tests - $(Get-Date)"
Write-Host "========================================================"
Write-Host ""

# Run UI tests
Write-Host "Running UI tests..."
$startTime = Get-Date

try {
    # Run the Python test script
    python "$projectRoot\src\tests\ui\run_ui_tests.py" --output $outputFile --report $reportFile
    $exitCode = $LASTEXITCODE
    
    # Get test duration
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    # Display results
    Write-Host ""
    Write-Host "Test execution completed in $([math]::Round($duration, 2)) seconds."
    Write-Host "Test output saved to: $outputFile"
    Write-Host "Test report saved to: $reportFile"
    
    # Display report summary
    if (Test-Path -Path $reportFile) {
        Write-Host ""
        Write-Host "Test Summary:"
        Write-Host "-------------"
        $reportContent = Get-Content -Path $reportFile
        $summaryLines = $reportContent | Select-String -Pattern "Tests run:|Errors:|Failures:|Skipped:|Success rate:"
        foreach ($line in $summaryLines) {
            Write-Host "  $($line.Line.Trim())"
        }
    }
    
    # Return exit code
    exit $exitCode
}
catch {
    Write-Host "Error running UI tests: $_" -ForegroundColor Red
    exit 1
}
