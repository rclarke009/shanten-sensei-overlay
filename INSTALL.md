# Install Shanten Sensei on Mac

Practice / friend / vs-AI only — **not for ranked**.

## Option A — Download (recommended when available)

1. Open [Shanten Sensei overlay Releases](https://github.com/rclarke009/shanten-sensei-overlay/releases) and download the latest **ShantenSensei-macOS.dmg**.
2. Open the DMG and drag **Shanten Sensei** to Applications.
3. First launch: if macOS blocks an unsigned build, right-click the app → **Open** → confirm.
4. Complete the **first-run wizard**:
   - Confirm practice-only use
   - Choose your Mortal `.pth` model ([Akagi](https://github.com/shinkuan/Akagi) compatible)
   - Keep **Safari companion** enabled (default)
   - Optional: paste an OpenAI API key for LLM **Why?** text
5. Open Majsoul in **Safari** (`https://mahjongsoul.game.yo-star.com/`), join friend / practice / vs-AI, and press **Why?** in the coach window.

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

Shanten Sensei does **not** ship Mortal weights. Download an Akagi-compatible `.pth` and select it in the first-run wizard or **Settings → Model**.

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
| No tips / not “Proxy Client” | Safari companion on; trust cert when prompted; quit Safari fully and reopen Majsoul |
| Why? disabled | Ranked or unknown mode — use friend / practice |
| Model error | Place `.pth` in `models/` via Settings or first-run wizard |
| Browsing broken after crash | Turn off Auto Proxy in Network settings — see [proxy-trust-precautions.md](proxy-trust-precautions.md) |

## Developers

From-source setup (two repos, Chromium path, tests): [shanten_sensei live-setup.md](https://github.com/rclarke009/shanten_sensei/blob/main/docs/live-setup.md)
