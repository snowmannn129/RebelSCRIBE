#!/usr/bin/env pwsh
# RebelSCRIBE Test Coverage Runner
# This script runs tests with coverage reporting to identify areas that need more testing

# Parse command line arguments
param(
    [string]$TestPath = "src/tests",
    [int]$MinCoverage = 80,
    [switch]$Html,
    [switch]$Xml,
    [switch]$FailUnderMin,
    [switch]$Verbose
)

# Set the Python executable path
$pythonExe = "python"

# Create output directory for coverage results if it doesn't exist
$coverageDir = "coverage_reports"
if (-not (Test-Path $coverageDir)) {
    New-Item -ItemType Directory -Path $coverageDir | Out-Null
    Write-Host "Created coverage directory: $coverageDir" -ForegroundColor Green
}

# Get current timestamp for the output files
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Set verbosity flag
$verbosityFlag = if ($Verbose) { "-v" } else { "" }

# Build the base command
$command = "$pythonExe -m pytest $TestPath $verbosityFlag --cov=src"

# Add coverage report formats
if ($Html) {
    $htmlReport = "$coverageDir/coverage_html_$timestamp"
    $command += " --cov-report=html:$htmlReport"
}

if ($Xml) {
    $xmlReport = "$coverageDir/coverage_$timestamp.xml"
    $command += " --cov-report=xml:$xmlReport"
}

# Always add terminal report
$command += " --cov-report=term"

# Add minimum coverage requirement if specified
if ($FailUnderMin) {
    $command += " --cov-fail-under=$MinCoverage"
}

# Start the timer
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Run the tests with coverage
Write-Host "Running tests with coverage..." -ForegroundColor Cyan
Write-Host "Command: $command" -ForegroundColor Yellow

# Create a log file for the output
$logFile = "$coverageDir/coverage_log_$timestamp.txt"
Write-Host "Test output will be saved to: $logFile" -ForegroundColor Yellow

# Run the command and capture output
Invoke-Expression "$command | Tee-Object -FilePath $logFile"

# Stop the timer
$stopwatch.Stop()
$elapsedTime = $stopwatch.Elapsed

# Check the exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "Tests completed successfully!" -ForegroundColor Green
    Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Green
    
    # Add summary to the log file
    Add-Content -Path $logFile -Value "`n`n===== TEST SUMMARY ====="
    Add-Content -Path $logFile -Value "Status: All tests passed"
    Add-Content -Path $logFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
    Add-Content -Path $logFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    
    # Report coverage report locations
    if ($Html) {
        Write-Host "HTML coverage report: $htmlReport/index.html" -ForegroundColor Green
        Add-Content -Path $logFile -Value "HTML coverage report: $htmlReport/index.html"
    }
    
    if ($Xml) {
        Write-Host "XML coverage report: $xmlReport" -ForegroundColor Green
        Add-Content -Path $logFile -Value "XML coverage report: $xmlReport"
    }
} else {
    if ($FailUnderMin -and $LASTEXITCODE -eq 2) {
        Write-Host "Tests passed but coverage is below the minimum threshold of $MinCoverage%." -ForegroundColor Yellow
    } else {
        Write-Host "Some tests failed. Please check the output above for details." -ForegroundColor Red
    }
    
    Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Red
    
    # Add summary to the log file
    Add-Content -Path $logFile -Value "`n`n===== TEST SUMMARY ====="
    
    if ($FailUnderMin -and $LASTEXITCODE -eq 2) {
        Add-Content -Path $logFile -Value "Status: Tests passed but coverage below minimum threshold"
    } else {
        Add-Content -Path $logFile -Value "Status: Some tests failed"
    }
    
    Add-Content -Path $logFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
    Add-Content -Path $logFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    
    # Report coverage report locations
    if ($Html) {
        Write-Host "HTML coverage report: $htmlReport/index.html" -ForegroundColor Yellow
        Add-Content -Path $logFile -Value "HTML coverage report: $htmlReport/index.html"
    }
    
    if ($Xml) {
        Write-Host "XML coverage report: $xmlReport" -ForegroundColor Yellow
        Add-Content -Path $logFile -Value "XML coverage report: $xmlReport"
    }
}

Write-Host "Coverage log saved to: $logFile" -ForegroundColor Green

# Example usage:
# Run all tests with coverage and generate HTML report:
# .\run_tests_with_coverage.ps1 -Html
#
# Run specific tests with coverage and fail if below 90%:
# .\run_tests_with_coverage.ps1 -TestPath "src/tests/ui" -MinCoverage 90 -FailUnderMin -Html
#
# Run all tests with coverage and generate both HTML and XML reports:
# .\run_tests_with_coverage.ps1 -Html -Xml
