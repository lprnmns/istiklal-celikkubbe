#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Tailscale = Get-Command tailscale.exe -ErrorAction SilentlyContinue
$TailscaleIp = $null
if ($Tailscale) { $TailscaleIp = (& $Tailscale.Source ip -4 2>$null | Select-Object -First 1) }
$Serial = @(Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue | Select-Object DeviceID, Name, Description, PNPDeviceID)
$Cameras = @(Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.Class -in @('Camera','Image') } | Select-Object Class, FriendlyName, InstanceId, Status)
$Usb = @(Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.Class -eq 'USB' } | Select-Object FriendlyName, InstanceId, Status)
$Ssh = Get-Service sshd -ErrorAction SilentlyContinue
$Result = [ordered]@{
    timestamp = (Get-Date).ToString('o')
    computer_name = $env:COMPUTERNAME
    windows_user = $env:USERNAME
    tailscale_ipv4 = $TailscaleIp
    ssh_service = if ($Ssh) { $Ssh.Status.ToString() } else { 'NOT_INSTALLED' }
    serial_ports = $Serial
    cameras = $Cameras
    usb_devices = $Usb
    serial_port_opened = $false
    serial_write_performed = $false
    physical_command_generated = $false
}
$Path = Join-Path $LogDir ("aygit_tani_$Stamp.json")
$Result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Path
Write-Host "Tailscale IP: $TailscaleIp" -ForegroundColor Cyan
Write-Host "Windows kullanicisi: $env:USERNAME" -ForegroundColor Cyan
Write-Host 'Seri portlar:' -ForegroundColor Cyan
$Serial | Format-Table -AutoSize
Write-Host 'Kameralar:' -ForegroundColor Cyan
$Cameras | Format-Table -AutoSize
Write-Host "Tani kaydi: $Path" -ForegroundColor Green
Write-Host 'Bu betik seri port acmadi ve fiziksel komut gondermedi.' -ForegroundColor Green
