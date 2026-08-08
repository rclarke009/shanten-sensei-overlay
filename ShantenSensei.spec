# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Shanten Sensei overlay (macOS, Safari companion default)."""

import platform
import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

_candidate_datas = [
    ("resources", "resources"),
    ("libriichi3p", "libriichi3p"),
    ("liqi_proto", "liqi_proto"),
    ("proxinject", "proxinject"),
    ("chrome_ext", "chrome_ext"),
    ("crx", "crx"),
    ("licenses", "licenses"),
    ("version", "."),
    ("NOTICE", "."),
    ("LICENSE", "."),
]
if (root / "bundled_models" / "mortal_298k.pth").is_file():
    _candidate_datas.append(("bundled_models", "bundled_models"))
# Vendored libriichi/ is Windows (.pyd); macOS builds use the riichi pip wheel instead.
if platform.system() != "Darwin":
    _candidate_datas.insert(1, ("libriichi", "libriichi"))
datas = [
    (str(root / src), dest)
    for src, dest in _candidate_datas
    if (root / src).exists()
]

hiddenimports = [
    "shanten_sensei",
    "shanten_sensei.cli",
    "shanten_sensei.envutil",
    "shanten_sensei.explain",
    "shanten_sensei.features",
    "shanten_sensei.glosses",
    "shanten_sensei.grounding",
    "shanten_sensei.ingest",
    "shanten_sensei.live",
    "shanten_sensei.mjai_board",
    "shanten_sensei.schema",
    "shanten_sensei.serve",
    "shanten_sensei.tiles",
    "mitmproxy",
    "mitmproxy.tools",
    "mitmproxy.tools.main",
    "playwright",
    "torch",
    "riichi",
    "libriichi",
    "libriichi3p",
    "PIL",
    "cryptography",
    "tkhtmlview",
]

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "scipy", "pandas"],
    noarchive=False,
)
pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ShantenSensei",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "resources" / "icon.ico") if (root / "resources" / "icon.ico").is_file() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ShantenSensei",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Shanten Sensei.app",
        icon=str(root / "resources" / "icon.ico") if (root / "resources" / "icon.ico").is_file() else None,
        bundle_identifier="com.shantensensei.overlay",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
            "CFBundleShortVersionString": "0.1.0",
        },
    )
