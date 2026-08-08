"""Quit Safari and reopen Majsoul for Safari companion reconnect."""

from __future__ import annotations

import subprocess
import sys
import time
from typing import Callable

from common.log_helper import LOGGER

RunFn = Callable[..., subprocess.CompletedProcess]


class SafariReconnectError(Exception):
    """Failed to quit Safari and reopen Majsoul."""


def _default_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
        **kwargs,
    )


def quit_safari_and_open(
    url: str,
    *,
    run: RunFn = _default_run,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    """Quit Safari entirely, wait briefly, then open Majsoul in a fresh window."""
    if sys.platform != "darwin":
        raise SafariReconnectError("Safari reconnect requires macOS.")
    url = (url or "").strip()
    if not url:
        raise SafariReconnectError("Majsoul URL is empty.")

    LOGGER.info("Quitting Safari for reconnect")
    quit_result = run(["osascript", "-e", 'tell application "Safari" to quit'])
    if quit_result.returncode != 0:
        LOGGER.warning(
            "Safari quit returned %s: %s",
            quit_result.returncode,
            quit_result.stderr or quit_result.stdout,
        )

    sleep_fn(0.75)

    LOGGER.info("Opening Majsoul in Safari: %s", url)
    open_result = run(["open", "-a", "Safari", url])
    if open_result.returncode != 0:
        raise SafariReconnectError(
            f"open -a Safari failed: {open_result.stderr or open_result.stdout}"
        )
