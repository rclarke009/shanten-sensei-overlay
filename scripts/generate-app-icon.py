#!/usr/bin/env python3
"""Regenerate resources/icon.png and icon.ico from yakuman_idle.png."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "resources"
SRC = RES / "yakuman_idle.png"
OUT_PNG = RES / "icon.png"
OUT_ICO = RES / "icon.ico"
OUT_ICNS = RES / "icon.icns"
ICONSET = RES / "icon.iconset"

# Match the companion window / legacy app icon background.
BG = (97, 209, 211, 255)
# Pixels near yakuman_idle's flat backdrop become the icon background.
BG_TOLERANCE = 28
ICON_SIZE = 400
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]


def _is_backdrop(r: int, g: int, b: int) -> bool:
    return abs(r - 22) <= BG_TOLERANCE and abs(g - 27) <= BG_TOLERANCE and abs(b - 33) <= BG_TOLERANCE


def yakuman_to_icon(size: int = ICON_SIZE) -> Image.Image:
    src = Image.open(SRC).convert("RGBA")
    out = Image.new("RGBA", src.size, BG)
    px = src.load()
    dst = out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if _is_backdrop(r, g, b):
                continue
            dst[x, y] = (r, g, b, a)
    return out.resize((size, size), Image.Resampling.LANCZOS)


def write_ico(img: Image.Image) -> None:
    frames = [img.resize(s, Image.Resampling.LANCZOS) for s in ICO_SIZES]
    frames[0].save(OUT_ICO, format="ICO", sizes=ICO_SIZES, append_images=frames[1:])


def write_icns(img: Image.Image) -> None:
    if sys.platform != "darwin":
        return
    if ICONSET.exists():
        for child in ICONSET.iterdir():
            child.unlink()
    else:
        ICONSET.mkdir()
    for n in ICNS_SIZES:
        resized = img.resize((n, n), Image.Resampling.LANCZOS)
        resized.save(ICONSET / f"icon_{n}x{n}.png")
        if n != 1024:
            half = n // 2
            resized.resize((half, half), Image.Resampling.LANCZOS).save(
                ICONSET / f"icon_{half}x{half}@2x.png"
            )
    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(OUT_ICNS)],
        check=True,
    )
    for child in ICONSET.iterdir():
        child.unlink()
    ICONSET.rmdir()


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Missing source sprite: {SRC}")
    icon = yakuman_to_icon()
    icon.save(OUT_PNG, format="PNG")
    write_ico(icon)
    write_icns(icon)
    print(f"Wrote {OUT_PNG}, {OUT_ICO}", end="")
    if OUT_ICNS.is_file():
        print(f", {OUT_ICNS}")
    else:
        print()


if __name__ == "__main__":
    main()
