@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Install.ps1"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo ISLEM BASARISIZ. Hata kodu: %RC%
pause
exit /b %RC%
