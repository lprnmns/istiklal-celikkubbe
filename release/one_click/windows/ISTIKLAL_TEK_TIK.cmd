@echo off
setlocal
set "HERE=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%HERE%ISTIKLAL_TEK_TIK.ps1"
endlocal
