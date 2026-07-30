Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Get-KitRoot { return (Split-Path -Parent $PSScriptRoot) }
function Get-LogRoot {
    $path = Join-Path (Get-KitRoot) 'logs'
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    return $path
}
function Start-KitLog([string]$Name) {
    $path = Join-Path (Get-LogRoot) ($Name + '_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
    Start-Transcript -Path $path -Force | Out-Null
    return $path
}
function Stop-KitLog { try { Stop-Transcript | Out-Null } catch {} }
function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Invoke-SelfElevated {
    param([Parameter(Mandatory=$true)][string]$ScriptPath)
    if (Test-IsAdministrator) { return $false }
    Write-Host 'Windows yonetici izni istenecek...' -ForegroundColor Yellow
    $args = '-NoProfile -ExecutionPolicy Bypass -File "' + $ScriptPath + '"'
    $process = Start-Process powershell.exe -Verb RunAs -ArgumentList $args -Wait -PassThru
    exit $process.ExitCode
}
function Get-RealPython {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:ProgramFiles 'Python312\python.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Python312\python.exe')
    )
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        try {
            $found = (& $launcher.Source -3.12 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
            if ($found -and (Test-Path $found)) { return $found.Trim() }
        } catch {}
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command -and $command.Source -notlike '*WindowsApps*') { return $command.Source }
    return $null
}
function Get-UvPath {
    $candidates = @(
        (Join-Path (Get-KitRoot) 'bin\uv.exe'),
        (Join-Path $env:USERPROFILE '.local\bin\uv.exe')
    )
    foreach ($candidate in $candidates) { if (Test-Path $candidate) { return $candidate } }
    $command = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
}
function Get-TailscalePath {
    $candidates = @(
        (Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Tailscale\tailscale.exe')
    )
    foreach ($candidate in $candidates) { if (Test-Path $candidate) { return $candidate } }
    $command = Get-Command tailscale.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
}
function Get-TailscaleIp {
    $tailscale = Get-TailscalePath
    if (-not $tailscale) { return $null }
    try { return ((& $tailscale ip -4 2>$null | Select-Object -First 1) -as [string]).Trim() } catch { return $null }
}
function Get-InstallRoot { return 'C:\ISTIKLAL' }
function Write-ResultJson([string]$Name, $Value) {
    $path = Join-Path (Get-LogRoot) $Name
    $Value | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 -Path $path
    return $path
}
function Wait-HttpHealth([string]$Url, [int]$Seconds = 45) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
            if ($response.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $false
}
