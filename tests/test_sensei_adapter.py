"""Adapter tests — requires shanten_sensei installed editable next door."""

from types import SimpleNamespace

from sensei_adapter import SENSEI_AVAILABLE, SenseiCoach, build_turn, status_line_from_turn
from sensei_mode import classify_mode

import pytest

pytestmark = pytest.mark.skipif(
    not SENSEI_AVAILABLE, reason="shanten_sensei not installed"
)

LIVE_HAND_13 = [
    "1m",
    "2m",
    "3m",
    "4m",
    "5m",
    "6m",
    "1p",
    "2p",
    "3p",
    "9p",
    "4s",
    "5s",
    "6s",
]


def _gi(**kwargs):
    """Minimal GameInfo-shaped object (avoids importing numpy via mj_helper)."""
    base = dict(
        bakaze="E",
        jikaze="E",
        kyoku=0,
        honba=0,
        my_tehai=LIVE_HAND_13,
        my_tsumohai="7s",
        self_reached=False,
        self_seat=0,
        player_reached=[False, False, False, False],
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_build_turn_pending():
    reaction = {
        "type": "dahai",
        "actor": 0,
        "pai": "9p",
        "meta_options": [("9p", 0.75), ("5s", 0.25)],
    }
    gi = _gi()
    turn = build_turn(reaction, gi, game_state=None)
    assert turn.diverge is False
    assert turn.mortal_best == "dahai 9p"
    assert turn.player_action == "dahai 9p"
    assert turn.source == "live-copilot"
    line = status_line_from_turn(turn)
    assert "shanten" in line


def test_coach_blocks_ranked():
    coach = SenseiCoach()
    reaction = {
        "type": "dahai",
        "pai": "9p",
        "meta_options": [("9p", 1.0)],
    }
    gi = _gi()
    ranked = classify_mode(category=2)
    result = coach.explain_why(reaction, gi, None, ranked, use_llm=False)
    assert result.ok is False
    assert "ranked" in (result.error or "").lower() or "段位" in (result.error or "")


def test_coach_explains_friend():
    coach = SenseiCoach()
    reaction = {
        "type": "dahai",
        "pai": "9p",
        "meta_options": [("9p", 0.8), ("5s", 0.2)],
    }
    gi = _gi()
    friend = classify_mode(category=1, room_id=1)
    result = coach.explain_why(reaction, gi, None, friend, use_llm=False)
    assert result.ok is True
    assert result.pinned_action == "dahai 9p"
    assert result.summary
    # cache hit
    result2 = coach.explain_why(reaction, gi, None, friend, use_llm=False)
    assert result2.summary == result.summary
