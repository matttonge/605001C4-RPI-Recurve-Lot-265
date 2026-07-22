# Wi-Fi HTTP + VBA Excel Transfer (Bass-320) — demo

Demo build: **Wi-Fi only**. USB Excel transfer UI and the Excel USB button are hidden
(hardware not required for the demo). Setup uses a single **Enable Wi-Fi Transfer** checkbox.

## Architecture

The Recurve UI owns a background HTTP server (`wifi_http_transfer.py`) on port **8765**:

- `GET /last_row` → `OK\t…` or `ERR\t…` (plain text)
- Uses [`bass320_transfer.py`](../bass320_transfer.py) for C–J field order
- Gated by Setup **Enable Wi-Fi Transfer** (persisted in `startup.json`)

LAN only — no authentication. Do not expose port 8765 beyond the shop network.

## Setup (Pi)

1. Ensure the Pi is on the same Wi-Fi/LAN as the PC.
2. Recurve → Setup → check **Enable Wi-Fi Transfer**.
3. On the main screen, press **Transfer** to see `WiFi: <state> <ip>:<port>`
   (e.g. `WiFi: Connected 192.168.1.186:8765` or `WiFi: No data …`).

Smoke test from the PC:

```powershell
curl http://192.168.1.186:8765/last_row
```

Expect `OK` plus eight tab-separated values, or `ERR	No data`.

## Excel

Workbook: `Bln. Inspection Data Sheet Bass-320 Templet.xlsm`

1. Cell **AA1** label: `BMS IP Address:`
2. Put the Pi IP in cell **AB1**.
3. Select a data row (**26+**).
4. Click **Get Balloon Measurement Data** (button at **AA2**) → columns **C–J** fill.

Macro: `GetFromRecurveWifi` in module `RecurveUsbTransfer`
(source: `tools/bass320_get_from_recurve.bas`).

## Config (`startup.json` / `app_config.py`)

| Key | Meaning |
|-----|---------|
| `wifi_transfer_enabled` | Setup Enable checkbox (also starts/stops the HTTP server) |
| `wifi_transfer_connected` | Kept in sync with enabled for the demo |
| `WIFI_HTTP_HOST` | default `0.0.0.0` |
| `WIFI_HTTP_PORT` | default `8765` |

USB transfer keys remain in `startup.json` but are forced off.

## Firewall note

If `curl` times out, allow inbound TCP **8765** on the Pi (usually open on local LAN).
