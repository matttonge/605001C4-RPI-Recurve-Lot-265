#!/usr/bin/env python3
"""Smoke-test Wi-Fi /last_row without the full Tk UI."""
import time
from unittest.mock import MagicMock

from wifi_http_transfer import WifiHttpTransferServer

tree = MagicMock()
tree.get_children.return_value = ("row1",)
tree.item.side_effect = lambda iid, key=None: (
    (1, "0.1", "1", "2", "3", "4", "5", "6", "0.2") if key == "values" else ()
)

server = WifiHttpTransferServer(
    tree_provider=lambda: tree,
    cone_flip_provider=lambda: False,
    host="0.0.0.0",
    port=8765,
)
server.start()
time.sleep(0.5)
print("status", server.last_status)
import urllib.request
print(urllib.request.urlopen("http://127.0.0.1:8765/last_row", timeout=3).read().decode())
server.stop()
print("DONE")
