@echo off
setlocal
set "HERE=%~dp0"
set "LAUNCHER=%HERE%..\launcher.py"
set "PYTHON="
set "PYTHON_ARGS="
if exist "%HERE%..\..\..\backend\.venv\Scripts\python.exe" set "PYTHON=%HERE%..\..\..\backend\.venv\Scripts\python.exe"
if not defined PYTHON (
  where py >nul 2>nul
  if not errorlevel 1 (
    set "PYTHON=py"
    set "PYTHON_ARGS=-3.12"
  )
)
if not defined PYTHON (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
  powershell.exe -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Python 3.12 bulunamadi. Once kurulum paketini calistirin.','ISTIKLAL Hata','OK','Error')"
  exit /b 1
)
"%PYTHON%" %PYTHON_ARGS% "%LAUNCHER%" start --gui
endlocal
