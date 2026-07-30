@echo off
setlocal enabledelayedexpansion
rem Safety invariant: DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false.
rem This launcher starts the software only. It never calls motor, fire, GPIO, STEP/DIR/PWM or hardware-enable endpoints.

set "ROOT_DIR=%~dp0..\.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"
set "PORT=%ISTIKLAL_PORT%"
if "%PORT%"=="" set "PORT=8000"
set "URL=http://127.0.0.1:%PORT%"
set "LOG_DIR=%ROOT_DIR%\logs\launcher"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
for /f "tokens=1-3 delims=/.- " %%a in ("%date%") do set "DATEPART=%%c%%b%%a"
for /f "tokens=1-3 delims=:., " %%a in ("%time%") do set "TIMEPART=%%a%%b%%c"
set "TIMEPART=%TIMEPART: =0%"
set "LOG_FILE=%LOG_DIR%\launcher_%DATEPART%_%TIMEPART%.log"

echo ISTIKLAL C2 Console portable launcher > "%LOG_FILE%"
echo Root: %ROOT_DIR% >> "%LOG_FILE%"
echo Log: %LOG_FILE% >> "%LOG_FILE%"
echo Safety: software startup only; physical commands remain disabled. >> "%LOG_FILE%"
echo ISTIKLAL C2 Console portable launcher
echo Root: %ROOT_DIR%
echo Log: %LOG_FILE%

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python bulunamadı. Python 3.12+ kurup tekrar çalıştırın. >> "%LOG_FILE%"
  echo ERROR: Python bulunamadı. Python 3.12+ kurup tekrar çalıştırın.
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo ERROR: Python bulunamadı veya sürüm yetersiz. Python 3.12+ kurup tekrar çalıştırın. >> "%LOG_FILE%"
  echo ERROR: Python bulunamadı veya sürüm yetersiz. Python 3.12+ kurup tekrar çalıştırın.
  pause
  exit /b 1
)

where uv >nul 2>nul
if errorlevel 1 (
  echo ERROR: uv bulunamadı. İlk kurulum için uv gereklidir. >> "%LOG_FILE%"
  echo Offline release kullanıyorsanız wheelhouse/önceden hazırlanmış .venv paketi gerekir. >> "%LOG_FILE%"
  echo ERROR: uv bulunamadı. İlk kurulum için uv gereklidir.
  pause
  exit /b 1
)

if not exist "%ROOT_DIR%\backend" goto missing_backend
if not exist "%ROOT_DIR%\config" goto missing_config
if not exist "%ROOT_DIR%\models" mkdir "%ROOT_DIR%\models"
if not exist "%ROOT_DIR%\release" goto missing_release
goto package_ok
:missing_backend
echo ERROR: Release paketi eksik veya bozuk: backend bulunamadı.
pause
exit /b 1
:missing_config
echo ERROR: Release paketi eksik veya bozuk: config bulunamadı.
pause
exit /b 1
:missing_release
echo ERROR: Release paketi eksik veya bozuk: release bulunamadı.
pause
exit /b 1
:package_ok

if not exist "%ROOT_DIR%\backend\pyproject.toml" (
  if not exist "%ROOT_DIR%\backend\requirements.txt" (
    echo ERROR: Backend bağımlılık tanımı bulunamadı.
    pause
    exit /b 1
  )
)

if not exist "%ROOT_DIR%\frontend\dist\index.html" (
  echo ERROR: Frontend static build bulunamadı. Release paketi eksik veya bozuk. >> "%LOG_FILE%"
  echo Runtime'da pnpm/npm build çalıştırılmayacak. >> "%LOG_FILE%"
  echo ERROR: Frontend static build bulunamadı. Release paketi eksik veya bozuk.
  pause
  exit /b 1
)

if not exist "%ROOT_DIR%\logs" mkdir "%ROOT_DIR%\logs"
if not exist "%ROOT_DIR%\exports" mkdir "%ROOT_DIR%\exports"
echo ok > "%ROOT_DIR%\logs\.launcher_write_test" 2>nul
if errorlevel 1 (
  echo ERROR: logs klasörü yazılabilir değil.
  pause
  exit /b 1
)
echo ok > "%ROOT_DIR%\exports\.launcher_write_test" 2>nul
if errorlevel 1 (
  echo ERROR: exports klasörü yazılabilir değil.
  pause
  exit /b 1
)
del "%ROOT_DIR%\logs\.launcher_write_test" >nul 2>nul
del "%ROOT_DIR%\exports\.launcher_write_test" >nul 2>nul

python -c "import socket, sys; s=socket.socket(); s.bind(('127.0.0.1', int(sys.argv[1]))); s.close()" %PORT% >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo ERROR: Port %PORT% is already in use. Close the other service or set ISTIKLAL_PORT. >> "%LOG_FILE%"
  echo ERROR: Port %PORT% is already in use. Close the other service or set ISTIKLAL_PORT.
  pause
  exit /b 1
)

echo İlk çalıştırma için backend bağımlılıkları kuruluyor. Bu işlem birkaç dakika sürebilir.
cd /d "%ROOT_DIR%\backend"
uv sync >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo ERROR: Bağımlılıklar indirilemedi. Offline wheelhouse/release paketi gerekli. >> "%LOG_FILE%"
  echo ERROR: Bağımlılıklar indirilemedi. Offline wheelhouse/release paketi gerekli.
  pause
  exit /b 1
)

start "" "%URL%"
echo Starting backend at %URL%
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%
