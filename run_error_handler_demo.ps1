Write-Host "Running Enhanced Error Handler Demo..." -ForegroundColor Cyan
python -m src.tests.ui.test_enhanced_error_handler_demo
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
