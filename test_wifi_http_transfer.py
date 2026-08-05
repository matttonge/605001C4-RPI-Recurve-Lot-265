import time
import unittest
import urllib.request
from unittest.mock import MagicMock, patch

from http.server import ThreadingHTTPServer

from wifi_http_transfer import WifiHttpTransferServer, get_lan_ip_address


class TestWifiHttpTransferServer(unittest.TestCase):
    def test_handle_last_row_ok(self):
        tree = MagicMock()
        tree.get_children.return_value = ("row1",)
        tree.item.side_effect = lambda iid, key=None: (
            (1, "0.1", "1", "2", "3", "4", "5", "6", "0.2")
            if key == "values"
            else ()
        )
        server = WifiHttpTransferServer(
            tree_provider=lambda: tree,
            cone_flip_provider=lambda: False,
        )
        self.assertEqual(server.handle_last_row(), "OK\t0.1\t1\t2\t3\t4\t5\t6\t0.2")

    def test_handle_last_row_no_data(self):
        tree = MagicMock()
        tree.get_children.return_value = ()
        server = WifiHttpTransferServer(
            tree_provider=lambda: tree,
            cone_flip_provider=lambda: False,
        )
        reply = server.handle_last_row()
        self.assertTrue(reply.startswith("ERR\t"))
        self.assertIn("No data", reply)

    def test_get_lan_ip_address_returns_string(self):
        ip = get_lan_ip_address()
        self.assertIsInstance(ip, str)
        self.assertTrue(len(ip) > 0)

    def test_get_lan_ip_prefers_wifi_iface(self):
        def fake_ip(name):
            return {"wlan0": "192.168.68.64", "eth0": "192.168.1.186"}.get(name)

        with patch(
            "wifi_http_transfer._list_netifaces",
            return_value=["lo", "eth0", "wlan0"],
        ), patch("wifi_http_transfer._ipv4_for_iface", side_effect=fake_ip):
            self.assertEqual(get_lan_ip_address(), "192.168.68.64")

    def _probe(self, port: int) -> str:
        try:
            return (
                urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/last_row", timeout=1
                )
                .read()
                .decode()
                .strip()
            )
        except Exception as exc:  # noqa: BLE001 - probe helper
            return f"FAIL:{type(exc).__name__}"

    def test_stop_then_start_serves_again(self):
        """Setup checkbox disable/enable must bring HTTP back."""
        tree = MagicMock()
        tree.get_children.return_value = ()
        port = 18781
        server = WifiHttpTransferServer(
            tree_provider=lambda: tree,
            cone_flip_provider=lambda: False,
            host="127.0.0.1",
            port=port,
        )
        server.start()
        time.sleep(0.3)
        self.assertIn("ERR", self._probe(port))
        server.stop()
        time.sleep(0.1)
        self.assertTrue(self._probe(port).startswith("FAIL"))
        server.start()
        time.sleep(0.3)
        self.assertIn("ERR", self._probe(port))
        self.assertTrue(server.running)
        server.stop()

    def test_start_retries_transient_bind_error(self):
        """Re-enable often races on the port; one OSError must not leave server dead."""
        tree = MagicMock()
        tree.get_children.return_value = ()
        port = 18782
        attempts = {"n": 0}
        real_server = ThreadingHTTPServer

        def flaky(addr, handler):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise OSError(98, "Address already in use")
            return real_server(addr, handler)

        server = WifiHttpTransferServer(
            tree_provider=lambda: tree,
            cone_flip_provider=lambda: False,
            host="127.0.0.1",
            port=port,
        )
        with patch("wifi_http_transfer.ThreadingHTTPServer", side_effect=flaky):
            server.start()
            time.sleep(0.6)
            self.assertIn("ERR", self._probe(port))
            self.assertTrue(server.running)
            self.assertGreaterEqual(attempts["n"], 2)
        server.stop()


if __name__ == "__main__":
    unittest.main()
