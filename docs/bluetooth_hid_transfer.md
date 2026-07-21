# Bluetooth HID Transfer to Bass-320 Excel

> **DEPRECATED.** Do not use this path on production machines. It disables BlueZ
> `input` and breaks physical Bluetooth keyboards. Excel transfer is now
> **USB COM + VBA** — see [`usb_com_excel_transfer.md`](usb_com_excel_transfer.md).
>
> To restore a normal BT keyboard after HID experiments:
> `sudo bash tools/restore_bluetooth_keyboard.sh`

The Recurve Pi app previously could act as a Bluetooth HID keyboard named **Recurve-Transfer**. After a balloon row is measured into the on-screen data table, the operator clicks the start cell of a lot row in the Bass-320 inspection sheet (column **C**), then presses **Transfer to Excel** on the machine. The Pi types the eight machine values into columns **C–J** (inches for Dist OD), separated by Tab.

## One-time Pi setup (legacy — do not run)

1. Install packages:

```bash
sudo apt-get update
sudo apt-get install -y python3-dbus python3-gi
```

2. Disable BlueZ `input` and audio plugins so the Pi advertises as a **keyboard**, not a speaker, and HID L2CAP ports 17/19 stay free:

```bash
bash tools/fix_bluetooth_hid_keyboard.sh
```

Or manually:

```bash
sudo mkdir -p /etc/systemd/system/bluetooth.service.d
sudo tee /etc/systemd/system/bluetooth.service.d/recurve-hid.conf >/dev/null <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/libexec/bluetooth/bluetoothd --noplugin=input,a2dp,avrcp
EOF
sudo systemctl daemon-reload
sudo systemctl restart bluetooth
```

If Windows previously paired Recurve-Transfer as a speaker, **remove/forget that device on Windows**, then pair again after the fix.

3. Install the root HID daemon (L2CAP keyboard ports require root; the UI talks to it over a local socket):

```bash
bash tools/install_recurve_bthid.sh
```

Confirm: `systemctl status recurve-bthid` and Transfer status **Wait HID pair** until Windows connects as a keyboard.

## One-time Windows pairing

1. Start the Recurve app on the Pi (HID service registers only while the app is running).
2. On Windows, if an older **Recurve-Transfer** entry exists as a Speaker/audio device, **Remove device** first.
3. **Settings → Bluetooth & devices → Add device → Bluetooth**.
4. Select **Recurve-Transfer** — it should appear as a **Keyboard** / input device, not a speaker.
5. Leave it connected. On the Pi, Transfer shows **HID ready** only after the HID keyboard link is up (Windows “Connected” as audio is not enough).

If Transfer shows **No HID link**, Windows is not connected on the keyboard profile — remove/re-pair as a keyboard.

## Operator checklist

1. Measure a balloon so the last row in the machine data table is complete.
2. On the PC, open the Bass-320 lot spreadsheet and click the target cell in column **C**.
3. Press **Transfer to Excel** on the machine.
4. Verify columns **C–J** filled; enter manual columns (**N+**) by hand and save the workbook.

## Config knobs (`app_config.py`)

| Name | Purpose |
|------|---------|
| `BT_HID_ENABLED` | Master enable/disable |
| `BT_HID_DEVICE_NAME` | Bluetooth advertise name |
| `BT_HID_KEY_DELAY_SEC` | Delay between key events (Excel reliability) |
| `BT_HID_HCI` | Adapter index (`hci0` → `0`) |

## Manual verification

- Distal-first and Prox-Left tree rows both produce the same C–J order (unit tests cover formatting).
- Empty cells still Tab-align so later values land in the correct columns.
- After Transfer, the Excel cursor should sit at/near column **K** (angles left for later), not in the manual block.
