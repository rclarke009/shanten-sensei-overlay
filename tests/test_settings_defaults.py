"""Fresh Settings defaults and locale migration for deliverable installs."""

from pathlib import Path

from common.lan_str import DEFAULT_MAJSOUL_URL
from common.settings import (
    LOCALE_DEFAULTS_VERSION,
    Settings,
    apply_deliverable_locale_defaults,
)

ENGLISH_MAJSOUL_URL = DEFAULT_MAJSOUL_URL


def test_fresh_settings_default_to_english(tmp_path: Path):
    path = tmp_path / "settings.json"
    st = Settings(str(path))
    assert st.language == "EN"
    assert st.ms_url == ENGLISH_MAJSOUL_URL
    assert st.locale_defaults_version == LOCALE_DEFAULTS_VERSION


def test_missing_settings_file_defaults_to_english(tmp_path: Path):
    path = tmp_path / "missing.json"
    assert not path.exists()
    st = Settings(str(path))
    assert st.language == "EN"
    assert st.ms_url == ENGLISH_MAJSOUL_URL
    assert st.locale_defaults_version == LOCALE_DEFAULTS_VERSION


def test_migrates_legacy_chinese_settings_on_update(tmp_path: Path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text(
        """{
    "language": "ZHS",
    "ms_url": "https://game.maj-soul.com/1/",
    "setup_complete": true,
    "locale_defaults_version": 0
}""",
        encoding="utf-8",
    )
    st = Settings(str(path))
    assert st.language == "EN"
    assert st.ms_url == ENGLISH_MAJSOUL_URL
    assert st.locale_defaults_version == LOCALE_DEFAULTS_VERSION
    assert st.setup_complete is True


def test_locale_migration_is_idempotent(tmp_path: Path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text(
        """{
    "language": "EN",
    "ms_url": "https://mahjongsoul.game.yo-star.com/",
    "locale_defaults_version": 1
}""",
        encoding="utf-8",
    )
    st = Settings(str(path))
    assert st.language == "EN"
    assert st.ms_url == ENGLISH_MAJSOUL_URL
    assert st.locale_defaults_version == LOCALE_DEFAULTS_VERSION


def test_apply_deliverable_locale_defaults_forces_english():
    class _Stub:
        language = "ZHS"
        ms_url = "https://game.maj-soul.com/1/"

    stub = _Stub()
    assert apply_deliverable_locale_defaults(stub) is True
    assert stub.language == "EN"
    assert stub.ms_url == ENGLISH_MAJSOUL_URL
