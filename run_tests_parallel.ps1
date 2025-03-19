#!/usr/bin/env pwsh
# RebelSCRIBE Parallel Test Runner
# This script runs tests in parallel to speed up the testing process

# Parse command line arguments
param(
    [string]$TestPath = "src/tests",
    [int]$NumProcesses = 4,
    [switch]$FailFast,
    [switch]$Verbose,
    [string]$OutputFile = ""
)

# Set the Python executable path
$pythonExe = "python"

# Create output directory for test results if it doesn't exist and output file is specified
if ($OutputFile -ne "") {
    $outputDir = Split-Path -Parent $OutputFile
    if ($outputDir -ne "" -and -not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
        Write-Host "Created output directory: $outputDir" -ForegroundColor Green
    }
}

# Set verbosity flag
$verbosityFlag = if ($Verbose) { "-v" } else { "" }

# Build the command
$command = "$pythonExe -m pytest $TestPath $verbosityFlag -xvs"

# Add parallel execution
$command += " -n $NumProcesses"

# Add fail-fast option if specified
if ($FailFast) {
    $command += " --exitfirst"
}

# Start the timer
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Run the tests
Write-Host "Running tests in parallel with $NumProcesses processes..." -ForegroundColor Cyan
Write-Host "Command: $command" -ForegroundColor Yellow

if ($OutputFile -ne "") {
    Write-Host "Test output will be saved to: $OutputFile" -ForegroundColor Yellow
    Invoke-Expression "$command | Tee-Object -FilePath $OutputFile"
} else {
    Invoke-Expression $command
}

# Stop the timer
$stopwatch.Stop()
$elapsedTime = $stopwatch.Elapsed

# Check the exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed successfully!" -ForegroundColor Green
    Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Green
    
    # Add summary to the output file if specified
    if ($OutputFile -ne "") {
        Add-Content -Path $OutputFile -Value "`n`n===== TEST SUMMARY ====="
        Add-Content -Path $OutputFile -Value "Status: All tests passed"
        Add-Content -Path $OutputFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
        Add-Content -Path $OutputFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        Add-Content -Path $OutputFile -Value "Processes: $NumProcesses"
    }
} else {
    Write-Host "Some tests failed. Please check the output above for details." -ForegroundColor Red
    Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Red
    
    # Add summary to the output file if specified
    if ($OutputFile -ne "") {
        Add-Content -Path $OutputFile -Value "`n`n===== TEST SUMMARY ====="
        Add-Content -Path $OutputFile -Value "Status: Some tests failed"
        Add-Content -Path $OutputFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
        Add-Content -Path $OutputFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        Add-Content -Path $OutputFile -Value "Processes: $NumProcesses"
    }
}

# Note: Before using this script, make sure to install pytest-xdist:
# pip install pytest-xdist

# Example usage:
# Run all tests in parallel with 4 processes:
# .\run_tests_parallel.ps1
#
# Run specific tests in parallel with 8 processes:
# .\run_tests_parallel.ps1 -TestPath "src/tests/ui" -NumProcesses 8
#
# Run tests in parallel and stop on first failure:
# .\run_tests_parallel.ps1 -FailFast
#
# Run tests in parallel with verbose output and save to a file:
# .\run_tests_parallel.ps1 -Verbose -OutputFile "test_results/parallel_tests.txt"
