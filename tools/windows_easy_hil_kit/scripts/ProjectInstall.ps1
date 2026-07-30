#requires -Version 5.1
. (Join-Path $PSScriptRoot 'Common.ps1')
Invoke-SelfElevated -ScriptPath $MyInvocation.MyCommand.Path | Out-Null
$log = Start-KitLog 'proje_kurulum'
try {
    $kit = Get-KitRoot
    $source = Join-Path $kit 'runtime'
    if (-not (Test-Path (Join-Path $source 'backend\pyproject.toml'))) { throw 'Runtime paketi eksik veya bozuk.' }
    $target = Get-InstallRoot
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $target 'models'), (Join-Path $target 'logs'), (Join-Path $target 'exports') | Out-Null
    Write-Host "Guncel runtime C:\ISTIKLAL konumuna kopyalaniyor..." -ForegroundColor Cyan
    & robocopy.exe $source $target /E /R:2 /W:2 /XD .venv __pycache__ .pytest_cache /XF *.pyc | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Runtime kopyalama hatasi: robocopy $LASTEXITCODE" }
    $python = Get-RealPython
    if (-not $python) { throw 'Gercek Python 3.12 bulunamadi. Once 01 kurulumunu calistirin.' }
    $uv = Get-UvPath
    if (-not $uv) { throw 'uv.exe bulunamadi. Once 01 kurulumunu calistirin.' }
    Push-Location (Join-Path $target 'backend')
    try {
        Write-Host 'Python sanal ortami ve GPU destekli YOLO bagimliliklari kuruluyor.' -ForegroundColor Cyan
        Write-Host 'Ilk kurulum internet ve GPU paketleri nedeniyle uzun surebilir.' -ForegroundColor Yellow
        & $uv venv --python $python --clear
        if ($LASTEXITCODE -ne 0) { throw 'uv venv basarisiz.' }
        & $uv sync --no-dev --python (Join-Path $target 'backend\.venv\Scripts\python.exe')
        if ($LASTEXITCODE -ne 0) { throw 'Backend bagimlilik kurulumu basarisiz.' }
        & (Join-Path $target 'backend\.venv\Scripts\python.exe') -c "import cv2, fastapi, serial, torch, ultralytics; print('CUDA:', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
        if ($LASTEXITCODE -ne 0) { throw 'Python import smoke testi basarisiz.' }
    } finally { Pop-Location }
    Write-Host 'PROJE KURULDU: C:\ISTIKLAL' -ForegroundColor Green
    Write-Host 'Simdi 05_SUNUCUYU_BASLAT.cmd dosyasini calistirin.' -ForegroundColor Yellow
} catch { Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red; exit 1 } finally { Stop-KitLog }
