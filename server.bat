@echo off
chcp 65001 >nul
title File Renamer - Launcher
setlocal

set PORT=8080
set PAGE=index.html

REM ---- Python 확인 ----
where python >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 없습니다.
    echo https://www.python.org/downloads/ 에서 설치 후 다시 실행하세요.
    pause
    exit /b 1
)

REM ---- 기존 서버 종료 ----
echo 포트 %PORT% 사용 중인 기존 서버를 종료합니다...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM ---- 서버 시작 ----
echo Python HTTP 서버를 시작합니다 (포트 %PORT%)...
start /min "FileRenamer-Server" cmd /c "python -m http.server %PORT%"

echo 서버 대기 중...
timeout /t 2 /nobreak >nul

echo 브라우저를 엽니다...
start "" "http://localhost:%PORT%/%PAGE%"

echo.
echo ───────────────────────────────────────────────
echo  서버 실행 중: http://localhost:%PORT%/%PAGE%
echo  종료하려면 "FileRenamer-Server" 창을 닫으세요.
echo ───────────────────────────────────────────────
timeout /t 3 /nobreak >nul
exit /b 0
