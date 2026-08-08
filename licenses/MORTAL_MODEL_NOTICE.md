# Bundled Mortal model — license and attribution

The macOS release of **Shanten Sensei** may include a pre-trained Mortal
checkpoint so users do not need a separate model download.

## What is bundled

| Field | Value |
|-------|--------|
| File in app | `bundled_models/mortal_298k.pth` |
| Installed as | `~/Library/Application Support/ShantenSensei/models/mortal.pth` |
| Checkpoint name | `mortal_298k` (298,000 training steps) |
| Game type | 4-player hanchan (south round) |

## Source and license (checkpoint)

This checkpoint is the community release **VoidShine/mortal-298k**:

- **Model page:** https://huggingface.co/VoidShine/mortal-298k  
- **License:** [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0.html)  
- **Framework:** [Mortal](https://github.com/Equim-chan/Mortal) by Equim (AGPL-3.0)

The checkpoint is **not** the official trained weights distributed by the Mortal
author. Equim publishes Mortal **code** under AGPL; official trained weights are
documented separately at https://gist.github.com/Equim-chan/cf3f01735d5d98f1e7be02e94b288c56.

## Your rights under AGPL-3.0 (summary)

If you received this checkpoint as part of a distributed app:

1. You may use, modify, and redistribute it under AGPL-3.0 terms.
2. If you convey this software (including the bundled checkpoint), you must
   preserve copyright/license notices and provide access to Corresponding
   Source for the covered work as AGPL requires.
3. See `licenses/AGPL-3.0.txt` in the app bundle (or the full text at
   https://www.gnu.org/licenses/agpl-3.0.txt).

This summary is not a substitute for the full license.

## Corresponding source (Shanten Sensei overlay)

Application source for this distribution:

- **Overlay (GPL-3.0):** https://github.com/rclarke009/shanten-sensei-overlay  
- **Sensei library (Apache-2.0):** https://github.com/rclarke009/shanten_sensei  
- **Checkpoint config / training notes:** https://huggingface.co/VoidShine/mortal-298k  

## Use restrictions (product policy)

**Practice / friend / vs-AI only — not for ranked.** The upstream checkpoint
README also discourages ranked use. Shanten Sensei enforces a practice-only gate
for Why? coaching.

## Replacing the model

You may point **Settings → Model** at any other Akagi-compatible Mortal `.pth`
you are licensed to use. The bundled file is a default convenience, not a
requirement.
