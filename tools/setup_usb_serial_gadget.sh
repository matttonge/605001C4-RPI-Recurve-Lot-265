#!/bin/bash
# Configure Raspberry Pi 4 USB-C OTG as a CDC ACM serial gadget (PC sees COMx).
# Safe to re-run. Does NOT disable Bluetooth or install any HID keyboard emulator.
set -euo pipefail

BOOT_CFG=""
for candidate in /boot/firmware/config.txt /boot/config.txt; do
  if [ -f "$candidate" ]; then
    BOOT_CFG="$candidate"
    break
  fi
done

if [ -z "$BOOT_CFG" ]; then
  echo "ERROR: could not find boot config.txt" >&2
  exit 1
fi

echo "Using boot config: $BOOT_CFG"

ensure_line() {
  local file="$1"
  local line="$2"
  if grep -Eq "^[[:space:]]*${line}([[:space:]]|$)" "$file"; then
    echo "already present: $line"
  else
    echo "$line" | sudo tee -a "$file" >/dev/null
    echo "added: $line"
  fi
}

# Pi 4 USB-C device mode
ensure_line "$BOOT_CFG" "dtoverlay=dwc2"

MODULES_FILE=/etc/modules
sudo touch "$MODULES_FILE"
ensure_line "$MODULES_FILE" "dwc2"
ensure_line "$MODULES_FILE" "g_serial"

# Prefer a clean bluetoothd (with input plugin) so physical BT keyboards work.
# Remove legacy HID-emulator style override if present.
BT_DROPIN_DIR=/etc/systemd/system/bluetooth.service.d
if [ -d "$BT_DROPIN_DIR" ]; then
  for f in "$BT_DROPIN_DIR"/*; do
    [ -f "$f" ] || continue
    if grep -Eq 'noplugin=.*input|ExecStart=.*bluetoothd.*--noplugin' "$f" 2>/dev/null; then
      echo "Neutralizing bluetoothd --noplugin override: $f"
      sudo mv "$f" "${f}.recurve-disabled"
    fi
  done
fi

# Stop/disable any leftover recurve-bthid HID keyboard emulator units.
for unit in recurve-bthid.service recurve-bt-hid.service bthid.service; do
  if systemctl list-unit-files "$unit" >/dev/null 2>&1; then
    echo "Disabling legacy HID unit: $unit"
    sudo systemctl disable --now "$unit" 2>/dev/null || true
  fi
done

# Reload modules now when possible (may fail if already bound differently).
sudo modprobe dwc2 || true
sudo modprobe g_serial || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UNIT_SRC="$SCRIPT_DIR/recurve-usb-gadget.service"
if [ -f "$UNIT_SRC" ]; then
  sudo cp "$UNIT_SRC" /etc/systemd/system/recurve-usb-gadget.service
  sudo systemctl daemon-reload
  sudo systemctl enable recurve-usb-gadget.service
  sudo systemctl restart recurve-usb-gadget.service || true
  echo "Enabled recurve-usb-gadget.service"
fi

# Ensure dialout can open ttyGS0 (Recurve UI user typically needs this).
if getent group dialout >/dev/null; then
  for user in rp pi ubuntu; do
    if id "$user" >/dev/null 2>&1; then
      sudo usermod -aG dialout "$user" || true
      echo "Added $user to dialout"
    fi
  done
fi

echo
echo "Gadget device (after reboot / cable connect): /dev/ttyGS0"
echo "PC side: Device Manager → Ports (COM & LPT) → USB Serial Device (COMx)"
echo "Cable: PC USB-A (data) ↔ Pi 4 USB-C (power/OTG) data-capable cable."
echo "Reboot recommended after first install so dtoverlay=dwc2 applies."
echo "DONE"
