# Install Shanten Sensei on Mac

Practice / friend / vs-AI only — **not for ranked**.

**Defaults:** English overlay UI and the English YoStar Majsoul client (`mahjongsoul.game.yo-star.com`). The setup wizard and app updates re-apply these defaults. Change either in **Settings** if you prefer another language or client URL.

## Option A — One-click install (recommended)

1. Open [Releases](https://github.com/rclarke009/shanten-sensei-overlay/releases/latest).
2. Download **`Install-Shanten-Sensei.zip`** (not the raw `.command` — GitHub strips execute permission).
3. Double-click the zip to unzip, then double-click **`Install-Shanten-Sensei.command`**.
   - If macOS blocks the script: right-click → **Open** → **Open** again.
4. The installer uses a `.dmg` from Downloads if present; otherwise it downloads the latest release, installs to `~/Applications/`, and opens the app.
5. Complete the **first-run wizard**, then play Majsoul in **Safari** and press **Why?**.

**Already have the `.dmg`?** Open it and double-click **`Install Shanten Sensei.command`** on the disk image (permissions are preserved there).

**Terminal fallback** (if double-click still fails):

```bash
bash ~/Downloads/Install-Shanten-Sensei.command
```

License files: on the DMG (`Model-License-AGPL.txt`) and in the app under `licenses/`. See [licenses/MORTAL_MODEL_NOTICE.md](licenses/MORTAL_MODEL_NOTICE.md).

Quit the app when done — it turns off the Safari proxy. If browsing breaks after a crash, see [proxy trust precautions](proxy-trust-precautions.md).

## Option B — One-click installer (from source)

If no Release build is published yet:

1. Install [Python 3.11](https://www.python.org/downloads/).
2. Clone the overlay repo: `git clone https://github.com/rclarke009/shanten-sensei-overlay.git`
3. Double-click **`scripts/install-macos.command`** in Finder (or run it in Terminal).
4. Open **Shanten Sensei** from `~/Applications/` and finish the first-run wizard.

The installer skips Chromium by default (Safari path). To also install Playwright Chromium:

```bash
INSTALL_CHROMIUM=1 ./scripts/install-macos.command
```

## Mortal model

**macOS Release builds** bundle the community checkpoint [VoidShine/mortal-298k](https://huggingface.co/VoidShine/mortal-298k) under **AGPL-3.0**. It installs automatically to:

`~/Library/Application Support/ShantenSensei/models/mortal.pth`

See [licenses/MORTAL_MODEL_NOTICE.md](licenses/MORTAL_MODEL_NOTICE.md) for attribution and your rights.

**From source / dev installs** do not include weights. Download an Akagi-compatible `.pth` and select it in the first-run wizard or **Settings → Model**.

## Optional: LLM Why?

Template explanations work without an API key. For richer wording, add a key in the first-run wizard or create:

`~/Library/Application Support/ShantenSensei/.env`

```env
OPENAI_API_KEY=sk-...
SENSEI_USE_LLM=1
```

Restart the app after changing keys.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Installer didn’t update / still old build | Re-run `Install-Shanten-Sensei.command` — it checks GitHub for the latest tag and re-downloads if your cached DMG is older. Or set `INSTALL_FORCE_DOWNLOAD=1` before running. |
| Coach UI still Chinese after update | Quit the app fully (`Cmd+Q`), reopen; check **Settings → Language → English**. Majsoul in Safari has its own in-game language. |
| No tips / not “Proxy Client” | Safari companion on; trust cert when prompted; quit Safari fully and reopen Majsoul |
| Why? disabled | Ranked or unknown mode — use friend / practice |
| Model error | Place `.pth` in `models/` via Settings or first-run wizard |
| Browsing broken after crash | Turn off Auto Proxy in Network settings — see [proxy-trust-precautions.md](proxy-trust-precautions.md) |

## Developers

From-source setup (two repos, Chromium path, tests): [shanten_sensei live-setup.md](https://github.com/rclarke009/shanten_sensei/blob/main/docs/live-setup.md)
