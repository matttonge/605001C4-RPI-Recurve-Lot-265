#!/bin/bash
# DEPRECATED — do not run on production Recurve machines.
# This installs the BT HID Excel emulator and strips BlueZ input, which breaks
# physical Bluetooth keyboards. Use USB COM + VBA instead:
#   docs/usb_com_excel_transfer.md
#   sudo bash tools/setup_usb_serial_gadget.sh
# To undo this script after an accidental run:
#   sudo bash tools/restore_bluetooth_keyboard.sh
echo "ERROR: install_recurve_bthid.sh is deprecated (breaks BT keyboards)." >&2
echo "Use USB COM Excel transfer (tools/setup_usb_serial_gadget.sh) instead." >&2
echo "To restore keyboards: sudo bash tools/restore_bluetooth_keyboard.sh" >&2
exit 1
