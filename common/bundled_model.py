"""Bundled Mortal checkpoint (AGPL) for frozen macOS installs."""

from __future__ import annotations

import shutil
import sys
import webbrowser
from pathlib import Path

BUNDLED_NAME = "mortal_298k.pth"
INSTALL_NAME = "mortal.pth"
NOTICE_NAME = "MORTAL_MODEL_NOTICE.md"


def _frozen_base() -> Path | None:
    root = getattr(sys, "_MEIPASS", None)
    return Path(root) if root else None


def bundled_model_source() -> Path | None:
    """Path to the checkpoint shipped inside a PyInstaller bundle."""
    base = _frozen_base()
    if base is None:
        return None
    candidate = base / "bundled_models" / BUNDLED_NAME
    return candidate if candidate.is_file() else None


def licenses_dir() -> Path | None:
    """Directory with third-party license texts inside a frozen bundle."""
    base = _frozen_base()
    if base is None:
        repo = Path(__file__).resolve().parent.parent / "licenses"
        return repo if repo.is_dir() else None
    candidate = base / "licenses"
    return candidate if candidate.is_dir() else None


def model_notice_path() -> Path | None:
    directory = licenses_dir()
    if directory is None:
        return None
    path = directory / NOTICE_NAME
    return path if path.is_file() else None


def install_bundled_model_if_needed() -> Path | None:
    """Copy bundled checkpoint into Application Support models/ (frozen only)."""
    source = bundled_model_source()
    if source is None:
        return None

    from common.sensei_paths import models_data_dir

    dest = models_data_dir() / INSTALL_NAME
    if dest.is_file():
        return dest

    shutil.copy2(source, dest)
    return dest


def open_model_license() -> bool:
    """Open bundled model license notice in the default browser or viewer."""
    path = model_notice_path()
    if path is None:
        return False
    if sys.platform == "darwin":
        import subprocess

        subprocess.run(["open", str(path)], check=False)
        return True
    webbrowser.open(path.as_uri())
    return True
