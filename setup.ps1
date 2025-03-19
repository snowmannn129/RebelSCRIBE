#!/usr/bin/env pwsh
# RebelSCRIBE Setup Script

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

# Create necessary directories
Write-Host "Creating necessary directories..." -ForegroundColor Green
$directories = @(
    "documents",
    "exports",
    "resources",
    "backups",
    "templates"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Yellow
    }
}

# Create user config directory
$userConfigDir = "$env:USERPROFILE\.rebelscribe"
if (-not (Test-Path $userConfigDir)) {
    New-Item -ItemType Directory -Path $userConfigDir -Force | Out-Null
    Write-Host "Created user config directory: $userConfigDir" -ForegroundColor Yellow
}

# Create user backups directory
$userBackupsDir = "$env:USERPROFILE\.rebelscribe\backups"
if (-not (Test-Path $userBackupsDir)) {
    New-Item -ItemType Directory -Path $userBackupsDir -Force | Out-Null
    Write-Host "Created user backups directory: $userBackupsDir" -ForegroundColor Yellow
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "You can now run the application using .\run.ps1" -ForegroundColor Cyan
