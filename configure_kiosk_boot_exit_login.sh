#!/bin/bash
# Boot: LightDM autologin straight into Recurve kiosk session (no desktop).
# Exit: disable one-shot autologin, end session → greeter; login → rpd-x desktop.
# Next reboot restores autologin via systemd oneshot before LightDM.
set -euo pipefail

INSTALL_DIR=/home/rp/Desktop/Recurve

sudo tee /usr/local/sbin/recurve-boot-autologin.sh >/dev/null <<'EOF'
#!/bin/bash
# Ensure cold boot autologins into the Recurve kiosk session.
set -euo pipefail
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

p.write_text("".join(out), encoding="utf-8")
PY
EOF
sudo chmod 755 /usr/local/sbin/recurve-boot-autologin.sh

sudo install -m 755 "$INSTALL_DIR/tools/recurve-exit-to-login.sh" \
  /usr/local/sbin/recurve-exit-to-login.sh 2>/dev/null \
  || sudo install -m 755 /home/rp/Desktop/Recurve/recurve-exit-to-login.sh \
       /usr/local/sbin/recurve-exit-to-login.sh

sudo tee /etc/systemd/system/recurve-boot-autologin.service >/dev/null <<'EOF'
[Unit]
Description=Restore Recurve LightDM autologin before display manager
DefaultDependencies=no
Before=lightdm.service display-manager.service
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/recurve-boot-autologin.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable recurve-boot-autologin.service

# Apply seat settings now (same as boot helper).
sudo /usr/local/sbin/recurve-boot-autologin.sh

# Recurve as an X session (kiosk) — keep / recreate xsessions entry.
sudo tee /usr/share/xsessions/recurve.desktop >/dev/null <<EOF
[Desktop Entry]
Name=Recurve
Comment=Recurve kiosk session
Exec=/bin/bash ${INSTALL_DIR}/start_recurve.sh
Type=Application
DesktopNames=Recurve
EOF

# Do not also start Recurve under the desktop session.
mkdir -p /home/rp/.config/autostart
if [ -f /home/rp/.config/autostart/recurve.desktop ]; then
  mv /home/rp/.config/autostart/recurve.desktop \
     /home/rp/.config/autostart/recurve.desktop.disabled
fi

# Desktop launcher for starting Recurve after Exit → login if needed.
cat > /home/rp/Desktop/Recurve.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Recurve
Comment=Start Recurve measurement application
Exec=/bin/bash ${INSTALL_DIR}/start_recurve.sh
Icon=utilities-terminal
Terminal=false
Categories=Utility;
EOF
chmod +x /home/rp/Desktop/Recurve.desktop
gio set /home/rp/Desktop/Recurve.desktop metadata::trusted true 2>/dev/null || true

echo "=== lightdm ==="
grep -nE 'autologin|user-session|^\[Seat' /etc/lightdm/lightdm.conf || true
echo "=== systemd ==="
systemctl is-enabled recurve-boot-autologin.service || true
echo "=== autostart ==="
ls -la /home/rp/.config/autostart/
echo "=== xsessions/recurve ==="
cat /usr/share/xsessions/recurve.desktop
echo "DONE"
