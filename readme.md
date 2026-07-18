# Shanten Sensei Overlay

Fork of [Mahjong Copilot](https://github.com/latorc/MahjongCopilot) with **Shanten Sensei** coaching: Mortal still recommends the move; Sensei explains **why** on demand.

**Practice / friend / vs-AI only — not for ranked.**

Upstream Copilot docs and community: [mjcopilot.com](https://mjcopilot.com) · [Discord](https://discord.gg/7hcZYTFw5r)

Explainer library (separate repo, Apache-2.0): [shanten_sensei](https://github.com/rclarke009/shanten_sensei) — see `docs/phase2-kickoff.md` there.

---

# 麻将 Copilot / Mahjong Copilot (upstream)

麻将 AI 助手，基于 mjai (Mortal模型) 实现的机器人。会对游戏对局的每一步进行指导。现支持雀魂三人、四人麻将。

Mahjong AI Assistant for Majsoul, based on mjai (Mortal model) bot implementation.

---

![](assets/shot3_lower.png)

特性：

- 对局每一步 AI 指导，可在游戏中覆盖显示
- 自动打牌，自动加入游戏
- 多语言支持
- 支持本地 Mortal 模型和在线模型，支持三麻和四麻

Features:

- Step-by-step AI guidance for the game, with optional in-game overlay.
- Auto play & auto joining next game
- Multi-language support
- Supports Mortal local models and online models, 3p and 4p mahjong modes.

<a id="instructions"></a>

## 使用方法 / Instructions

### 开发

1. 克隆 repo
2. 安装 Python 虚拟环境。Python 版本推荐 3.11.
3. 安装 requirements.txt 中的依赖。
4. 安装 Playwright + Chromium
5. 主程序入口: main.py

### To Develop (Sensei overlay)

1. Clone this fork **and** sibling `shanten_sensei`
2. Python 3.11+ venv; `pip install -r requirements.txt`
3. `pip install -e ../shanten_sensei` (or your clone path)
4. Playwright + Chromium; Akagi-compatible local Mortal model in settings
5. Optional: `OPENAI_API_KEY` / `SENSEI_API_KEY` for LLM Why? (template fallback otherwise)
6. `python main.py` — enable Overlay, play friend / vs-AI, press **Why?**

Unit tests (no Majsoul):

```bash
pip install -e ../shanten_sensei pytest
python -m pytest tests/test_sensei_mode.py tests/test_sensei_adapter.py -q
```

### 示例脚本 Sample script：
```batch
git clone https://github.com/rclarke009/shanten-sensei-overlay.git
cd shanten-sensei-overlay
python -m venv venv
CALL venv\Scripts\activate.bat
pip install -r requirements.txt
pip install -e ..\shanten_sensei
set PLAYWRIGHT_BROWSERS_PATH=0
playwright install chromium
python main.py
```
### 配置模型
本程序支持几种模型来源。其中，本地模型（Local）是基于 Akagi 兼容的 Mortal 模型。要获取 Akagi 的模型，请参见 <a href="https://github.com/shinkuan/Akagi" target="_blank"> Akagi Github </a> 的说明。
### Model Configuration
This program supports different types of AI models. The 'Local' Model type uses Mortal models compatible with Akagi. To acquire Akagi's models, please refer to <a href="https://github.com/shinkuan/Akagi" target="_blank"> Akagi Github </a>.


## 截图 / Screenshots

界面 / GUI

![](assets/shot1.png)
![](assets/settings.png)

游戏中覆盖显示 (HUD）/ In-game Overlay (HUD)

![](assets/shot2.png)

![](assets/shot3.png)

## 设计 / Design

![](assets/design_struct.png)

  
目录说明 Description for folders：
* gui: tkinter GUI 相关类 / tkinter GUI related classes
* game: 雀魂游戏相关类 / classes related to Majsoul game
* bot: AI 模型和机器人实现 / implementations for AI models and bots 
* common: 共同使用的支持代码 commonly used supporting code
* libriichi & libriichi3p: 编译完成的 libriichi 库文件 / For compiled libriichi libraries

## 鸣谢 / Credit

- 基于 Mortal 模型和 MJAI 协议
  Based on Mortal Model an MJAI protocol
  
  Mortal: https://github.com/Equim-chan/Mortal
- 设计和功能实现基于 Akagi
  Design and implementation based on Akagi
  
  Akagi: https://github.com/shinkuan/Akagi
- 参考 Reference
  Mahjong Soul API: https://github.com/MahjongRepository/mahjong_soul_api
- MJAI协议参考 / MJAI Protocol Reference
  
  MJAI: https://mjai.app

## 许可 / License
本项目使用 GNU GPL v3 许可协议（继承上游 Mahjong Copilot）。  
协议全文请见 [LICENSE](LICENSE)。归属说明见 [NOTICE](NOTICE)。

Sensei explainer library is Apache-2.0 and lives in a separate repository.
