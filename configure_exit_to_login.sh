#!/bin/bash
# Configure Pi so Exit from Recurve shows LightDM login, then desktop.
set -euo pipefail

# 1) Disable LightDM autologin so the greeter appears after session end / boot.
if [ -f /etc/lightdm/lightdm.conf ]; then
  sudo cp -a /etc/lightdm/lightdm.conf "/etc/lightdm/lightdm.conf.bak.exit-login-$(date +%Y%m%d%H%M%S)"
fi

sudo python3 <<'PY'
from pathlib import Path
import re

p = Path("/etc/lightdm/lightdm.conf")
text = p.read_text(encoding="utf-8")

# Comment out autologin-user lines (keep history in file).
text = re.sub(
    r"^(autologin-user=.*)$",
    r"#\1  # disabled: require login after Recurve Exit / boot",
    text,
    flags=re.M,
)

# Ensure desktop session is used after login.
if re.search(r"^autologin-session=", text, flags=re.M):
    text = re.sub(
        r"^autologin-session=.*$",
        "autologin-session=rpd-x",
        text,
        flags=re.M,
    )
if re.search(r"^user-session=", text, flags=re.M):
    text = re.sub(r"^user-session=.*$", "user-session=rpd-x", text, flags=re.M)
else:
    # Add under first [Seat:*] if missing.
    text = re.sub(
        r"(\[Seat:\*\])",
        r"\1\nuser-session=rpd-x",
        text,
        count=1,
    )

p.write_text(text, encoding="utf-8")
print("lightdm.conf updated")
PY

# 2) Disable Recurve autostart so login lands on desktop (not the app).
mkdir -p /home/rp/.config/autostart
if [ -f /home/rp/.config/autostart/recurve.desktop ]; then
  mv /home/rp/.config/autostart/recurve.desktop \
     /home/rp/.config/autostart/recurve.desktop.disabled
  echo "disabled Recurve autostart"
fi

# 3) Desktop launcher so Recurve can be started manually after login.
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
# Mark trusted for PCManFM on Pi desktop if present.
gio set /home/rp/Desktop/Recurve.desktop metadata::trusted true 2>/dev/null || true

echo "=== lightdm autologin/session lines ==="
grep -nE 'autologin|user-session' /etc/lightdm/lightdm.conf || true
echo "=== autostart ==="
ls -la /home/rp/.config/autostart/
echo "=== desktop launcher ==="
ls -la /home/rp/Desktop/Recurve.desktop
echo "DONE"
