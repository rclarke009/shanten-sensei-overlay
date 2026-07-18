"""Practice / friend / vs-AI mode gate for Shanten Sensei coaching."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ModePolicy(str, Enum):
    ALLOWED = "allowed"  # friend / practice / vs-AI
    RESTRICTED = "restricted"  # ranked ladder or unknown


# Majsoul gameConfig.meta.category: 1 = friend (友人戦), 2 = ranked (段位戦)
CATEGORY_FRIEND = 1
CATEGORY_RANKED = 2

PRACTICE_BANNER = "Practice / vs-AI / friend only — not for ranked"


@dataclass(frozen=True)
class ModeVerdict:
    policy: ModePolicy
    reason: str
    category: int | None
    mode_id: int | None
    room_id: int | None

    @property
    def why_enabled(self) -> bool:
        return self.policy == ModePolicy.ALLOWED


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_auth_meta(game_config: dict[str, Any] | None) -> tuple[int | None, int | None, int | None]:
    """Extract (mode_id, category, room_id) from authGame gameConfig."""
    if not game_config:
        return None, None, None
    meta = game_config.get("meta") or {}
    mode_id = _int_or_none(meta.get("modeId") if "modeId" in meta else meta.get("mode_id"))
    category = _int_or_none(meta.get("category"))
    room_id = _int_or_none(
        meta.get("roomId") if "roomId" in meta else meta.get("room_id")
    )
    # Some payloads put roomId on gameConfig root
    if room_id is None:
        room_id = _int_or_none(
            game_config.get("roomId") if "roomId" in game_config else game_config.get("room_id")
        )
    return mode_id, category, room_id


def classify_mode(
    *,
    mode_id: int | None = None,
    category: int | None = None,
    room_id: int | None = None,
) -> ModeVerdict:
    """Classify whether Why? coaching is allowed.

    Rules (kickoff soft gate):
    - category 2 (ranked) → restricted
    - category 1 (friend) or room_id > 0 → allowed (covers friend + vs-AI in room)
    - everything else / unknown → restricted
    """
    if category == CATEGORY_RANKED:
        return ModeVerdict(
            policy=ModePolicy.RESTRICTED,
            reason="ranked (段位戦)",
            category=category,
            mode_id=mode_id,
            room_id=room_id,
        )
    if category == CATEGORY_FRIEND or (room_id is not None and room_id > 0):
        return ModeVerdict(
            policy=ModePolicy.ALLOWED,
            reason="friend / practice room",
            category=category,
            mode_id=mode_id,
            room_id=room_id,
        )
    return ModeVerdict(
        policy=ModePolicy.RESTRICTED,
        reason="unknown mode (treat as restricted)",
        category=category,
        mode_id=mode_id,
        room_id=room_id,
    )


def classify_from_game_config(game_config: dict[str, Any] | None) -> ModeVerdict:
    mode_id, category, room_id = parse_auth_meta(game_config)
    return classify_mode(mode_id=mode_id, category=category, room_id=room_id)
