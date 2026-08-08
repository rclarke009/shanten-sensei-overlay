"""safari_mode setting persistence and companion-only expectations."""

import json
from pathlib import Path

from common.settings import Settings


def test_safari_mode_default_false(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    st = Settings(str(tmp_path / "settings.json"))
    assert st.safari_mode is False


def test_safari_mode_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "settings.json"
    st = Settings(str(path))
    st.safari_mode = True
    st.auto_launch_browser = False
    st.save_json()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["safari_mode"] is True

    st2 = Settings(str(path))
    assert st2.safari_mode is True
