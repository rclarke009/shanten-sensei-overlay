# Install Shanten Sensei on Mac

Practice / friend / vs-AI only — **not for ranked**. Coaching (Why?, live tips) and Autoplay are disabled in ranked or unknown mode. Auto Join is off.

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

Quit the app when done — it turns off the Safari proxy. If browsing breaks after a crash, see [proxy trust precautions](https://github.com/rclarke009/shanten_sensei/blob/main/docs/proxy-trust-precautions.md).

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
| Coaching disabled | Ranked or unknown mode — use friend / practice. Autoplay and live tips are off too. |
| Model error | Place `.pth` in `models/` via Settings or first-run wizard |
| Browsing broken after crash | Turn off Auto Proxy in Network settings — see [proxy-trust-precautions.md](https://github.com/rclarke009/shanten_sensei/blob/main/docs/proxy-trust-precautions.md) |

## Developers

From-source setup (clone repos, `scripts/install-macos.command`, Chromium path, tests): [shanten_sensei live-setup.md](https://github.com/rclarke009/shanten_sensei/blob/main/docs/live-setup.md)
