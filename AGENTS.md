# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **host GUI half** of the "Recurve" product: a Python **Tkinter/pygubu
kiosk application** that runs on a Raspberry Pi touchscreen and drives a pneumatic
leak-test / dimensional-measurement machine. It talks over a USB serial UART (115200
baud) to a companion Raspberry Pi Pico firmware repo (`605002C2-pico-*`, **not present**
in this workspace) and reads/writes lot data as `.xlsx` files in `Data_Files/`.

### Services / how to run

There is a single application. Dependencies are installed into a `venv/` at the repo
root by the startup update script (see `requirements.txt`). `tkinter` comes from the
system package `python3-tk` (already installed in the VM snapshot, not via pip).

| Task | Command | Notes |
|------|---------|-------|
| Lint | none configured | No linter/config in repo. |
| Test | `venv/bin/python -m unittest test_conversions.py` | Pure-logic unit tests (unit conversions). Headless, no display/hardware needed. The `test_ttk_styles.py` / `test2_ttk_styles.py` files are manual ttk demos, not unit tests. |
| Run app | `DISPLAY=:1 venv/bin/python Run_Screen_1b.py` | Main operator screen (entry point). `screen_2_app.py` is the setup/calibration screen launched from within it. |

`start_recurve.sh` is the **production** Pi launcher — it hardcodes `/home/rp/Desktop/Recurve`
paths and openbox/xrandr/unclutter kiosk setup that do NOT apply in this VM. Do not use it
here; run `Run_Screen_1b.py` directly as above.

### Non-obvious gotchas for running the GUI headlessly

1. **Display**: The app is a Tkinter GUI and needs an X display. Use the VM's existing
   VNC desktop on `DISPLAY=:1` (this is what the visual/computer-use tooling sees). The UI
   is designed for 1024x600 but renders fine as a smaller window on the larger desktop.
2. **Serial port is opened eagerly at startup** (`serial_transfer.py` `COM_DATA.__init__`
   opens `SERIAL_LINUX_PORT = /dev/ttyUSB0` unconditionally). With no Pico attached the app
   crashes immediately on launch. To run without hardware, create a virtual serial device
   at `/dev/ttyUSB0` before launching, e.g.:
   `sudo socat -d -d PTY,raw,echo=0,link=/dev/ttyUSB0,mode=666 PTY,raw,echo=0,link=/tmp/ttyPICO,mode=666 &`
   No telemetry needs to be fed for the GUI to run; pressure/position/diameter fields simply
   stay blank/stale without a real Pico. `socat` is installed in the VM snapshot.
3. Core no-hardware functionality that can be exercised end-to-end: entering a Lot Number
   (via the on-screen touch keypad) and clicking **"Save Data File (.xlsx)"**, which writes
   `Data_Files/<LotNumber>.xlsx` (backing up any existing file to `.bakN`). Features gated on
   live telemetry (Get Data, pressure/diameter readouts) require the Pico or a serial emulator.
