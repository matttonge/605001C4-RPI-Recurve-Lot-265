#!/bin/bash
# LightDM session-cleanup-script: after Recurve Exit, force desktop for next login.
# Session teardown can rewrite dmrc back to "recurve"; this runs after that.
set -euo pipefail

FLAG=/run/recurve-want-desktop
HIDDEN_DIR=/var/lib/recurve
HIDDEN_SESSION=$HIDDEN_DIR/recurve.desktop.hidden

[ -f "$FLAG" ] || exit 0

if [ -f /usr/share/xsessions/recurve.desktop ]; then
  mkdir -p "$HIDDEN_DIR"
  mv /usr/share/xsessions/recurve.desktop "$HIDDEN_SESSION"
fi

tee /home/rp/.dmrc >/dev/null <<'DMRC'
[Desktop]
Session=rpd-x
DMRC
chown rp:rp /home/rp/.dmrc

mkdir -p /var/cache/lightdm/dmrc
tee /var/cache/lightdm/dmrc/rp.dmrc >/dev/null <<'DMRC'
[Desktop]
Session=rpd-x
DMRC
chown lightdm:lightdm /var/cache/lightdm/dmrc/rp.dmrc 2>/dev/null || true

python3 <<'PY'
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
text = re.sub(r"^user-session=.*$", "user-session=rpd-x", text, flags=re.M)
p.write_text(text, encoding="utf-8")
PY

# Leave FLAG in place until a successful desktop login or reboot restore.
