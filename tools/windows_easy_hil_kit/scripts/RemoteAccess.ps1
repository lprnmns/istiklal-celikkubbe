#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
$log = Start-KitLog 'uzak_erisim'
try {
    $tailscale = Get-TailscalePath
    if (-not $tailscale) { throw 'Tailscale kurulu degil. Once 01 kurulumunu calistirin.' }
    $ip = Get-TailscaleIp
    if (-not $ip) {
        $gui = Join-Path $env:ProgramFiles 'Tailscale\tailscale-ipn.exe'
        if (Test-Path $gui) { Start-Process $gui }
        throw 'Tailscale oturumu henuz acik degil. Acilan pencerede giris yapip tekrar deneyin.'
    }
    $ssh = Get-Service sshd -ErrorAction SilentlyContinue
    if (-not $ssh -or $ssh.Status -ne 'Running') { throw 'SSH servisi calismiyor. 08_SSH_ONAR_YONETICI.cmd dosyasini calistirin.' }
    $result = [ordered]@{ computer=$env:COMPUTERNAME; user=$env:USERNAME; tailscale_ipv4=$ip; ssh='RUNNING'; ssh_command="ssh $env:USERNAME@$ip"; ui_url="http://${ip}:8000/" }
    Write-ResultJson 'uzak_erisim_sonucu.json' $result | Out-Null
    $desktop = [Environment]::GetFolderPath('Desktop')
    @("Bilgisayar: $env:COMPUTERNAME", "Windows kullanicisi: $env:USERNAME", "Tailscale IP: $ip", "SSH: ssh $env:USERNAME@$ip", "Arayuz: http://${ip}:8000/") | Set-Content -Encoding UTF8 (Join-Path $desktop 'ISTIKLAL_BAGLANTI_BILGISI.txt')
    Write-Host 'UZAK ERISIM HAZIR' -ForegroundColor Green
    Write-Host "Windows kullanicisi : $env:USERNAME"
    Write-Host "Tailscale IP         : $ip"
    Write-Host "SSH komutu           : ssh $env:USERNAME@$ip"
    Write-Host "Arayuz                : http://${ip}:8000/"
} catch { Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red; exit 1 } finally { Stop-KitLog }
