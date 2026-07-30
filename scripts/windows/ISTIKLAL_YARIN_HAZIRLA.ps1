#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$ProjectRoot = 'C:\ISTIKLAL'
$TaskName = 'ISTIKLAL_UI_8000'
$BaseUrl = 'http://127.0.0.1:8000'
$Desktop = [Environment]::GetFolderPath('Desktop')
$ReportPath = Join-Path $Desktop 'ISTIKLAL_YARIN_HAZIRLIK_RAPORU.txt'
$ConnectionPath = Join-Path $Desktop 'ISTIKLAL_BAGLANTI_BILGISI.txt'
$Results = New-Object System.Collections.Generic.List[string]

function Add-Result([string]$Name, [string]$State, [string]$Detail) {
    $line = ('{0,-28} {1,-8} {2}' -f $Name, $State, $Detail)
    $Results.Add($line)
    $color = if ($State -eq 'OK') { 'Green' } elseif ($State -eq 'UYARI') { 'Yellow' } else { 'Red' }
    Write-Host $line -ForegroundColor $color
}

function Invoke-Api([string]$Method, [string]$Path, $Body = $null, [int]$Retries = 3) {
    $last = $null
    for ($attempt = 1; $attempt -le $Retries; $attempt++) {
        try {
            $params = @{ Method = $Method; Uri = "$BaseUrl$Path"; TimeoutSec = 20 }
            if ($null -ne $Body) {
                $params.ContentType = 'application/json'
                $params.Body = ($Body | ConvertTo-Json -Depth 10)
            }
            return Invoke-RestMethod @params
        } catch {
            $last = $_
            Start-Sleep -Seconds ([Math]::Min(2 * $attempt, 5))
        }
    }
    throw $last
}

function Test-Health {
    try { return [bool](Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 4).ok } catch { return $false }
}

