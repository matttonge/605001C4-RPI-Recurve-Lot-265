"""Wi-Fi HTTP Excel transfer server owned by the Recurve UI.

Serves GET /last_row with the same OK/ERR tab-separated Bass-320 payload used
by USB COM. See docs/wifi_http_excel_transfer.md.
"""

from __future__ import annotations

import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional
from urllib.parse import urlparse

# Re-enable after Setup checkbox can race the prior socket close (EADDRINUSE).
_BIND_ATTEMPTS = 15
_BIND_RETRY_SEC = 0.1

from app_config import WIFI_HTTP_HOST, WIFI_HTTP_PORT
from bass320_transfer import (
    format_err_response,
    handle_get_last_row_command,
)


def _list_netifaces() -> list:
    try:
        return [name for _idx, name in socket.if_nameindex()]
    except (OSError, AttributeError):
        return ["wlan0", "eth0"]


def _is_wifi_iface(name: str) -> bool:
    n = (name or "").lower()
    return n.startswith("wlan") or n.startswith("wlp") or n.startswith("wl")


def _ipv4_for_iface(iface: str) -> Optional[str]:
    """Return IPv4 for a named interface (Linux ioctl); None if unavailable."""
    try:
        import fcntl
        import struct
    except ImportError:
        return None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ifreq = struct.pack("256s", iface[:15].encode("utf-8"))
            # SIOCGIFADDR
            res = fcntl.ioctl(sock.fileno(), 0x8915, ifreq)
            ip = socket.inet_ntoa(res[20:24])
        finally:
            sock.close()
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        return None
    return None


def _dedupe_preserve_order(ips: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for ip in ips:
        if ip not in seen:
            seen.add(ip)
            out.append(ip)
    return out


def _fallback_lan_ip_address() -> Optional[str]:
    """Default-route / hostname IPv4 when no iface has an address."""
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
    return None


def list_lan_ip_addresses() -> list[str]:
    """Active non-loopback IPv4s: Wi-Fi (wlan*) first, then other interfaces."""
    wifi_ips: list[str] = []
    other_ips: list[str] = []
    for name in _list_netifaces():
        ip = _ipv4_for_iface(name)
        if not ip:
            continue
        if _is_wifi_iface(name):
            wifi_ips.append(ip)
        else:
            other_ips.append(ip)
    ips = _dedupe_preserve_order(wifi_ips + other_ips)
    if ips:
        return ips
    fallback = _fallback_lan_ip_address()
    if fallback:
        return [fallback]
    return []


def format_lan_ip_status() -> str:
    """Primary Wi-Fi IP, then other active IPv4s separated by ' -- '."""
    ips = list_lan_ip_addresses()
    if not ips:
        return "0.0.0.0"
    return " -- ".join(ips)


def get_lan_ip_address() -> str:
    """Best-effort primary IPv4 for Excel BMS IP (not the bind address).

    Demo preference: Wi-Fi (wlan*) first so customer-LAN demos without ethernet
    show the correct address; fall back to default-route / any non-loopback IPv4.
    """
    ips = list_lan_ip_addresses()
    if ips:
        return ips[0]
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
        """Start the HTTP server. Safe to call after stop (Setup re-enable)."""
        with self._lock:
            if (
                self._running
                and self._thread is not None
                and self._thread.is_alive()
                and self._httpd is not None
            ):
                return
            need_stop = self._thread is not None and self._thread.is_alive()
        # Tear down any half-dead listener before binding again.
        if need_stop:
            self.stop()
        with self._lock:
            if (
                self._running
                and self._thread is not None
                and self._thread.is_alive()
                and self._httpd is not None
            ):
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
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        with self._lock:
            self._httpd = None
            self._thread = None
        self._set_status("Wi-Fi off")

    def _run(self) -> None:
        outer = self
        httpd: Optional[ThreadingHTTPServer] = None

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
            for _attempt in range(_BIND_ATTEMPTS):
                if not self._running:
                    return
                try:
                    httpd = ThreadingHTTPServer((self.host, self.port), Handler)
                    break
                except OSError:
                    time.sleep(_BIND_RETRY_SEC)
            if httpd is None:
                if self._running:
                    self._set_status("Waiting")
                return
            with self._lock:
                self._httpd = httpd
            self._set_status("Connected")
            httpd.serve_forever(poll_interval=0.5)
        finally:
            if httpd is not None:
                try:
                    httpd.server_close()
                except Exception:
                    pass
            with self._lock:
                if self._httpd is httpd:
                    self._httpd = None
            was_running = self._running
            self._running = False
            # Bind failure leaves status as Waiting; don't clobber it to off.
            if was_running and httpd is not None:
                self._set_status("Wi-Fi off")
