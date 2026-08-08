"""Tests for Application Support paths."""

from pathlib import Path

from common.sensei_paths import app_support_dir, sensei_env_path, write_sensei_env


def test_app_support_dir_creates(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("common.sensei_paths.Path.home", lambda: tmp_path)
    root = app_support_dir()
    assert root.is_dir()
    assert root.name == "ShantenSensei"


def test_write_sensei_env(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("common.sensei_paths.Path.home", lambda: tmp_path)
    path = write_sensei_env(openai_api_key="sk-test", use_llm=True)
    assert path == sensei_env_path()
    text = path.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=sk-test" in text
    assert "SENSEI_USE_LLM=1" in text
