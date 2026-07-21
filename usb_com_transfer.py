"""USB CDC ACM (COM) Excel transfer server owned by the Recurve UI.

Design choice: the running UI owns /dev/ttyGS0 in a daemon thread so GET_LAST_ROW
can read the live tree without a separate IPC process. Gadget bring-up is handled
by tools/setup_usb_serial_gadget.sh (+ systemd unit). See docs/usb_com_excel_transfer.md.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from app_config import (
    USB_COM_BAUDRATE,
    USB_COM_DEVICE,
    USB_COM_OPEN_RETRY_SEC,
)
from bass320_transfer import (
    format_err_response,
    handle_get_last_row_command,
    parse_request_line,
)

try:
    import serial
    from serial import SerialException
except ImportError:  # pragma: no cover - unit tests mock without pyserial
    serial = None
    SerialException = OSError


class UsbComTransferServer:
    """Line-based serial server: PC sends GET_LAST_ROW, Pi replies OK/ERR."""

    def __init__(
        self,
        tree_provider: Callable,
        cone_flip_provider: Callable[[], bool],
        device: str = USB_COM_DEVICE,
        baudrate: int = USB_COM_BAUDRATE,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        self._tree_provider = tree_provider
        self._cone_flip_provider = cone_flip_provider
        self.device = device
        self.baudrate = baudrate
        self._status_callback = status_callback
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._running = False
        self._last_status = "USB off"

    @property
    def running(self) -> bool:
        return self._running

    @property
    def last_status(self) -> str:
        return self._last_status

    def _set_status(self, status: str) -> None:
        self._last_status = status
        cb = self._status_callback
        if cb is not None:
            try:
                cb(status)
            except Exception:
                pass

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._running = True
            self._set_status("Waiting")
            self._thread = threading.Thread(
                target=self._run,
                name="usb-com-transfer",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            self._running = False
            thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            self._thread = None
        self._set_status("USB off")

    def _open_serial(self):
        if serial is None:
            raise RuntimeError("pyserial is not installed")
        return serial.Serial(
            port=self.device,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.25,
            write_timeout=1.0,
        )

    def _handle_line(self, line: str) -> str:
        cmd = parse_request_line(line)
        if not cmd:
            return ""
        if cmd != "GET_LAST_ROW":
            return format_err_response(f"Unknown command: {cmd}")
        try:
            tree = self._tree_provider()
            cone_flip = bool(self._cone_flip_provider())
            return handle_get_last_row_command(tree, cone_flip=cone_flip)
        except Exception as exc:
            return format_err_response(str(exc) or "handler error")

    def _run(self) -> None:
        while not self._stop.is_set():
            ser = None
            try:
                ser = self._open_serial()
                self._set_status("Connected")
                buf = bytearray()
                while not self._stop.is_set():
                    try:
                        chunk = ser.read(256)
                    except SerialException:
                        break
                    if not chunk:
                        continue
                    buf.extend(chunk)
                    while True:
                        nl = buf.find(b"\n")
                        if nl < 0:
                            break
                        raw = bytes(buf[:nl])
                        del buf[: nl + 1]
                        if raw.endswith(b"\r"):
                            raw = raw[:-1]
                        reply = self._handle_line(raw.decode("utf-8", errors="replace"))
                        if not reply:
                            continue
                        try:
                            ser.write((reply + "\n").encode("utf-8"))
                            ser.flush()
                        except SerialException:
                            raise
            except (SerialException, OSError, RuntimeError, ValueError) as exc:
                if self._stop.is_set():
                    break
                # Port may appear only after PC cable plug / gadget load.
                self._set_status("Waiting")
                time.sleep(USB_COM_OPEN_RETRY_SEC)
                _ = exc
            finally:
                if ser is not None:
                    try:
                        ser.close()
                    except Exception:
                        pass
        if not self._stop.is_set():
            self._set_status("USB off")
