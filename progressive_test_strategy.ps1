#!/usr/bin/env pwsh
# RebelSCRIBE Progressive Testing Strategy
# This script implements a progressive testing approach, starting with small unit tests
# and gradually building up to comprehensive system tests.

# Set the Python executable path
$pythonExe = "python"

# Create output directory for test results if it doesn't exist
$outputDir = "test_results"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
    Write-Host "Created output directory: $outputDir" -ForegroundColor Green
}

# Get current timestamp for the output files
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Function to run tests and log results
function Run-TestPhase {
    param (
        [string]$PhaseName,
        [string]$Command,
        [string]$OutputFile
    )
    
    Write-Host "`n========== PHASE: $PhaseName ==========" -ForegroundColor Cyan
    Write-Host "Running command: $Command" -ForegroundColor Yellow
    Write-Host "Test output will be saved to: $OutputFile" -ForegroundColor Yellow
    
    # Start the timer
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    # Run the tests and capture output
    Invoke-Expression "$Command | Tee-Object -FilePath $OutputFile"
    
    # Stop the timer
    $stopwatch.Stop()
    $elapsedTime = $stopwatch.Elapsed
    
    # Check the exit code
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Phase '$PhaseName' completed successfully!" -ForegroundColor Green
        Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Green
        
        # Add summary to the output file
        Add-Content -Path $OutputFile -Value "`n`n===== TEST SUMMARY ====="
        Add-Content -Path $OutputFile -Value "Phase: $PhaseName"
        Add-Content -Path $OutputFile -Value "Status: All tests passed"
        Add-Content -Path $OutputFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
        Add-Content -Path $OutputFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        
        return $true
    } else {
        Write-Host "Phase '$PhaseName' failed. Please check the output above for details." -ForegroundColor Red
        Write-Host "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Red
        
        # Add summary to the output file
        Add-Content -Path $OutputFile -Value "`n`n===== TEST SUMMARY ====="
        Add-Content -Path $OutputFile -Value "Phase: $PhaseName"
        Add-Content -Path $OutputFile -Value "Status: Some tests failed"
        Add-Content -Path $OutputFile -Value "Total time: $($elapsedTime.ToString('hh\:mm\:ss'))"
        Add-Content -Path $OutputFile -Value "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        
        return $false
    }
}

# Parse command line arguments
param(
    [switch]$SkipUnitTests,
    [switch]$SkipIntegrationTests,
    [switch]$SkipFunctionalTests,
    [switch]$SkipUITests,
    [switch]$SkipComprehensiveTests,
    [switch]$SkipAdapterTests,
    [switch]$SkipAdvancedAITests,
    [switch]$FailFast,
    [switch]$Verbose
)

# Set verbosity flag
$verbosityFlag = if ($Verbose) { "-v" } else { "" }

# Phase 1: Unit Tests (Backend)
if (-not $SkipUnitTests) {
    $phase1Output = "$outputDir/phase1_unit_tests_$timestamp.txt"
    $phase1Command = "$pythonExe -m unittest discover -s src/tests/unit -p 'test_*.py' $verbosityFlag"
    $phase1Success = Run-TestPhase -PhaseName "Unit Tests (Backend)" -Command $phase1Command -OutputFile $phase1Output
    
    if (-not $phase1Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 1." -ForegroundColor Red
        exit 1
    }
}

# Phase 2: Unit Tests (AI)
if (-not $SkipUnitTests) {
    $phase2Output = "$outputDir/phase2_ai_unit_tests_$timestamp.txt"
    $phase2Command = "$pythonExe -m unittest discover -s src/tests/ai -p 'test_*.py' $verbosityFlag"
    $phase2Success = Run-TestPhase -PhaseName "Unit Tests (AI)" -Command $phase2Command -OutputFile $phase2Output
    
    if (-not $phase2Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 2." -ForegroundColor Red
        exit 1
    }
}

# Phase 3: Unit Tests (Utils)
if (-not $SkipUnitTests) {
    $phase3Output = "$outputDir/phase3_utils_unit_tests_$timestamp.txt"
    $phase3Command = "$pythonExe -m unittest discover -s src/tests/utils -p 'test_*.py' $verbosityFlag"
    $phase3Success = Run-TestPhase -PhaseName "Unit Tests (Utils)" -Command $phase3Command -OutputFile $phase3Output
    
    if (-not $phase3Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 3." -ForegroundColor Red
        exit 1
    }
}

