$ErrorActionPreference = 'Stop'
$root = 'C:\ISTIKLAL'
$logDir = Join-Path $root 'logs\server'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stdoutLog = Join-Path $logDir ('server_' + (Get-Date -Format 'yyyyMMdd') + '.out.log')
$stderrLog = Join-Path $logDir ('server_' + (Get-Date -Format 'yyyyMMdd') + '.err.log')
Set-Location (Join-Path $root 'backend')
$env:PYTHONUNBUFFERED = '1'
$process = Start-Process -FilePath (Join-Path $root 'backend\.venv\Scripts\python.exe') `
    -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000') `
    -WorkingDirectory (Join-Path $root 'backend') `
    -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog `
    -NoNewWindow -Wait -PassThru
exit $process.ExitCode
