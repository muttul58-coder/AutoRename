@echo off
title File Renamer - Local
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 goto :no_python

if not exist ".venv\Scripts\python.exe" goto :setup
goto :run

:setup
echo [Setup] Creating virtual environment...
python -m venv .venv
if errorlevel 1 goto :setup_fail

echo [Setup] Installing dependencies. This runs only once.
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :setup_fail
goto :run

:run
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:no_python
echo [Error] Python is not installed or not in PATH.
echo Install Python 3.9+ from https://www.python.org/downloads/
pause
exit /b 1

:setup_fail
echo [Error] Setup failed. Please check your Python installation and network connection.
pause
exit /b 1
