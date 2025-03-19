#!/usr/bin/env pwsh
# RebelSCRIBE Run Script

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Run the application
python src\main.py

# Deactivate virtual environment
if (Test-Path function:deactivate) {
    deactivate
}
