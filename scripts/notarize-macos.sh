#!/bin/bash
# Submit an .app (zipped) or .dmg to Apple notarytool and staple the ticket.
set -euo pipefail

TARGET="${1:-}"
if [[ -z "${TARGET}" ]]; then
  echo "Usage: $0 <path-to-Shanten Sensei.app|file.dmg>" >&2
  exit 1
fi
if [[ ! -e "${TARGET}" ]]; then
  echo "Nothing to notarize at ${TARGET}" >&2
  exit 1
fi

: "${APPLE_ID:?APPLE_ID is required}"
: "${APPLE_APP_PASSWORD:?APPLE_APP_PASSWORD is required}"
: "${APPLE_TEAM_ID:?APPLE_TEAM_ID is required}"

SUBMIT="${TARGET}"
CLEANUP=""
if [[ -d "${TARGET}" ]]; then
  SUBMIT="$(mktemp -t ShantenSensei-notarize).zip"
  CLEANUP="${SUBMIT}"
  ditto -c -k --keepParent "${TARGET}" "${SUBMIT}"
fi

echo "Submitting $(basename "${SUBMIT}") to notarytool…"
xcrun notarytool submit "${SUBMIT}" \
  --apple-id "${APPLE_ID}" \
  --password "${APPLE_APP_PASSWORD}" \
  --team-id "${APPLE_TEAM_ID}" \
  --wait

if [[ -n "${CLEANUP}" ]]; then
  rm -f "${CLEANUP}"
fi

echo "Stapling ${TARGET}…"
xcrun stapler staple "${TARGET}"
xcrun stapler validate "${TARGET}"
echo "Notarized ${TARGET}"
