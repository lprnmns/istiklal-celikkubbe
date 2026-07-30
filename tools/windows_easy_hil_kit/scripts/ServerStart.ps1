#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
Invoke-SelfElevated -ScriptPath $MyInvocation.MyCommand.Path | Out-Null
$log = Start-KitLog 'sunucu_baslat'
try {
    $root = Get-InstallRoot
    $python = Join-Path $root 'backend\.venv\Scripts\python.exe'
    if (-not (Test-Path $python)) { throw 'Proje kurulu degil. Once 04_PROJEYI_KUR.cmd dosyasini calistirin.' }
    $taskName = 'ISTIKLAL_UI_8000'
    $runner = Join-Path $root 'release\windows\run_server_task.ps1'
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`"" -WorkingDirectory (Join-Path $root 'backend')
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentIdentity
    $principal = New-ScheduledTaskPrincipal -UserId $currentIdentity -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    if (-not (Wait-HttpHealth 'http://127.0.0.1:8000/api/health' 60)) { throw 'Sunucu 60 saniye icinde health yaniti vermedi. 09 tani paketini olusturun.' }
    $ip = Get-TailscaleIp
    Write-Host 'SUNUCU CALISIYOR' -ForegroundColor Green
    Write-Host 'Yerel : http://127.0.0.1:8000/'
    if ($ip) { Write-Host "Uzak  : http://${ip}:8000/" }
    Start-Process 'http://127.0.0.1:8000/'
} catch { Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red; exit 1 } finally { Stop-KitLog }
