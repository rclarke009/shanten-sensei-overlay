"""Tests for Safari companion PAC + macOS proxy session helpers."""

from __future__ import annotations

import pathlib
import subprocess
from unittest.mock import MagicMock

import pytest

from common.macos_proxy import (
    MacOSProxySession,
    SafariProxyError,
    build_pac_contents,
    list_network_services,
    pac_matches_host,
    pick_network_services,
)
from common.lan_str import LanStr, LanStrZHS


def test_build_pac_proxies_majsoul_hosts():
    pac = build_pac_contents(10999)
    assert "PROXY 127.0.0.1:10999" in pac
    assert "return \"DIRECT\"" in pac
    assert pac_matches_host(pac, "mahjongsoul.game.yo-star.com")
    assert pac_matches_host(pac, "game.maj-soul.com")
    assert pac_matches_host(pac, "www.mahjongsoul.com")
    assert not pac_matches_host(pac, "example.com")
    assert not pac_matches_host(pac, "google.com")


def test_build_pac_requires_domains():
    with pytest.raises(ValueError):
        build_pac_contents(10999, domains=[])


def test_list_and_pick_network_services():
    def run(cmd, **_kwargs):
        assert cmd[:2] == ["networksetup", "-listallnetworkservices"]
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout=(
                "An asterisk (*) denotes that a network service is disabled.\n"
                "Wi-Fi\n"
                "Ethernet\n"
                "iPhone USB\n"
            ),
            stderr="",
        )

    services = list_network_services(run)
    assert services == ["Wi-Fi", "Ethernet", "iPhone USB"]
    assert pick_network_services(run) == ["Wi-Fi", "Ethernet", "iPhone USB"]


def test_enable_disable_restores_previous(tmp_path: pathlib.Path, monkeypatch):
    monkeypatch.setattr("common.macos_proxy.sys.platform", "darwin")
    calls: list[list[str]] = []

    def run(cmd, **_kwargs):
        calls.append(list(cmd))
        if cmd[:2] == ["networksetup", "-listallnetworkservices"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="Wi-Fi\n", stderr=""
            )
        if cmd[:2] == ["networksetup", "-getautoproxyurl"]:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="URL: http://old.example/pac\nEnabled: Yes\n",
                stderr="",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    pac_path = tmp_path / "sensei-majsoul.pac"
    # Use an ephemeral-ish PAC HTTP port to avoid clashing with a running overlay
    session = MacOSProxySession(
        mitm_port=10999,
        pac_path=pac_path,
        pac_http_port=18999,
        run=run,
    )
    # Avoid real atexit side effects in other tests
    session._atexit_registered = True
    session.enable()

    assert pac_path.exists()
    pac_text = pac_path.read_text(encoding="utf-8")
    assert pac_matches_host(pac_text, "game.yo-star.com")
    set_url_calls = [
        c for c in calls if c[:3] == ["networksetup", "-setautoproxyurl", "Wi-Fi"]
    ]
    assert set_url_calls
    assert set_url_calls[0][3].startswith("http://127.0.0.1:18999/")
    assert ["networksetup", "-setautoproxystate", "Wi-Fi", "on"] in calls

    # PAC URL must be fetchable over HTTP (Safari ignores file://)
    import urllib.request

    with urllib.request.urlopen(set_url_calls[0][3], timeout=2) as resp:
        assert b"FindProxyForURL" in resp.read()

    session.disable()
    assert ["networksetup", "-setautoproxyurl", "Wi-Fi", "http://old.example/pac"] in calls
    assert ["networksetup", "-setautoproxystate", "Wi-Fi", "on"] in calls


def test_enable_rejects_non_darwin(monkeypatch, tmp_path):
    monkeypatch.setattr("common.macos_proxy.sys.platform", "linux")
    session = MacOSProxySession(
        mitm_port=10999,
        pac_path=tmp_path / "x.pac",
        run=MagicMock(),
    )
    with pytest.raises(SafariProxyError, match="macOS"):
        session.enable()


def test_safari_strings_present():
    assert "Safari" in LanStr.SAFARI_MODE
    assert LanStr.SAFARI_HINT
    assert LanStr.SAFARI_WAITING
    assert LanStrZHS.SAFARI_MODE
    assert LanStrZHS.SAFARI_WAITING
