# PowerShell script to run advanced AI tests
# Usage: .\run_advanced_ai_tests.ps1 [options]

param(
    [switch]$pytest = $false,
    [switch]$coverage = $false,
    [switch]$verbose = $false,
    [string]$testFile = "",
    [string]$testClass = "",
    [string]$testMethod = "",
    [ValidateSet("local", "llama", "mistral", "phi", "falcon", "mpt", "adapter", "progress", "gguf", "registry", "benchmark", "visualization", "all")]
    [string]$model = "all",
    [ValidateSet("term", "html", "xml", "all")]
    [string]$covReport = "term",
    [switch]$failFast = $false,
    [int]$repeat = 1,
    [string]$output = ""
)

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Build command
$command = "python src/run_advanced_ai_tests.py"

# Add pytest flag if specified
if ($pytest) {
    $command += " --pytest"
}

# Add coverage if specified
if ($coverage) {
    $command += " --cov --cov-report=$covReport"
}

# Add verbose flag if specified
if ($verbose) {
    $command += " -v"
}

# Add test file if specified
if ($testFile -ne "") {
    $command += " --test-file=$testFile"
}

# Add test class if specified
if ($testClass -ne "") {
    $command += " --test-class=$testClass"
}

# Add test method if specified
if ($testMethod -ne "") {
    $command += " --test-method=$testMethod"
}

# Add model if specified
if ($model -ne "all") {
    $command += " --model=$model"
}

# Add fail-fast if specified
if ($failFast) {
    $command += " --fail-fast"
}

# Add repeat if specified
if ($repeat -gt 1) {
    $command += " --repeat=$repeat"
}

# Add output if specified
if ($output -ne "") {
    $command += " --output=$output"
}

# Display the command
Write-Host "Running: $command" -ForegroundColor Green

# Execute the command
Invoke-Expression $command

# Deactivate virtual environment if it was activated
if (Test-Path function:deactivate) {
    deactivate
}
