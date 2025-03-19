#!/usr/bin/env pwsh
# RebelSCRIBE Enhanced Test Runner Script

# Parse command line arguments
param(
    [string]$TestType = "all",  # Options: unit, integration, functional, e2e, performance, all
    [string]$TestPath = "",     # Specific test path to run
    [switch]$Coverage = $false, # Generate coverage report
    [switch]$Verbose = $false,  # Verbose output
    [switch]$Parallel = $false, # Run tests in parallel
    [switch]$FailFast = $false, # Stop on first failure
    [int]$RepeatCount = 1,      # Repeat tests multiple times
    [int]$CoverageThreshold = 80, # Minimum coverage percentage
    [switch]$NoOutput = $false, # Suppress output
    [string]$OutputFile = "",   # Output file for test results
    [switch]$Quiet = $false     # Minimal output
)

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Ensure required packages are installed
$requiredPackages = @(
    "pytest",
    "pytest-cov",
    "pytest-qt",
    "pytest-xvs",
    "pytest-repeat"
)

foreach ($package in $requiredPackages) {
    $installed = pip list | Select-String -Pattern "^$package\s"
    if (-not $installed) {
        Write-Host "Installing required package: $package" -ForegroundColor Yellow
        pip install $package
    }
}

# Set up base command
$command = "pytest"

# Add test type filter
if ($TestPath -ne "") {
    $command += " $TestPath"
}
elseif ($TestType -ne "all") {
    $testDir = "src\tests\$TestType"
    if (Test-Path $testDir) {
        $command += " $testDir"
    }
    else {
        Write-Host "Test type directory not found: $testDir" -ForegroundColor Red
        Write-Host "Available test types: unit, integration, functional, e2e, performance" -ForegroundColor Yellow
        exit 1
    }
}
else {
    $command += " src\tests"
}

# Add options
if ($Coverage) {
    $command += " --cov=src --cov-report=term --cov-report=html:coverage_report --cov-fail-under=$CoverageThreshold"
}

if ($Verbose) {
    $command += " -v"
}

if ($Parallel) {
    $command += " -xvs"
}

if ($FailFast) {
    $command += " -x"
}

if ($RepeatCount -gt 1) {
    $command += " --count=$RepeatCount"
}

if ($NoOutput) {
    $command += " -q"
}

if ($OutputFile -ne "") {
    $command += " --junitxml=$OutputFile"
}

if ($Quiet) {
    $command += " -q"
}

# Display test configuration
if (-not $Quiet) {
    Write-Host "RebelSCRIBE Test Runner" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    Write-Host "Test Type: $TestType" -ForegroundColor Cyan
    if ($TestPath -ne "") {
        Write-Host "Test Path: $TestPath" -ForegroundColor Cyan
    }
    Write-Host "Coverage: $Coverage" -ForegroundColor Cyan
    if ($Coverage) {
        Write-Host "Coverage Threshold: $CoverageThreshold%" -ForegroundColor Cyan
    }
    Write-Host "Verbose: $Verbose" -ForegroundColor Cyan
    Write-Host "Parallel: $Parallel" -ForegroundColor Cyan
    Write-Host "Fail Fast: $FailFast" -ForegroundColor Cyan
    if ($RepeatCount -gt 1) {
        Write-Host "Repeat Count: $RepeatCount" -ForegroundColor Cyan
    }
    Write-Host "Command: $command" -ForegroundColor Green
    Write-Host "======================" -ForegroundColor Cyan
}

# Run tests
$startTime = Get-Date
if (-not $Quiet) {
    Write-Host "Starting tests at $startTime" -ForegroundColor Green
}

try {
    Invoke-Expression $command
    $exitCode = $LASTEXITCODE
}
catch {
    Write-Host "Error running tests: $_" -ForegroundColor Red
    $exitCode = 1
}

$endTime = Get-Date
$duration = $endTime - $startTime

if (-not $Quiet) {
    Write-Host "Tests completed at $endTime" -ForegroundColor Green
    Write-Host "Duration: $($duration.TotalSeconds) seconds" -ForegroundColor Green
    
    if ($exitCode -eq 0) {
        Write-Host "All tests passed!" -ForegroundColor Green
    }
    else {
        Write-Host "Tests failed with exit code $exitCode" -ForegroundColor Red
    }
    
    if ($Coverage) {
        Write-Host "Coverage report generated in coverage_report directory" -ForegroundColor Green
        Write-Host "Open coverage_report\index.html to view detailed coverage information" -ForegroundColor Green
    }
}

# Deactivate virtual environment
if (Test-Path function:deactivate) {
    deactivate
}

exit $exitCode
