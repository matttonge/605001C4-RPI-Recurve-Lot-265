# Wi-Fi HTTP + VBA Excel Transfer (Bass-320)

Pulls the last measurement row over Wi-Fi using the same `OK\tv1…v8` payload as USB COM.
USB and Wi-Fi can both be enabled; Excel has separate buttons for each.

## Architecture

The Recurve UI owns a background HTTP server (`wifi_http_transfer.py`) on port **8765**:

- `GET /last_row` → `OK\t…` or `ERR\t…` (plain text)
- Uses [`bass320_transfer.py`](../bass320_transfer.py) for C–J field order
- Gated by Setup **Enable Wi-Fi Transfer** + **Connect** (persisted in `startup.json`)

LAN only — no authentication. Do not expose port 8765 beyond the shop network.

## Setup (Pi)

1. Ensure the Pi is on the same Wi-Fi/LAN as the PC.
2. Recurve → Setup → **Enable Wi-Fi Transfer** → **Connect** (status → Connected / No data).
3. Note the Pi IP (e.g. `192.168.1.186`).

Smoke test from the PC:

```powershell
curl http://192.168.1.186:8765/last_row
```

Expect `OK` plus eight tab-separated values, or `ERR	No data`.

## Excel

Workbook: `Bln. Inspection Data Sheet Bass-320 Templet.xlsm`

1. Put the Pi IP in cell **AA1**.
2. Select a data row (**26+**).
3. Click **Get from Recurve (Wi-Fi)** → columns **C–J** fill.
4. **Get from Recurve** still uses USB COM (default COM3).

Macros: `GetFromRecurveWifi` and `GetFromRecurve` in module `RecurveUsbTransfer`
(source: `tools/bass320_get_from_recurve.bas`).

## Config (`startup.json` / `app_config.py`)

| Key | Meaning |
|-----|---------|
| `wifi_transfer_enabled` | Setup Enable checkbox |
| `wifi_transfer_connected` | Connect/Disconnect |
| `WIFI_HTTP_HOST` | default `0.0.0.0` |
| `WIFI_HTTP_PORT` | default `8765` |

## Firewall note

If `curl` times out, allow inbound TCP **8765** on the Pi (usually open on local LAN).
