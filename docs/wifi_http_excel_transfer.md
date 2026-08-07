# Wi-Fi HTTP + VBA Excel Transfer (Bass-320) — demo

Demo build: **Wi-Fi only**. USB Excel transfer UI and the Excel USB button are hidden
(hardware not required for the demo). Setup shows **Excel Transfer** radios:
**On** = HTTP server running, **Off** = stopped.

## Architecture

The Recurve UI owns a background HTTP server (`wifi_http_transfer.py`) on port **8765**:

- `GET /last_row` → `OK\t…` or `ERR\t…` (plain text)
- Uses [`bass320_transfer.py`](../bass320_transfer.py) for C–J field order
- Gated by Setup **Connect** (persisted in `startup.json`)

LAN only — no authentication. Do not expose port 8765 beyond the shop network.
OS Wi-Fi stays up; Disconnect only stops the HTTP transfer server.

## Setup (Pi)

1. Ensure the Pi is on the same Wi-Fi/LAN as the PC.
2. Recurve → Setup → set **Excel Transfer** to **On**.
3. On the main screen, press **Transfer** to see `WiFi: <state> <ip>`
   (status stays ~6 seconds so you can read the IP). The first IP is **Wi-Fi
   (`wlan0`)** when available; other active IPv4s (e.g. ethernet DHCP) follow
   separated by ` -- ` (example: `WiFi: Connected 192.168.68.64 -- 192.168.1.186`).

Smoke test from the PC:

```powershell
curl http://192.168.68.64:8765/last_row
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
| `wifi_transfer_enabled` | Always `true` (Enable UI removed for demo) |
| `wifi_transfer_connected` | Connect/Disconnect (starts/stops HTTP server) |
| `WIFI_HTTP_HOST` | default `0.0.0.0` |
| `WIFI_HTTP_PORT` | default `8765` |

USB transfer keys remain in `startup.json` but are forced off.

## Firewall note

If `curl` times out, allow inbound TCP **8765** on the Pi (usually open on local LAN).
