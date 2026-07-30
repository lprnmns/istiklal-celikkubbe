$ErrorActionPreference = "Stop"

$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profile = "C:\Users\mehme\istiklal_headless_profile"
$screenshot = "C:\Users\mehme\istiklal_cockpit_check.png"

Get-CimInstance Win32_Process -Filter "Name = 'chrome.exe'" |
    Where-Object { $_.CommandLine -like "*istiklal_headless_profile*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$arguments = @(
    "--headless=new"
    "--use-angle=swiftshader"
    "--enable-unsafe-swiftshader"
    "--no-first-run"
    "--disable-default-apps"
    "--hide-scrollbars"
    "--user-data-dir=$profile"
    "--window-size=1920,1080"
    "--virtual-time-budget=15000"
    "--screenshot=$screenshot"
    "http://127.0.0.1:8000/cockpit"
)

Start-Process -FilePath $chrome -ArgumentList $arguments -Wait -NoNewWindow
Get-Item $screenshot | Select-Object FullName, Length, LastWriteTime
