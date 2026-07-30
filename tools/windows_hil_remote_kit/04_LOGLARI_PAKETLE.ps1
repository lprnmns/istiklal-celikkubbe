#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root 'logs'
if (-not (Test-Path $LogDir)) { throw 'Henuz log klasoru olusmadi.' }
$Files = @(Get-ChildItem -Path $LogDir -File)
if ($Files.Count -eq 0) { throw 'Paketlenecek log bulunamadi.' }
$Out = Join-Path $Root ('ISTIKLAL_WINDOWS_TANI_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.zip')
Compress-Archive -Path (Join-Path $LogDir '*') -DestinationPath $Out -CompressionLevel Optimal
$Hash = Get-FileHash -Algorithm SHA256 -Path $Out
Write-Host "Tani ZIP: $Out" -ForegroundColor Green
Write-Host "SHA256: $($Hash.Hash)" -ForegroundColor Green