function Get-TailscaleExe {
    @(
        (Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Tailscale\tailscale.exe')
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
}

function Ensure-FirewallRule([string]$Name, [int]$Port) {
    $existing = Get-NetFirewallRule -Name $Name -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-NetFirewallRule -Name $Name -DisplayName $Name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -RemoteAddress '100.64.0.0/10' -Profile Any | Out-Null
    } else {
        Enable-NetFirewallRule -Name $Name | Out-Null
    }
}

Write-Host ''
Write-Host 'ISTIKLAL GUNLUK HAZIRLIK BASLADI' -ForegroundColor Cyan
Write-Host 'Bu islem hareket veya FIRE komutu gondermez.' -ForegroundColor DarkGray
Write-Host ''

try {
    if (-not (Test-Path $ProjectRoot)) { throw "Proje bulunamadi: $ProjectRoot" }
    Add-Result 'Proje dosyalari' 'OK' $ProjectRoot

    $tailscaleService = Get-Service -Name 'Tailscale*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($tailscaleService) {
        Set-Service -Name $tailscaleService.Name -StartupType Automatic
        if ($tailscaleService.Status -ne 'Running') { Start-Service -Name $tailscaleService.Name }
        Add-Result 'Tailscale servisi' 'OK' $tailscaleService.Name
    } else {
        Add-Result 'Tailscale servisi' 'HATA' 'Tailscale kurulu degil.'
    }

    $tailscaleExe = Get-TailscaleExe
    $tailscaleIp = ''
    if ($tailscaleExe) {
        $tailscaleIp = (& $tailscaleExe ip -4 2>$null | Select-Object -First 1).Trim()
    }
    if ($tailscaleIp) {
        Add-Result 'Tailscale baglantisi' 'OK' $tailscaleIp
    } else {
        $gui = Join-Path $env:ProgramFiles 'Tailscale\tailscale-ipn.exe'
        if (Test-Path $gui) { Start-Process $gui -ErrorAction SilentlyContinue }
        Add-Result 'Tailscale baglantisi' 'UYARI' 'Oturum acilmamis; Tailscale penceresinden giris yapin.'
    }

    $sshd = Get-Service sshd -ErrorAction SilentlyContinue
    if (-not $sshd) { throw 'OpenSSH Server (sshd) kurulu degil.' }
    Set-Service sshd -StartupType Automatic
    if ($sshd.Status -ne 'Running') { Start-Service sshd }
    Add-Result 'OpenSSH Server' 'OK' 'TCP 22 hazir'

    Ensure-FirewallRule 'ISTIKLAL-SSH-TAILSCALE' 22
    Ensure-FirewallRule 'ISTIKLAL-UI-TAILSCALE' 8000
    Add-Result 'Windows Firewall' 'OK' 'Tailscale uzerinden 22 ve 8000 acik'

    & powercfg.exe /change standby-timeout-ac 0 | Out-Null
    Add-Result 'Guc yonetimi' 'OK' 'Prize takiliyken uyku kapali'

    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        $runner = Join-Path $ProjectRoot 'release\windows\run_server_task.ps1'
        if (-not (Test-Path $runner)) { throw "Sunucu baslatma dosyasi yok: $runner" }
        & schtasks.exe /Create /TN $TaskName /SC ONLOGON /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runner`"" /RL HIGHEST /F | Out-Null
    }
    $taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
    Set-ScheduledTask -TaskName $TaskName -Settings $taskSettings | Out-Null

    if (-not (Test-Health)) {
        & schtasks.exe /End /TN $TaskName 2>$null | Out-Null
        $portOwner = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($portOwner) {
            $process = Get-Process -Id $portOwner.OwningProcess -ErrorAction SilentlyContinue
            if ($process -and $process.Path -like "$ProjectRoot*") { Stop-Process -Id $process.Id -Force }
        }
        Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.ExecutablePath -like "$ProjectRoot*" } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Remove-Item (Join-Path $ProjectRoot 'config\runtime\windows_camera_worker') -Recurse -Force -ErrorAction SilentlyContinue
        & schtasks.exe /Run /TN $TaskName | Out-Null
        $deadline = (Get-Date).AddSeconds(35)
        while ((Get-Date) -lt $deadline -and -not (Test-Health)) { Start-Sleep -Seconds 2 }
    }
    if (-not (Test-Health)) { throw 'Backend 35 saniye icinde ayaga kalkmadi.' }
    Add-Result 'ISTIKLAL backend' 'OK' 'http://127.0.0.1:8000'

    try { Invoke-Api 'POST' '/api/motion/tracking/stop' | Out-Null } catch {}
    $profile = Invoke-Api 'POST' '/api/device-profiles/apply' @{ profile_id = 'windows-taret-hil'; connect_hardware = $true }
    $profileCamera = $profile.profile.camera_profile.device_path
    if ($profileCamera -ne 'camera-index:2') {
        Add-Result 'Donanim profili' 'UYARI' "Profil uygulandi fakat kamera yolu $profileCamera"
    } else {
        Add-Result 'Donanim profili' 'OK' 'windows-taret-hil / camera-index:2 / COM8'
    }

    $camera = Invoke-Api 'POST' '/api/camera/runtime/start-preview'
    Start-Sleep -Seconds 3
    $camera = Invoke-Api 'GET' '/api/camera/runtime/status'
    if ($camera.running -and $camera.profile.device_path -eq 'camera-index:2' -and -not $camera.last_capture_error) {
        Add-Result 'Harici USB kamera' 'OK' "index 2 / $($camera.actual_width)x$($camera.actual_height)"
    } else {
        Add-Result 'Harici USB kamera' 'HATA' "path=$($camera.profile.device_path), error=$($camera.last_capture_error)"
    }

    $vision = Invoke-Api 'POST' '/api/vision/start'
    Start-Sleep -Seconds 2
    $vision = Invoke-Api 'GET' '/api/vision/status'
    if ($vision.running -and $vision.balloon_model_loaded) {
        Add-Result 'CUDA YOLO' 'OK' "model yuklu / detector FPS=$($vision.detector_fps)"
    } else {
        Add-Result 'CUDA YOLO' 'HATA' "running=$($vision.running), model=$($vision.balloon_model_loaded)"
    }

    try {
        Invoke-Api 'POST' '/api/motion/tracking/tuning/apply/field_baseline_pd' | Out-Null
        Add-Result 'Takip profili' 'OK' 'Saha Referansi / Dogrudan PD'
    } catch {
        Add-Result 'Takip profili' 'UYARI' 'Aktif takip nedeniyle degistirilmedi.'
    }

    $gateway = Invoke-Api 'POST' '/api/safety/command-profile' @{ profile = 'LIVE_TEST'; actuator_arm = $true }
    if ($gateway.ready) {
        Add-Result 'Gateway preflight' 'OK' 'LIVE_TEST READY / actuator armed'
    } else {
        $codes = @($gateway.reason_codes) -join ', '
        Add-Result 'Gateway preflight' 'UYARI' "Komutlar engelli: $codes"
    }

    $serial = Invoke-Api 'GET' '/api/serial/status'
    $picoState = if ($serial.pico_verified -and $serial.transport_source -eq 'real_serial') { 'OK' } else { 'UYARI' }
    Add-Result 'Pico seri yolu' $picoState "source=$($serial.transport_source), verified=$($serial.pico_verified), ACK=$($serial.last_command_ack_state)"

    $localUrl = "$BaseUrl/cockpit?daily_ready=$([DateTimeOffset]::Now.ToUnixTimeSeconds())"
    $remoteUrl = if ($tailscaleIp) { "http://${tailscaleIp}:8000/cockpit" } else { 'Tailscale IP bekleniyor' }
    @(
        "Hazirlik zamani : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "Bilgisayar       : $env:COMPUTERNAME",
        "Windows kullanici: $env:USERNAME",
        "Tailscale IP     : $tailscaleIp",
        "SSH              : ssh $env:USERNAME@$tailscaleIp",
        "Yerel arayuz     : http://127.0.0.1:8000/cockpit",
        "Uzak arayuz      : $remoteUrl"
    ) | Set-Content -Encoding UTF8 $ConnectionPath
    Start-Process $localUrl
} catch {
    Add-Result 'GENEL SONUC' 'HATA' $_.Exception.Message
}

@(
    'ISTIKLAL GUNLUK HAZIRLIK RAPORU',
    "Zaman: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "Bilgisayar: $env:COMPUTERNAME / $env:USERNAME",
    '',
    $Results,
    '',
    "Rapor: $ReportPath"
) | Set-Content -Encoding UTF8 $ReportPath

Write-Host ''
Write-Host "Rapor kaydedildi: $ReportPath" -ForegroundColor Cyan
Write-Host 'Bu pencereyi kapatmadan once yukaridaki HATA/UYARI satirlarini okuyun.' -ForegroundColor Yellow
Write-Host ''
Read-Host 'Kapatmak icin ENTER'
