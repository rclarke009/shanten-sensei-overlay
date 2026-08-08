#!/bin/bash
# Create ShantenSensei-macOS.dmg with app + license notice at volume root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

APP_PATH="dist/Shanten Sensei.app"
STAGING="dist/dmg-staging"
DMG_PATH="dist/ShantenSensei-macOS.dmg"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "Expected app bundle at ${APP_PATH}" >&2
  ls -la dist/ >&2 || true
  exit 1
fi

rm -rf "${STAGING}"
mkdir -p "${STAGING}"
cp -R "${APP_PATH}" "${STAGING}/"
cp licenses/MORTAL_MODEL_NOTICE.md "${STAGING}/Model-License-AGPL.txt"
cp licenses/README.md "${STAGING}/Third-Party-Licenses.txt"

hdiutil create -volname "Shanten Sensei" -srcfolder "${STAGING}" -ov -format UDZO "${DMG_PATH}"
shasum -a 256 "${DMG_PATH}" > "${DMG_PATH}.sha256"
cat "${DMG_PATH}.sha256"
ls -lh "${DMG_PATH}"
