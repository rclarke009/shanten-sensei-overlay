"""Bridge MahjongCopilot live state → Shanten Sensei explain()."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sensei_mode import ModeVerdict, PRACTICE_BANNER

try:
    from common.log_helper import LOGGER, dt_string
    from common.utils import Folder, sub_file
except ImportError:  # pragma: no cover
    import logging

    LOGGER = logging.getLogger("sensei_adapter")

    def dt_string() -> str:
        import datetime

        return datetime.datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")

    class Folder:  # type: ignore
        LOG = "log"

    def sub_file(folder: str, name: str) -> str:
        import os

        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, name)


try:
    from shanten_sensei.explain import explain
    from shanten_sensei.features import extract_features
    from shanten_sensei.glosses import (
        format_aiming_for,
        glossed_furiten,
        glossed_ukeire_count,
    )
    from shanten_sensei.live import candidates_from_meta_options, turn_from_live
    from shanten_sensei.schema import Explanation, TurnExplainInput

    SENSEI_AVAILABLE = True
except ImportError as e:  # pragma: no cover - depends on local install
    LOGGER.warning("shanten_sensei not installed: %s", e)
    SENSEI_AVAILABLE = False
    Explanation = Any  # type: ignore
    TurnExplainInput = Any  # type: ignore

    def glossed_furiten(  # type: ignore
        *,
        furiten: bool = False,
        temporary: bool = False,
        known_terms=None,
    ) -> str:
        if temporary:
            return "temp furiten"
        return "furiten" if furiten else "not furiten"

    def glossed_ukeire_count(count: int, *, known_terms=None) -> str:  # type: ignore
        return f"ukeire {count}"

    def format_aiming_for(shape_goals, *, known_terms=None) -> str:  # type: ignore
        goals = [g for g in (shape_goals or []) if g]
        return " / ".join(goals) if goals else "no clear yaku shape yet"


def _cvt_ms2mjai(ms_tile: str) -> str:
    try:
        from common.mj_helper import cvt_ms2mjai

        return cvt_ms2mjai(ms_tile)
    except Exception:
        return ms_tile


@dataclass
class WhyResult:
    ok: bool
    summary: str
    pinned_action: str | None = None
    status_line: str | None = None
    aiming_for: str | None = None
    source: str = "template"
    error: str | None = None


@dataclass
class ReasonLogEntry:
    kyoku: int | None
    honba: int | None
    pinned_action: str | None
    summary: str
    source: str


def status_line_from_features(
    features: Any, *, known_terms: list[str] | tuple[str, ...] | None = None
) -> str:
    # Sentinel from features._shanten_with_melds when closed+melds ≠ 13/14.
    if getattr(features, "shanten", None) == 8:
        return "hand sync · status unavailable"
    st = features.statuses
    parts = [
        f"shanten {features.shanten}",
        glossed_ukeire_count(features.ukeire.count, known_terms=known_terms),
    ]
    if st.tenpai:
        parts.append("tenpai")
        if st.wait_shape:
            parts.append(st.wait_shape)
    if st.temporary_furiten:
        parts.append(glossed_furiten(temporary=True, known_terms=known_terms))
    elif st.furiten:
        parts.append(glossed_furiten(furiten=True, known_terms=known_terms))
    if st.riichi:
        parts.append("riichi")
    if not st.menzen:
        parts.append("open")
    if st.dora_in_hand:
        parts.append("dora:" + ",".join(st.dora_in_hand[:3]))
    return " · ".join(parts)


def calls_from_game_info(gi: Any, game_state=None) -> list[dict]:
    """Player open melds for Sensei (GameInfo.my_calls, else kyoku_state)."""
    calls = getattr(gi, "my_calls", None) if gi is not None else None
    if calls:
        return list(calls)
    if game_state is not None:
        ks = getattr(game_state, "kyoku_state", None)
        if ks is not None:
            return list(getattr(ks, "my_calls", None) or [])
    return []


def _tile_missing_from_hand(tile: str, hand: list[str]) -> bool:
    """True when tile (aka-aware) is not among hand tiles."""
    if not SENSEI_AVAILABLE or not tile or not hand:
        return False
    try:
        from shanten_sensei.tiles import deaka, normalize_tile
    except ImportError:  # pragma: no cover
        return False
    want = deaka(normalize_tile(tile))
    return not any(deaka(normalize_tile(t)) == want for t in hand)


def _dahai_reaction_missing_from_hand(reaction: dict, game_info: Any) -> bool:
    """True when a dahai reaction's pai is not in the current hand."""
    if (reaction.get("type") or "") != "dahai":
        return False
    pai = reaction.get("pai")
    if not pai:
        return False
    return _tile_missing_from_hand(str(pai), hand_tiles_from_game_info(game_info))


