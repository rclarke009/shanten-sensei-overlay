"""Tests for collapsible play toolbars geometry helper."""

from gui.utils import window_size, TOOLBAR_COLLAPSE_DELTA
from common.lan_str import LanStr, LanStrZHS


def test_window_size_compact_default():
    assert window_size(True, False) == (480, 520)


def test_window_size_full_default():
    assert window_size(False, False) == (620, 620)


def test_window_size_shrinks_when_toolbars_hidden():
    w, h = window_size(True, True)
    assert w == 480
    assert h == 520 - TOOLBAR_COLLAPSE_DELTA
    assert h >= 300


def test_window_size_full_shrinks_when_toolbars_hidden():
    w, h = window_size(False, True)
    assert w == 620
    assert h == 620 - TOOLBAR_COLLAPSE_DELTA


def test_controls_strings_present():
    assert "Controls" in LanStr.CONTROLS_SHOW
    assert "Controls" in LanStr.CONTROLS_HIDE
    assert LanStrZHS.CONTROLS_SHOW
    assert LanStrZHS.CONTROLS_HIDE
