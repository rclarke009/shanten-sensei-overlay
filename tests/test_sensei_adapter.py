"""Adapter tests — requires shanten_sensei installed editable next door."""

from types import SimpleNamespace

from sensei_adapter import (
    SENSEI_AVAILABLE,
    SenseiCoach,
    build_turn,
    status_line_from_features,
    status_line_from_turn,
)
from sensei_mode import classify_mode
from shanten_sensei.features import extract_features

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

# 11 closed tiles after chi (pre-discard)
OPEN_HAND_11 = [
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
    "7s",
]
OPEN_CALL = {"type": "chi", "pai": "5s", "consumed": ["3s", "4s"]}


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
        my_calls=[],
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


def test_sync_with_reaction_clears_stale():
    coach = SenseiCoach()
    reaction_a = {
        "type": "dahai",
        "pai": "9p",
        "meta_options": [("9p", 0.8), ("5s", 0.2)],
    }
    reaction_b = {
        "type": "dahai",
        "pai": "5s",
        "meta_options": [("5s", 0.7), ("9p", 0.3)],
    }
    gi = _gi()
    friend = classify_mode(category=1, room_id=1)
    result = coach.explain_why(reaction_a, gi, None, friend, use_llm=False)
    assert result.ok is True
    assert coach.sync_with_reaction(reaction_a, gi) is True
    assert coach.sync_with_reaction(reaction_b, gi) is False
    assert coach.last_result is None
    assert coach.sync_with_reaction(None, gi) is False
    assert coach.last_result is None


def test_score_tips_flag_busts_why_cache():
    coach = SenseiCoach()
    reaction = {
        "type": "dahai",
        "pai": "9p",
        "meta_options": [("9p", 0.8), ("5s", 0.2)],
    }
    gi = _gi()
    friend = classify_mode(category=1, room_id=1)
    result = coach.explain_why(
        reaction, gi, None, friend, use_llm=False, include_score_tips=False
    )
    assert result.ok is True
    assert coach.sync_with_reaction(reaction, gi, include_score_tips=False) is True
    assert coach.sync_with_reaction(reaction, gi, include_score_tips=True) is False
    assert coach.last_result is None


def test_build_turn_with_open_calls_avoids_shanten_sentinel():
    reaction = {
        "type": "dahai",
        "actor": 0,
        "pai": "9p",
        "meta_options": [("9p", 0.9), ("7s", 0.1)],
    }
    gi = _gi(my_tehai=OPEN_HAND_11, my_tsumohai=None, my_calls=[OPEN_CALL])
    turn = build_turn(reaction, gi, game_state=None)
    assert turn.features.shanten < 8
    assert turn.features.statuses.menzen is False
    line = status_line_from_turn(turn)
    assert "shanten 8" not in line
    assert "hand sync" not in line
    assert "open" in line


def test_status_line_hides_shanten_sentinel():
    short = list(OPEN_HAND_11)
    feats = extract_features(short)
    assert feats.shanten == 8
    assert status_line_from_features(feats) == "hand sync · status unavailable"


def test_coach_skips_why_when_dahai_not_in_hand():
    coach = SenseiCoach()
    reaction = {
        "type": "dahai",
        "pai": "P",  # Haku — not in LIVE_HAND_13 + 7s
        "meta_options": [("P", 0.8), ("9p", 0.2)],
    }
    gi = _gi()
    friend = classify_mode(category=1, room_id=1)
    result = coach.explain_why(reaction, gi, None, friend, use_llm=False)
    assert result.ok is False
    assert "not in hand" in (result.error or "").lower()
    assert result.summary == ""


def test_coach_skips_why_when_shanten_sentinel():
    coach = SenseiCoach()
    reaction = {
        "type": "dahai",
        "pai": "9p",
        "meta_options": [("9p", 0.9), ("7s", 0.1)],
    }
    # Short closed hand, no calls → features.shanten sentinel 8
    gi = _gi(my_tehai=OPEN_HAND_11, my_tsumohai=None, my_calls=[])
    friend = classify_mode(category=1, room_id=1)
    result = coach.explain_why(reaction, gi, None, friend, use_llm=False)
    assert result.ok is False
    assert "sync" in (result.error or "").lower()
    assert result.summary == ""
    assert result.status_line == "hand sync · status unavailable"
