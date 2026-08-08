"""setup_complete setting for first-run wizard."""

from pathlib import Path

from common.settings import Settings


def test_setup_complete_default_false(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    st = Settings(str(tmp_path / "settings.json"))
    assert st.setup_complete is False


def test_setup_complete_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "settings.json"
    st = Settings(str(path))
    st.setup_complete = True
    st.save_json()
    st2 = Settings(str(path))
    assert st2.setup_complete is True
