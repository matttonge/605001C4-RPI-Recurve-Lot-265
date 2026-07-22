import unittest
from unittest.mock import MagicMock

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


if __name__ == "__main__":
    unittest.main()
