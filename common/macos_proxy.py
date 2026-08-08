"""macOS PAC-scoped system proxy for Safari companion mode.

Routes Majsoul-related hosts to local mitmproxy; everything else DIRECT.
Serves the PAC over http://127.0.0.1 (Safari often ignores file:// PAC URLs).
Non-Darwin callers get a clear error from enable().
"""

from __future__ import annotations

import atexit
import pathlib
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional
from urllib.parse import urlparse

from common.log_helper import LOGGER
from common.utils import MAJSOUL_DOMAINS, Folder, sub_file

RunFn = Callable[..., subprocess.CompletedProcess]


class SafariProxyError(Exception):
    """Failed to apply or remove the macOS auto-proxy / PAC."""


def build_pac_contents(mitm_port: int, domains: list[str] | None = None) -> str:
    """Return a PAC script that proxies matching Majsoul hosts to 127.0.0.1:port."""
    domains = list(MAJSOUL_DOMAINS if domains is None else domains)
    checks: list[str] = []
    for d in domains:
        d = d.strip().lower()
        if not d:
            continue
        checks.append(f'dnsDomainIs(host, "{d}") || host == "{d}"')
    if not checks:
        raise ValueError("PAC requires at least one domain")
    condition = " ||\n        ".join(checks)
    return f"""// Shanten Sensei — Majsoul-only PAC (do not leave enabled after coaching)
function FindProxyForURL(url, host) {{
    host = host.toLowerCase();
    if (
        {condition}
    ) {{
        return "PROXY 127.0.0.1:{int(mitm_port)}";
    }}
    return "DIRECT";
}}
"""


def pac_matches_host(pac_text: str, host: str) -> bool:
    """True if build_pac_contents-style PAC would proxy this host (static parse)."""
    host = host.lower().strip()
    domains = set(re.findall(r'dnsDomainIs\(host,\s*"([^"]+)"\)', pac_text))
    domains.update(re.findall(r'host\s*==\s*"([^"]+)"', pac_text))
    for d in domains:
        d = d.lower()
        if host == d or host.endswith("." + d):
            return True
    return False


def _default_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
        **kwargs,
    )


def list_network_services(run: RunFn = _default_run) -> list[str]:
    """Return networksetup service names (skip the asterisk header line)."""
    p = run(["networksetup", "-listallnetworkservices"])
    if p.returncode != 0:
        raise SafariProxyError(
            f"networksetup -listallnetworkservices failed: {p.stderr or p.stdout}"
        )
    services: list[str] = []
    for line in (p.stdout or "").splitlines():
        line = line.strip()
        if not line or line.startswith("An asterisk"):
            continue
        if line.startswith("*"):
            line = line.lstrip("*").strip()
        services.append(line)
    return services


def pick_network_services(run: RunFn = _default_run) -> list[str]:
    """Prefer Wi-Fi / Ethernet-like services; fall back to all hardware services."""
    services = list_network_services(run)
    preferred = [
        s
        for s in services
        if any(
            key in s.lower()
            for key in ("wi-fi", "wifi", "ethernet", "thunderbolt", "usb")
        )
    ]
    return preferred or services


@dataclass
class _ServiceProxyState:
    name: str
    url: str = ""
    enabled: bool = False


class _PacRequestHandler(BaseHTTPRequestHandler):
    """Serves a single PAC body for Auto Proxy Discovery."""

    pac_body: bytes = b""

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/sensei-majsoul.pac", "/proxy.pac", "/wpad.dat"):
            body = type(self).pac_body
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def log_message(self, fmt: str, *args) -> None:
        LOGGER.debug("PAC HTTP: " + fmt, *args)


