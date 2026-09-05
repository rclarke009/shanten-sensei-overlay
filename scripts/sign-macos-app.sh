#!/bin/bash
# Sign a PyInstaller .app (or a .dmg) with Developer ID Application.
# Nested Mach-O files are signed first; entitlements apply only to the app/main binary.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-}"
ENTITLEMENTS="${ROOT}/scripts/macos-entitlements.plist"

if [[ -z "${TARGET}" ]]; then
  echo "Usage: $0 <path-to-Shanten Sensei.app|file.dmg>" >&2
  exit 1
fi
if [[ ! -e "${TARGET}" ]]; then
  echo "Nothing to sign at ${TARGET}" >&2
  exit 1
fi

if [[ -z "${CODESIGN_IDENTITY:-}" ]]; then
  CODESIGN_IDENTITY="$(security find-identity -v -p codesigning \
    | awk -F'"' '/Developer ID Application/ {print $2; exit}')"
fi
if [[ -z "${CODESIGN_IDENTITY}" ]]; then
  echo "No Developer ID Application identity found. Import the .p12 first." >&2
  security find-identity -v -p codesigning >&2 || true
  exit 1
fi

echo "Signing with: ${CODESIGN_IDENTITY}"

if [[ "${TARGET}" == *.dmg ]]; then
  codesign --force --sign "${CODESIGN_IDENTITY}" --timestamp "${TARGET}"
  codesign --verify --verbose=2 "${TARGET}"
  echo "Signed ${TARGET}"
  exit 0
fi

if [[ ! -d "${TARGET}" ]]; then
  echo "Expected an .app bundle directory: ${TARGET}" >&2
  exit 1
fi

python3 - "${TARGET}" <<'PY' | while IFS= read -r -d '' f; do
import os
import subprocess
import sys

app = sys.argv[1]
paths = []
for root, _dirs, files in os.walk(app):
    for name in files:
        paths.append(os.path.join(root, name))
paths.sort(key=lambda p: p.count(os.sep), reverse=True)
for path in paths:
    try:
        out = subprocess.check_output(["file", "-b", path], text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        continue
    if "Mach-O" not in out:
        continue
    sys.stdout.buffer.write(path.encode() + b"\0")
PY
  echo "  nested: ${f}"
  codesign --force --options runtime --timestamp \
    --sign "${CODESIGN_IDENTITY}" \
    "${f}"
done

MAIN="${TARGET}/Contents/MacOS/ShantenSensei"
if [[ -f "${MAIN}" ]]; then
  codesign --force --options runtime --timestamp \
    --entitlements "${ENTITLEMENTS}" \
    --sign "${CODESIGN_IDENTITY}" \
    "${MAIN}"
fi

codesign --force --options runtime --timestamp \
  --entitlements "${ENTITLEMENTS}" \
  --sign "${CODESIGN_IDENTITY}" \
  "${TARGET}"

codesign --verify --deep --strict --verbose=2 "${TARGET}"
echo "Signed ${TARGET}"
