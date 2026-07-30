#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallerDir = Join-Path $Root 'installers'
$Expected = [ordered]@{
    'python-3.12.10-amd64.exe' = '67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb'
    'rustdesk-1.4.9-x86_64.exe' = 'eaedeb0088e687bf46f7c46a9c6ea5493ce51f3134dfd6acbedb47b5b9136274'
    'tailscale-setup-1.98.9-amd64.msi' = '07bcb57d3bd34a0299d98133f1a0091db2ce66831aa7c100f456e2269a41e665'
    'uv-0.11.32-x86_64-pc-windows-msvc.zip' = 'acfde570451cfdb8689fa159a138ee805ba4e241c466432750302c86254b0984'
}
foreach ($Name in $Expected.Keys) {
    $Path = Join-Path $InstallerDir $Name
    if (-not (Test-Path $Path -PathType Leaf)) { throw "Eksik kurucu: $Name" }
    $Actual = (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected[$Name]) { throw "SHA256 uyusmazligi: $Name" }
    Write-Host "SHA256 OK: $Name" -ForegroundColor Green
}
foreach ($Name in @('python-3.12.10-amd64.exe','rustdesk-1.4.9-x86_64.exe','tailscale-setup-1.98.9-amd64.msi')) {
    $Signature = Get-AuthenticodeSignature -FilePath (Join-Path $InstallerDir $Name)
    if ($Signature.Status -ne 'Valid') {
        throw "Authenticode gecersiz: $Name - $($Signature.Status)"
    }
    Write-Host "IMZA OK: $Name - $($Signature.SignerCertificate.Subject)" -ForegroundColor Green
}
Write-Host 'PASS: Tum gomulu kurucular dogrulandi.' -ForegroundColor Green
