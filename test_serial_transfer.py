"""Regression: serial tick must not crash when Setup clears COM_DATA.master."""

from unittest.mock import patch
import unittest

import serial

from serial_transfer import COM_DATA


class _FakeScreen:
    def __init__(self):
        self.rt_chuck = None
        self.lft_chuck = None
        self.rt_clamp = None
        self.lft_clamp = None
        self.input_press = None

    def set_cur_press(self, value):
        pass

    def set_cur_clamp_press(self, value):
        pass

    def set_cur_dia(self, value):
        pass

    def set_cur_pos(self, value):
        pass

    def set_cur_input_press(self, value):
        self.input_press = value

    def set_cur_rt_chuck(self, value):
        self.rt_chuck = value

    def set_cur_lft_chuck(self, value):
        self.lft_chuck = value

    def set_cur_rt_clamp(self, value):
        self.rt_clamp = value

    def set_cur_lft_clamp(self, value):
        self.lft_clamp = value

    def callback_get_data(self):
        pass


class SerialMasterDispatchTests(unittest.TestCase):
    def _make_com_data(self, master=None):
        with patch("serial_transfer.serial.Serial"), patch(
            "serial_transfer.threading.Thread"
        ):
            cd = COM_DATA(master)
        cd.serial_run = False
        return cd

    def test_init_without_serial_port_does_not_raise(self):
        """Ubuntu/dev: missing /dev/ttyUSB0 must not prevent the GUI from starting."""
        with patch(
            "serial_transfer.serial.Serial",
            side_effect=serial.SerialException(2, "could not open port /dev/ttyUSB0"),
        ), patch("serial_transfer.threading.Thread"):
            cd = COM_DATA(None)
        self.assertIsNone(cd.ser)
        cd.serial_run = False
        cd.deinit()

    def test_missing_port_warns_once(self):
        """Ubuntu without Pico: do not reprint /dev/ttyUSB0 missing every few seconds."""
        exc = serial.SerialException(
            2,
            "could not open port /dev/ttyUSB0: [Errno 2] No such file or directory: '/dev/ttyUSB0'",
        )
        times = iter([1000.0, 1006.0, 1012.0])
        with patch("serial_transfer.serial.Serial", side_effect=exc), patch(
            "serial_transfer.threading.Thread"
        ), patch("serial_transfer.time.time", side_effect=lambda: next(times)), patch(
            "builtins.print"
        ) as mock_print:
            cd = COM_DATA(None)
            cd._try_open_serial()
            cd._try_open_serial()
        cd.serial_run = False
        serial_lines = [
            call.args[0]
            for call in mock_print.call_args_list
            if call.args and "[serial]" in str(call.args[0])
        ]
        self.assertEqual(len(serial_lines), 1)
        self.assertIn("/dev/ttyUSB0", serial_lines[0])

    def test_uart0_send_with_no_port_does_not_raise(self):
        cd = self._make_com_data()
        cd.ser = None
        cd.uart0_send()

    def test_push_state_survives_setup_clearing_master(self):
        """Setup __init__ calls set_master(None) while a telemetry packet is applied."""
        cd = self._make_com_data()
        cd._pressure_telemetry_seen = True

        class ClearingScreen(_FakeScreen):
            def set_cur_clamp_press(self, value):
                cd.set_master(None)

        screen = ClearingScreen()
        cd.set_master(screen)
        prev_rt = COM_DATA.right_chuck_state
        try:
            COM_DATA.right_chuck_state = True
            cd._push_state_to_master()
            self.assertIsNone(cd.master)
            self.assertTrue(screen.rt_chuck)
        finally:
            COM_DATA.right_chuck_state = prev_rt

    def test_push_state_with_none_master_does_not_raise(self):
        cd = self._make_com_data()
        cd._pressure_telemetry_seen = True
        cd.set_master(None)
        cd._push_state_to_master()

    def test_push_state_updates_chuck_on_live_master(self):
        cd = self._make_com_data()
        cd._pressure_telemetry_seen = True
        screen = _FakeScreen()
        cd.set_master(screen)
        prev_rt, prev_lft = COM_DATA.right_chuck_state, COM_DATA.left_chuck_state
        try:
            COM_DATA.right_chuck_state = True
            COM_DATA.left_chuck_state = False
            cd._push_state_to_master()
            self.assertTrue(screen.rt_chuck)
            self.assertFalse(screen.lft_chuck)
        finally:
            COM_DATA.right_chuck_state = prev_rt
            COM_DATA.left_chuck_state = prev_lft


if __name__ == "__main__":
    unittest.main()
