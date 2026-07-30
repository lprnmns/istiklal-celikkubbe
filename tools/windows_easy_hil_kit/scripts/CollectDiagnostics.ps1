#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
$log = Start-KitLog 'tani_paketi'
try {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $work = Join-Path $env:TEMP "ISTIKLAL_TANI_$stamp"
    New-Item -ItemType Directory -Force -Path $work | Out-Null
    Copy-Item (Join-Path (Get-KitRoot) 'logs') (Join-Path $work 'kit_logs') -Recurse -Force -ErrorAction SilentlyContinue
    $appLogs = Join-Path (Get-InstallRoot) 'logs'
    if (Test-Path $appLogs) { Copy-Item $appLogs (Join-Path $work 'app_logs') -Recurse -Force -ErrorAction SilentlyContinue }
    Get-ComputerInfo | Out-File -Encoding UTF8 (Join-Path $work 'computer_info.txt')
    Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.Class -in @('Camera','Image','Ports','USB') } | Format-Table -AutoSize | Out-File -Encoding UTF8 (Join-Path $work 'devices.txt')
    Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $work 'serial_ports.json')
    & schtasks.exe /Query /TN 'ISTIKLAL_UI_8000' /FO LIST /V 2>&1 | Out-File -Encoding UTF8 (Join-Path $work 'server_task.txt')
    try { Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/health' -TimeoutSec 4 | Select-Object StatusCode,Content | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $work 'health.json') } catch { $_ | Out-File -Encoding UTF8 (Join-Path $work 'health_error.txt') }
    $ip = Get-TailscaleIp
    [ordered]@{timestamp=(Get-Date).ToString('o'); computer=$env:COMPUTERNAME; user=$env:USERNAME; tailscale_ipv4=$ip; secrets_included=$false} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $work 'summary.json')
    $desktop = [Environment]::GetFolderPath('Desktop')
    $zip = Join-Path $desktop "ISTIKLAL_TANI_$stamp.zip"
    Compress-Archive -Path (Join-Path $work '*') -DestinationPath $zip -CompressionLevel Optimal
    Remove-Item $work -Recurse -Force
    Write-Host "TANI PAKETI HAZIR: $zip" -ForegroundColor Green
    Invoke-Item $desktop
} catch { Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red; exit 1 } finally { Stop-KitLog }
