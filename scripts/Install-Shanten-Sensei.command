#!/bin/bash
# Double-click to install Shanten Sensei from the latest GitHub Release (macOS).
# Downloads the .dmg if needed, copies the app to ~/Applications, and opens it.
set -euo pipefail

REPO="rclarke009/shanten-sensei-overlay"
APP_NAME="Shanten Sensei"
APP_PATH="${HOME}/Applications/${APP_NAME}.app"
DMG_NAME="ShantenSensei-macOS.dmg"
DOWNLOADS_DMG="${HOME}/Downloads/${DMG_NAME}"
CACHE_DIR="${HOME}/Library/Caches/ShantenSensei"
CACHE_DMG="${CACHE_DIR}/${DMG_NAME}"
MOUNT_POINT=""

cleanup() {
  if [[ -n "${MOUNT_POINT}" && -d "${MOUNT_POINT}" ]]; then
    hdiutil detach "${MOUNT_POINT}" -quiet 2>/dev/null || true
  fi
}
trap cleanup EXIT

pause() {
  read -r -p "Press Enter to close…" _
}

echo "=== Install Shanten Sensei ==="
echo "Practice / friend / vs-AI only — not for ranked."
echo ""

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer is for macOS only." >&2
  pause
  exit 1
fi

choose_dmg() {
  if [[ -f "${DOWNLOADS_DMG}" ]]; then
    echo "Using DMG already in Downloads." >&2
    echo "${DOWNLOADS_DMG}"
    return
  fi
  if [[ -f "${CACHE_DMG}" ]]; then
    echo "Using cached DMG." >&2
    echo "${CACHE_DMG}"
    return
  fi

  mkdir -p "${CACHE_DIR}"
  echo "Finding latest release…" >&2
  local meta
  meta="$(python3 - <<'PY'
import json
import sys
import urllib.request

repo = "rclarke009/shanten-sensei-overlay"
url = f"https://api.github.com/repos/{repo}/releases/latest"
with urllib.request.urlopen(url, timeout=90) as resp:
    data = json.load(resp)
tag = data.get("tag_name", "latest")
for asset in data.get("assets", []):
    if asset.get("name") == "ShantenSensei-macOS.dmg":
        print(asset["browser_download_url"])
        print(tag)
        break
else:
    sys.exit("No ShantenSensei-macOS.dmg in latest release")
PY
)" || {
    echo "Could not find a release DMG. Download ${DMG_NAME} manually from:" >&2
    echo "  https://github.com/${REPO}/releases/latest" >&2
    pause
    exit 1
  }

  local url tag
  url="$(echo "${meta}" | sed -n '1p')"
  tag="$(echo "${meta}" | sed -n '2p')"
  echo "Latest release: ${tag}" >&2
  echo "Downloading ${DMG_NAME}…" >&2
  curl -fL --progress-bar "${url}" -o "${CACHE_DMG}"
  echo "${CACHE_DMG}"
}

DMG_PATH="$(choose_dmg)"

# Clear quarantine on downloaded images (can block attach on some macOS versions).
xattr -dr com.apple.quarantine "${DMG_PATH}" 2>/dev/null || true

if ! hdiutil imageinfo "${DMG_PATH}" >/dev/null 2>&1; then
  echo "Downloaded file is not a valid disk image. Delete it and run this installer again:" >&2
  echo "  ${DMG_PATH}" >&2
  pause
  exit 1
fi

echo "Mounting disk image…"
ATTACH_OUT="$(hdiutil attach "${DMG_PATH}" -nobrowse 2>&1)" || {
  echo "${ATTACH_OUT}" >&2
  echo "Could not mount ${DMG_PATH}" >&2
  pause
  exit 1
}
MOUNT_POINT="$(echo "${ATTACH_OUT}" | grep -o '/Volumes/.*' | head -1)"
if [[ -z "${MOUNT_POINT}" || ! -d "${MOUNT_POINT}" ]]; then
  echo "${ATTACH_OUT}" >&2
  echo "Could not find a mount point for ${DMG_PATH}" >&2
  pause
  exit 1
fi

SOURCE_APP="${MOUNT_POINT}/${APP_NAME}.app"
if [[ ! -d "${SOURCE_APP}" ]]; then
  echo "Could not find ${APP_NAME}.app on the disk image." >&2
  pause
  exit 1
fi

echo "Installing to ${APP_PATH}…"
mkdir -p "${HOME}/Applications"
rm -rf "${APP_PATH}"
ditto "${SOURCE_APP}" "${APP_PATH}"
xattr -dr com.apple.quarantine "${APP_PATH}" 2>/dev/null || true

echo ""
echo "Done! Opening Shanten Sensei…"
echo ""
echo "First time only: if macOS warns the app is unsigned,"
echo "  right-click Shanten Sensei → Open → Open again."
echo ""
echo "Then complete the setup wizard and play Majsoul in Safari."
echo ""

open "${APP_PATH}" || true
pause
