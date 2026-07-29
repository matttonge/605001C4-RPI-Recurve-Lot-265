# Deploy Recurve Wi-Fi demo to the Pi from a Windows PC on the shop LAN.
# Run in PowerShell from the repo root (or set $RepoRoot).
#
#   .\tools\deploy_to_pi.ps1
#   .\tools\deploy_to_pi.ps1 -PiHost rp@192.168.68.64

param(
    [string]$PiHost = "rp@192.168.1.186",
    [string]$RemoteDir = "/home/rp/Desktop/Recurve",
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
Set-Location $RepoRoot

Write-Host "Deploying $RepoRoot -> ${PiHost}:${RemoteDir}"

$files = @(
    "app_config.py",
    "bass320_transfer.py",
    "wifi_http_transfer.py",
    "usb_com_transfer.py",
    "io_.py",
    "Run_Screen_1b.py",
    "screen_2_app.py",
    "RC_page1b.ui",
    "RC_Setup_Page_2.ui",
    "startup.json",
    "start_recurve.sh",
    "Bln. Inspection Data Sheet Bass-320 Templet.xlsm",
    "tools/restart_recurve_ui.sh",
    "tools/enable_wifi_and_restart.sh",
    "tools/bass320_get_from_recurve.bas",
    "docs/wifi_http_excel_transfer.md"
)

ssh $PiHost "mkdir -p '$RemoteDir/tools' '$RemoteDir/docs'"

foreach ($f in $files) {
    $local = Join-Path $RepoRoot $f
    if (-not (Test-Path $local)) {
        throw "Missing local file: $local"
    }
    $remote = "${PiHost}:${RemoteDir}/$($f.Replace('\','/'))"
    Write-Host "  scp $f"
    scp $local $remote
}

$remoteScript = @'
set -e
cd /home/rp/Desktop/Recurve
sed -i 's/\r$//' tools/restart_recurve_ui.sh tools/enable_wifi_and_restart.sh start_recurve.sh
chmod +x tools/restart_recurve_ui.sh tools/enable_wifi_and_restart.sh start_recurve.sh
bash tools/enable_wifi_and_restart.sh
echo "=== hostname -I ==="
hostname -I
echo "=== listening 8765 ==="
ss -lntp 2>/dev/null | grep 8765 || true
echo "=== local last_row ==="
curl -sS --max-time 3 http://127.0.0.1:8765/last_row || true
echo
'@

$remoteScript | ssh $PiHost "bash -s"

Write-Host ""
Write-Host "Deploy complete."
Write-Host "Excel BMS IP (AB1) should be Wi-Fi: 192.168.68.64"
Write-Host "Smoke test:  curl http://192.168.68.64:8765/last_row"
