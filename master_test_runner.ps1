#!/usr/bin/env pwsh
# RebelSCRIBE Master Test Runner
# This script provides a unified interface to all testing tools

# Parse command line arguments
param(
    [Parameter(Position=0)]
    [ValidateSet("progressive", "single", "coverage", "parallel", "ui", "adapter", "advanced-ai", "help")]
    [string]$TestMode = "progressive",
    
    [string]$TestPath = "",
    [string]$TestClass = "",
    [string]$TestMethod = "",
    [int]$MinCoverage = 80,
    [int]$NumProcesses = 4,
    [switch]$Html,
    [switch]$Xml,
    [switch]$FailFast,
    [switch]$FailUnderMin,
    [switch]$VerboseOutput,
    [string]$OutputFile = ""
)

# Function to display help
function Show-Help {
    Write-Host "RebelSCRIBE Master Test Runner" -ForegroundColor Cyan
    Write-Host "Usage: .\master_test_runner.ps1 [mode] [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Modes:" -ForegroundColor Yellow
    Write-Host "  progressive   Run tests progressively (default)" -ForegroundColor Green
    Write-Host "  single        Run a single test method" -ForegroundColor Green
    Write-Host "  coverage      Run tests with coverage reporting" -ForegroundColor Green
    Write-Host "  parallel      Run tests in parallel" -ForegroundColor Green
    Write-Host "  ui            Run UI tests" -ForegroundColor Green
    Write-Host "  adapter       Run adapter tests" -ForegroundColor Green
    Write-Host "  advanced-ai   Run advanced AI tests" -ForegroundColor Green
    Write-Host "  help          Show this help message" -ForegroundColor Green
    Write-Host ""
    Write-Host "Common Options:" -ForegroundColor Yellow
    Write-Host "  -VerboseOutput  Increase verbosity" -ForegroundColor Green
    Write-Host "  -FailFast       Stop on first failure" -ForegroundColor Green
    Write-Host "  -OutputFile     File to write test output to" -ForegroundColor Green
    Write-Host ""
    Write-Host "Mode-Specific Options:" -ForegroundColor Yellow
    Write-Host "  progressive:" -ForegroundColor Cyan
    Write-Host "    -SkipUnitTests            Skip unit tests" -ForegroundColor Green
    Write-Host "    -SkipIntegrationTests     Skip integration tests" -ForegroundColor Green
    Write-Host "    -SkipFunctionalTests      Skip functional tests" -ForegroundColor Green
    Write-Host "    -SkipUITests              Skip UI tests" -ForegroundColor Green
    Write-Host "    -SkipComprehensiveTests   Skip comprehensive tests" -ForegroundColor Green
    Write-Host "    -SkipAdapterTests         Skip adapter tests" -ForegroundColor Green
    Write-Host "    -SkipAdvancedAITests      Skip advanced AI tests" -ForegroundColor Green
    Write-Host ""
    Write-Host "  single:" -ForegroundColor Cyan
    Write-Host "    -TestPath     Test file to run (required)" -ForegroundColor Green
    Write-Host "    -TestClass    Test class to run (required)" -ForegroundColor Green
    Write-Host "    -TestMethod   Test method to run (required)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  coverage:" -ForegroundColor Cyan
    Write-Host "    -TestPath      Path to test directory" -ForegroundColor Green
    Write-Host "    -MinCoverage   Minimum coverage percentage" -ForegroundColor Green
    Write-Host "    -Html          Generate HTML report" -ForegroundColor Green
    Write-Host "    -Xml           Generate XML report" -ForegroundColor Green
    Write-Host "    -FailUnderMin  Fail if coverage is below minimum" -ForegroundColor Green
    Write-Host ""
    Write-Host "  parallel:" -ForegroundColor Cyan
    Write-Host "    -TestPath      Path to test directory" -ForegroundColor Green
    Write-Host "    -NumProcesses  Number of processes to use" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ui:" -ForegroundColor Cyan
    Write-Host "    -Comprehensive  Run comprehensive UI tests" -ForegroundColor Green
    Write-Host ""
    Write-Host "  adapter:" -ForegroundColor Cyan
    Write-Host "    -TestClass     Test class to run" -ForegroundColor Green
    Write-Host "    -TestMethod    Test method to run" -ForegroundColor Green
    Write-Host "    -Repeat        Number of times to repeat tests" -ForegroundColor Green
    Write-Host ""
    Write-Host "  advanced-ai:" -ForegroundColor Cyan
    Write-Host "    -TestClass     Test class to run" -ForegroundColor Green
    Write-Host "    -TestMethod    Test method to run" -ForegroundColor Green
    Write-Host "    -ModelType     Model type to test" -ForegroundColor Green
    Write-Host "    -Repeat        Number of times to repeat tests" -ForegroundColor Green
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\master_test_runner.ps1 progressive -FailFast" -ForegroundColor Green
    Write-Host "  .\master_test_runner.ps1 single -TestPath 'src/tests/ui/test_comprehensive_ui.py' -TestClass 'TestComprehensiveUI' -TestMethod 'test_main_window_ai_menu_complete'" -ForegroundColor Green
    Write-Host "  .\master_test_runner.ps1 coverage -TestPath 'src/tests/ui' -Html -MinCoverage 90 -FailUnderMin" -ForegroundColor Green
    Write-Host "  .\master_test_runner.ps1 parallel -NumProcesses 8 -FailFast" -ForegroundColor Green
    Write-Host "  .\master_test_runner.ps1 ui -Comprehensive" -ForegroundColor Green
    Write-Host "  .\master_test_runner.ps1 adapter -TestClass 'TestAdapterManager'" -ForegroundColor Green
    Write-Host "  .\master_test_runner.ps1 advanced-ai -ModelType 'llama'" -ForegroundColor Green
}

