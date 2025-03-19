#!/usr/bin/env pwsh
# RebelSCRIBE Single Test Method Runner
# This script runs a single test method from a specified test file

# Parse command line arguments
param(
    [Parameter(Mandatory=$true)]
    [string]$TestFile,
    
    [Parameter(Mandatory=$true)]
    [string]$TestClass,
    
    [Parameter(Mandatory=$true)]
    [string]$TestMethod,
    
    [switch]$VerboseOutput,
    
    [string]$OutputFile = ""
)

# Set the Python executable path
$pythonExe = "python"

# Validate that the test file exists
if (-not (Test-Path $TestFile)) {
    Write-Error "Test file not found: $TestFile"
    exit 1
}

# Create output directory for test results if it doesn't exist and output file is specified
if ($OutputFile -ne "") {
    $outputDir = Split-Path -Parent $OutputFile
    if ($outputDir -ne "" -and -not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
        Write-Host "Created output directory: $outputDir" -ForegroundColor Green
    }
}

# Set verbosity flag
$verbosityFlag = if ($VerboseOutput) { "--verbose" } else { "" }

# Build the command
$command = "$pythonExe src/run_single_test_method.py --test-file $TestFile --test-class $TestClass --test-method $TestMethod $verbosityFlag"

# Start the timer
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Run the test
Write-Host "Running test: $TestClass.$TestMethod from $TestFile" -ForegroundColor Cyan
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
    Write-Host "Test passed successfully!" -ForegroundColor Green
    Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Green
    
    # Add summary to the output file if specified
    if ($OutputFile -ne "") {
        Add-Content -Path $OutputFile -Value "`n`n===== TEST SUMMARY ====="
        Add-Content -Path $OutputFile -Value "Test: $TestClass.$TestMethod"
        Add-Content -Path $OutputFile -Value "Status: Passed"
        Add-Content -Path $OutputFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
        Add-Content -Path $OutputFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }
} else {
    Write-Host "Test failed. Please check the output above for details." -ForegroundColor Red
    Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Red
    
    # Add summary to the output file if specified
    if ($OutputFile -ne "") {
        Add-Content -Path $OutputFile -Value "`n`n===== TEST SUMMARY ====="
        Add-Content -Path $OutputFile -Value "Test: $TestClass.$TestMethod"
        Add-Content -Path $OutputFile -Value "Status: Failed"
        Add-Content -Path $OutputFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
        Add-Content -Path $OutputFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }
}

# Example usage:
# .\run_single_test_method.ps1 -TestFile "src/tests/ui/test_comprehensive_ui.py" -TestClass "TestComprehensiveUI" -TestMethod "test_main_window_ai_menu_complete" -VerboseOutput
