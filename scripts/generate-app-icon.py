#!/usr/bin/env python3
"""Regenerate resources/icon.png, icon.ico, and icon.icns from yakuman_icon.png."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "resources"
SRC = RES / "yakuman_icon.png"
OUT_PNG = RES / "icon.png"
OUT_ICO = RES / "icon.ico"
OUT_ICNS = RES / "icon.icns"
ICONSET = RES / "icon.iconset"

# Match the companion window / legacy app icon background.
BG = (97, 209, 211, 255)
# Pixels near yakuman sprites' flat backdrop become transparent.
BG_TOLERANCE = 28
ICON_SIZE = 400
PAD_RATIO = 0.10
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ICNS_ICONSET = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]


def _is_backdrop(r: int, g: int, b: int) -> bool:
    return abs(r - 22) <= BG_TOLERANCE and abs(g - 27) <= BG_TOLERANCE and abs(b - 33) <= BG_TOLERANCE


def _remove_backdrop(img: Image.Image) -> Image.Image:
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    px = img.load()
    dst = out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a < 128 or _is_backdrop(r, g, b):
                continue
            dst[x, y] = (r, g, b, a)
    return out


def _trim_sprite(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    if bbox is None:
        return img
    return img.crop(bbox)


def yakuman_to_icon(size: int = ICON_SIZE) -> Image.Image:
    src = _trim_sprite(_remove_backdrop(Image.open(SRC).convert("RGBA")))
    canvas = Image.new("RGBA", (size, size), BG)
    pad = int(size * PAD_RATIO)
    inner = size - 2 * pad
    scale = min(inner / src.width, inner / src.height)
    scaled_w = max(1, int(src.width * scale))
    scaled_h = max(1, int(src.height * scale))
    scaled = src.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    offset = ((size - scaled_w) // 2, (size - scaled_h) // 2)
    canvas.paste(scaled, offset, scaled)
    return canvas


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
    for name, icns_size in ICNS_ICONSET:
        img.resize((icns_size, icns_size), Image.Resampling.LANCZOS).save(ICONSET / name)
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
