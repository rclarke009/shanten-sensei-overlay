"""Tests for PyInstaller bundle path resolution."""

import sys
from pathlib import Path

from common.utils import Folder, bundled_file, sub_file, sub_folder


def test_frozen_bundled_data_uses_meipass(monkeypatch, tmp_path: Path):
    resources = tmp_path / "Contents" / "Resources"
    resources.mkdir(parents=True)
    liqi_dir = resources / "liqi_proto"
    liqi_dir.mkdir()
    (liqi_dir / "liqi.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(resources), raising=False)

    assert sub_file("liqi_proto", "liqi.json") == str((liqi_dir / "liqi.json").resolve())
    assert sub_folder(Folder.RES) == (resources / Folder.RES).resolve()


def test_frozen_runtime_data_uses_contents_parent(monkeypatch, tmp_path: Path):
    resources = tmp_path / "Contents" / "Resources"
    resources.mkdir(parents=True)

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(resources), raising=False)

    log_dir = sub_folder(Folder.LOG)
    assert log_dir == (tmp_path / "Contents" / Folder.LOG).resolve()
    assert log_dir.is_dir()


def test_bundled_file_uses_meipass_when_frozen(monkeypatch, tmp_path: Path):
    resources = tmp_path / "Contents" / "Resources"
    resources.mkdir(parents=True)
    (resources / "version").write_text("0.6.7", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(resources), raising=False)

    assert bundled_file("version") == str((resources / "version").resolve())
