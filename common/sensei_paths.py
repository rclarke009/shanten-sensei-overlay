"""Paths for Shanten Sensei config outside the overlay repo."""

from __future__ import annotations

import sys
from pathlib import Path


def app_support_dir() -> Path:
    """Per-user data dir for Sensei (.env, optional future state)."""
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "ShantenSensei"
    else:
        root = Path.home() / ".local" / "share" / "ShantenSensei"
    root.mkdir(parents=True, exist_ok=True)
    return root


def sensei_env_path() -> Path:
    return app_support_dir() / ".env"


def write_sensei_env(
    *,
    openai_api_key: str = "",
    sensei_api_key: str = "",
    use_llm: bool = False,
) -> Path:
    """Write Application Support .env for Why? LLM calls."""
    path = sensei_env_path()
    lines = [
        "# Shanten Sensei — created by first-run setup",
        f"OPENAI_API_KEY={openai_api_key.strip()}",
    ]
    if sensei_api_key.strip():
        lines.append(f"SENSEI_API_KEY={sensei_api_key.strip()}")
    if use_llm:
        lines.append("SENSEI_USE_LLM=1")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
