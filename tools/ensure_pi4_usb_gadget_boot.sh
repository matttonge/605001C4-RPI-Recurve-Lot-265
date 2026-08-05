#!/bin/bash
# Ensure Pi 4 USB-C peripheral gadget boot settings.
set -euo pipefail
CFG=/boot/firmware/config.txt
[ -f "$CFG" ] || CFG=/boot/config.txt
[ -f "$CFG" ] || { echo "no config.txt"; exit 1; }

sudo cp -a "$CFG" "${CFG}.bak.recurve-usb"

# Remove existing otg_mode / dwc2 overlay lines, then add correct ones under [all].
# otg_mode=1 must NOT be present: it enables XHCI host-only and blocks DWC2 gadget.
sudo sed -i -E '/^[[:space:]]*otg_mode=/d' "$CFG"
sudo sed -i -E '/^[[:space:]]*dtoverlay=dwc2/d' "$CFG"

if grep -Eq '^[[:space:]]*\[all\]' "$CFG"; then
  sudo awk '
    BEGIN { done=0 }
    /^\[all\]/ && !done {
      print
      print "dtoverlay=dwc2,dr_mode=peripheral"
      done=1
      next
    }
    { print }
    END {
      if (!done) {
        print ""
        print "[all]"
        print "dtoverlay=dwc2,dr_mode=peripheral"
      }
    }
  ' "$CFG" | sudo tee "${CFG}.new" >/dev/null
  sudo mv "${CFG}.new" "$CFG"
else
  printf '\n[all]\ndtoverlay=dwc2,dr_mode=peripheral\n' | sudo tee -a "$CFG" >/dev/null
fi

echo "==== relevant boot lines ===="
grep -nE 'otg_mode|dwc2|^\[' "$CFG" | tail -40
echo "Reboot required."
