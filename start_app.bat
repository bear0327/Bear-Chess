@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

set "NEED_INSTALL=0"
if /I "%~1"=="--install" set "NEED_INSTALL=1"

if "%NEED_INSTALL%"=="0" (
    %PY% -c "import pygame, chess, requests, websockets" >nul 2>&1
    if errorlevel 1 set "NEED_INSTALL=1"
)

if "%NEED_INSTALL%"=="1" (
    echo [Bear-Chess] Installing/updating dependencies...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [Bear-Chess] Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo [Bear-Chess] Starting app...
%PY% main.py
if errorlevel 1 (
    echo [Bear-Chess] App exited with error.
    pause
    exit /b 1
)

endlocal