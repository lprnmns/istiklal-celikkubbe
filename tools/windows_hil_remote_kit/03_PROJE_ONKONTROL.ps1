#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ProjectRoot)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Required = @('backend', 'frontend', 'config', 'models', 'release\windows\start_istiklal_c2.bat')
$Missing = @($Required | Where-Object { -not (Test-Path (Join-Path $ProjectRoot $_)) })
$Python = Get-Command python.exe -ErrorAction SilentlyContinue
$Uv = Get-Command uv.exe -ErrorAction SilentlyContinue
$Node = Get-Command node.exe -ErrorAction SilentlyContinue
$PythonVersion = if ($Python) { (& $Python.Source --version 2>&1 | Out-String).Trim() } else { $null }
$Result = [ordered]@{
    timestamp = (Get-Date).ToString('o')
    project_root = $ProjectRoot
    missing_items = $Missing
    python_path = if ($Python) { $Python.Source } else { $null }
    python_version = $PythonVersion
    uv_path = if ($Uv) { $Uv.Source } else { $null }
    node_path = if ($Node) { $Node.Source } else { $null }
    frontend_dist_ready = Test-Path (Join-Path $ProjectRoot 'frontend\dist\index.html')
    hardware_actions_executed = $false
}
$Path = Join-Path $LogDir ('proje_onkontrol_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json')
$Result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Path
$Result | Format-List
if ($Missing.Count -gt 0) { throw ('Eksik proje ogeleri: ' + ($Missing -join ', ')) }
if (-not $Python -or -not $Uv) { Write-Warning 'Python 3.12+ ve uv eksik. Kurulum tamamlanmadan proje baslatilmayacak.' }
Write-Host "Proje on kontrol kaydi: $Path" -ForegroundColor Green
