#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
$log = Start-KitLog 'sunucu_durum'
try {
    $task = (& schtasks.exe /Query /TN 'ISTIKLAL_UI_8000' /FO LIST /V 2>&1 | Out-String)
    $healthy = $false
    try { $healthy = (Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/health' -TimeoutSec 4).StatusCode -eq 200 } catch {}
    $ip = Get-TailscaleIp
    Write-Host "Health: $(if ($healthy) {'HAZIR'} else {'YANIT YOK'})" -ForegroundColor $(if ($healthy) {'Green'} else {'Red'})
    Write-Host "Yerel URL: http://127.0.0.1:8000/"
    if ($ip) { Write-Host "Uzak URL : http://${ip}:8000/" }
    Write-Host $task
    if (-not $healthy) { exit 2 }
} finally { Stop-KitLog }
