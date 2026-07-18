"""Bridge MahjongCopilot live state → Shanten Sensei explain()."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sensei_mode import ModeVerdict, PRACTICE_BANNER

try:
    from common.log_helper import LOGGER
except ImportError:  # pragma: no cover
    import logging

    LOGGER = logging.getLogger("sensei_adapter")

try:
    from shanten_sensei.explain import explain
    from shanten_sensei.live import candidates_from_meta_options, turn_from_live
    from shanten_sensei.schema import Explanation, TurnExplainInput

    SENSEI_AVAILABLE = True
except ImportError as e:  # pragma: no cover - depends on local install
    LOGGER.warning("shanten_sensei not installed: %s", e)
    SENSEI_AVAILABLE = False
    Explanation = Any  # type: ignore
    TurnExplainInput = Any  # type: ignore


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
    source: str = "template"
    error: str | None = None


def status_line_from_turn(turn: TurnExplainInput) -> str:
    st = turn.features.statuses
    parts = [
        f"shanten {turn.features.shanten}",
        f"ukeire {turn.features.ukeire.count}",
    ]
    if st.tenpai:
        parts.append("tenpai")
        if st.wait_shape:
            parts.append(st.wait_shape)
    if st.furiten:
        parts.append("furiten")
    if st.riichi:
        parts.append("riichi")
    if not st.menzen:
        parts.append("open")
    if st.dora_in_hand:
        parts.append("dora:" + ",".join(st.dora_in_hand[:3]))
    return " · ".join(parts)


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

    scores = None
    if game_state is not None and getattr(game_state, "player_scores", None):
        scores = list(game_state.player_scores)

    dora = dora_indicators_from_game_state(game_state) if game_state is not None else []

    return turn_from_live(
        hand=hand,
        recommended=reaction,
        candidates=candidates,
        dora_indicators=dora,
        turn=None,
        honba=honba,
        scores=scores,
        kyoku=kyoku,
        riichi=riichi,
        riichi_flags=riichi_flags,
        diverge=False,
        source="live-copilot",
        context={"bakaze": getattr(game_info, "bakaze", None)},
    )


class SenseiCoach:
    """On-demand Why? with per-turn cache."""

    def __init__(self) -> None:
        self._cache_key: tuple | None = None
        self._cache_result: WhyResult | None = None
        self.last_result: WhyResult | None = None
        self.last_status_line: str | None = None

    def clear(self) -> None:
        self._cache_key = None
        self._cache_result = None
        self.last_result = None
        self.last_status_line = None

    def _key(self, reaction: dict, game_info: Any) -> tuple:
        kyoku = getattr(game_info, "kyoku", None) if game_info else None
        honba = getattr(game_info, "honba", None) if game_info else None
        return (
            kyoku,
            honba,
            reaction.get("type"),
            reaction.get("pai"),
            tuple(reaction.get("consumed") or ()),
        )

    def explain_why(
        self,
        reaction: dict | None,
        game_info: Any,
        game_state,
        mode: ModeVerdict,
        *,
        use_llm: bool | None = None,
    ) -> WhyResult:
        if not SENSEI_AVAILABLE:
            return WhyResult(
                ok=False,
                summary="",
                error="Install shanten_sensei: pip install -e ../shanten_sensei",
            )
        if not mode.why_enabled:
            return WhyResult(
                ok=False,
                summary="",
                error=f"{PRACTICE_BANNER} (blocked: {mode.reason})",
            )
        if not reaction:
            return WhyResult(ok=False, summary="", error="No pending Mortal recommendation")

        key = self._key(reaction, game_info)
        if key == self._cache_key and self._cache_result is not None:
            self.last_result = self._cache_result
            return self._cache_result

        try:
            turn = build_turn(reaction, game_info, game_state)
            status = status_line_from_turn(turn)
            self.last_status_line = status
            explanation: Explanation = explain(turn, use_llm=use_llm)
            # detect template vs llm roughly via env inside explain; surface pin
            result = WhyResult(
                ok=True,
                summary=explanation.summary,
                pinned_action=explanation.pinned_action,
                status_line=status,
                source="llm" if use_llm else "auto",
            )
        except Exception as e:
            LOGGER.error("Sensei explain failed: %s", e, exc_info=True)
            result = WhyResult(ok=False, summary="", error=str(e))

        self._cache_key = key
        self._cache_result = result
        self.last_result = result
        return result
