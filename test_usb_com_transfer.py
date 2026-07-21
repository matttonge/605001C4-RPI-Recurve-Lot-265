import unittest
from unittest.mock import MagicMock

from usb_com_transfer import UsbComTransferServer


class TestUsbComTransferServer(unittest.TestCase):
    def test_handle_get_last_row(self):
        tree = MagicMock()
        tree.get_children.return_value = ("row1",)
        tree.item.side_effect = lambda iid, key=None: (
            (1, "0.1", "1", "2", "3", "4", "5", "6", "0.2")
            if key == "values"
            else ()
        )
        server = UsbComTransferServer(
            tree_provider=lambda: tree,
            cone_flip_provider=lambda: False,
        )
        reply = server._handle_line("GET_LAST_ROW\n")
        self.assertEqual(reply, "OK\t0.1\t1\t2\t3\t4\t5\t6\t0.2")

    def test_handle_unknown_command(self):
        server = UsbComTransferServer(
            tree_provider=lambda: MagicMock(),
            cone_flip_provider=lambda: False,
        )
        reply = server._handle_line("PING")
        self.assertTrue(reply.startswith("ERR\t"))


if __name__ == "__main__":
    unittest.main()
