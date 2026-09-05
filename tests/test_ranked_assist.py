"""Ranked/unknown hard-stop: no HUD, Autoplay, or Auto Join."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from bot_manager import BotManager
from common.lan_str import LanStr
from sensei_mode import classify_mode


class _FakeGameState:
    def __init__(self, verdict):
        self._verdict = verdict

    def get_mode_verdict(self):
        return self._verdict


def _bare_manager(*, verdict=None, in_game=True):
    bm = BotManager.__new__(BotManager)
    bm.st = SimpleNamespace(
        enable_automation=False,
        auto_join_game=True,
        known_terms=[],
        auto_why=False,
        score_tips=False,
        table_tips=False,
        lan=LanStr,
    )
    bm.game_state = _FakeGameState(verdict) if in_game else None
    bm.automation = MagicMock()
    bm.automation.is_running_execution.return_value = False
    bm.sensei = MagicMock()
    bm.sensei.last_status_line = "2-shanten"
    bm.sensei.last_aiming_for = "tanyao"
    bm.sensei.last_result = SimpleNamespace(ok=True, summary="Throw 9-pin", error=None)
    bm.browser = MagicMock()
    return bm


def test_ranked_enable_automation_refused():
    bm = _bare_manager(verdict=classify_mode(category=2))
    assert bm.enable_automation() is False
    assert bm.st.enable_automation is False


def test_friend_enable_automation_ok():
    bm = _bare_manager(verdict=classify_mode(category=1, room_id=1))
    assert bm.enable_automation() is True
    assert bm.st.enable_automation is True


def test_lobby_enable_automation_ok():
    bm = _bare_manager(in_game=False)
    assert bm.enable_automation() is True
    assert bm.st.enable_automation is True


def test_restricted_lock_turns_autoplay_off():
    bm = _bare_manager(verdict=classify_mode(category=2))
    bm.st.enable_automation = True
    bm.apply_restricted_mode_lock()
    assert bm.st.enable_automation is False
    bm.automation.stop_previous.assert_called()
    assert bm.st.auto_join_game is False


def test_do_automation_skips_ranked():
    bm = _bare_manager(verdict=classify_mode(category=2))
    bm.st.enable_automation = True
    assert bm._do_automation({"type": "dahai", "pai": "9p"}) is False
    bm.automation.automate_action.assert_not_called()


def test_do_automation_runs_friend():
    bm = _bare_manager(verdict=classify_mode(category=1, room_id=1))
    bm._do_automation({"type": "dahai", "pai": "9p"})
    bm.automation.automate_action.assert_called_once()


def test_overlay_guide_clears_when_restricted():
    bm = _bare_manager(verdict=classify_mode())
    bm._update_overlay_guide()
    bm.browser.overlay_clear_guidance.assert_called()
    bm.browser.overlay_update_guidance.assert_not_called()


def test_enable_autojoin_always_refused():
    bm = _bare_manager(verdict=classify_mode(category=1, room_id=1))
    assert bm.enable_autojoin() is False
    assert bm.st.auto_join_game is False


def test_refresh_board_features_clears_when_restricted():
    bm = _bare_manager(verdict=classify_mode(category=2))
    bm.refresh_board_features()
    assert bm.sensei.last_status_line is None
    assert bm.sensei.last_aiming_for is None
    bm.sensei.refresh_board_features.assert_not_called()


def test_why_disabled_copy():
    assert LanStr.WHY_DISABLED == "Coaching disabled in this mode"
