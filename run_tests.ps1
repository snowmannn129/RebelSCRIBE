#!/usr/bin/env pwsh
# RebelSCRIBE Test Runner Script

# Parse command line arguments
param(
    [string]$TestPath = "src\tests",
    [switch]$Coverage = $false,
    [switch]$Verbose = $false
)

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Set up command
$command = "pytest $TestPath"

# Add options
if ($Coverage) {
    $command += " --cov=src --cov-report=term --cov-report=html"
}

if ($Verbose) {
    $command += " -v"
}

# Run tests
Write-Host "Running tests: $command" -ForegroundColor Green
Invoke-Expression $command

# Deactivate virtual environment
if (Test-Path function:deactivate) {
    deactivate
}
