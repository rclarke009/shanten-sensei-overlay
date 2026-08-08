"""Tests for bundled Mortal model install (AGPL checkpoint)."""

import sys
from pathlib import Path

from common.bundled_model import BUNDLED_NAME, INSTALL_NAME, install_bundled_model_if_needed
from common.sensei_paths import models_data_dir


def test_install_bundled_model_copies_once(monkeypatch, tmp_path: Path):
    bundle_root = tmp_path / "bundle"
    bundled = bundle_root / "bundled_models" / BUNDLED_NAME
    bundled.parent.mkdir(parents=True)
    bundled.write_bytes(b"fake-model-bytes")

    support = tmp_path / "Library/Application Support/ShantenSensei"
    monkeypatch.setattr("common.sensei_paths.Path.home", lambda: tmp_path)
    monkeypatch.setattr("common.bundled_model._frozen_base", lambda: bundle_root)
    monkeypatch.setattr("sys.frozen", True, raising=False)

    first = install_bundled_model_if_needed()
    second = install_bundled_model_if_needed()

    assert first == models_data_dir() / INSTALL_NAME
    assert second == first
    assert first.read_bytes() == b"fake-model-bytes"
    assert bundled.read_bytes() == b"fake-model-bytes"


def test_install_bundled_model_noop_without_bundle(monkeypatch):
    monkeypatch.setattr("common.bundled_model._frozen_base", lambda: None)
    assert install_bundled_model_if_needed() is None
