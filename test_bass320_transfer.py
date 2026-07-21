import unittest
from unittest.mock import MagicMock

from bass320_transfer import (
    BASS320_FIELD_COUNT,
    format_cell_value,
    format_err_response,
    format_ok_response,
    handle_get_last_row_command,
    last_row_to_bass320_fields,
    parse_request_line,
    tree_row_to_bass320_fields,
)


class TestBass320Transfer(unittest.TestCase):
    def test_format_cell_value_empty_and_number(self):
        self.assertEqual(format_cell_value(None), "")
        self.assertEqual(format_cell_value(""), "")
        self.assertEqual(format_cell_value("  "), "")
        self.assertEqual(format_cell_value(12), "12")
        self.assertEqual(format_cell_value(12.5), "12.5")
        self.assertEqual(format_cell_value("0.250"), "0.25")

    def test_tree_row_no_flip_keeps_distal_first(self):
        row = (1, "0.1", "1.2", "3.4", "5.6", "7.8", "9.0", "11.2", "13.4")
        fields = tree_row_to_bass320_fields(row, cone_flip=False)
        self.assertEqual(len(fields), BASS320_FIELD_COUNT)
        self.assertEqual(
            fields,
            ("0.1", "1.2", "3.4", "5.6", "7.8", "9", "11.2", "13.4"),
        )

    def test_tree_row_cone_flip_remaps_to_bass320_order(self):
        # Prox-first tree → distal-first Bass-320 C–J
        row = (2, "P_OD", "P_CONE", "BODY", "A1", "A2", "A3", "D_CONE", "D_OD")
        fields = tree_row_to_bass320_fields(row, cone_flip=True)
        self.assertEqual(
            fields,
            ("D_OD", "D_CONE", "BODY", "A1", "A2", "A3", "P_CONE", "P_OD"),
        )

    def test_ok_and_err_protocol_lines(self):
        fields = ("1", "2", "3", "4", "5", "6", "7", "8")
        self.assertEqual(format_ok_response(fields), "OK\t1\t2\t3\t4\t5\t6\t7\t8")
        self.assertEqual(format_err_response("No data"), "ERR\tNo data")

    def test_parse_request_line(self):
        self.assertEqual(parse_request_line("GET_LAST_ROW\n"), "GET_LAST_ROW")
        self.assertEqual(parse_request_line(b"get_last_row\r\n"), "GET_LAST_ROW")

    def test_handle_get_last_row_no_data(self):
        tree = MagicMock()
        tree.get_children.return_value = ()
        self.assertEqual(handle_get_last_row_command(tree), "ERR\tNo data")

    def test_handle_get_last_row_ok(self):
        tree = MagicMock()
        tree.get_children.return_value = ("iid1",)
        tree.item.return_value = {
            "values": (1, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.3),
        }
        # item() is called as tree.item(iid, 'values') → returns the values tuple
        tree.item.side_effect = lambda iid, key=None: (
            (1, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.3)
            if key == "values"
            else {"values": (1, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.3)}
        )
        line = handle_get_last_row_command(tree, cone_flip=False)
        self.assertTrue(line.startswith("OK\t"))
        parts = line.split("\t")
        self.assertEqual(len(parts), 9)
        self.assertEqual(parts[1], "0.2")
        self.assertEqual(parts[-1], "0.3")

    def test_last_row_helper_uses_last_child(self):
        tree = MagicMock()
        tree.get_children.return_value = ("a", "b")
        tree.item.side_effect = lambda iid, key=None: (
            (9, "a", "b", "c", "d", "e", "f", "g", "h")
            if iid == "b" and key == "values"
            else ()
        )
        fields = last_row_to_bass320_fields(tree, cone_flip=False)
        self.assertEqual(fields, ("a", "b", "c", "d", "e", "f", "g", "h"))


if __name__ == "__main__":
    unittest.main()
