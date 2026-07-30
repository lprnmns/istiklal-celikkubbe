#requires -Version 5.1
#requires -RunAsAdministrator
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ('kurulum_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
Start-Transcript -Path $Log -Force
try {
    & (Join-Path $Root '00_KURUCULARI_DOGRULA.ps1')
    Write-Host 'Windows on kontrolu yapiliyor...' -ForegroundColor Cyan
    if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows gereklidir.' }
    $os = Get-CimInstance Win32_OperatingSystem
    $os | Select-Object Caption, Version, BuildNumber, OSArchitecture | Format-List
    $systemDrive = Get-PSDrive -Name $env:SystemDrive.TrimEnd(':')
    if ($systemDrive.Free -lt 15GB) { throw 'Sistem diskinde en az 15 GB bos alan gereklidir.' }

    Write-Host 'OpenSSH Server denetleniyor...' -ForegroundColor Cyan
    $capability = Get-WindowsCapability -Online | Where-Object Name -Like 'OpenSSH.Server*' | Select-Object -First 1
    if (-not $capability) { throw 'OpenSSH.Server Windows capability bulunamadi.' }
    if ($capability.State -ne 'Installed') {
        Add-WindowsCapability -Online -Name $capability.Name | Out-Null
    }
    Set-Service -Name sshd -StartupType Manual
    Start-Service -Name sshd

    Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue | Disable-NetFirewallRule
    Get-NetFirewallRule -Name 'ISTIKLAL-HIL-SSH-Tailscale' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -Name 'ISTIKLAL-HIL-SSH-Tailscale' -DisplayName 'ISTIKLAL HIL SSH - Tailscale only' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 22 -RemoteAddress '100.64.0.0/10' -Profile Any | Out-Null

    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw 'winget bulunamadi. Microsoft App Installer guncellenmeli; rastgele bir EXE indirilmeyecek.'
    }
    Write-Host 'Tailscale resmi winget paketinden kuruluyor...' -ForegroundColor Cyan
    & winget.exe install --id Tailscale.Tailscale --exact --source winget --accept-source-agreements --accept-package-agreements --disable-interactivity
    if ($LASTEXITCODE -notin @(0, -1978335189)) { throw "Tailscale kurulumu basarisiz. winget exit code: $LASTEXITCODE" }

    if (-not (Get-Command python.exe -ErrorAction SilentlyContinue)) {
        Write-Host 'Python 3.12 resmi winget paketinden kuruluyor...' -ForegroundColor Cyan
        & winget.exe install --id Python.Python.3.12 --exact --source winget --scope user --accept-source-agreements --accept-package-agreements --disable-interactivity
        if ($LASTEXITCODE -notin @(0, -1978335189)) { throw "Python 3.12 kurulumu basarisiz. winget exit code: $LASTEXITCODE" }
    }
    if (-not (Get-Command uv.exe -ErrorAction SilentlyContinue)) {
        Write-Host 'uv resmi winget paketinden kuruluyor...' -ForegroundColor Cyan
        & winget.exe install --id astral-sh.uv --exact --source winget --scope user --accept-source-agreements --accept-package-agreements --disable-interactivity
        if ($LASTEXITCODE -notin @(0, -1978335189)) { throw "uv kurulumu basarisiz. winget exit code: $LASTEXITCODE" }
    }
    Write-Host 'Istege bagli ekran destegi icin RustDesk kuruluyor...' -ForegroundColor Cyan
    & winget.exe install --id RustDesk.RustDesk --exact --source winget --accept-source-agreements --accept-package-agreements --disable-interactivity
    if ($LASTEXITCODE -notin @(0, -1978335189)) {
        Write-Warning "RustDesk otomatik kurulamadi. Terminal/SSH kurulumu tamamlandi; hata kodu: $LASTEXITCODE"
    }

    $rule = Get-NetFirewallRule -Name 'ISTIKLAL-HIL-SSH-Tailscale'
    $port = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule
    $address = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule
    [ordered]@{
        timestamp = (Get-Date).ToString('o')
        openssh_service = (Get-Service sshd).Status.ToString()
        firewall_rule = $rule.Enabled.ToString()
        local_port = $port.LocalPort
        remote_address = $address.RemoteAddress
        tailscale_package = 'Tailscale.Tailscale'
        python_package = 'Python.Python.3.12'
        uv_package = 'astral-sh.uv'
        optional_desktop_package = 'RustDesk.RustDesk'
        physical_command_generated = $false
    } | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $LogDir 'kurulum_sonucu.json')
    Write-Host 'PASS: SSH yalniz Tailscale adreslerinden kabul edilecek.' -ForegroundColor Green
    Write-Host 'Simdi Tailscale uygulamasinda cihaz basindaki kisi oturum acmali.' -ForegroundColor Yellow
} finally {
    Stop-Transcript
}
