"""Mahjong glyph font family follows the host OS."""

import sys

import pytest

pytest.importorskip("PIL")

from gui.utils import GuiStyle


def test_tile_font_family_has_mahjong_block():
    family = GuiStyle().tile_font_family()
    if sys.platform == "darwin":
        assert family == "Apple Symbols"
    else:
        assert family == "Segoe UI Emoji"
    font = GuiStyle().font_tile(14)
    assert font[0] == family
    assert font[1] == 14
