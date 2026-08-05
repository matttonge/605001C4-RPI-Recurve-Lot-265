#!/bin/bash
# Apply the "hide Recurve session on Exit" fix now and return to greeter.
set -euo pipefail
cd /home/rp/Desktop/Recurve
sed -i 's/\r$//' recurve-exit-to-login.sh recurve-session-cleanup.sh recurve-boot-autologin.sh

sudo install -m 755 recurve-exit-to-login.sh /usr/local/sbin/recurve-exit-to-login.sh
sudo install -m 755 recurve-session-cleanup.sh /usr/local/sbin/recurve-session-cleanup.sh
sudo install -m 755 recurve-boot-autologin.sh /usr/local/sbin/recurve-boot-autologin.sh

# Wire cleanup script into lightdm without restoring autologin yet.
sudo python3 <<'PY'
from pathlib import Path
import re
p = Path("/etc/lightdm/lightdm.conf")
text = p.read_text(encoding="utf-8")
if re.search(r"^session-cleanup-script=", text, flags=re.M):
    text = re.sub(
        r"^session-cleanup-script=.*$",
        "session-cleanup-script=/usr/local/sbin/recurve-session-cleanup.sh",
        text,
        flags=re.M,
    )
elif re.search(r"^\[Seat:\*\]", text, flags=re.M):
    text = re.sub(
        r"^(\[Seat:\*\])$",
        r"\1\nsession-cleanup-script=/usr/local/sbin/recurve-session-cleanup.sh",
        text,
        flags=re.M,
    )
text = re.sub(r"^user-session=.*$", "user-session=rpd-x", text, flags=re.M)
text = re.sub(
    r"^#?autologin-user=.*$",
    "#autologin-user=rp  # disabled until reboot (Recurve Exit)",
    text,
    flags=re.M,
)
p.write_text(text, encoding="utf-8")
print("lightdm updated")
PY

# Hide Recurve session + force desktop dmrc, then end current graphical session.
sudo mkdir -p /var/lib/recurve
sudo touch /run/recurve-want-desktop
if [ -f /usr/share/xsessions/recurve.desktop ]; then
  sudo mv /usr/share/xsessions/recurve.desktop /var/lib/recurve/recurve.desktop.hidden
fi
printf '%s\n' '[Desktop]' 'Session=rpd-x' | sudo tee /home/rp/.dmrc >/dev/null
sudo chown rp:rp /home/rp/.dmrc
sudo mkdir -p /var/cache/lightdm/dmrc
printf '%s\n' '[Desktop]' 'Session=rpd-x' | sudo tee /var/cache/lightdm/dmrc/rp.dmrc >/dev/null
sudo chown lightdm:lightdm /var/cache/lightdm/dmrc/rp.dmrc 2>/dev/null || true

echo "=== xsessions now ==="
ls -la /usr/share/xsessions/
echo "=== dmrc cache ==="
sudo cat /var/cache/lightdm/dmrc/rp.dmrc
echo "=== lightdm seat ==="
grep -nE 'autologin|user-session|cleanup' /etc/lightdm/lightdm.conf

sid="$(loginctl list-sessions --no-legend | awk '/rp/ && /seat0/ && !/tty1/ {print $1; exit}')"
echo "terminating: ${sid:-none}"
if [ -n "${sid:-}" ]; then
  loginctl terminate-session "$sid" || true
fi
echo DONE
