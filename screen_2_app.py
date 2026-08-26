#!/usr/bin/python3
import ensure_venv  # re-execs ./venv when launched with system Python
import tkinter as tk
from tkinter import ttk
import pathlib
import pygubu
import time
import math
import platform
from app_config import UI_SCREEN2_FILE
from conversions import CONVERSIONS
from serial_transfer import COM_DATA
from io_ import I_O,json_cls
from touch_numeric_keypad import TouchNumericKeypad
from inline_numeric_keypad import InlineNumericKeypad
from keypad_layout import configure_linux_kiosk_window, release_linux_keyboard_field


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / UI_SCREEN2_FILE


class RcSetupPage2App:
    #def __init__(self,cv, master=None):
    def __init__(self, my_cd,my_cv , parent, master=None, translator=None):
        self.master = master
        self.parent = parent
        self.cd = my_cd #COM_DATA(self)
        self.cd.set_master(None)
     
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("SetupFrame", master)
        configure_linux_kiosk_window(self.mainwindow)
        # Match Screen 1: borderless Toplevel must accept focus or Linux touch
        # often never delivers focus/clicks to children (UI had takefocus=false).
        try:
            self.mainwindow.configure(takefocus=True)
            self.mainwindow.lift()
            self.mainwindow.after(50, self.mainwindow.focus_force)
        except tk.TclError:
            pass
        
        self.balloon_press_str = None
        self.cur_dia_mm_str = None
        self.clamp_press_str = None
        self.input_press_str = None
        self.cur_pos_str = None
        self.v_bal_units = None
        self.v_dia_units = None
        self.v_clampl_units = None
        self.v_pos_units = None
        self.bal_trgt_press_str = None
        self.v_bal_target_press = None
        self.bal_track_checked = None
        self.clamp_trgt_press_str = None
        self.v_clamp_target_press = None
        self.clamp_track_checked = None
        self.right_clamp_enabled = None
        self.left_clamp_enabled = None
        self.bal_sol_track_checked = None
        self.v_bal_press_sol = None
        self.v_bal_relief_sol = None
        self.clamp_sol_track_checked = None
        self.v_clamp_press_sol = None
        self.v_clamp_relief_sol = None
        self.bal_cal_checked = None
        self.v_bal_ref_sldr = None
        self.bal_ref_press_str = None
        self.v_bal_cal_rb = None
        self.clamp_cal_checked = None
        self.v_clamp_ref_sldr = None
        self.clamp_ref_press_str = None
        self.v_clamp_cal_rb = None
        self.v_load_position = None
        self.v_excel_transfer = None
        self._suppress_pressure_entry_focusout = False
        self._numeric_keypad_win = None
        self._active_keypad_var = None
        self._active_keypad_commit_fn = None
        self._last_keypad_open_ms = 0
        self._ignore_focus_open_until_ms = 0
        self._keypad_cls = InlineNumericKeypad if platform.system() == "Linux" else TouchNumericKeypad
        self._keypad_parent = self.builder.get_object('setup_frm')
        builder.import_variables(self,
                                 ['balloon_press_str',
                                  'cur_dia_mm_str',
                                  'clamp_press_str',
                                  'input_press_str',
                                  'cur_pos_str',
                                  'v_bal_units',
                                  'v_dia_units',
                                  'v_clampl_units',
                                  'v_pos_units',
                                  'bal_trgt_press_str',
                                  'v_bal_target_press',
                                  'bal_track_checked',
                                  'clamp_trgt_press_str',
                                  'v_clamp_target_press',
                                  'clamp_track_checked',
                                  'right_clamp_enabled',
                                  'left_clamp_enabled',
                                  'bal_sol_track_checked',
                                  'v_bal_press_sol',
                                  'v_bal_relief_sol',
                                  'clamp_sol_track_checked',
                                  'v_clamp_press_sol',
                                  'v_clamp_relief_sol',
                                  'bal_cal_checked',
                                  'v_bal_ref_sldr',
                                  'bal_ref_press_str',
                                  'v_bal_cal_rb',
                                  'clamp_cal_checked',
                                  'v_clamp_ref_sldr',
                                  'clamp_ref_press_str',
                                  'v_clamp_cal_rb',
                                  'v_load_position',
                                  'v_excel_transfer'])


        self.v_bal_units = self.builder.get_variable('v_bal_units')
        self.v_clamp_units = self.builder.get_variable('v_clampl_units')
        self.v_dia_units = self.builder.get_variable('v_dia_units')
        self.v_pos_units = self.builder.get_variable('v_pos_units')
        
        self.cur_bal_press_frm = self.builder.get_object('cur_bal_press_frm')
        self.cur_dia_frm = self.builder.get_object('cur_dia_frm')
        self.cur_clamp_press_frm = self.builder.get_object('cur_clamp_press_frm')
        self.cur_position_frm = self.builder.get_object('cur_position_frm')
        
        self.trgt_bal_press_frm = self.builder.get_object('trgt_bal_press_frm')
        self.trgt_c_press_frm = self.builder.get_object('trgt_c_press_frm')
       
        self.bal_sol_en_cb = self.builder.get_object('bal_sol_en_cb')
        self.clamp_sol_en_cb = self.builder.get_object('clamp_sol_en_cb')
        
        
        self.v_bal_press_sol_sldr = self.builder.get_object('v_bal_press_sol_sldr')
        self.v_bal_relief_sol_sldr = self.builder.get_object('v_bal_relief_sol_sldr')
        self.v_clamp_press_sol_sldr = self.builder.get_object('v_clamp_press_sol_sldr')
        self.v_clamp_relief_sol_sldr = self.builder.get_object('v_clamp_relief_sol_sldr')

        self.bal_trgt_press_sldr = self.builder.get_object('bal_trgt_press_sldr')
        self.clamp_trgt_press_sldr = self.builder.get_object('clamp_trgt_press_sldr')

        self.bal_cal_ref_sldr = self.builder.get_object('bal_cal_ref_sldr')
        self.clamp_cal_ref_sldr = self.builder.get_object('clamp_cal_ref_sldr')
        self.bal_trgt_press_entry = self.builder.get_object('bal_trgt_press_str_id')
        self.clamp_trgt_press_entry = self.builder.get_object('clamp_trgt_press_str_id')
        self.bal_cal_ref_entry = self.builder.get_object('bal_cal_ref_press_str')
        self.clamp_cal_ref_entry = self.builder.get_object('clamp_cal_ref_press_str')
        self.prox_right_rb = self.builder.get_object('prox_right_rb')
        self.prox_left_rb = self.builder.get_object('prox_left_rb')
        self.wifi_transfer_on_rb = self.builder.get_object('wifi_transfer_on_rb')
        self.wifi_transfer_off_rb = self.builder.get_object('wifi_transfer_off_rb')
         
        self.msg_box = self.builder.get_object('msg_box_tx')
         
        self.msg_box.insert(1.0," Screen Software: " + I_O.Software_Model_Rev + "\n PCB Software: " + COM_DATA.version.decode("utf-8"))
        #self.bal_trgt_press_sldr.configure(tickinterval=1)


        self.cv = my_cv #CONVERSIONS(self)

        self.v_clamp_target_press.set(COM_DATA.target_chuck_pressure)
        self.v_bal_target_press.set(COM_DATA.target_balloon_pressure)  
        self.bal_track_checked.set(COM_DATA.enable_balloon_tracking)
        self.clamp_track_checked.set(COM_DATA.enable_chuck_tracking)
        
        

        
        self.v_bal_units.set(self.cv.get_cur_bal_units())
        self.v_clamp_units.set(self.cv.get_cur_clamp_units())
        self.v_dia_units.set(self.cv.get_cur_dia_units())
        self.v_pos_units.set(self.cv.get_cur_pos_units())
        self.cur_pos_str.set("")
        self.cur_dia_mm_str.set("")
        self.balloon_press_str.set("")
        self.clamp_press_str.set("")

        self.cur_bal_press_frm.config(text="Current Balloon Pressure ("+self.cv.get_cur_bal_units()+")")
        self.cur_dia_frm.config(text="Current Diameter ("+self.cv.get_cur_dia_units()+")")
        self.cur_clamp_press_frm.config(text="Current Chuck Pressure ("+self.cv.get_cur_clamp_units()+")")
        self.cur_position_frm.config(text="Current Position ("+self.cv.get_cur_pos_units()+")")
        
        self.trgt_bal_press_frm.config(text="Balloon Pressure Target ("+self.cv.get_cur_bal_units()+")")
      #  self.v_bal_target_press.set(0.0)
        self.bal_target_press_call(self.v_bal_target_press.get())

        self.trgt_c_press_frm.config(text="Chuck Pressure Target ("+self.cv.get_cur_clamp_units()+")")
      #  self.v_clamp_target_press.set(0.0)
        self.clamp_target_press_call(self.v_clamp_target_press.get())
     
        self.setup_ttk_styles()
        
        builder.connect_callbacks(self)

        self._bind_pressure_entry_controls()
        self._bind_touch_numeric_keypad()
        self._raise_pressure_entries_for_touch()

        self.cd.set_master(self)
        self.set_cur_input_press(COM_DATA.current_input_pressure)
        # Prox Left => cone_flip True; Prox Right => False (same as old checkbox).
        self.v_load_position.set("left" if I_O.cone_flip else "right")

        self._init_wifi_transfer_controls()

      #  self.cd = my_cd #COM_DATA(self)
        
    def run(self):
        # Wait inside Screen 1's existing mainloop. A nested mainloop() here can
        # unwind the outer loop when Setup closes and leave Screen 1 widgets dead.
        self.mainwindow.wait_window(self.mainwindow)

    def _init_wifi_transfer_controls(self):
        # On/Off radios start/stop the HTTP transfer server (On = connected).
        if hasattr(self.parent, "wifi_transfer_enabled"):
            self.parent.wifi_transfer_enabled = True
        connected = bool(getattr(self.parent, "wifi_transfer_connected", False))
        self.v_excel_transfer.set("on" if connected else "off")
        self._refresh_wifi_transfer_ui()

    def _refresh_wifi_transfer_ui(self):
        connected = bool(getattr(self.parent, "wifi_transfer_connected", False))
        try:
            self.v_excel_transfer.set("on" if connected else "off")
        except Exception:
            pass

    def callback_wifi_transfer_toggle(self):
        connected = self.v_excel_transfer.get() == "on"
        if hasattr(self.parent, "set_wifi_transfer_connected"):
            self.parent.set_wifi_transfer_connected(connected)
        self._refresh_wifi_transfer_ui()

    def setup_ttk_styles(self):
        self.style = style = ttk.Style()      
       # style.configure("mylable.Labelframe",  font=("arial", 8))

    @staticmethod
    def _parse_float(s):
        if s is None:
            return None
        try:
            return float(str(s).strip())
        except (TypeError, ValueError):
            return None

    def _bind_pressure_entry_controls(self):
        pairs = (
            (self.builder.get_object('bal_trgt_press_str_id'), self._apply_bal_target_from_entry),
            (self.builder.get_object('clamp_trgt_press_str_id'), self._apply_clamp_target_from_entry),
            (self.builder.get_object('bal_cal_ref_press_str'), self._apply_bal_ref_from_entry),
            (self.builder.get_object('clamp_cal_ref_press_str'), self._apply_clamp_ref_from_entry),
        )
        for widget, handler in pairs:
            widget.bind('<Return>', handler)
            widget.bind('<KP_Enter>', handler)
            widget.bind('<FocusOut>', handler)

    def _bind_touch_numeric_keypad(self):
        triples = (
            (self.builder.get_object('bal_trgt_press_str_id'), self.bal_trgt_press_str, self._apply_bal_target_from_entry),
            (self.builder.get_object('clamp_trgt_press_str_id'), self.clamp_trgt_press_str, self._apply_clamp_target_from_entry),
            (self.builder.get_object('bal_cal_ref_press_str'), self.bal_ref_press_str, self._apply_bal_ref_from_entry),
            (self.builder.get_object('clamp_cal_ref_press_str'), self.clamp_ref_press_str, self._apply_clamp_ref_from_entry),
        )
        # Use a single trigger event to avoid duplicate open/close churn from one tap.
        open_events = ('<ButtonRelease-1>',)
        for widget, var, commit in triples:
            try:
                widget.configure(takefocus=1)
            except tk.TclError:
                pass
            for event_name in open_events:
                widget.bind(
                    event_name,
                    lambda e, v=var, c=commit: self._on_pressure_entry_touch(e, v, c),
                    add='+'
                )

    def _raise_pressure_entries_for_touch(self):
        """Later-placed siblings (e.g. vertical scales) can sit above entries and
        steal taps on Linux; raise entries so they receive touch and focus."""
        for oid in (
            'bal_trgt_press_str_id',
            'clamp_trgt_press_str_id',
            'bal_cal_ref_press_str',
            'clamp_cal_ref_press_str',
        ):
            w = self.builder.get_object(oid)
            try:
                w.configure(takefocus=1)
            except tk.TclError:
                pass
            try:
                w.lift()
            except tk.TclError:
                pass

    def _keypad_side_for_entry(self, entry_widget):
        """Balloon fields use left-side keypad; Chuck fields use right-side keypad."""
        if entry_widget in (self.bal_trgt_press_entry, self.bal_cal_ref_entry):
            return "left"
        return "right"

    def _keypad_title_for_entry(self, entry_widget):
        if entry_widget is self.bal_trgt_press_entry:
            return "Balloon Pressure Target ({})".format(self.cv.get_cur_bal_units())
        if entry_widget is self.clamp_trgt_press_entry:
            return "Chuck Pressure Target ({})".format(self.cv.get_cur_clamp_units())
        if entry_widget is self.bal_cal_ref_entry:
            return "Balloon Pressure Calibration (psi)"
        if entry_widget is self.clamp_cal_ref_entry:
            return "Chuck Pressure Calibration (psi)"
        return "Numeric entry"

    def _on_pressure_entry_touch(self, event, string_var, commit_fn):
        now_ms = int(time.time() * 1000)
        if now_ms < self._ignore_focus_open_until_ms:
            return

        if (now_ms - self._last_keypad_open_ms) < 150:
            return
        self._last_keypad_open_ms = now_ms

        entry_widget = event.widget
        side = self._keypad_side_for_entry(entry_widget)
        title = self._keypad_title_for_entry(entry_widget)

        def open_keypad():
            try:
                self._open_touch_numeric_keypad(string_var, commit_fn, side, title)
            except Exception:
                self._suppress_pressure_entry_focusout = False
                self._numeric_keypad_win = None
                raise

        self.mainwindow.after_idle(open_keypad)

    def _open_touch_numeric_keypad(self, string_var, commit_fn, side, title):
        if self._numeric_keypad_win is not None:
            try:
                if self._numeric_keypad_win.winfo_exists():
                    if self._active_keypad_var is string_var:
                        self._numeric_keypad_win.lift()
                        return

                    # Commit the previous field before switching target.
                    self._suppress_pressure_entry_focusout = False
                    prev_commit = self._active_keypad_commit_fn
                    if prev_commit is not None:
                        try:
                            prev_commit()
                        except Exception:
                            pass

                    self._suppress_pressure_entry_focusout = True

                    def on_exit():
                        self._ignore_focus_open_until_ms = int(time.time() * 1000) + 500
                        self._suppress_pressure_entry_focusout = False
                        self._numeric_keypad_win = None
                        self._active_keypad_var = None
                        self._active_keypad_commit_fn = None
                        commit_fn()

                    self._numeric_keypad_win.set_target(
                        string_var, on_exit=on_exit, side=side, title=title
                    )
                    self._active_keypad_var = string_var
                    self._active_keypad_commit_fn = commit_fn
                    return
            except tk.TclError:
                pass
            self._numeric_keypad_win = None
            self._active_keypad_var = None
            self._active_keypad_commit_fn = None

        self._suppress_pressure_entry_focusout = True

        def on_exit():
            self._ignore_focus_open_until_ms = int(time.time() * 1000) + 500
            self._suppress_pressure_entry_focusout = False
            self._numeric_keypad_win = None
            self._active_keypad_var = None
            self._active_keypad_commit_fn = None
            commit_fn()

        try:
            self._numeric_keypad_win = self._keypad_cls(
                self._keypad_parent, string_var, on_exit=on_exit, side=side, title=title
            )
            self._active_keypad_var = string_var
            self._active_keypad_commit_fn = commit_fn
        except tk.TclError:
            self._suppress_pressure_entry_focusout = False
            self._numeric_keypad_win = None
            self._active_keypad_var = None
            self._active_keypad_commit_fn = None
            raise

    def _apply_bal_target_from_entry(self, event=None):
        if self._suppress_pressure_entry_focusout:
            return
        v = self._parse_float(self.bal_trgt_press_str.get())
        if v is None:
            self.bal_target_press_call(self.v_bal_target_press.get())
            return
        psi = self.cv.cnvrt_press_units(v, self.cv.CurBalUnits, 'psi')
        if psi is None:
            self.bal_target_press_call(self.v_bal_target_press.get())
            return
        psi = max(0.0, min(150.0, round(psi * 10.0) / 10.0))
        self.v_bal_target_press.set(psi)
        self.bal_target_press_call(psi)

    def _apply_clamp_target_from_entry(self, event=None):
        if self._suppress_pressure_entry_focusout:
            return
        v = self._parse_float(self.clamp_trgt_press_str.get())
        if v is None:
            self.clamp_target_press_call(self.v_clamp_target_press.get())
            return
        psi = self.cv.cnvrt_press_units(v, self.cv.CurClampUnits, 'psi')
        if psi is None:
            self.clamp_target_press_call(self.v_clamp_target_press.get())
            return
        psi = max(0.0, min(150.0, float(round(psi))))
        self.v_clamp_target_press.set(psi)
        self.clamp_target_press_call(psi)

    def _apply_bal_ref_from_entry(self, event=None):
        if self._suppress_pressure_entry_focusout:
            return
        v = self._parse_float(self.bal_ref_press_str.get())
        if v is None:
            self.bal_ref_press_call(self.v_bal_ref_sldr.get())
            return
        v = max(9.0, min(150.0, round(v / 0.01) * 0.01))
        self.v_bal_ref_sldr.set(v)
        self.bal_ref_press_call(v)

    def _apply_clamp_ref_from_entry(self, event=None):
        if self._suppress_pressure_entry_focusout:
            return
        v = self._parse_float(self.clamp_ref_press_str.get())
        if v is None:
            self.clamp_ref_press_call(self.v_clamp_ref_sldr.get())
            return
        v = max(9.0, min(150.0, round(v * 10.0) / 10.0))
        self.v_clamp_ref_sldr.set(v)
        self.clamp_ref_press_call(v)

    def callback_get_data(self):
        pass

    def callback_load_position(self):
        """Load Position radios: Prox Left / Prox Right (same as former Proximal Left checkbox)."""
        I_O.cone_flip = self.v_load_position.get() == "left"
        # Keep Screen 1 Excel headers, diagram labels, and message orientation in sync.
        if hasattr(self.parent, "apply_cone_orientation"):
            self.parent.apply_cone_orientation(preserve_rows=True)

    def btn_exit(self):
        self.parent.bal_btn_bg()
        self.parent.chuck_btn_bg()
        self.cd.set_master(self.parent)
        self.parent.j.write_to_json(
            COM_DATA.target_balloon_pressure,
            COM_DATA.target_chuck_pressure,
            self.parent.cv.CurBalUnits,
            self.parent.cv.CurClampUnits,
            self.parent.cv.CurDiaUnits,
            self.parent.cv.CurPosUnits,
            self.parent.TreeFileName,
            usb_transfer_enabled=False,
            usb_transfer_connected=False,
            wifi_transfer_enabled=True,
            wifi_transfer_connected=getattr(self.parent, "wifi_transfer_connected", False),
        )
        # Reload under Setup's cover, lift Screen 1, then destroy Setup so the
        # desktop never shows between screens.
        if hasattr(self.parent, "reload_current_lot"):
            self.parent.reload_current_lot()
        self._close_numeric_keypad()
        release_linux_keyboard_field(self.parent.entry1_)
        try:
            self.parent.balloonwindow.lift()
            self.parent.balloonwindow.update_idletasks()
        except tk.TclError:
            pass
        self.mainwindow.destroy()

    def _close_numeric_keypad(self):
        if self._numeric_keypad_win is None:
            return
        try:
            if self._numeric_keypad_win.winfo_exists():
                self._numeric_keypad_win.close_modal()
        except tk.TclError:
            pass
        self._numeric_keypad_win = None
        self._active_keypad_var = None
        self._active_keypad_commit_fn = None
        self._suppress_pressure_entry_focusout = False
        

    def zero_SV(self):
        self.v_bal_press_sol.set(0)
        self.v_bal_relief_sol.set(0)  
        self.v_clamp_press_sol.set(0)
        self.v_clamp_relief_sol.set(0)

    def set_cur_rt_chuck(self,right_clamp_state):
        if(COM_DATA.right_chuck==0):
            self.right_clamp_enabled.set(right_clamp_state)

    def set_cur_lft_chuck(self,left_clamp_state):
        if(COM_DATA.left_chuck==0):
            self.left_clamp_enabled.set(left_clamp_state)
        



    def set_cur_press(self, cur_press_psi):
        if cur_press_psi is None:
            myStr = ""
        elif(self.cv.CurBalUnits=='psi'):
            myStr = "{:3.2f} ".format(self.cv.to_cur_bal_units(cur_press_psi,'psi'))
        else:
            myStr = "{:3.2f} ".format(self.cv.to_cur_bal_units(cur_press_psi,'psi'))

        if self.balloon_press_str.get()!=myStr:
            self.balloon_press_str.set(myStr)

    def set_cur_clamp_press(self, cur_press_psi):
        if cur_press_psi is None:
            myStr = ""
        elif(self.cv.CurClampUnits=='psi'):
            myStr = "{:3.1f} ".format(self.cv.to_cur_clamp_units(cur_press_psi,'psi'))
        else:
            myStr = "{:3.2f} ".format(self.cv.to_cur_clamp_units(cur_press_psi,'psi'))
        
        if self.clamp_press_str.get()!=myStr:
            self.clamp_press_str.set(myStr)

    def set_cur_input_press(self, cur_press_psi):
        myStr = "{:.1f}".format(float(cur_press_psi))
        if self.input_press_str.get() != myStr:
            self.input_press_str.set(myStr)
    
    def set_cur_dia(self, cur_dia_mm):
        if cur_dia_mm is None:
            myStr = ""
        elif(self.cv.CurDiaUnits=='inch'):
            myStr = "{:2.3f}".format(self.cv.to_cur_dia_units(cur_dia_mm,"mm"))
        else:
            myStr = "{:3.2f}".format(self.cv.to_cur_dia_units(cur_dia_mm,"mm"))
        if self.cur_dia_mm_str.get()!=myStr:
            self.cur_dia_mm_str.set(myStr)
       
    def set_cur_pos(self, cur_pos_mm):
        if cur_pos_mm is None:
            myStr = ""
        else:
            if self.cv.CurPosUnits == 'inch':
                myStr = "{:2.3f}".format(self.cv.to_cur_pos_units(cur_pos_mm, "mm"))
            else:
                myStr = "{:3.2f}".format(self.cv.to_cur_pos_units(cur_pos_mm, 'mm'))

        if self.cur_pos_str.get() != myStr:
            self.cur_pos_str.set(myStr)



    def bal_target_press_call(self, target_press):
        #COM_DATA.target_balloon_pressure = round(float(target_press))
        if(self.cv.CurBalUnits=='psi'):
            #COM_DATA.target_balloon_pressure = round(float(target_press))
            myStr = "{:3.1f} ".format(self.cv.to_cur_bal_units(float(target_press),'psi'))
            COM_DATA.target_balloon_pressure = float(myStr)
        else:
            #COM_DATA.target_balloon_pressure = float(target_press)
            myStr = "{:2.1f} ".format(self.cv.to_cur_bal_units(float(target_press),'psi'))

            COM_DATA.target_balloon_pressure = self.cv.cnvrt_press_units(float(myStr),self.cv.CurBalUnits,'psi')
            
        if self.bal_trgt_press_str.get()!=myStr:
            self.bal_trgt_press_str.set(myStr)


    def clamp_target_press_call(self, target_press):
        #COM_DATA.target_chuck_pressure = round(float(target_press))
        if(self.cv.CurClampUnits=='psi'):
            myStr = "{:3.0f} ".format(self.cv.to_cur_clamp_units(float(target_press),'psi'))
            COM_DATA.target_chuck_pressure = float(myStr)
        else:
            myStr = "{:2.1f} ".format(self.cv.to_cur_clamp_units(float(target_press),'psi'))
            COM_DATA.target_chuck_pressure = self.cv.cnvrt_press_units(float(myStr),self.cv.CurClampUnits,'psi')
            
        if self.clamp_trgt_press_str.get()!=myStr:
            self.clamp_trgt_press_str.set(myStr)



    def bal_ref_press_call(self, target_press):
        myStr = "{:3.2f} ".format(float(target_press))
        if self.bal_ref_press_str.get()!=myStr:
            self.bal_ref_press_str.set(myStr)
        COM_DATA.balloon_reference_pressure = float(target_press)   

    def clamp_ref_press_call(self, target_press):
        myStr = "{:3.1f} ".format(float(target_press))
        if self.clamp_ref_press_str.get()!=myStr:
            self.clamp_ref_press_str.set(myStr)
        COM_DATA.chuck_reference_pressure = float(target_press)   


    def callback_bal_units(self):
        self.cv.set_cur_bal_units(self.v_bal_units.get())
        self.cur_bal_press_frm.config(text="Current Balloon Pressure ("+self.cv.get_cur_bal_units()+")")
        self.trgt_bal_press_frm.config(text="Balloon Pressure Target ("+self.cv.get_cur_bal_units()+")")
        self.bal_target_press_call( self.v_bal_target_press.get())
        
    def callback_dia_units(self):
        self.cv.set_cur_dia_units(self.v_dia_units.get())
        self.cur_dia_frm.config(text="Current Diameter ("+self.cv.get_cur_dia_units()+")")
       
    def callback_clamp_units(self):
        self.cv.set_cur_clamp_units(self.v_clamp_units.get())
        self.cur_clamp_press_frm.config(text="Current Chuck Pressure ("+self.cv.get_cur_clamp_units()+")")
        self.trgt_c_press_frm.config(text="Chuck Pressure Target ("+self.cv.get_cur_clamp_units()+")")
        self.clamp_target_press_call(self.v_clamp_target_press.get())
        
    def callback_pos_units(self):       
        self.cv.set_cur_pos_units(self.v_pos_units.get())
        self.cur_position_frm.config(text="Current Position ("+self.cv.get_cur_pos_units()+")")
    
    def callback_bal_track_en(self):
        COM_DATA.enable_balloon_tracking  = self.bal_track_checked.get()
        if(self.bal_track_checked.get()):
            self.bal_sol_track_checked.set(False)
            self.bal_cal_checked.set(False)
            COM_DATA.enable_balloon_SV = self.bal_sol_track_checked.get()
            COM_DATA.enable_balloon_cal = self.bal_cal_checked.get()
           
    def callback_clamp_track_en(self):
        COM_DATA.enable_chuck_tracking  = self.clamp_track_checked.get()
        if(self.clamp_track_checked.get()):
            self.clamp_sol_track_checked.set(False)
            self.clamp_cal_checked.set(False)
            COM_DATA.enable_chuck_SV = self.clamp_sol_track_checked.get()
            COM_DATA.enable_chuck_cal = self.clamp_cal_checked.get()
           
    def callback_right_clamp_cb(self):
        COM_DATA.right_chuck = 1   # toggle chuck
       
    def callback_left_clamp_cb(self):
        COM_DATA.left_chuck = 1    # toggle chuck
        
    def callback_bal_sol_en(self):
        COM_DATA.enable_balloon_SV = self.bal_sol_track_checked.get()
        if(self.bal_sol_track_checked.get()):
            self.bal_track_checked.set(False)
            self.bal_cal_checked.set(False)
            COM_DATA.enable_balloon_cal = self.bal_cal_checked.get()
            COM_DATA.enable_balloon_tracking  = self.bal_track_checked.get()
        
        

    def callback_bal_press_sol(self, scale_value):
        COM_DATA.balloon_SV3_pressure_percent_on= self.v_bal_press_sol.get()
  
    def callback_bal_relief_sol(self, scale_value):
        COM_DATA.balloon_SV5_relief_percent_on= self.v_bal_relief_sol.get()
  
 
    def callback_clamp_sol_en(self):
        COM_DATA.enable_chuck_SV = self.clamp_sol_track_checked.get()
        if(self.clamp_sol_track_checked.get()):
            self.clamp_track_checked.set(False)
            self.clamp_cal_checked.set(False)
            COM_DATA.enable_chuck_cal = self.clamp_cal_checked.get()
            COM_DATA.enable_chuck_tracking  = self.clamp_track_checked.get()

            
        
    def callback_chuck_press_sol(self, scale_value):
        COM_DATA.chuck_SV4_pressure_percent_on = self.v_clamp_press_sol.get()
        
        #if(self.v_clamp_press_sol.get()):
        #    self.clamp_track_checked.set(False)
        #    self.clamp_cal_checked.set(False)

    def callback_chuck_relief_sol(self, scale_value):
        COM_DATA.chuck_SV6_relief_percent_on= self.v_clamp_relief_sol.get()
  
    def callback_bal_cal_cb(self):
        COM_DATA.enable_balloon_cal = self.bal_cal_checked.get()
        #self.bal_cal_checked.set(False)
        if(self.bal_cal_checked.get()):
            self.bal_track_checked.set(False)
            self.bal_sol_track_checked.set(False)
            COM_DATA.enable_balloon_SV = self.bal_sol_track_checked.get()
            COM_DATA.enable_balloon_tracking  = self.bal_track_checked.get()
        
        
    
    def callback_bal_cal_store(self):
        COM_DATA.balloon_cal_button = 1

    def callback_bal_cal_rb(self): 
        if(self.v_bal_cal_rb.get()=="scale"):
            COM_DATA.scale_balloon_pressure = 1
            if(self.bal_cal_checked.get()):
                self.bal_track_checked.set(True)
                self.clamp_track_checked.set('True')
                COM_DATA.enable_balloon_tracking  = self.bal_track_checked.get()
        else:
            COM_DATA.scale_balloon_pressure = 0
            if(self.bal_cal_checked.get()):
                self.bal_track_checked.set(False)
                COM_DATA.enable_balloon_tracking  = self.bal_track_checked.get()
          
                    
        if(self.v_bal_cal_rb.get()=="zero"):
            COM_DATA.zero_balloon_pressure = 1
        else:
            COM_DATA.zero_balloon_pressure = 0
        
    def callback_clamp_cal_cb(self):
        COM_DATA.enable_chuck_cal = self.clamp_cal_checked.get()
        if(self.clamp_cal_checked.get()):
            self.clamp_track_checked.set(False)
            self.clamp_sol_track_checked.set(False)
            self.v_clamp_cal_rb.set("zero")
            COM_DATA.enable_chuck_SV = self.clamp_sol_track_checked.get()
            COM_DATA.enable_chuck_tracking  = self.clamp_track_checked.get()


            
    def callback_clamp_cal_store(self):
        COM_DATA.chuck_cal_button = 1
       
    def callback_clamp_cal_rb(self):
        if(self.v_clamp_cal_rb.get()=="scale"):
            COM_DATA.scale_chuck_pressure = 1
            if(self.clamp_cal_checked.get()):
                self.clamp_track_checked.set(True)
                COM_DATA.enable_chuck_tracking  = self.clamp_track_checked.get()
        else:
            COM_DATA.scale_chuck_pressure = 0
            if(self.clamp_cal_checked.get()):
                self.clamp_track_checked.set(False)
                COM_DATA.enable_chuck_tracking  = self.clamp_track_checked.get()

                    
        if(self.v_clamp_cal_rb.get()=="zero"):
            COM_DATA.zero_chuck_pressure = 1
        else:
            COM_DATA.zero_chuck_pressure = 0
            COM_DATA.enable_chuck_tracking  = self.clamp_track_checked.get()
        
    def set_cur_rt_clamp(self,mitutoyo_button):
        pass

    def set_cur_lft_clamp(self,diameter_button):
        pass

   
        


  



'''
if __name__ == "__main__":
    app = RcSetupPage2App()
    app.run()
'''