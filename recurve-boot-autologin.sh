#!/bin/bash
# Ensure cold boot autologins into the Recurve kiosk session.
set -euo pipefail

HIDDEN_DIR=/var/lib/recurve
HIDDEN_SESSION=$HIDDEN_DIR/recurve.desktop.hidden
FLAG=/run/recurve-want-desktop

# Restore Recurve as an available xsession for autologin.
if [ -f "$HIDDEN_SESSION" ] && [ ! -f /usr/share/xsessions/recurve.desktop ]; then
  mv "$HIDDEN_SESSION" /usr/share/xsessions/recurve.desktop
fi
if [ ! -f /usr/share/xsessions/recurve.desktop ]; then
  cat > /usr/share/xsessions/recurve.desktop <<'EOF'
[Desktop Entry]
Name=Recurve
Comment=Recurve kiosk session
Exec=/bin/bash /home/rp/Desktop/Recurve/start_recurve.sh
Type=Application
DesktopNames=Recurve
EOF
fi

rm -f "$FLAG"

python3 <<'PY'
from pathlib import Path

p = Path("/etc/lightdm/lightdm.conf")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
out = []
i = 0
seat_written = False
while i < len(lines):
    line = lines[i]
    if (not seat_written) and line.startswith(
        ("user-session=", "autologin-user=", "autologin-session=", "xserver-command=")
    ):
        i += 1
        continue
    if line.strip() == "[Seat:*]":
        i += 1
        while i < len(lines) and not (
            lines[i].startswith("[") and lines[i].strip().endswith("]")
        ):
            i += 1
        out.append("[Seat:*]\n")
        out.append("user-session=rpd-x\n")
        out.append("autologin-user=rp\n")
        out.append("autologin-session=recurve\n")
        out.append("xserver-command=X -s 0 -dpms\n")
        out.append("session-cleanup-script=/usr/local/sbin/recurve-session-cleanup.sh\n")
        out.append("\n")
        seat_written = True
        continue
    out.append(line)
    i += 1

if not seat_written:
    out.append("\n[Seat:*]\n")
    out.append("user-session=rpd-x\n")
    out.append("autologin-user=rp\n")
    out.append("autologin-session=recurve\n")
    out.append("xserver-command=X -s 0 -dpms\n")
    out.append("session-cleanup-script=/usr/local/sbin/recurve-session-cleanup.sh\n")

p.write_text("".join(out), encoding="utf-8")
PY
