@echo off
echo ============================================================
echo CRYPTOCURRENCY PREDICTION SYSTEM - STARTUP
echo ============================================================
echo.
echo Starting API Server...
echo.

cd /d "%~dp0"

start "Prediction API Server" cmd /k "python prediction_api.py"

timeout /t 3 /nobreak > nul

echo.
echo Starting Web Server...
echo.

start "Web Server" cmd /k "python -m http.server 8000"

timeout /t 2 /nobreak > nul

echo.
echo ============================================================
echo SERVERS STARTED SUCCESSFULLY!
echo ============================================================
echo.
echo API Server: http://localhost:5000
echo Web App: http://localhost:8000
echo.
echo Opening web browser...
echo.

start http://localhost:8000

echo.
echo Press any key to stop all servers...
pause > nul

taskkill /FI "WINDOWTITLE eq Prediction API Server*" /F
taskkill /FI "WINDOWTITLE eq Web Server*" /F

echo.
echo Servers stopped.
echo.
