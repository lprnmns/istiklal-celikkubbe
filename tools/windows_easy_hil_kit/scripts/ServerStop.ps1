#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
$log = Start-KitLog 'sunucu_durdur'
try {
    & schtasks.exe /End /TN 'ISTIKLAL_UI_8000' 2>$null | Out-Null
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'uvicorn app\.main:app' -and $_.CommandLine -match 'ISTIKLAL' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Write-Host 'ISTIKLAL sunucusu durduruldu.' -ForegroundColor Green
} catch { Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red; exit 1 } finally { Stop-KitLog }
