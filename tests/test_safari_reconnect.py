"""Tests for Safari companion reconnect helper."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from common.lan_str import LanStr, LanStrZHS
from common.safari_reconnect import SafariReconnectError, quit_safari_and_open
from common.utils import error_to_str


def test_quit_safari_and_open_runs_osascript_then_open(monkeypatch):
    calls: list[list[str]] = []
    sleeps: list[float] = []

    def run(cmd, **_kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(sys, "platform", "darwin")
    quit_safari_and_open(
        "https://mahjongsoul.game.yo-star.com/",
        run=run,
        sleep_fn=lambda s: sleeps.append(s),
    )

    assert calls == [
        ["osascript", "-e", 'tell application "Safari" to quit'],
        ["open", "-a", "Safari", "https://mahjongsoul.game.yo-star.com/"],
    ]
    assert sleeps == [0.75]


def test_quit_safari_and_open_continues_when_safari_not_running(monkeypatch):
    calls: list[list[str]] = []

    def run(cmd, **_kwargs):
        calls.append(cmd)
        if cmd[0] == "osascript":
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not running")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(sys, "platform", "darwin")
    quit_safari_and_open("https://example.test/", run=run, sleep_fn=lambda _s: None)
    assert len(calls) == 2


def test_quit_safari_and_open_raises_on_non_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(SafariReconnectError, match="macOS"):
        quit_safari_and_open("https://example.test/")


def test_quit_safari_and_open_raises_on_empty_url(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(SafariReconnectError, match="empty"):
        quit_safari_and_open("  ")


def test_quit_safari_and_open_raises_when_open_fails(monkeypatch):
    def run(cmd, **_kwargs):
        if cmd[0] == "open":
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="failed")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(SafariReconnectError, match="open -a Safari failed"):
        quit_safari_and_open("https://example.test/", run=run, sleep_fn=lambda _s: None)


def test_reconnect_safari_client_resets_flow_ids(monkeypatch):
    from bot_manager import BotManager
    from common.settings import Settings

    st = Settings()
    st.safari_mode = True
    st.ms_url = "https://mahjongsoul.game.yo-star.com/"
    bm = BotManager(st)
    bm.lobby_flow_id = "lobby-1"
    bm.game_flow_id = "game-1"
    bm.game_state = MagicMock()

    called = {"url": None}

    def fake_quit(url):
        called["url"] = url

    monkeypatch.setattr("bot_manager.quit_safari_and_open", fake_quit)
    monkeypatch.setattr(bm, "_process_end_game", MagicMock())

    bm.reconnect_safari_client()

    assert bm.lobby_flow_id is None
    assert bm.game_flow_id is None
    bm._process_end_game.assert_called_once()
    assert called["url"] == st.ms_url


def test_reconnect_safari_client_requires_safari_mode():
    from bot_manager import BotManager
    from common.settings import Settings

    st = Settings()
    st.safari_mode = False
    bm = BotManager(st)
    with pytest.raises(SafariReconnectError, match="Safari companion"):
        bm.reconnect_safari_client()


def test_lan_strings_present():
    assert "Quit Safari" in LanStr.SAFARI_RECONNECT
    assert "退出 Safari" in LanStrZHS.SAFARI_RECONNECT


def test_error_to_str_safari_reconnect():
    msg = error_to_str(SafariReconnectError("boom"), LanStr())
    assert LanStr.SAFARI_RECONNECT_ERROR in msg
    assert "boom" in msg
