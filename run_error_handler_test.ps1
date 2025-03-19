Write-Host "Running Enhanced Error Handler Test..." -ForegroundColor Cyan
python test_error_handler.py
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
