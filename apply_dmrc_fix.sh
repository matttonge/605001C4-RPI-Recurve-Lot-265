#!/bin/bash
set -euo pipefail
sed -i 's/\r$//' /home/rp/Desktop/Recurve/recurve-exit-to-login.sh
sudo install -m 755 /home/rp/Desktop/Recurve/recurve-exit-to-login.sh \
  /usr/local/sbin/recurve-exit-to-login.sh

# Restore a clean gtk-greeter config (previous edit corrupted a comment line).
sudo tee /etc/lightdm/lightdm-gtk-greeter.conf >/dev/null <<'EOF'
# LightDM GTK+ Configuration
[greeter]
default-session=rpd-x
EOF

sudo tee /home/rp/.dmrc >/dev/null <<'DMRC'
[Desktop]
Session=rpd-x
DMRC
sudo chown rp:rp /home/rp/.dmrc

sudo mkdir -p /var/cache/lightdm/dmrc
sudo tee /var/cache/lightdm/dmrc/rp.dmrc >/dev/null <<'DMRC'
[Desktop]
Session=rpd-x
DMRC
sudo chown lightdm:lightdm /var/cache/lightdm/dmrc/rp.dmrc 2>/dev/null || true

# Keep autologin disabled until reboot so greeter stays up.
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
p.write_text(text, encoding="utf-8")
PY

echo "=== home dmrc ==="
cat /home/rp/.dmrc
echo "=== cache dmrc ==="
sudo cat /var/cache/lightdm/dmrc/rp.dmrc
echo "=== gtk greeter ==="
cat /etc/lightdm/lightdm-gtk-greeter.conf

sid="$(loginctl list-sessions --no-legend | awk '/rp/ && /seat0/ && !/tty1/ {print $1; exit}')"
echo "terminating session: ${sid:-none}"
if [ -n "${sid:-}" ]; then
  loginctl terminate-session "$sid" || true
fi
echo DONE
