#!/usr/bin/env pwsh
# RebelSCRIBE GPU Acceleration Test Script

# Parse command line arguments
param(
    [string]$Model = "gpt2",
    [string]$Prompt = "Once upon a time in a land far away,",
    [int]$MaxLength = 50,
    [switch]$InfoOnly = $false
)

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Build the command
$command = "python src/run_gpu_test.py"

# Add options
if ($Model) {
    $command += " --model `"$Model`""
}

if ($Prompt) {
    $command += " --prompt `"$Prompt`""
}

if ($MaxLength -gt 0) {
    $command += " --max-length $MaxLength"
}

if ($InfoOnly) {
    $command += " --info-only"
}

# Run the GPU test
Write-Host "Running GPU acceleration test: $command" -ForegroundColor Green
Invoke-Expression $command

# Deactivate virtual environment
if (Test-Path function:deactivate) {
    deactivate
}
