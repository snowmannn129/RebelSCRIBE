Write-Host "Running Enhanced Error Handler Tests..." -ForegroundColor Cyan
python -m unittest src.tests.ui.test_error_handler_integration
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
