"""Wi-Fi HTTP Excel transfer server owned by the Recurve UI.

Serves GET /last_row with the same OK/ERR tab-separated Bass-320 payload used
by USB COM. See docs/wifi_http_excel_transfer.md.
"""

from __future__ import annotations

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional
from urllib.parse import urlparse

from app_config import WIFI_HTTP_HOST, WIFI_HTTP_PORT
from bass320_transfer import (
    format_err_response,
    handle_get_last_row_command,
)


def get_lan_ip_address() -> str:
    """Best-effort LAN IPv4 for status display (not the bind address)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
        finally:
            sock.close()
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass
    return "0.0.0.0"


class WifiHttpTransferServer:
    """Background HTTP server: GET /last_row → OK\\tv1…v8 or ERR\\tmessage."""

    def __init__(
        self,
        tree_provider: Callable,
        cone_flip_provider: Callable[[], bool],
        host: str = WIFI_HTTP_HOST,
        port: int = WIFI_HTTP_PORT,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        self._tree_provider = tree_provider
        self._cone_flip_provider = cone_flip_provider
        self.host = host
        self.port = int(port)
        self._status_callback = status_callback
        self._thread: Optional[threading.Thread] = None
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._lock = threading.Lock()
        self._running = False
        self._last_status = "Wi-Fi off"

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

    def handle_last_row(self) -> str:
        """Return protocol line without trailing newline (testable)."""
        try:
            tree = self._tree_provider()
            cone_flip = bool(self._cone_flip_provider())
            return handle_get_last_row_command(tree, cone_flip=cone_flip)
        except Exception as exc:
            return format_err_response(str(exc) or "handler error")

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._running = True
            self._set_status("Waiting")
            self._thread = threading.Thread(
                target=self._run,
                name="wifi-http-transfer",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._running = False
            httpd = self._httpd
            thread = self._thread
        if httpd is not None:
            try:
                httpd.shutdown()
            except Exception:
                pass
            try:
                httpd.server_close()
            except Exception:
                pass
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            self._httpd = None
            self._thread = None
        self._set_status("Wi-Fi off")

    def _run(self) -> None:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):  # noqa: A003
                return

            def do_GET(self):  # noqa: N802
                path = urlparse(self.path).path.rstrip("/") or "/"
                if path != "/last_row":
                    body = format_err_response("Not found")
                    raw = (body + "\n").encode("utf-8")
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                    return
                body = outer.handle_last_row()
                raw = (body + "\n").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(raw)
                if body.startswith("OK"):
                    outer._set_status("Connected")
                elif "No data" in body:
                    outer._set_status("No data")
                else:
                    outer._set_status("Connected")

        try:
            httpd = ThreadingHTTPServer((self.host, self.port), Handler)
            with self._lock:
                self._httpd = httpd
            self._set_status("Connected")
            httpd.serve_forever(poll_interval=0.5)
        except OSError:
            if self._running:
                self._set_status("Waiting")
        finally:
            with self._lock:
                self._httpd = None
            if self._running:
                self._set_status("Wi-Fi off")
            self._running = False
