#!/bin/bash
# Boot: autologin to desktop + start Recurve.
# Exit: show login greeter; after login resume desktop without restarting Recurve.
set -euo pipefail

# Re-enable LightDM autologin for boot.
sudo python3 <<'PY'
from pathlib import Path
import re

p = Path("/etc/lightdm/lightdm.conf")
text = p.read_text(encoding="utf-8")

# Uncomment / restore autologin-user=rp
text = re.sub(
    r"^#\s*autologin-user=rp\b.*$",
    "autologin-user=rp",
    text,
    flags=re.M,
)
if not re.search(r"^autologin-user=rp\s*$", text, flags=re.M):
    text = re.sub(
        r"(\[Seat:\*\])",
        r"\1\nautologin-user=rp",
        text,
        count=1,
    )

# Keep desktop session (not Recurve-as-session).
text = re.sub(
    r"^autologin-session=.*$",
    "autologin-session=rpd-x",
    text,
    flags=re.M,
)
if re.search(r"^user-session=", text, flags=re.M):
    text = re.sub(r"^user-session=.*$", "user-session=rpd-x", text, flags=re.M)
else:
    text = re.sub(r"(\[Seat:\*\])", r"\1\nuser-session=rpd-x", text, count=1)

p.write_text(text, encoding="utf-8")
print("lightdm autologin restored")
PY

# Re-enable Recurve autostart on login/boot.
mkdir -p /home/rp/.config/autostart
if [ -f /home/rp/.config/autostart/recurve.desktop.disabled ]; then
  mv /home/rp/.config/autostart/recurve.desktop.disabled \
     /home/rp/.config/autostart/recurve.desktop
elif [ ! -f /home/rp/.config/autostart/recurve.desktop ]; then
  cat > /home/rp/.config/autostart/recurve.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Recurve
Exec=/bin/bash /home/rp/Desktop/Recurve/start_recurve.sh
EOF
fi

# Keep a desktop launcher for starting Recurve after Exit/login if needed.
cat > /home/rp/Desktop/Recurve.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Recurve
Comment=Start Recurve measurement application
Exec=/bin/bash /home/rp/Desktop/Recurve/start_recurve.sh
Icon=utilities-terminal
Terminal=false
Categories=Utility;
EOF
chmod +x /home/rp/Desktop/Recurve.desktop
gio set /home/rp/Desktop/Recurve.desktop metadata::trusted true 2>/dev/null || true

echo "=== lightdm ==="
grep -nE 'autologin|user-session' /etc/lightdm/lightdm.conf || true
echo "=== autostart ==="
ls -la /home/rp/.config/autostart/
echo "DONE"
