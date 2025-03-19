#!/usr/bin/env pwsh
# RebelSCRIBE Build and Run Script

# Run setup script
Write-Host "Running setup script..." -ForegroundColor Green
& ".\setup.ps1"

# Run the application
Write-Host "Starting RebelSCRIBE..." -ForegroundColor Green
& ".\run.ps1"
