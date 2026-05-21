@echo off
chcp 65001 >nul
title File Renamer - Launcher

echo Stopping existing server on port 8080...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo Starting Python HTTP server...
start /min "FileRenamer-Server" cmd /c "python -m http.server 8080"

echo Waiting for server...
timeout /t 2 /nobreak >nul

echo Opening browser...
start "" "http://localhost:8080/index.html"

REM Close this launcher window. Server keeps running in the minimized "FileRenamer-Server" window.
exit
