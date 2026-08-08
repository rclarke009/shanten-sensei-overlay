# Bundled Mortal checkpoint (not in git)

Release builds download `mortal_298k.pth` here before PyInstaller runs.

- **Source:** https://huggingface.co/VoidShine/mortal-298k  
- **License:** AGPL-3.0 — see `licenses/MORTAL_MODEL_NOTICE.md`  
- **CI script:** `scripts/download-bundled-model.sh`

Local release builds:

```bash
bash scripts/download-bundled-model.sh
pyinstaller ShantenSensei.spec --noconfirm
```

The `.pth` file is gitignored (~125 MB).
