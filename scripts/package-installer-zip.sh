#!/bin/bash
# Zip the one-click installer so macOS keeps the executable bit after download.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

SCRIPT="scripts/Install-Shanten-Sensei.command"
ZIP="dist/Install-Shanten-Sensei.zip"
README="dist/Install-Shanten-Sensei-README.txt"

mkdir -p dist
chmod +x "${SCRIPT}"

cat > "${README}" <<'EOF'
Install Shanten Sensei (Mac)
============================

1. Double-click Install-Shanten-Sensei.command
2. If macOS blocks it: right-click → Open → Open again
3. Finish the setup wizard, then play Majsoul in Safari (practice/friend)

Practice / friend / vs-AI only — not for ranked.
EOF

rm -f "${ZIP}"
(
  cd "$(dirname "${SCRIPT}")"
  zip -j "${ROOT}/${ZIP}" "$(basename "${SCRIPT}")"
  cd "${ROOT}"
  zip -j "${ZIP}" "${README}"
)

ls -lh "${ZIP}"
