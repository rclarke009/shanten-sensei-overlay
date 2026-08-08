"""Aiming-for strip, reason log, and river wiring for SenseiCoach."""

from types import SimpleNamespace

import pytest

from sensei_adapter import (
    SENSEI_AVAILABLE,
    SenseiCoach,
    build_turn,
    player_discards_from_game_state,
    visible_discards_from_game_state,
)
from sensei_mode import classify_mode

pytestmark = pytest.mark.skipif(
    not SENSEI_AVAILABLE, reason="shanten_sensei not installed"
)

LIVE_HAND_14 = [
    "1m", "2m", "3m", "4m", "5m", "6m",
    "1p", "2p", "3p", "9p",
    "4s", "5s", "6s", "7s",
]


def _gi(**kwargs):
    base = dict(
        bakaze="E",
        jikaze="E",
        kyoku=1,
        honba=0,
        my_tehai=LIVE_HAND_14[:-1],
        my_tsumohai=LIVE_HAND_14[-1],
        self_reached=False,
        self_seat=0,
        player_reached=[False, False, False, False],
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def _reaction(pai="9p"):
    return {
        "type": "dahai",
        "pai": pai,
        "meta_options": [(pai, 0.8), ("5s", 0.2)],
    }


def test_visible_discards_from_game_state():
    gs = SimpleNamespace(
        get_visible_discards=lambda: {"1": ["4s", "4s"]},
    )
    assert visible_discards_from_game_state(gs) == {"1": ["4s", "4s"]}

    ks = SimpleNamespace(rivers=[[], ["4s"], [], []])
    gs2 = SimpleNamespace(kyoku_state=ks)
    assert visible_discards_from_game_state(gs2)["1"] == ["4s"]


def test_build_turn_rivers_adjust_ukeire():
    gi = _gi()
    ks = SimpleNamespace(
        rivers=[[], ["4s", "4s"], [], []],
        doras_ms=[],
    )
    gs = SimpleNamespace(
        kyoku_state=ks,
        player_scores=[25000, 25000, 25000, 25000],
        get_visible_discards=lambda: {"1": ["4s", "4s"]},
    )
    turn = build_turn(_reaction("9p"), gi, game_state=gs)
    assert turn.features.ukeire.count == 4
    assert turn.features.ukeire.remaining_by_tile["4s"] == 1
    assert turn.game_state.visible_discards["1"] == ["4s", "4s"]


def test_player_discards_from_game_state_uses_self_seat():
    gi = _gi(self_seat=2)
    gs = SimpleNamespace(
        get_visible_discards=lambda: {
            "0": ["1m"],
            "2": ["7s", "5p"],
        },
        seat=2,
    )
    assert player_discards_from_game_state(gs, gi) == ["7s", "5p"]


def test_build_turn_passes_player_river_for_furiten():
    # LIVE_HAND_14 cuts 9p → waits 4s/7s; seat 0 river has 7s → furiten.
    gi = _gi(self_seat=0)
    gs = SimpleNamespace(
        seat=0,
        kyoku_state=SimpleNamespace(rivers=[["7s"], ["4s", "4s"], [], []], doras_ms=[]),
        player_scores=[25000, 25000, 25000, 25000],
        get_visible_discards=lambda: {"0": ["7s"], "1": ["4s", "4s"]},
    )
    turn = build_turn(_reaction("9p"), gi, game_state=gs)
    assert turn.game_state.discards == ["7s"]
    assert turn.features.statuses.furiten is True


def test_refresh_board_features_sets_aiming():
    coach = SenseiCoach()
    gi = _gi()
    coach.refresh_board_features(gi, None, _reaction())
    assert coach.last_aiming_for
    assert coach.last_status_line
    assert "shanten" in coach.last_status_line


def test_reason_log_appends_and_clears_on_kyoku():
    coach = SenseiCoach()
    friend = classify_mode(category=1, room_id=1)
    gi1 = _gi(kyoku=1, honba=0)
    r1 = coach.explain_why(_reaction("9p"), gi1, None, friend, use_llm=False)
    assert r1.ok
    assert len(coach.reason_log) == 1
    assert coach.reason_log[0].summary == r1.summary

    # Cache hit does not double-append
    coach.explain_why(_reaction("9p"), gi1, None, friend, use_llm=False)
    assert len(coach.reason_log) == 1

    # New tip within same kyoku appends
    coach.sync_with_reaction(_reaction("5s"), gi1)
    r2 = coach.explain_why(_reaction("5s"), gi1, None, friend, use_llm=False)
    assert r2.ok
    assert len(coach.reason_log) == 2

    # New kyoku clears log
    gi2 = _gi(kyoku=2, honba=0)
    coach.refresh_board_features(gi2, None, None)
    assert coach.reason_log == []


def test_leave_game_clears_reason_log():
    coach = SenseiCoach()
    friend = classify_mode(category=1, room_id=1)
    gi = _gi()
    coach.explain_why(_reaction("9p"), gi, None, friend, use_llm=False)
    assert coach.reason_log
    coach.refresh_board_features(None, None, None)
    assert coach.reason_log == []
    assert coach.last_aiming_for is None
