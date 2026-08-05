# AGENTS.md

## Cursor Cloud / multi-machine notes

Recurve is a Tkinter/pygubu kiosk GUI. Production runs on a Raspberry Pi
(`/home/rp/Desktop/Recurve`). Development also happens on Windows and Ubuntu.

### Install (Ubuntu / Pi)

```bash
# Ubuntu: ensure python3-venv + python3-tk (apt). If ensurepip is missing:
#   python3 -m venv --without-pip venv
#   curl -fsSL https://bootstrap.pypa.io/get-pip.py | venv/bin/python
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### Tests

```bash
venv/bin/python -m unittest test_conversions.py
venv/bin/python -m unittest test_wifi_http_transfer test_bass320_transfer test_usb_com_transfer
```

### Run on Ubuntu / Windows (dev)

Do **not** use `start_recurve.sh` on Ubuntu — it hardcodes Pi paths and kiosk display setup.

On Ubuntu/Windows/Jetson the UI opens as a **movable 1024×600** window titled "Recurve"
(not borderless kiosk). Raspberry Pi still auto-detects kiosk mode. Override with
`RECURVE_KIOSK=1` (force kiosk) or `RECURVE_KIOSK=0` (force windowed).

```bash
# Pico/FTDI attached as /dev/ttyUSB0 (or set RECURVE_SERIAL_PORT):
DISPLAY=:1 venv/bin/python Run_Screen_1b.py

# No hardware: create a virtual serial endpoint first
socat -d -d \
  PTY,raw,echo=0,link=/tmp/recurve_ttyUSB0,mode=666 \
  PTY,raw,echo=0,link=/tmp/recurve_ttyPICO,mode=666 &
RECURVE_SERIAL_PORT=/tmp/recurve_ttyUSB0 DISPLAY=:1 venv/bin/python Run_Screen_1b.py
```

If the device shows up as `/dev/ttyACM0` instead of `ttyUSB0`:

```bash
RECURVE_SERIAL_PORT=/dev/ttyACM0 DISPLAY=:1 venv/bin/python Run_Screen_1b.py
```

### Run on Raspberry Pi (production)

```bash
cd /home/rp/Desktop/Recurve
# Prefer: git pull, then restart the kiosk session / start_recurve.sh
./start_recurve.sh
```

Serial telemetry expects `SERIAL_LINUX_PORT` (`/dev/ttyUSB0` by default). The app
opens that port eagerly at startup.

### Git / deploy

- Source of truth: GitHub (`sync/pi-production` imported the shop Pi tree).
- Pi checkout: `/home/rp/Desktop/Recurve` tracks git; update with `git pull`.
- Do not leave the only copy of a change on the Pi disk.
