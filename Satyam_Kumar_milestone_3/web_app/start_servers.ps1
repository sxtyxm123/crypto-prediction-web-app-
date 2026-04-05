# PowerShell script to start both servers
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "CRYPTOCURRENCY PREDICTION SYSTEM - STARTUP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start API Server
Write-Host "Starting Prediction API Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python prediction_api.py"

Start-Sleep -Seconds 3

# Start Web Server
Write-Host "Starting Web Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python -m http.server 8000"

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "SERVERS STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "API Server: http://localhost:5000" -ForegroundColor White
Write-Host "Web App: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "Opening web browser..." -ForegroundColor Yellow
Write-Host ""

Start-Sleep -Seconds 1
Start-Process "http://localhost:8000"

Write-Host ""
Write-Host "Both servers are running in separate windows." -ForegroundColor Green
Write-Host "Close those windows to stop the servers." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
