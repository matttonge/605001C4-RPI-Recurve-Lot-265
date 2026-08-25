import os
import serial
import time
import struct
import threading
import math
from conversions import CONVERSIONS
from app_config import (
    SERIAL_BAUDRATE,
    SERIAL_WINDOWS_PORT,
    SERIAL_LINUX_PORT,
    SERIAL_INIT_SLEEP_SEC,
    SERIAL_DEINIT_SLEEP_SEC,
    SERIAL_TICK_SLEEP_SEC,
    POS_STALE_SEC,
    DIA_STALE_SEC,
)
import platform


def resolve_serial_port():
    """Port for Pico telemetry. Override with env RECURVE_SERIAL_PORT (e.g. /dev/ttyACM0)."""
    override = os.environ.get("RECURVE_SERIAL_PORT", "").strip()
    if override:
        return override
    if platform.system() == "Windows":
        return SERIAL_WINDOWS_PORT
    return SERIAL_LINUX_PORT 

TELEMETRY_FORMAT = 'fffbb13sbfbb10s'
TELEMETRY_PACKET_SIZE = struct.calcsize(TELEMETRY_FORMAT)

def _is_missing_serial_port(exc):
    if getattr(exc, "errno", None) == 2:
        return True
    text = str(exc).lower()
    return "no such file" in text or "file not found" in text

"""
current_balloon_pressure = float(0.0)
current_clamp_pressure   = float(0.1)
right_clamp_state        = bool(False)  # set=1;  off=0;
left_clamp_state         = bool(True)  # set=1;  off=0;
mitutoyo_val             = bytearray(b"1234567890123")
mitutoyo_button          = bool(False)
diameter_val             = float(0.2)
diameter_button          = bool(True)   
k=0
"""
        


