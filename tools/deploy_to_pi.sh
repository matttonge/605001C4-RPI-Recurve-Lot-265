#!/bin/bash
# Deploy Recurve Wi-Fi demo build to a Raspberry Pi on the LAN.
#
# Usage (from a PC that can reach the Pi):
#   bash tools/deploy_to_pi.sh
#   bash tools/deploy_to_pi.sh 192.168.1.186
#   PI_HOST=rp@192.168.68.64 bash tools/deploy_to_pi.sh
#
# Default target: rp@192.168.1.186  (wired). Wi-Fi IP for Excel: 192.168.68.64

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PI_HOST="${PI_HOST:-rp@${1:-192.168.1.186}}"
REMOTE_DIR="${REMOTE_DIR:-/home/rp/Desktop/Recurve}"
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=accept-new -o ConnectTimeout=10}"

echo "Deploying $ROOT → $PI_HOST:$REMOTE_DIR"

# Core app + UI + transfer modules needed for the Wi-Fi demo.
FILES=(
  app_config.py
  bass320_transfer.py
  wifi_http_transfer.py
  usb_com_transfer.py
  io_.py
  Run_Screen_1b.py
  screen_2_app.py
  RC_page1b.ui
  RC_Setup_Page_2.ui
  startup.json
  start_recurve.sh
  "Bln. Inspection Data Sheet Bass-320 Templet.xlsm"
  tools/restart_recurve_ui.sh
  tools/enable_wifi_and_restart.sh
  tools/bass320_get_from_recurve.bas
  docs/wifi_http_excel_transfer.md
)

ssh $SSH_OPTS "$PI_HOST" "mkdir -p '$REMOTE_DIR/tools' '$REMOTE_DIR/docs'"

for f in "${FILES[@]}"; do
  scp $SSH_OPTS "$ROOT/$f" "$PI_HOST:$REMOTE_DIR/$f"
done

# Normalize CRLF on shell helpers, enable Wi-Fi transfer, restart UI.
ssh $SSH_OPTS "$PI_HOST" "bash -s" <<'REMOTE'
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
REMOTE

echo
echo "Deploy complete."
echo "Excel BMS IP (AB1) should be the Pi Wi-Fi address: 192.168.68.64"
echo "Smoke test from PC:  curl http://192.168.68.64:8765/last_row"
