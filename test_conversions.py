import unittest

from conversions import CONVERSIONS


class TestConversions(unittest.TestCase):
    def setUp(self):
        self.conv = CONVERSIONS()

    def test_linear_same_units_returns_input(self):
        self.assertEqual(self.conv.cnvrt_lin_units(10.5, "mm", "mm"), 10.5)

    def test_linear_mm_to_inch(self):
        result = self.conv.cnvrt_lin_units(25.4, "mm", "inch")
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_linear_inch_to_mm(self):
        result = self.conv.cnvrt_lin_units(1.0, "inch", "mm")
        self.assertAlmostEqual(result, 25.4, places=6)

    def test_pressure_atm_to_psi(self):
        result = self.conv.cnvrt_press_units(1.0, "atm", "psi")
        self.assertAlmostEqual(result, 14.6959, places=4)

    def test_pressure_psi_to_bar_accepts_string(self):
        result = self.conv.cnvrt_press_units("14.5038", "psi", "bar")
        self.assertAlmostEqual(result, 1.0, places=3)

    def test_cur_bal_units_conversion(self):
        self.conv.set_cur_bal_units("psi")
        result = self.conv.to_cur_bal_units(1.0, "atm")
        self.assertAlmostEqual(result, 14.6959, places=4)

    def test_mitutoyo_mm_to_mm(self):
        result = self.conv.mit_val_to_position("12.5mm", "mm")
        self.assertAlmostEqual(result, 12.5, places=6)

    def test_mitutoyo_in_to_mm(self):
        result = self.conv.mit_val_to_position("2.0in", "mm")
        self.assertAlmostEqual(result, 50.8, places=6)

    def test_mitutoyo_unknown_suffix_returns_none(self):
        self.assertIsNone(self.conv.mit_val_to_position("123abc", "mm"))


if __name__ == "__main__":
    unittest.main()
