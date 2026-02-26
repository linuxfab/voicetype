@echo off
chcp 65001 >nul
title VoiceType - 打包成 EXE

echo.
echo  📦 正在打包 VoiceType 為獨立 EXE...
echo.

:: 建立環境與安裝 pyinstaller 及相依套件
uv venv -q
uv pip install pyinstaller -q
uv pip install -r requirements.txt -q

:: 打包
uv run pyinstaller ^
    --name VoiceType ^
    --onefile ^
    --windowed ^
    --icon assets\icon.ico ^
    --add-data "ui;ui" ^
    --add-data "assets;assets" ^
    --add-data "config;config" ^
    --hidden-import pystray._win32 ^
    --hidden-import win32gui ^
    --hidden-import win32api ^
    main.py

echo.
if exist dist\VoiceType.exe (
    echo  ✅ 打包成功！
    echo  📁 輸出位置: dist\VoiceType.exe
) else (
    echo  ❌ 打包失敗，請檢查錯誤訊息
)
echo.
pause
