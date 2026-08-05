#!/bin/bash
# One-shot: deploy gadget config on this Pi and reboot into peripheral USB-C mode.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

sed -i 's/\r$//' tools/setup_usb_serial_gadget.sh tools/restore_bluetooth_keyboard.sh 2>/dev/null || true
chmod +x tools/setup_usb_serial_gadget.sh tools/restore_bluetooth_keyboard.sh

sudo bash tools/setup_usb_serial_gadget.sh

echo "==== boot config dwc2 lines ===="
grep -n 'dwc2' /boot/firmware/config.txt /boot/config.txt 2>/dev/null || true

echo
echo "Rebooting in 3s so USB-C peripheral mode takes effect..."
sleep 3
sudo reboot
