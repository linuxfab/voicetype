@echo off
chcp 65001 >nul 2>&1
title VoiceType - Install and Launch

echo.
echo  ==========================================
echo    VoiceType v0.1.0 (uv env)
echo  ==========================================
echo.

:: Check uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] uv not found. Please install uv first.
    echo          https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo  [INFO] uv found:
uv --version

:: Install dependencies
echo.
echo  [INFO] Installing dependencies using uv...
uv venv -q
uv pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo  [DEBUG] Some packages failed to install, checking error...
    pause
    exit /b 1
)

echo.
echo  [OK] Installation complete!
echo.
echo  ------------------------------------------
echo  First time setup:
echo    1. Right-click tray icon - Open Settings
echo    2. Or edit: %APPDATA%\voicetype\config.json
echo  ------------------------------------------
echo.

:: Launch
echo  [INFO] Starting VoiceType...
echo.
uv run main.py

pause