# Check if help is requested
if ($TestMode -eq "help" -or $args -contains "-h" -or $args -contains "--help") {
    Show-Help
    exit 0
}

# Function to build command arguments
function Build-CommandArgs {
    param (
        [hashtable]$Params
    )
    
    $args = @()
    
    foreach ($key in $Params.Keys) {
        $value = $Params[$key]
        
        if ($value -is [bool] -and $value) {
            $args += "-$key"
        } elseif ($value -isnot [bool] -and $value -ne $null -and $value -ne "") {
            $args += "-$key"
            $args += "$value"
        }
    }
    
    return $args -join " "
}

# Set verbosity flag
$verbosityFlag = if ($VerboseOutput) { "-v" } else { "" }

# Execute the appropriate test script based on the mode
switch ($TestMode) {
    "progressive" {
        $scriptPath = ".\progressive_test_strategy.ps1"
        
        $params = @{
            "SkipUnitTests" = $args -contains "-SkipUnitTests"
            "SkipIntegrationTests" = $args -contains "-SkipIntegrationTests"
            "SkipFunctionalTests" = $args -contains "-SkipFunctionalTests"
            "SkipUITests" = $args -contains "-SkipUITests"
            "SkipComprehensiveTests" = $args -contains "-SkipComprehensiveTests"
            "SkipAdapterTests" = $args -contains "-SkipAdapterTests"
            "SkipAdvancedAITests" = $args -contains "-SkipAdvancedAITests"
            "FailFast" = $FailFast
            "Verbose" = $VerboseOutput
        }
        
        $commandArgs = Build-CommandArgs -Params $params
        $command = "$scriptPath $commandArgs"
    }
    
    "single" {
        $scriptPath = ".\run_single_test_method.ps1"
        
        if (-not $TestPath) {
            Write-Error "TestPath parameter is required for single mode"
            exit 1
        }
        
        if (-not $TestClass) {
            Write-Error "TestClass parameter is required for single mode"
            exit 1
        }
        
        if (-not $TestMethod) {
            Write-Error "TestMethod parameter is required for single mode"
            exit 1
        }
        
        $params = @{
            "TestFile" = $TestPath
            "TestClass" = $TestClass
            "TestMethod" = $TestMethod
            "Verbose" = $VerboseOutput
            "OutputFile" = $OutputFile
        }
        
        $commandArgs = Build-CommandArgs -Params $params
        $command = "$scriptPath $commandArgs"
    }
    
    "coverage" {
        $scriptPath = ".\run_tests_with_coverage.ps1"
        
        $params = @{
            "TestPath" = $TestPath
            "MinCoverage" = $MinCoverage
            "Html" = $Html
            "Xml" = $Xml
            "FailUnderMin" = $FailUnderMin
            "Verbose" = $VerboseOutput
        }
        
        $commandArgs = Build-CommandArgs -Params $params
        $command = "$scriptPath $commandArgs"
    }
    
    "parallel" {
        $scriptPath = ".\run_tests_parallel.ps1"
        
        $params = @{
            "TestPath" = $TestPath
            "NumProcesses" = $NumProcesses
            "FailFast" = $FailFast
            "Verbose" = $VerboseOutput
            "OutputFile" = $OutputFile
        }
        
        $commandArgs = Build-CommandArgs -Params $params
        $command = "$scriptPath $commandArgs"
    }
    
    "ui" {
        if ($args -contains "-Comprehensive") {
            $scriptPath = ".\run_comprehensive_ui_tests.ps1"
            $command = $scriptPath
        } else {
            $scriptPath = ".\run_all_ui_tests.ps1"
            $command = $scriptPath
        }
    }
    
    "adapter" {
        $scriptPath = ".\run_adapter_tests.ps1"
        
        $params = @{
            "TestClass" = $TestClass
            "TestMethod" = $TestMethod
            "Verbose" = $VerboseOutput
            "Output" = $OutputFile
            "FailFast" = $FailFast
        }
        
        # Add repeat parameter if specified
        if ($args -contains "-Repeat") {
            $repeatIndex = $args.IndexOf("-Repeat")
            if ($repeatIndex -lt $args.Length - 1) {
                $params["Repeat"] = $args[$repeatIndex + 1]
            }
        }
        
        $commandArgs = Build-CommandArgs -Params $params
        $command = "$scriptPath $commandArgs"
    }
    
    "advanced-ai" {
        $scriptPath = ".\run_advanced_ai_tests.ps1"
        
        $params = @{
            "TestClass" = $TestClass
            "TestMethod" = $TestMethod
            "Verbose" = $VerboseOutput
            "Output" = $OutputFile
            "FailFast" = $FailFast
        }
        
        # Add model type parameter if specified
        if ($args -contains "-ModelType") {
            $modelTypeIndex = $args.IndexOf("-ModelType")
            if ($modelTypeIndex -lt $args.Length - 1) {
                $params["ModelType"] = $args[$modelTypeIndex + 1]
            }
        }
        
        # Add repeat parameter if specified
        if ($args -contains "-Repeat") {
            $repeatIndex = $args.IndexOf("-Repeat")
            if ($repeatIndex -lt $args.Length - 1) {
                $params["Repeat"] = $args[$repeatIndex + 1]
            }
        }
        
        $commandArgs = Build-CommandArgs -Params $params
        $command = "$scriptPath $commandArgs"
    }
}

# Execute the command
Write-Host "Executing: $command" -ForegroundColor Cyan
Invoke-Expression $command