# Phase 4: Integration Tests
if (-not $SkipIntegrationTests) {
    $phase4Output = "$outputDir/phase4_integration_tests_$timestamp.txt"
    $phase4Command = "$pythonExe -m unittest discover -s src/tests/integration -p 'test_*.py' $verbosityFlag"
    $phase4Success = Run-TestPhase -PhaseName "Integration Tests" -Command $phase4Command -OutputFile $phase4Output
    
    if (-not $phase4Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 4." -ForegroundColor Red
        exit 1
    }
}

# Phase 5: Functional Tests
if (-not $SkipFunctionalTests) {
    $phase5Output = "$outputDir/phase5_functional_tests_$timestamp.txt"
    $phase5Command = "$pythonExe -m unittest discover -s src/tests/functional -p 'test_*.py' $verbosityFlag"
    $phase5Success = Run-TestPhase -PhaseName "Functional Tests" -Command $phase5Command -OutputFile $phase5Output
    
    if (-not $phase5Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 5." -ForegroundColor Red
        exit 1
    }
}

# Phase 6: UI Component Tests
if (-not $SkipUITests) {
    $phase6Output = "$outputDir/phase6_ui_component_tests_$timestamp.txt"
    $phase6Command = "$pythonExe -m unittest discover -s src/tests/ui -p 'test_*_dialog.py' $verbosityFlag"
    $phase6Success = Run-TestPhase -PhaseName "UI Component Tests" -Command $phase6Command -OutputFile $phase6Output
    
    if (-not $phase6Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 6." -ForegroundColor Red
        exit 1
    }
}

# Phase 7: UI Integration Tests
if (-not $SkipUITests) {
    $phase7Output = "$outputDir/phase7_ui_integration_tests_$timestamp.txt"
    $phase7Command = "$pythonExe -m unittest discover -s src/tests/ui -p 'test_*_integration.py' $verbosityFlag"
    $phase7Success = Run-TestPhase -PhaseName "UI Integration Tests" -Command $phase7Command -OutputFile $phase7Output
    
    if (-not $phase7Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 7." -ForegroundColor Red
        exit 1
    }
}

# Phase 8: Adapter Tests
if (-not $SkipAdapterTests) {
    $phase8Output = "$outputDir/phase8_adapter_tests_$timestamp.txt"
    $phase8Command = "$pythonExe src/run_adapter_tests.py --output $phase8Output $verbosityFlag"
    $phase8Success = Run-TestPhase -PhaseName "Adapter Tests" -Command $phase8Command -OutputFile $phase8Output
    
    if (-not $phase8Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 8." -ForegroundColor Red
        exit 1
    }
}

# Phase 9: Advanced AI Tests
if (-not $SkipAdvancedAITests) {
    $phase9Output = "$outputDir/phase9_advanced_ai_tests_$timestamp.txt"
    $phase9Command = "$pythonExe src/run_advanced_ai_tests.py --output $phase9Output $verbosityFlag"
    $phase9Success = Run-TestPhase -PhaseName "Advanced AI Tests" -Command $phase9Command -OutputFile $phase9Output
    
    if (-not $phase9Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 9." -ForegroundColor Red
        exit 1
    }
}

# Phase 10: Comprehensive UI Tests
if (-not $SkipComprehensiveTests) {
    $phase10Output = "$outputDir/phase10_comprehensive_ui_tests_$timestamp.txt"
    $phase10Command = "$pythonExe -m unittest src/tests/ui/test_comprehensive_ui.py $verbosityFlag | Tee-Object -FilePath $phase10Output"
    $phase10Success = Run-TestPhase -PhaseName "Comprehensive UI Tests" -Command $phase10Command -OutputFile $phase10Output
    
    if (-not $phase10Success -and $FailFast) {
        Write-Host "Stopping due to test failures in Phase 10." -ForegroundColor Red
        exit 1
    }
}

# Final summary
Write-Host "`n========== TESTING COMPLETE ==========" -ForegroundColor Cyan
Write-Host "All test results have been saved to the $outputDir directory." -ForegroundColor Green
Write-Host "Review the individual test files for detailed results." -ForegroundColor Green
