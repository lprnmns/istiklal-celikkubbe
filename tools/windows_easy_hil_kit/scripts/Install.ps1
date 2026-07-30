#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
Invoke-SelfElevated -ScriptPath $MyInvocation.MyCommand.Path | Out-Null
$log = Start-KitLog 'kurulum'
try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows 10/11 gereklidir.' }
    $kit = Get-KitRoot
    $installers = Join-Path $kit 'installers'
    $manifest = Join-Path $installers 'SHA256SUMS.txt'
    if (-not (Test-Path $manifest)) { throw 'Kurucu checksum listesi bulunamadi.' }
    foreach ($line in Get-Content $manifest) {
        if (-not $line.Trim()) { continue }
        $parts = $line -split '\s+', 2
        $file = Join-Path $installers $parts[1]
        if (-not (Test-Path $file)) { throw "Kurucu eksik: $($parts[1])" }
        $actual = (Get-FileHash -Algorithm SHA256 $file).Hash.ToLowerInvariant()
        if ($actual -ne $parts[0].ToLowerInvariant()) { throw "Kurucu checksum hatasi: $($parts[1])" }
    }
    Write-Host 'Kurucu dosyalari dogrulandi.' -ForegroundColor Green

    $python = Get-RealPython
    if (-not $python) {
        Write-Host 'Python 3.12 kuruluyor...' -ForegroundColor Cyan
        $pythonInstaller = Join-Path $installers 'python-3.12.10-amd64.exe'
        $proc = Start-Process $pythonInstaller -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1' -Wait -PassThru
        if ($proc.ExitCode -ne 0) { throw "Python kurulumu basarisiz: $($proc.ExitCode)" }
        $python = Get-RealPython
        if (-not $python) { throw 'Python kuruldu ancak gercek python.exe bulunamadi.' }
    }
    $version = (& $python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
    if (-not $version.StartsWith('3.12.')) { throw "Python 3.12 gerekli; bulunan: $version" }

    $uv = Get-UvPath
    if (-not $uv) {
        Write-Host 'uv paket yoneticisi kuruluyor...' -ForegroundColor Cyan
        $bin = Join-Path $kit 'bin'
        New-Item -ItemType Directory -Force -Path $bin | Out-Null
        Expand-Archive -Path (Join-Path $installers 'uv-0.11.32-x86_64-pc-windows-msvc.zip') -DestinationPath $bin -Force
        $uv = Get-UvPath
        if (-not $uv) { throw 'uv.exe ZIP icinden cikarilamadi.' }
    }

    $tailscale = Get-TailscalePath
    if (-not $tailscale) {
        Write-Host 'Tailscale kuruluyor...' -ForegroundColor Cyan
        $proc = Start-Process msiexec.exe -ArgumentList @('/i', ('"' + (Join-Path $installers 'tailscale-setup-1.98.9-amd64.msi') + '"'), '/qn', '/norestart') -Wait -PassThru
        if ($proc.ExitCode -notin @(0, 3010)) { throw "Tailscale kurulumu basarisiz: $($proc.ExitCode)" }
    }
    $rustdesk = Join-Path $env:ProgramFiles 'RustDesk\rustdesk.exe'
    if (-not (Test-Path $rustdesk)) {
        Write-Host 'Istege bagli ekran paylasimi icin RustDesk kuruluyor...' -ForegroundColor Cyan
        try {
            $proc = Start-Process (Join-Path $installers 'rustdesk-1.4.9-x86_64.exe') -ArgumentList '--silent-install' -Wait -PassThru
            if ($proc.ExitCode -ne 0) { Write-Warning "RustDesk sessiz kurulum kodu: $($proc.ExitCode)" }
        } catch { Write-Warning "RustDesk kurulumu atlandi: $($_.Exception.Message)" }
    }

    Write-Host 'OpenSSH Server denetleniyor...' -ForegroundColor Cyan
    $cap = Get-WindowsCapability -Online | Where-Object Name -Like 'OpenSSH.Server*' | Select-Object -First 1
    if (-not $cap) { throw 'OpenSSH Server Windows ozelligi bulunamadi.' }
    if ($cap.State -ne 'Installed') { Add-WindowsCapability -Online -Name $cap.Name | Out-Null }
    Set-Service sshd -StartupType Automatic
    Start-Service sshd

    $keySource = Join-Path $kit 'public_keys\alperen_ed25519.pub'
    if (Test-Path $keySource) {
        $sshDir = Join-Path $env:USERPROFILE '.ssh'
        New-Item -ItemType Directory -Force -Path $sshDir | Out-Null
        $authorized = Join-Path $sshDir 'authorized_keys'
        $key = (Get-Content $keySource -Raw).Trim()
        $existing = if (Test-Path $authorized) { Get-Content $authorized -Raw } else { '' }
        if ($existing -notmatch [regex]::Escape($key)) { Add-Content -Encoding ascii -Path $authorized -Value $key }
        & icacls.exe $sshDir /inheritance:r /grant:r "${env:USERNAME}:(OI)(CI)F" /grant:r '*S-1-5-18:(OI)(CI)F' | Out-Null
        & icacls.exe $authorized /inheritance:r /grant:r "${env:USERNAME}:F" /grant:r '*S-1-5-18:F' | Out-Null
        $adminKeys = Join-Path $env:ProgramData 'ssh\administrators_authorized_keys'
        $adminExisting = if (Test-Path $adminKeys) { Get-Content $adminKeys -Raw } else { '' }
        if ($adminExisting -notmatch [regex]::Escape($key)) { Add-Content -Encoding ascii -Path $adminKeys -Value $key }
        & icacls.exe $adminKeys /inheritance:r /grant:r '*S-1-5-32-544:F' /grant:r '*S-1-5-18:F' | Out-Null
    }

    Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue | Disable-NetFirewallRule
    Get-NetFirewallRule -Name 'ISTIKLAL-SSH-TAILSCALE' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -Name 'ISTIKLAL-SSH-TAILSCALE' -DisplayName 'ISTIKLAL SSH - Tailscale' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 22 -RemoteAddress '100.64.0.0/10' -Profile Any | Out-Null
    Get-NetFirewallRule -Name 'ISTIKLAL-UI-TAILSCALE' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -Name 'ISTIKLAL-UI-TAILSCALE' -DisplayName 'ISTIKLAL UI - Tailscale' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress '100.64.0.0/10' -Profile Any | Out-Null

    $tailscaleGui = Join-Path $env:ProgramFiles 'Tailscale\tailscale-ipn.exe'
    if (Test-Path $tailscaleGui) { Start-Process $tailscaleGui }
    Write-Host ''
    Write-Host 'KURULUM TAMAM.' -ForegroundColor Green
    Write-Host 'Tailscale penceresinde ayni hesaba giris yapin; sonra 02_UZAK_ERISIMI_AC.cmd dosyasini calistirin.' -ForegroundColor Yellow
} catch {
    Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally { Stop-KitLog }
