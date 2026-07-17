@echo off
setlocal
cd /d "%~dp0"

set "APP_NAME=Bible_Reference_Study_Tool"
set "PYTHON_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py"

if "%PYTHON_CMD%"=="" (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if "%PYTHON_CMD%"=="" (
  echo Python was not found.
  pause
  exit /b 1
)

echo ============================================
echo Bible Reference Study Tool - Release Build
echo ============================================
echo.

echo Installing/checking build dependencies from requirements-dev.txt...
%PYTHON_CMD% -m pip install -r requirements-dev.txt
if errorlevel 1 goto failed

echo Checking Python files...
%PYTHON_CMD% -m compileall -q bible_app bible_reference_app.py setup.py
if errorlevel 1 goto failed

echo Running module tests...
%PYTHON_CMD% -m unittest tests.test_bible_app_modules
if errorlevel 1 goto failed

echo Removing previous release output...
if exist build rmdir /s /q build
if exist "dist\%APP_NAME%.exe" del /q "dist\%APP_NAME%.exe"
if exist "dist\%APP_NAME%.zip" del /q "dist\%APP_NAME%.zip"

echo Building one-file Windows executable...
%PYTHON_CMD% -m PyInstaller --clean --noconfirm "%APP_NAME%.spec"
if errorlevel 1 goto failed

if not exist "dist\%APP_NAME%.exe" goto missing_exe

echo Creating zip package...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'dist\%APP_NAME%.exe','README.md','USER_GUIDE.md','REFERENCE_GUIDE.md','DEVELOPERS_GUIDE.md','PACKAGING.md' -DestinationPath 'dist\%APP_NAME%.zip' -Force"
if errorlevel 1 goto failed

echo.
echo Build complete:
echo %~dp0dist\%APP_NAME%.exe
echo %~dp0dist\%APP_NAME%.zip
echo.
pause
exit /b 0

:missing_exe
echo.
echo Build finished, but the executable was not found.
goto failed

:failed
echo.
echo Build failed. Check the messages above.
pause
exit /b 1