class COM_DATA:
    """Pico to computer"""
    current_balloon_pressure = float(0.0)
    current_clamp_pressure   = float(0.1)
    current_input_pressure   = float(0.0)
    right_chuck_state        = bool(False)  # set=1;  off=0;
    left_chuck_state         = bool(False)  # set=1;  off=0;
    mitutoyo_val             = bytearray(b"             ")
    right_clamp_state         = bool(False)
    diameter_val             = float("nan")
    left_clamp_state         = bool(False)
    get_data                 = bool(False)  
    version                  = bytearray(b"----------")
    """Computer to pico"""
    
    enable_balloon_tracking = int(0)  # 1 enable balloon pressure tracking
    target_balloon_pressure = float(0.0)   # 0 - max pressure in psi (150)
        
    enable_chuck_tracking = int(0)  # # 1 enable chuck pressure tracking
    target_chuck_pressure = float(0.0)     # 0 - max pressure in psi (150)
       
    right_chuck = int(0)   # proximal chuck  toggle=1;  no_action=0
    left_chuck = int(0)    # distal chuck    toggle=1;  no_action=0
        
    enable_balloon_SV = int(0)  # 1 enable balloon pressure solenoid valve tracking
    balloon_SV3_pressure_percent_on = float(0.0)   # 0 - 100.0 %
    balloon_SV5_relief_percent_on = float(0.0)   # 0 - 100.0 %
        
    enable_chuck_SV = int(0)  # 1 enable chuck pressure solenoid valve tracking
    chuck_SV4_pressure_percent_on = float(0.0)   # 0 - 100.0 %
    chuck_SV6_relief_percent_on = float(0.0)   # 0 - 100.0 %
        
    enable_balloon_cal = int(0)  # 1 start zero 
    zero_balloon_pressure = int(0)  #   zero 
    scale_balloon_pressure = int(0)  #   scale 
    balloon_cal_button = int(0)  # 1 start scale of zero
    balloon_reference_pressure = float(0.0)   # 0 - max pressure in psi (150)
        
    enable_chuck_cal = int(0)  # 1 start zero 
    zero_chuck_pressure = int(0)  # 1 start zero 
    scale_chuck_pressure = int(0)  # 1 start zero 
    chuck_cal_button = int(0)  # 1 start zero 
    chuck_reference_pressure = float(0.0)   # 0 - max pressure in psi (150)
    
    right_clamp = int(0)   # proximal clamp    toggle=1;  no_action=0
    left_clamp = int(0)    # distal clamp  toggle=1;  no_action=0
    
    mode = int(0)  # 0=load 1=auto 2= manual 
    k=0
    
    def __init__(self,master=None):
        
        self.master=master
        self.cvrt = CONVERSIONS()
        self.ser = None
        self._serial_warn_at = 0.0
        self.serial_run = True
        self._last_valid_pos_time = None
        self._last_valid_dia_time = None
        self._pressure_telemetry_seen = False
        self._try_open_serial()
        self.t=threading.Thread(target = self.tick, daemon=True)
        self.t.start()

    def _try_open_serial(self):
        """Open Pico telemetry. Missing/unplugged port is normal on Ubuntu without hardware."""
        if self.ser is not None and getattr(self.ser, "is_open", False):
            return True
        port = resolve_serial_port()
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=SERIAL_BAUDRATE,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            print(f"[serial] opened {port}")
            return True
        except (serial.SerialException, OSError) as exc:
            self.ser = None
            now = time.time()
            if _is_missing_serial_port(exc):
                if self._serial_warn_at == 0.0:
                    print(
                        f"[serial] {port} not present (no Pico/FTDI). "
                        "UI running; will connect when the device appears."
                    )
                    self._serial_warn_at = now
            elif now - self._serial_warn_at >= 5.0:
                print(f"[serial] waiting for {port}: {exc}")
                self._serial_warn_at = now
            return False

    def deinit(self):
        self.serial_run = False 
        time.sleep(SERIAL_DEINIT_SLEEP_SEC)
        ser = self.ser
        if ser is not None:
            try:
                ser.close()
            except (serial.SerialException, OSError):
                pass
        self.ser = None 
         
    def set_master(self,master):
        self.master=master

    @staticmethod
    def _invoke_master(master, name, *args):
        if master is None:
            return
        fn = getattr(master, name, None)
        if callable(fn):
            fn(*args)

    def _update_position(self):
        master = self.master
        if master is None:
            return
        t = self.cvrt.mit_val_to_position(COM_DATA.mitutoyo_val, "mm")
        if t is not None:
            self._last_valid_pos_time = time.time()
            self._invoke_master(master, "set_cur_pos", abs(t))

    def _check_pos_stale(self):
        master = self.master
        if master is None or self._last_valid_pos_time is None:
            return
        if time.time() - self._last_valid_pos_time > POS_STALE_SEC:
            self._invoke_master(master, "set_cur_pos", None)
            self._last_valid_pos_time = None

    @staticmethod
    def _is_valid_dia(val):
        if val is None or math.isnan(val):
            return False
        return val >= 0

    def _update_diameter(self):
        master = self.master
        if master is None:
            return
        if self._is_valid_dia(COM_DATA.diameter_val):
            self._last_valid_dia_time = time.time()
            self._invoke_master(master, "set_cur_dia", COM_DATA.diameter_val)

    def _check_dia_stale(self):
        master = self.master
        if master is None or self._last_valid_dia_time is None:
            return
        if time.time() - self._last_valid_dia_time > DIA_STALE_SEC:
            self._invoke_master(master, "set_cur_dia", None)
            self._last_valid_dia_time = None

    def _update_pressure(self):
        master = self.master
        if master is None or not self._pressure_telemetry_seen:
            return
        self._invoke_master(master, "set_cur_press", COM_DATA.current_balloon_pressure)
        self._invoke_master(master, "set_cur_clamp_press", COM_DATA.current_clamp_pressure)

    def _push_state_to_master(self):
        # Snapshot: Setup sets master=None while this thread is mid-packet.
        master = self.master
        if master is None:
            return
        self._update_pressure()
        self._update_diameter()
        self._update_position()
        self._invoke_master(master, "set_cur_input_press", COM_DATA.current_input_pressure)
        self._invoke_master(master, "set_cur_rt_chuck", COM_DATA.right_chuck_state)
        self._invoke_master(master, "set_cur_lft_chuck", COM_DATA.left_chuck_state)
        self._invoke_master(master, "set_cur_rt_clamp", COM_DATA.right_clamp_state)
        self._invoke_master(master, "set_cur_lft_clamp", COM_DATA.left_clamp_state)
        if COM_DATA.get_data:
            self._invoke_master(master, "callback_get_data")
            COM_DATA.get_data = False

    def uart0_send(self):
      #  buf=struct.pack('ffiiii', self.target_balloon_pressure, self.target_chuck_pressure, self.right_chuck,
      #                  self.left_chuck, self.zero_balloon_pressure, self.zero_chuck_pressure)
        buf=struct.pack('ififiiiffiffiiiifiiiifiii', COM_DATA.enable_balloon_tracking, COM_DATA.target_balloon_pressure, COM_DATA.enable_chuck_tracking, COM_DATA.target_chuck_pressure, 
                                                COM_DATA.right_chuck, COM_DATA.left_chuck, 
                                                COM_DATA.enable_balloon_SV, COM_DATA.balloon_SV3_pressure_percent_on, COM_DATA.balloon_SV5_relief_percent_on,
                                                COM_DATA.enable_chuck_SV, COM_DATA.chuck_SV4_pressure_percent_on, COM_DATA.chuck_SV6_relief_percent_on,
                                                COM_DATA.enable_balloon_cal, COM_DATA.zero_balloon_pressure, COM_DATA.scale_balloon_pressure, COM_DATA.balloon_cal_button, COM_DATA.balloon_reference_pressure, 
                                                COM_DATA.enable_chuck_cal, COM_DATA.zero_chuck_pressure, COM_DATA.scale_chuck_pressure, COM_DATA.chuck_cal_button, COM_DATA.chuck_reference_pressure,
                                                COM_DATA.mode, COM_DATA.right_clamp, COM_DATA.left_clamp)
        if self.ser is None:
            return
        try:
            self.ser.write(buf)
        except (serial.SerialException, OSError, TypeError) as exc:
            print(f"[serial] write error: {exc}")
            self.ser = None
            return
      #  print(COM_DATA.target_balloon_pressure)
      #  print(buf)
        if(COM_DATA.right_chuck==1):   # toggle commands 
             COM_DATA.right_chuck=2 
        if(COM_DATA.left_chuck==1): 
            COM_DATA.left_chuck = 2
        if(COM_DATA.right_clamp==1): 
             COM_DATA.right_clamp=2 
        if(COM_DATA.left_clamp==1): 
            COM_DATA.left_clamp = 2

        COM_DATA.balloon_cal_button = 0
        COM_DATA.chuck_cal_button = 0
       
       

    def tick(self):
        off_on_str = ["OFF","ON"]
        time.sleep(SERIAL_INIT_SLEEP_SEC)
        #self.master.zero_SV()
        
      
        while self.serial_run:
          #  print(str(self.ser.in_waiting))
            if self.ser is None:
                self._try_open_serial()
                time.sleep(SERIAL_TICK_SLEEP_SEC)
                continue
            try:
                in_waiting = self.ser.in_waiting
            except (serial.SerialException, OSError, TypeError, AttributeError) as exc:
                # Seen on Linux when USB serial momentarily drops/invalidates.
                print(f"[serial] in_waiting error: {exc}")
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None
                time.sleep(0.25)
                continue

            if in_waiting > TELEMETRY_PACKET_SIZE:
                try:
                    self.ser.read_all()
                except (serial.SerialException, OSError, TypeError) as exc:
                    print(f"[serial] read_all error: {exc}")
                    time.sleep(0.25)
                    continue
                
            if in_waiting == TELEMETRY_PACKET_SIZE:
               # print(self.ser.in_waiting) 
                try:
                    buf = self.ser.read(TELEMETRY_PACKET_SIZE)
                    ubuf = struct.unpack(TELEMETRY_FORMAT, buf)
                except (serial.SerialException, OSError, TypeError, struct.error) as exc:
                    print(f"[serial] packet read/unpack error: {exc}")
                    time.sleep(0.25)
                    continue
                COM_DATA.current_balloon_pressure   = ubuf[0]
                COM_DATA.current_clamp_pressure     = ubuf[1]
                COM_DATA.current_input_pressure     = ubuf[2]
                COM_DATA.right_chuck_state          = ubuf[3]
                COM_DATA.left_chuck_state           = ubuf[4]
                COM_DATA.mitutoyo_val               = ubuf[5]
                COM_DATA.right_clamp_state          = ubuf[6]
                COM_DATA.diameter_val               = ubuf[7]
                COM_DATA.left_clamp_state           = ubuf[8]   
                COM_DATA.get_data                   = ubuf[9]   
                COM_DATA.version                    = ubuf[10]    
                COM_DATA.k=COM_DATA.k+1
                self._pressure_telemetry_seen = True
                #print(buf)
                     
                self._push_state_to_master()

                if(COM_DATA.right_chuck==2): 
                    COM_DATA.right_chuck= 0
                if(COM_DATA.left_chuck==2): 
                    COM_DATA.left_chuck = 0
                if(COM_DATA.right_clamp==2): 
                    COM_DATA.right_clamp= 0
                if(COM_DATA.left_clamp==2): 
                    COM_DATA.left_clamp = 0
                
                
                """
                myStr = "Balloon Pressure \t\t{:4.1f} \tpsi\n\n".format(COM_DATA.current_balloon_pressure)
                myStr += "Clamp Pressure \t\t{:3.1f} \tpsi\n".format(COM_DATA.current_clamp_pressure)
                myStr += "Right Chuck \t\t"+off_on_str[COM_DATA.right_clamp_state]+"\n"
                myStr += "Left Chuck  \t\t"+off_on_str[COM_DATA.left_clamp_state]+"\n\n"
                myStr += ("Mitutoyo Reading\t\t" + str(COM_DATA.mitutoyo_val).strip("b.'").lstrip()+"\n")
                myStr += ("Mitutoyo Store\t\t"+off_on_str[COM_DATA.mitutoyo_button]+"\n\n")
                myStr += ("Diameter Reading\t\t{:2.3f} mm".format(COM_DATA.diameter_val)+"\n")
                myStr += ("Diameter Store\t\t"+off_on_str[COM_DATA.diameter_button])            
                """
                
                self.uart0_send()
            self._check_pos_stale()
            self._check_dia_stale()
            time.sleep(SERIAL_TICK_SLEEP_SEC) 
    
    

    