#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
$log = Start-KitLog 'cihaz_tarama'
try {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $out = Join-Path (Get-LogRoot) "cihaz_tarama_$stamp"
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    $cameras = @(Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.Class -in @('Camera','Image') } | Select-Object FriendlyName,InstanceId,Status)
    $serial = @(Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue | Select-Object DeviceID,Name,Description,PNPDeviceID)
    $pico = @($serial | Where-Object { $_.PNPDeviceID -match 'VID_2E8A&PID_000F' -or $_.Name -match 'Pico' })
    $projectPython = Join-Path (Get-InstallRoot) 'backend\.venv\Scripts\python.exe'
    $python = Get-RealPython
    $uv = Get-UvPath
    if (Test-Path $projectPython) {
        $python = $projectPython
        try { & $python (Join-Path (Get-KitRoot) 'tools\hil_camera_probe.py') --max-index 5 --width 640 --height 480 --frames 45 --output-dir (Join-Path $out 'camera') } catch { Write-Warning "OpenCV kamera taramasi calismadi: $_" }
        foreach ($item in $pico) {
            try { & $python (Join-Path (Get-KitRoot) 'tools\hil_serial_probe.py') --port $item.DeviceID --output (Join-Path $out ("pico_" + $item.DeviceID + '.json')) } catch { Write-Warning "Pico PING/STAT taramasi calismadi: $_" }
        }
    } elseif ($python -and $uv) {
        Write-Host 'Kamera/Pico tani araclari icin hafif gecici Python paketleri hazirlaniyor...' -ForegroundColor Cyan
        try { & $uv run --no-project --python $python --with opencv-python-headless --with numpy python (Join-Path (Get-KitRoot) 'tools\hil_camera_probe.py') --max-index 5 --width 640 --height 480 --frames 45 --output-dir (Join-Path $out 'camera') } catch { Write-Warning "OpenCV kamera taramasi calismadi: $_" }
        foreach ($item in $pico) {
            try { & $uv run --no-project --python $python --with pyserial python (Join-Path (Get-KitRoot) 'tools\hil_serial_probe.py') --port $item.DeviceID --output (Join-Path $out ("pico_" + $item.DeviceID + '.json')) } catch { Write-Warning "Pico PING/STAT taramasi calismadi: $_" }
        }
    } else { Write-Warning 'Python/uv henuz kurulu degil; yalniz Windows PnP taramasi yapildi.' }
    $result = [ordered]@{ timestamp=(Get-Date).ToString('o'); cameras=$cameras; serial_ports=$serial; pico_candidates=$pico; automatic_physical_command=$false; commands_sent=@('PING','STAT') }
    $result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'windows_devices.json')
    Write-Host 'KAMERALAR' -ForegroundColor Cyan; $cameras | Format-Table -AutoSize
    Write-Host 'SERI PORTLAR / PICO' -ForegroundColor Cyan; $serial | Format-Table -AutoSize
    Write-Host "Tani klasoru: $out" -ForegroundColor Green
    Invoke-Item $out
} catch { Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red; exit 1 } finally { Stop-KitLog }
