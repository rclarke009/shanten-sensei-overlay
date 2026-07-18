"""Unit tests for practice / ranked mode gate (no Majsoul required)."""

from sensei_mode import (
    ModePolicy,
    classify_from_game_config,
    classify_mode,
    parse_auth_meta,
)


def test_ranked_category_restricted():
    v = classify_mode(category=2, mode_id=9, room_id=0)
    assert v.policy == ModePolicy.RESTRICTED
    assert not v.why_enabled


def test_friend_category_allowed():
    v = classify_mode(category=1, mode_id=0, room_id=12345)
    assert v.policy == ModePolicy.ALLOWED
    assert v.why_enabled


def test_room_id_allows_without_category():
    v = classify_mode(category=None, room_id=42)
    assert v.policy == ModePolicy.ALLOWED


def test_unknown_restricted():
    v = classify_mode()
    assert v.policy == ModePolicy.RESTRICTED
    assert "unknown" in v.reason


def test_parse_auth_meta_friend():
    cfg = {"meta": {"modeId": 0, "category": 1, "roomId": 999}}
    mode_id, category, room_id = parse_auth_meta(cfg)
    assert mode_id == 0
    assert category == 1
    assert room_id == 999
    v = classify_from_game_config(cfg)
    assert v.why_enabled


def test_parse_auth_meta_ranked():
    cfg = {"meta": {"modeId": 12, "category": 2, "roomId": 0}}
    v = classify_from_game_config(cfg)
    assert v.policy == ModePolicy.RESTRICTED
