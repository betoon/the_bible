@echo off
REM Bible Reference App Launcher with Error Display
REM This batch file keeps the command window open so you can see errors

echo ============================================
echo Bible Reference Study Tool - Starting...
echo ============================================
echo.

REM Change to the directory where the script is located
cd /d "%~dp0"

REM Run the Python script
python bible_reference_app.py

REM Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo ERROR: The application crashed!
    echo Error Code: %errorlevel%
    echo ============================================
    echo.
    pause
) else (
    echo Application closed normally.
)
