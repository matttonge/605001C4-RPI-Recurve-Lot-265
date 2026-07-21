#!/bin/bash
# Restore normal BlueZ bluetoothd so physical Bluetooth keyboards work.
# The old Excel transfer path used a BT HID keyboard emulator and often ran
# bluetoothd with --noplugin=input,a2dp,avrcp, which blocks BT keyboard input.
set -euo pipefail

echo "=== Restoring Bluetooth keyboard support ==="

# Disable legacy Recurve HID keyboard emulator services if present.
for unit in recurve-bthid.service recurve-bt-hid.service bthid.service; do
  if systemctl list-unit-files "$unit" >/dev/null 2>&1; then
    echo "Disabling $unit"
    sudo systemctl disable --now "$unit" 2>/dev/null || true
  fi
done

# Neutralize drop-ins that strip the BlueZ input plugin.
BT_DROPIN_DIR=/etc/systemd/system/bluetooth.service.d
if [ -d "$BT_DROPIN_DIR" ]; then
  for f in "$BT_DROPIN_DIR"/*; do
    [ -f "$f" ] || continue
    if grep -Eq 'noplugin|ExecStart=.*bluetoothd' "$f" 2>/dev/null; then
      echo "Disabling override: $f"
      sudo mv "$f" "${f}.recurve-disabled" || true
    fi
  done
fi

# Prefer stock bluetooth.service ExecStart (with input plugin).
sudo systemctl daemon-reload
sudo systemctl enable bluetooth.service >/dev/null 2>&1 || true
sudo systemctl restart bluetooth.service

echo "bluetoothd active: $(systemctl is-active bluetooth.service || true)"
echo "Check plugins: bluetoothd should NOT show --noplugin=input"
ps -eo args | grep -E '[b]luetoothd' || true
echo
echo "Pair/connect your keyboard with: bluetoothctl"
echo "  power on"
echo "  agent on"
echo "  default-agent"
echo "  scan on"
echo "  pair <MAC>"
echo "  trust <MAC>"
echo "  connect <MAC>"
echo "DONE"
