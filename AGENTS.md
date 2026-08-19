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

### Multi-repo Cursor workspace

Open both host + Pico trees together:

`/home/matt/Documents/SB-120psi-System/SB-120psi-System.code-workspace`

(or **File → Open Workspace from File…** and pick that file).

### Git / deploy

- Source of truth: Cursor Origin (`origin.cursor.com`, remote `origin`). `main` includes the Pi production import + Ubuntu windowed-dev support.
- GitHub is frozen as remote `github` (fetch only; push disabled). Do not push to GitHub.
- Pi checkout: `/home/rp/Desktop/Recurve` tracks git; update with `git pull` on `main` from `origin` after migrating that clone (see below).
- Do not leave the only copy of a change on the Pi disk.

**Other clones (Pi, Windows):** on each checkout, run once:

```bash
origin auth login   # browser sign-in; once per machine
git remote rename origin github
git remote set-url --push github DISABLED
git remote add origin https://origin.cursor.com/cki-mft/605001C4-RPI-Recurve-Lot-265.git
git fetch origin
git branch --set-upstream-to=origin/main main
```
