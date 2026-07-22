#!/bin/bash
set -e
cd /home/rp/Desktop/Recurve
python3 <<'PY'
import json
p = "startup.json"
d = json.load(open(p))
d["wifi_transfer_enabled"] = True
d["wifi_transfer_connected"] = True
# Keep USB as previously configured if keys exist; default keep True for prototype
d.setdefault("usb_transfer_enabled", True)
d.setdefault("usb_transfer_connected", True)
json.dump(d, open(p, "w"), indent=4)
print(
    "usb", d.get("usb_transfer_enabled"), d.get("usb_transfer_connected"),
    "wifi", d.get("wifi_transfer_enabled"), d.get("wifi_transfer_connected"),
)
PY
bash tools/restart_recurve_ui.sh
sleep 2
ss -lntp 2>/dev/null | grep 8765 || netstat -lntp 2>/dev/null | grep 8765 || echo "port 8765 not listed yet"
curl -sS --max-time 3 http://127.0.0.1:8765/last_row || echo "curl_local_failed"
