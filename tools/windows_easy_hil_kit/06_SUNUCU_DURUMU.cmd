@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ServerStatus.ps1"
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%
