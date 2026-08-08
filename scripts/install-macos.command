#!/bin/bash
# Double-click in Finder to install Shanten Sensei (macOS, Safari companion default).
set -euo pipefail

INSTALL_ROOT="${HOME}/Applications/ShantenSensei"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="python3.11"
VENV="${INSTALL_ROOT}/venv"
APP_NAME="Shanten Sensei"
APP_PATH="${HOME}/Applications/${APP_NAME}.app"
SENSEI_GIT="${SENSEI_GIT:-git+https://github.com/rclarke009/shanten_sensei.git}"
OVERLAY_GIT="${OVERLAY_GIT:-git+https://github.com/rclarke009/shanten-sensei-overlay.git}"

echo "=== Shanten Sensei installer (macOS) ==="
echo ""

if ! command -v "${PYTHON}" &>/dev/null; then
  echo "Python 3.11 is required."
  echo "Install from https://www.python.org/downloads/ then run this script again."
  read -r -p "Press Enter to close…"
  exit 1
fi

mkdir -p "${INSTALL_ROOT}"
if [[ ! -d "${VENV}" ]]; then
  echo "Creating virtual environment at ${VENV}"
  "${PYTHON}" -m venv "${VENV}"
fi

# shellcheck source=/dev/null
source "${VENV}/bin/activate"
python -m pip install -U pip wheel

echo "Installing Shanten Sensei packages…"
if [[ -f "${REPO_DIR}/main.py" && -f "${REPO_DIR}/requirements.txt" ]]; then
  pip install -r "${REPO_DIR}/requirements.txt"
  pip install -e "${REPO_DIR}"
else
  pip install "${SENSEI_GIT}"
  pip install "${OVERLAY_GIT}"
fi

pip install 'numpy<2' 'httpx>=0.27,<0.28' 'httpcore>=1.0,<1.0.9' 'h11>=0.11,<0.15'

# Safari companion default — skip Chromium unless requested
if [[ "${INSTALL_CHROMIUM:-0}" == "1" ]]; then
  echo "Installing Playwright Chromium (optional)…"
  PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium
else
  echo "Skipping Chromium (Safari companion is the default)."
  echo "Set INSTALL_CHROMIUM=1 to install Playwright Chromium."
fi

mkdir -p "${INSTALL_ROOT}/models" "${INSTALL_ROOT}/log" "${INSTALL_ROOT}/mitm_config"
SETTINGS="${INSTALL_ROOT}/settings.json"
if [[ ! -f "${SETTINGS}" ]]; then
  cat >"${SETTINGS}" <<'JSON'
{
    "safari_mode": true,
    "auto_launch_browser": false,
    "enable_proxinject": false,
    "setup_complete": false,
    "model_type": "Local",
    "model_file": "mortal.pth",
    "language": "EN",
    "ms_url": "https://mahjongsoul.game.yo-star.com/"
}
JSON
fi

LAUNCHER="${INSTALL_ROOT}/launch.sh"
cat >"${LAUNCHER}" <<EOF
#!/bin/bash
set -euo pipefail
cd "${REPO_DIR}"
source "${VENV}/bin/activate"
if [[ -f "${SETTINGS}" && ! -f "${REPO_DIR}/settings.json" ]]; then
  cp "${SETTINGS}" "${REPO_DIR}/settings.json"
fi
exec python main.py
EOF
chmod +x "${LAUNCHER}"

# Minimal .app bundle
rm -rf "${APP_PATH}"
mkdir -p "${APP_PATH}/Contents/MacOS" "${APP_PATH}/Contents/Resources"
cat >"${APP_PATH}/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>launcher</string>
  <key>CFBundleIdentifier</key>
  <string>com.shantensensei.overlay</string>
  <key>CFBundleName</key>
  <string>${APP_NAME}</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.1.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
PLIST

cat >"${APP_PATH}/Contents/MacOS/launcher" <<EOF
#!/bin/bash
exec "${LAUNCHER}"
EOF
chmod +x "${APP_PATH}/Contents/MacOS/launcher"

echo ""
echo "=== Install complete ==="
echo "Launcher: ${APP_PATH}"
echo ""
echo "Next steps:"
echo "  1. Download a Mortal .pth model (see https://github.com/shinkuan/Akagi)"
echo "  2. Open '${APP_NAME}' from Applications"
echo "  3. Complete the first-run wizard (model + Safari)"
echo "  4. Join a friend / practice / vs-AI game — not ranked"
echo ""
read -r -p "Press Enter to close…"
