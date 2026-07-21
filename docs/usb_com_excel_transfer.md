# USB COM + VBA Excel Transfer (Bass-320)

Replaces the Bluetooth-HID-as-keyboard Excel transfer path. The Pi exposes a USB serial port (CDC ACM). Excel VBA requests the last measurement row; the Recurve UI replies with eight Bass-320 fields for columns **C–J**. Bluetooth is left free for a physical keyboard.

## Architecture choice

**The Recurve UI owns `/dev/ttyGS0` in a background thread** (`usb_com_transfer.py`).

Reasons:

- Last-row data lives in the live Tk tree; embedding the listener avoids a second process and fragile IPC.
- Pico telemetry continues to use `/dev/ttyUSB0` (USB-A host ports); gadget serial is a separate device.
- Setup **Enable** / **Connect** state is persisted in `startup.json`.

Kernel gadget bring-up is still installed as a small systemd oneshot (`tools/recurve-usb-gadget.service`) so `/dev/ttyGS0` exists after boot when the PC cable is attached.

## Cabling

| End | Port |
|-----|------|
| PC | USB-A (data) |
| Raspberry Pi 4 | **USB-C** (power / OTG) |

Use a **data-capable** USB-A ↔ USB-C cable. After connect, Windows Device Manager shows a **USB Serial Device (COMx)** under Ports (COM & LPT).

Baud: **115200**, 8N1.

## Protocol

Line-based text:

```
PC → Pi:  GET_LAST_ROW\n
Pi → PC:  OK\t<v1>\t<v2>\t...\t<v8>\n
       or ERR\t<message>\n
```

Field order is always Bass-320 distal→proximal (columns C–J), independent of Prox Left. When Prox Left is checked, tree columns are remapped by `bass320_transfer.tree_row_to_bass320_fields`.

The same `GET_LAST_ROW` protocol can later be reused over Wi-Fi (TCP/HTTP) without changing Excel field mapping.

## Install on the Pi

From the Recurve project directory:

```bash
chmod +x tools/setup_usb_serial_gadget.sh tools/restore_bluetooth_keyboard.sh
sudo ./tools/setup_usb_serial_gadget.sh
sudo ./tools/restore_bluetooth_keyboard.sh   # once, if BT keyboard was broken
sudo reboot
```

What the gadget script does:

- Adds `dtoverlay=dwc2` to boot config
- Loads `dwc2` + `g_serial` via `/etc/modules` and `recurve-usb-gadget.service`
- Adds the UI user to group `dialout`
- Disables leftover `recurve-bthid` / `--noplugin=input` overrides if found

Confirm after reboot (with PC cable attached):

```bash
ls -l /dev/ttyGS0
systemctl status recurve-usb-gadget.service
ps -eo args | grep bluetoothd   # should NOT show --noplugin=input
```

## Setup page (Screen 2)

In **USB Excel Transfer**:

1. Check **Enable USB Transfer** (persisted).
2. Press **Connect** (persisted). Status shows Connected / Waiting / USB off / No data.
3. On boot: if enabled **and** connected, the UI starts listening on `/dev/ttyGS0`.

If not Connected, main-screen **Transfer** and Excel Get are unavailable (`USB off`).

## Main screen Transfer button

Does **not** type into Excel. It flashes the USB status (`Connected`, `Waiting`, `USB off`, or `No data`). Excel VBA is the primary pull path.

## VBA in Bass-320 template

The template file `Bln. Inspection Data Sheet Bass-320 Templet.xlsx` is **not in this git repo**. Import the macro source manually:

1. Open the Bass-320 template in Excel (enable macros / Trusted Location).
2. Developer → Visual Basic → **File → Import File…** → `tools/bass320_get_from_recurve.bas`.
3. Insert a button labeled **Get from Recurve**; assign macro `GetFromRecurve`.
4. Optional Config sheet: create sheet `Config`, put the COM port in **B2** (e.g. `COM7`). Fallback: active sheet **Z1**, then default `COM3`.

Usage:

1. On the Pi: Enable + Connect USB Transfer; take a measurement so the tree has a last row.
2. On the PC: select the target Bass-320 data row (row **26+**).
3. Click **Get from Recurve** → columns C–J fill for that row.
4. Errors appear in a MsgBox.

### Trusted Location / macros

- File → Options → Trust Center → Trust Center Settings → **Trusted Locations** → add the folder that holds the template.
- Or keep the file macro-enabled (`.xlsm`) and enable content when prompted.
- Save as `.xlsm` after importing VBA if the original was `.xlsx`.

Macro embedding into the `.xlsx` was **not** performed in this environment (template absent; openpyxl cannot reliably author VBA projects without a pre-existing `vbaProject.bin`).

## Bluetooth keyboard restore

Do **not** run `bluetoothd --noplugin=input,a2dp,avrcp` for this product. That strips BlueZ input and breaks physical BT keyboards.

```bash
sudo ./tools/restore_bluetooth_keyboard.sh
```

Then pair with `bluetoothctl` as usual.

## Config keys (`startup.json` / `app_config.py`)

| Key | Meaning |
|-----|---------|
| `usb_transfer_enabled` | Setup Enable checkbox |
| `usb_transfer_connected` | Connect/Disconnect toggle |
| `USB_COM_DEVICE` | default `/dev/ttyGS0` |
| `USB_COM_BAUDRATE` | `115200` |
| `BT_HID_TRANSFER_DEPRECATED` | marker that HID typing is not the active path |

## Quick PC smoke test (optional)

With Pi Connected and a tree row present:

```powershell
# PowerShell example
$port = New-Object System.IO.Ports.SerialPort COM7,115200,None,8,One
$port.Open()
$port.WriteLine("GET_LAST_ROW")
$port.ReadLine()
$port.Close()
```
