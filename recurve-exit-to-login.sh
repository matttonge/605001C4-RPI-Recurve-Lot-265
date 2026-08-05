#!/bin/bash
# Called from Recurve Exit.
# 1) Hide the Recurve xsession so the greeter cannot relaunch it.
# 2) Force desktop session in both dmrc locations.
# 3) Disable autologin until the next reboot.
# 4) End this kiosk session → LightDM greeter → login → rpd-x.
set -euo pipefail

FLAG=/run/recurve-want-desktop
HIDDEN_DIR=/var/lib/recurve
HIDDEN_SESSION=$HIDDEN_DIR/recurve.desktop.hidden

sudo mkdir -p "$HIDDEN_DIR"
sudo touch "$FLAG"

# Remove Recurve from the greeter's session list immediately.
if [ -f /usr/share/xsessions/recurve.desktop ]; then
  sudo mv /usr/share/xsessions/recurve.desktop "$HIDDEN_SESSION"
fi

write_dmrc() {
  sudo tee "$1" >/dev/null <<'DMRC'
[Desktop]
Session=rpd-x
DMRC
}

write_dmrc /home/rp/.dmrc
sudo chown rp:rp /home/rp/.dmrc
sudo mkdir -p /var/cache/lightdm/dmrc
write_dmrc /var/cache/lightdm/dmrc/rp.dmrc
sudo chown lightdm:lightdm /var/cache/lightdm/dmrc/rp.dmrc 2>/dev/null || true

sudo python3 <<'PY'
from pathlib import Path
import re

p = Path("/etc/lightdm/lightdm.conf")
text = p.read_text(encoding="utf-8")
text = re.sub(
    r"^#?autologin-user=.*$",
    "#autologin-user=rp  # disabled until reboot (Recurve Exit)",
    text,
    flags=re.M,
)
# Keep manual login on desktop.
if re.search(r"^user-session=", text, flags=re.M):
    text = re.sub(r"^user-session=.*$", "user-session=rpd-x", text, flags=re.M)
else:
    text = re.sub(r"^(\[Seat:\*\])$", r"\1\nuser-session=rpd-x", text, flags=re.M)
p.write_text(text, encoding="utf-8")
PY

sid="${XDG_SESSION_ID:-}"
if [ -n "$sid" ]; then
  loginctl terminate-session "$sid" || true
else
  dm-tool switch-to-greeter || true
fi