@dataclass
class MacOSProxySession:
    """Apply/restore auto-proxy PAC for Safari companion mode."""

    mitm_port: int
    domains: list[str] = field(default_factory=lambda: list(MAJSOUL_DOMAINS))
    pac_path: Optional[pathlib.Path] = None
    pac_http_port: Optional[int] = None
    run: RunFn = field(default=_default_run)
    _previous: list[_ServiceProxyState] = field(default_factory=list)
    _enabled: bool = False
    _atexit_registered: bool = False
    _httpd: Optional[ThreadingHTTPServer] = None
    _http_thread: Optional[threading.Thread] = None
    _pac_url: str = ""

    def write_pac(self) -> pathlib.Path:
        path = self.pac_path or pathlib.Path(
            sub_file(Folder.MITM_CONF, "sensei-majsoul.pac")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            build_pac_contents(self.mitm_port, self.domains), encoding="utf-8"
        )
        self.pac_path = path
        return path

    def _start_pac_http(self) -> str:
        """Serve PAC over loopback HTTP; return the URL for networksetup."""
        path = self.write_pac()
        body = path.read_bytes()
        port = int(self.pac_http_port or (self.mitm_port + 1))

        handler = type(
            "BoundPacHandler",
            (_PacRequestHandler,),
            {"pac_body": body},
        )
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
        except OSError as e:
            raise SafariProxyError(
                f"Could not bind PAC HTTP server on 127.0.0.1:{port}: {e}"
            ) from e

        thread = threading.Thread(
            target=httpd.serve_forever,
            name="SenseiPacHttp",
            daemon=True,
        )
        thread.start()
        self._httpd = httpd
        self._http_thread = thread
        self.pac_http_port = port
        self._pac_url = f"http://127.0.0.1:{port}/sensei-majsoul.pac"
        LOGGER.info("PAC HTTP server listening at %s", self._pac_url)
        return self._pac_url

    def _stop_pac_http(self) -> None:
        if self._httpd is not None:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception as e:  # pylint: disable=broad-exception-caught
                LOGGER.warning("PAC HTTP shutdown: %s", e)
            self._httpd = None
            self._http_thread = None

    def _get_autoproxy(self, service: str) -> _ServiceProxyState:
        p = self.run(["networksetup", "-getautoproxyurl", service])
        url = ""
        enabled = False
        for line in (p.stdout or "").splitlines():
            lower = line.lower().strip()
            if lower.startswith("url:"):
                url = line.split(":", 1)[1].strip()
            elif lower.startswith("enabled:"):
                enabled = "yes" in lower
        return _ServiceProxyState(name=service, url=url, enabled=enabled)

    def enable(self) -> None:
        if sys.platform != "darwin":
            raise SafariProxyError(
                "Safari companion mode requires macOS (networksetup / PAC)."
            )
        pac_url = self._start_pac_http()
        services = pick_network_services(self.run)
        if not services:
            self._stop_pac_http()
            raise SafariProxyError("No network services found for PAC apply.")

        previous: list[_ServiceProxyState] = []
        errors: list[str] = []
        for service in services:
            previous.append(self._get_autoproxy(service))
            set_url = self.run(
                ["networksetup", "-setautoproxyurl", service, pac_url]
            )
            set_on = self.run(
                ["networksetup", "-setautoproxystate", service, "on"]
            )
            if set_url.returncode != 0 or set_on.returncode != 0:
                err = (set_url.stderr or set_url.stdout or "") + (
                    set_on.stderr or set_on.stdout or ""
                )
                errors.append(f"{service}: {err.strip()}")
        if errors and len(errors) == len(services):
            self._stop_pac_http()
            raise SafariProxyError(
                "Failed to enable auto-proxy on all services: " + "; ".join(errors)
            )
        if errors:
            LOGGER.warning("Partial PAC apply: %s", "; ".join(errors))

        self._previous = previous
        self._enabled = True
        if not self._atexit_registered:
            atexit.register(self.disable)
            self._atexit_registered = True
        LOGGER.info(
            "Safari PAC enabled on %s → %s",
            ", ".join(s.name for s in previous),
            pac_url,
        )

    def disable(self) -> None:
        """Restore previous auto-proxy settings (best effort)."""
        if not self._enabled and not self._previous:
            self._stop_pac_http()
            return
        if sys.platform != "darwin":
            self._enabled = False
            self._previous = []
            self._stop_pac_http()
            return

        for state in self._previous:
            try:
                if state.url and not _is_our_pac_url(state.url, self.pac_path):
                    self.run(
                        ["networksetup", "-setautoproxyurl", state.name, state.url]
                    )
                    self.run(
                        [
                            "networksetup",
                            "-setautoproxystate",
                            state.name,
                            "on" if state.enabled else "off",
                        ]
                    )
                else:
                    self.run(
                        ["networksetup", "-setautoproxystate", state.name, "off"]
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                LOGGER.warning("Failed restoring proxy for %s: %s", state.name, e)

        self._stop_pac_http()
        self._enabled = False
        self._previous = []
        self._pac_url = ""
        LOGGER.info("Safari PAC disabled / restored")


def _is_our_pac_url(url: str, pac_path: Optional[pathlib.Path]) -> bool:
    if not url:
        return False
    lower = url.lower()
    if "sensei-majsoul.pac" in lower or "127.0.0.1" in lower and "pac" in lower:
        return True
    if not pac_path:
        return False
    try:
        return pathlib.Path(urlparse(url).path) == pac_path.resolve()
    except Exception:  # pylint: disable=broad-exception-caught
        return "sensei-majsoul.pac" in url


def manual_disable_hint() -> str:
    """User-facing commands if the app crashes with PAC still on."""
    return (
        "If browsing is broken after a crash, turn off Auto Proxy:\n"
        '  networksetup -setautoproxystate "Wi-Fi" off\n'
        '  networksetup -setautoproxystate "Ethernet" off\n'
        "(Use your real service name from: networksetup -listallnetworkservices)\n"
        "Also turn off iCloud Private Relay while coaching (it can bypass proxies)."
    )
