#!/bin/bash
# Download the AGPL-licensed Mortal checkpoint bundled in macOS releases.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/bundled_models/mortal_298k.pth"
URL="https://huggingface.co/VoidShine/mortal-298k/resolve/main/mortal_298k.pth"
# Pinned size + SHA256 for VoidShine/mortal-298k mortal_298k.pth (verify after download).
EXPECTED_BYTES=130774416
EXPECTED_SHA256="bfb3a6c072aa0bfd4171a9cdc77cb6c02ae42cde920843f9e5784394f23447d8"

mkdir -p "${ROOT}/bundled_models"

echo "Downloading mortal_298k.pth from Hugging Face…"
curl -fsSL "${URL}" -o "${DEST}"

ACTUAL_BYTES="$(wc -c < "${DEST}" | tr -d ' ')"
if [[ "${ACTUAL_BYTES}" != "${EXPECTED_BYTES}" ]]; then
  echo "ERROR: unexpected file size ${ACTUAL_BYTES} (expected ${EXPECTED_BYTES})" >&2
  exit 1
fi

ACTUAL_SHA256="$(shasum -a 256 "${DEST}" | awk '{print $1}')"
if [[ "${ACTUAL_SHA256}" != "${EXPECTED_SHA256}" ]]; then
  echo "ERROR: SHA256 mismatch" >&2
  echo "  got:      ${ACTUAL_SHA256}" >&2
  echo "  expected: ${EXPECTED_SHA256}" >&2
  exit 1
fi

echo "OK: ${DEST} (${ACTUAL_BYTES} bytes)"
