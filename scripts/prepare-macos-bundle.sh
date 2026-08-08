#!/bin/bash
# Copy platform-native libs into overlay tree before PyInstaller (macOS CI / local builds).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYVER="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
ARCH="$(uname -m)"
if [[ "$ARCH" == "arm64" ]]; then
  ARCH_TAG="aarch64"
else
  ARCH_TAG="x86_64"
fi

DEST="${ROOT}/libriichi3p/libriichi3p-${PYVER}-${ARCH_TAG}-apple-darwin.so"

FOUND="$(python - <<'PY'
import glob
import os
import site

for base in site.getsitepackages():
    for pattern in ("**/libriichi3p*.so", "**/libriichi3p*.dylib"):
        hits = glob.glob(os.path.join(base, pattern), recursive=True)
        if hits:
            print(hits[0])
            raise SystemExit
PY
)"

if [[ -n "${FOUND:-}" && -f "$FOUND" ]]; then
  cp "$FOUND" "$DEST"
  echo "Prepared 3P native lib: $DEST"
else
  echo "WARNING: libriichi3p native library not found; 3-player mode may not work in this build."
  echo "4-player mode uses the riichi pip package bundled by PyInstaller."
fi
