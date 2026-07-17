@echo off
setlocal
cd /d "%~dp0"

where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "%~dp0bible_reference_app.py"
  exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
  start "" python "%~dp0bible_reference_app.py"
  exit /b 0
)

echo Python was not found.
pause
exit /b 1
