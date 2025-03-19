# RebelSCRIBE Adapter Tests Runner
# This script runs the adapter tests with the specified options

param(
    [string]$TestClass = "",        # Run only tests from the specified class
    [string]$TestMethod = "",       # Run only the specified test method
    [int]$Verbose = 2,              # Verbosity level (0=quiet, 1=normal, 2=verbose)
    [string]$Output = "",           # File to write test output to
    [int]$Repeat = 1,               # Number of times to repeat the tests
    [switch]$FailFast = $false      # Stop on first failure
)

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Build the command
$command = "python src/run_adapter_tests.py"

# Add options
if ($TestClass) {
    $command += " --test-class $TestClass"
}

if ($TestMethod) {
    $command += " --test-method $TestMethod"
}

$command += " --verbose $Verbose"

if ($Output) {
    $command += " --output `"$Output`""
}

if ($Repeat -gt 1) {
    $command += " --repeat $Repeat"
}

if ($FailFast) {
    $command += " --fail-fast"
}

# Display the command
Write-Host "Running command: $command" -ForegroundColor Cyan

# Run the command
Invoke-Expression $command

# Get the exit code
$exitCode = $LASTEXITCODE

# Deactivate virtual environment if it was activated
if (Test-Path function:deactivate) {
    deactivate
}

# Return the exit code
exit $exitCode
