import os
import unittest

from keypad_layout import use_kiosk_mode


class TestUseKioskMode(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("RECURVE_KIOSK", None)

    def test_env_forces_off(self):
        os.environ["RECURVE_KIOSK"] = "0"
        self.assertFalse(use_kiosk_mode())

    def test_env_forces_on(self):
        os.environ["RECURVE_KIOSK"] = "1"
        self.assertTrue(use_kiosk_mode())


if __name__ == "__main__":
    unittest.main()
