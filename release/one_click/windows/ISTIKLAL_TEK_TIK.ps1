param([switch]$NoGui)

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = (Resolve-Path (Join-Path $here '..\..\..')).Path
$launcher = Join-Path $root 'release\one_click\launcher.py'
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'
$taskName = 'ISTIKLAL_UI_8000'
$healthUrl = 'http://127.0.0.1:8000/api/health'
$appUrl = 'http://127.0.0.1:8000/'

function Show-Result([string]$title, [string]$message, [bool]$error = $false) {
    if ($NoGui) {
        Write-Output ("${title}: ${message}")
        return
    }
    Add-Type -AssemblyName PresentationFramework
    $icon = if ($error) { 'Error' } else { 'Information' }
    [System.Windows.MessageBox]::Show($message, $title, 'OK', $icon) | Out-Null
}

function Test-Health {
    try {
        $result = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
        return [bool]$result.ok
    } catch {
        return $false
    }
}

try {
    if (-not (Test-Path $python)) {
        throw 'Backend Python ortami bulunamadi. Kurulum paketi eksik.'
    }

    if (Test-Health) {
        & $python $launcher toggle --no-browser
        if ($LASTEXITCODE -ne 0) { throw 'Sistem durdurulamadi.' }
        Show-Result 'ISTIKLAL' 'Sistem guvenli bicimde durduruldu.'
        exit 0
    }

    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        & $python $launcher start --port 8000 --no-browser
        if ($LASTEXITCODE -ne 0) { throw 'Sistem baslatilamadi.' }
    } else {
        Enable-ScheduledTask -TaskName $taskName | Out-Null
        if ($task.State -eq 'Running') {
            Stop-ScheduledTask -TaskName $taskName
            Start-Sleep -Milliseconds 800
        }
        Start-ScheduledTask -TaskName $taskName
        $deadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $deadline -and -not (Test-Health)) {
            Start-Sleep -Milliseconds 500
        }
        if (-not (Test-Health)) {
            throw 'Sunucu 90 saniyede saglik kontrolunu gecemedi. logs\server klasorunu kontrol edin.'
        }
        # Adopt the Task Scheduler process so the next click can stop exactly
        # this project-owned Uvicorn instance.
        & $python $launcher status | Out-Null
    }

    $addresses = @($appUrl)
    $tailscale = Get-Command tailscale.exe -ErrorAction SilentlyContinue
    if ($tailscale) {
        $tailIp = (& $tailscale.Source ip -4 | Select-Object -First 1).Trim()
        if ($tailIp) { $addresses += "http://${tailIp}:8000/" }
    }
    $addresses | Set-Content -Path (Join-Path $root 'ISTIKLAL_URL.txt') -Encoding UTF8
    Start-Process $appUrl
    Show-Result 'ISTIKLAL Hazir' ("Sistem baslatildi.`n`n" + ($addresses -join "`n"))
    exit 0
} catch {
    Show-Result 'ISTIKLAL Hata' $_.Exception.Message $true
    exit 1
}