def status_line_from_turn(
    turn: TurnExplainInput, *, known_terms: list[str] | tuple[str, ...] | None = None
) -> str:
    return status_line_from_features(turn.features, known_terms=known_terms)


def hand_tiles_from_game_info(gi: Any) -> list[str]:
    if gi is None or not getattr(gi, "my_tehai", None):
        return []
    hand = list(gi.my_tehai)
    tsumo = getattr(gi, "my_tsumohai", None)
    if tsumo:
        hand = hand + [tsumo]
    return hand


def dora_indicators_from_game_state(game_state) -> list[str]:
    """Convert Majsoul dora markers stored on kyoku_state to mjai tiles."""
    doras_ms = getattr(getattr(game_state, "kyoku_state", None), "doras_ms", None) or []
    out: list[str] = []
    for d in doras_ms:
        try:
            # doras_ms may already be mjai (start_kyoku path stores mjai in first slot
            # then later overwrites with raw ms strings — normalize both)
            if isinstance(d, str) and len(d) <= 3 and not d.isdigit():
                # try as mjai first; cvt may fail
                if d[-1:] in "mpsz" or d in "ESWNPFC" or d.endswith("r"):
                    out.append(d)
                    continue
            out.append(_cvt_ms2mjai(d))
        except Exception:
            if isinstance(d, str):
                out.append(d)
    return out


def visible_discards_from_game_state(game_state) -> dict[str, list[str]]:
    if game_state is None:
        return {}
    getter = getattr(game_state, "get_visible_discards", None)
    if callable(getter):
        return getter()
    ks = getattr(game_state, "kyoku_state", None)
    rivers = getattr(ks, "rivers", None) if ks is not None else None
    if not rivers:
        return {}
    return {str(i): list(r) for i, r in enumerate(rivers) if r}


def player_discards_from_game_state(game_state, game_info=None) -> list[str]:
    """Player's own river (for furiten), keyed by self_seat / game_state.seat."""
    visible = visible_discards_from_game_state(game_state)
    seat = None
    if game_info is not None:
        seat = getattr(game_info, "self_seat", None)
    if seat is None and game_state is not None:
        seat = getattr(game_state, "seat", None)
    if seat is None:
        return []
    return list(visible.get(str(seat), []))


def build_turn(
    reaction: dict,
    game_info: Any,
    game_state=None,
) -> TurnExplainInput:
    if not SENSEI_AVAILABLE:
        raise RuntimeError("shanten_sensei package not installed")

    hand = hand_tiles_from_game_info(game_info)
    if not hand:
        raise ValueError("no hand available for explain")

    meta_options = reaction.get("meta_options") or []
    candidates = candidates_from_meta_options(meta_options)

    kyoku = game_info.kyoku if game_info else None
    honba = game_info.honba if game_info else None
    riichi = bool(game_info.self_reached) if game_info else False
    riichi_flags = list(game_info.player_reached) if game_info else []
    self_seat = getattr(game_info, "self_seat", None)

    scores = None
    if game_state is not None and getattr(game_state, "player_scores", None):
        scores = list(game_state.player_scores)

    dora = dora_indicators_from_game_state(game_state) if game_state is not None else []
    visible = visible_discards_from_game_state(game_state)
    discards = player_discards_from_game_state(game_state, game_info)

    call_tile = reaction.get("pai")
    call_consumed = reaction.get("consumed")
    if isinstance(call_consumed, list):
        call_consumed = list(call_consumed)
    else:
        call_consumed = None

    return turn_from_live(
        hand=hand,
        recommended=reaction,
        candidates=candidates,
        calls=calls_from_game_info(game_info, game_state),
        discards=discards,
        dora_indicators=dora,
        visible_discards=visible,
        turn=None,
        honba=honba,
        scores=scores,
        kyoku=kyoku,
        riichi=riichi,
        riichi_flags=riichi_flags,
        diverge=False,
        source="live-copilot",
        call_tile=str(call_tile) if call_tile else None,
        call_consumed=call_consumed,
        player_seat=self_seat,
        context={
            "bakaze": getattr(game_info, "bakaze", None),
            "jikaze": getattr(game_info, "jikaze", None),
            "call_tile": str(call_tile) if call_tile else None,
            "self_seat": self_seat,
        },
    )


