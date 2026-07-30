#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
Invoke-SelfElevated -ScriptPath $MyInvocation.MyCommand.Path | Out-Null
$log = Start-KitLog 'ssh_onar'
try {
    $cap = Get-WindowsCapability -Online | Where-Object Name -Like 'OpenSSH.Server*' | Select-Object -First 1
    if (-not $cap -or $cap.State -ne 'Installed') { throw 'OpenSSH Server kurulu degil; once 01 kurulumunu calistirin.' }
    Set-Service sshd -StartupType Automatic
    Stop-Service sshd -Force -ErrorAction SilentlyContinue
    Start-Service sshd
    Start-Sleep -Seconds 2
    $test = Test-NetConnection -ComputerName 127.0.0.1 -Port 22 -WarningAction SilentlyContinue
    if (-not $test.TcpTestSucceeded) { throw 'SSH servisi basladi ancak TCP 22 cevap vermiyor.' }
    Write-Host 'SSH ONARILDI VE TCP 22 HAZIR.' -ForegroundColor Green
} catch { Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red; exit 1 } finally { Stop-KitLog }
