#requires -Version 5.1
#requires -RunAsAdministrator
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Get-NetFirewallRule -Name 'ISTIKLAL-HIL-SSH-Tailscale' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
Stop-Service sshd -ErrorAction SilentlyContinue
Set-Service sshd -StartupType Manual -ErrorAction SilentlyContinue
Write-Host 'ISTIKLAL firewall kurali kaldirildi ve SSH servisi durduruldu.' -ForegroundColor Green
Write-Host 'Tailscale gerekiyorsa Windows Ayarlar > Uygulamalar bolumunden kaldirilabilir.' -ForegroundColor Yellow