class SenseiCoach:
    """On-demand Why? with per-turn cache, aiming strip, and reason journal."""

    def __init__(self) -> None:
        self._cache_key: tuple | None = None
        self._cache_result: WhyResult | None = None
        self.last_result: WhyResult | None = None
        self.last_status_line: str | None = None
        self.last_aiming_for: str | None = None
        self.reason_log: list[ReasonLogEntry] = []
        self._last_kyoku_key: tuple | None = None
        self._coach_log_path: str | None = None

    def clear(self) -> None:
        self._cache_key = None
        self._cache_result = None
        self.last_result = None
        self.last_status_line = None
        # Keep aiming_for + reason_log across tip changes within a kyoku

    def clear_reason_log(self) -> None:
        self.reason_log = []
        self._reason_log_len_shown = 0

    def _kyoku_key(self, game_info: Any) -> tuple | None:
        if game_info is None:
            return None
        return (
            getattr(game_info, "bakaze", None),
            getattr(game_info, "kyoku", None),
            getattr(game_info, "honba", None),
        )

    def _maybe_roll_kyoku(self, game_info: Any) -> None:
        key = self._kyoku_key(game_info)
        if game_info is None:
            if self._last_kyoku_key is not None:
                self.clear_reason_log()
                self.last_aiming_for = None
                self.last_status_line = None
                self._last_kyoku_key = None
            return
        if self._last_kyoku_key is not None and key != self._last_kyoku_key:
            self.clear_reason_log()
        self._last_kyoku_key = key

    def _append_reason(self, entry: ReasonLogEntry) -> None:
        self.reason_log.append(entry)
        try:
            if self._coach_log_path is None:
                self._coach_log_path = sub_file(Folder.LOG, f"coach_{dt_string()}.jsonl")
            with open(self._coach_log_path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "kyoku": entry.kyoku,
                            "honba": entry.honba,
                            "pinned_action": entry.pinned_action,
                            "summary": entry.summary,
                            "source": entry.source,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception as e:  # pragma: no cover
            LOGGER.warning("Failed to append coach JSONL: %s", e)

    def refresh_board_features(
        self,
        game_info: Any,
        game_state=None,
        reaction: dict | None = None,
        *,
        known_terms: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        """Update Aiming-for + status from hand/rivers without calling the LLM."""
        self._maybe_roll_kyoku(game_info)
        if not SENSEI_AVAILABLE or game_info is None:
            return
        hand = hand_tiles_from_game_info(game_info)
        if not hand:
            return
        try:
            if reaction:
                turn = build_turn(reaction, game_info, game_state)
                self.last_status_line = status_line_from_turn(
                    turn, known_terms=known_terms
                )
                self.last_aiming_for = format_aiming_for(
                    turn.features.shape_goals, known_terms=known_terms
                )
            else:
                feats = extract_features(
                    hand,
                    calls=calls_from_game_info(game_info, game_state),
                    discards=player_discards_from_game_state(game_state, game_info),
                    visible_discards=visible_discards_from_game_state(game_state),
                    dora_indicators=dora_indicators_from_game_state(game_state)
                    if game_state is not None
                    else [],
                    riichi=bool(getattr(game_info, "self_reached", False)),
                    context={
                        "bakaze": getattr(game_info, "bakaze", None),
                        "jikaze": getattr(game_info, "jikaze", None),
                        "self_seat": getattr(game_info, "self_seat", None),
                    },
                )
                self.last_status_line = status_line_from_features(
                    feats, known_terms=known_terms
                )
                self.last_aiming_for = format_aiming_for(
                    feats.shape_goals, known_terms=known_terms
                )
        except Exception as e:
            LOGGER.error("Sensei board refresh failed: %s", e, exc_info=True)

    def _key(
        self,
        reaction: dict,
        game_info: Any,
        *,
        include_score_tips: bool = False,
        known_terms: list[str] | tuple[str, ...] | None = None,
    ) -> tuple:
        kyoku = getattr(game_info, "kyoku", None) if game_info else None
        honba = getattr(game_info, "honba", None) if game_info else None
        known_key = tuple(sorted(known_terms or ()))
        return (
            kyoku,
            honba,
            reaction.get("type"),
            reaction.get("pai"),
            tuple(reaction.get("consumed") or ()),
            bool(include_score_tips),
            known_key,
        )

    def sync_with_reaction(
        self,
        reaction: dict | None,
        game_info: Any,
        *,
        include_score_tips: bool = False,
        known_terms: list[str] | tuple[str, ...] | None = None,
    ) -> bool:
        """Clear Why if reaction is gone or key differs. Returns True if still current."""
        if not reaction:
            if (
                self.last_result is not None
                or self._cache_key is not None
            ):
                self.clear()
            return False
        key = self._key(
            reaction,
            game_info,
            include_score_tips=include_score_tips,
            known_terms=known_terms,
        )
        if self._cache_key is not None and key != self._cache_key:
            self.clear()
            return False
        return self._cache_key == key and self.last_result is not None

    def explain_why(
        self,
        reaction: dict | None,
        game_info: Any,
        game_state,
        mode: ModeVerdict,
        *,
        use_llm: bool | None = None,
        include_score_tips: bool = False,
        known_terms: list[str] | tuple[str, ...] | None = None,
    ) -> WhyResult:
        self._maybe_roll_kyoku(game_info)
        if not SENSEI_AVAILABLE:
            return WhyResult(
                ok=False,
                summary="",
                error="Install shanten-sensei: pip install 'shanten-sensei>=0.1.0'",
            )
        if not mode.why_enabled:
            return WhyResult(
                ok=False,
                summary="",
                error=f"{PRACTICE_BANNER} (blocked: {mode.reason})",
            )
        if not reaction:
            return WhyResult(ok=False, summary="", error="No pending Mortal recommendation")

        key = self._key(
            reaction,
            game_info,
            include_score_tips=include_score_tips,
            known_terms=known_terms,
        )
        if key == self._cache_key and self._cache_result is not None:
            self.last_result = self._cache_result
            return self._cache_result

        if _dahai_reaction_missing_from_hand(reaction, game_info):
            self.refresh_board_features(
                game_info, game_state, reaction=None, known_terms=known_terms
            )
            result = WhyResult(
                ok=False,
                summary="",
                pinned_action=f"dahai {reaction.get('pai')}",
                status_line=self.last_status_line,
                aiming_for=self.last_aiming_for,
                error="Recommended discard not in hand",
            )
            self._cache_key = key
            self._cache_result = result
            self.last_result = result
            return result

        try:
            turn = build_turn(reaction, game_info, game_state)
            status = status_line_from_turn(turn, known_terms=known_terms)
            aiming = format_aiming_for(
                turn.features.shape_goals, known_terms=known_terms
            )
            self.last_status_line = status
            self.last_aiming_for = aiming
            # Sentinel shanten 8 → refuse Why so tips cannot invent "8-shanten / 0 ukeire".
            if getattr(turn.features, "shanten", None) == 8:
                result = WhyResult(
                    ok=False,
                    summary="",
                    pinned_action=action_to_label(reaction)
                    if "action_to_label" in dir()
                    else str(reaction.get("type") or ""),
                    status_line=status,
                    aiming_for=aiming,
                    error="Hand sync unavailable",
                )
                self._cache_key = key
                self._cache_result = result
                self.last_result = result
                return result
            explanation: Explanation = explain(
                turn,
                use_llm=use_llm,
                include_score_tips=include_score_tips,
                known_terms=known_terms,
            )
            result = WhyResult(
                ok=True,
                summary=explanation.summary,
                pinned_action=explanation.pinned_action,
                status_line=status,
                aiming_for=aiming,
                source="llm" if use_llm else "auto",
            )
            self._append_reason(
                ReasonLogEntry(
                    kyoku=getattr(game_info, "kyoku", None),
                    honba=getattr(game_info, "honba", None),
                    pinned_action=explanation.pinned_action,
                    summary=explanation.summary,
                    source=result.source,
                )
            )
        except Exception as e:
            LOGGER.error("Sensei explain failed: %s", e, exc_info=True)
            result = WhyResult(ok=False, summary="", error=str(e))

        self._cache_key = key
        self._cache_result = result
        self.last_result = result
        return result
