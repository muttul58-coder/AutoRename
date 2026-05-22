@echo off
title File Renamer - Build EXE
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 goto :no_python

if not exist ".venv\Scripts\python.exe" (
    echo [Setup] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 goto :fail
)

echo [Setup] Installing dependencies including PyInstaller...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo.
echo [Build] Running PyInstaller. This may take several minutes...
".venv\Scripts\python.exe" -m PyInstaller --name "FileRenamer" --onefile --windowed --add-data "index.html;." --clean --noconfirm main.py
if errorlevel 1 goto :fail

echo.
echo -----------------------------------------------
echo  Build complete: dist\FileRenamer.exe
echo  Copy this .exe to any PC. Python is not required on the target PC.
echo -----------------------------------------------
pause
exit /b 0

:no_python
echo [Error] Python is not installed or not in PATH.
echo Install Python 3.9+ from https://www.python.org/downloads/
pause
exit /b 1

:fail
echo [Error] Build failed.
pause
exit /b 1
