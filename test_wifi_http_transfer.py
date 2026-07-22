import unittest
from unittest.mock import MagicMock

from wifi_http_transfer import WifiHttpTransferServer


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


if __name__ == "__main__":
    unittest.main()
