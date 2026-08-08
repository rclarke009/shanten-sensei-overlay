"""First-run setup for non-developer macOS installs."""

from typing import Callable
import shutil
import sys
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from common.log_helper import LOGGER
from common.safari_reconnect import SafariReconnectError, quit_safari_and_open
from common.sensei_paths import write_sensei_env
from common.settings import Settings
from common.utils import Folder, sub_folder
from .utils import GUI_STYLE


AKAGI_MODEL_URL = "https://github.com/shinkuan/Akagi"


class FirstRunWizard(tk.Toplevel):
    """Walk through model, Safari companion, and optional API key."""

    def __init__(self, parent: tk.Tk, setting: Settings, *, on_done: Callable | None = None):
        super().__init__(parent)
        self.st = setting
        self._on_done = on_done
        self.title("Welcome to Shanten Sensei")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        style = ttk.Style(self)
        GUI_STYLE.set_style_normal(style, dark=self.st.dark_theme)
        GUI_STYLE.paint_root(self)

        self._practice_var = tk.BooleanVar(value=False)
        self._safari_var = tk.BooleanVar(value=True)
        self._api_key_var = tk.StringVar()
        self._model_path: Path | None = None

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_skip)

    def _build(self) -> None:
        pad = {"padx": 16, "pady": 6}
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Label(
            frame,
            text="Quick setup (practice / friend / vs-AI only — not ranked)",
            wraplength=520,
            font=("", 12, "bold"),
        ).pack(anchor=tk.W, **pad)

        ttk.Checkbutton(
            frame,
            text="I understand this is for learning in practice modes only",
            variable=self._practice_var,
        ).pack(anchor=tk.W, **pad)

        ttk.Separator(frame).pack(fill=tk.X, pady=8)

        ttk.Label(
            frame,
            text="1. Mortal model (.pth)",
            font=("", 11, "bold"),
        ).pack(anchor=tk.W, **pad)
        ttk.Label(
            frame,
            text="Download an Akagi-compatible Mortal model, then select the file.",
            wraplength=520,
        ).pack(anchor=tk.W, padx=16)
        model_row = ttk.Frame(frame)
        model_row.pack(fill=tk.X, **pad)
        self._model_label = ttk.Label(model_row, text="No model selected")
        self._model_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(model_row, text="Choose file…", command=self._pick_model).pack(
            side=tk.RIGHT
        )
        ttk.Button(
            frame,
            text="Get model from Akagi",
            command=lambda: webbrowser.open(AKAGI_MODEL_URL),
        ).pack(anchor=tk.W, padx=16)

        ttk.Separator(frame).pack(fill=tk.X, pady=8)

        ttk.Label(frame, text="2. Safari companion (recommended)", font=("", 11, "bold")).pack(
            anchor=tk.W, **pad
        )
        ttk.Checkbutton(
            frame,
            text="Use Safari companion mode (play Majsoul in Safari beside this window)",
            variable=self._safari_var,
        ).pack(anchor=tk.W, padx=16)
        ttk.Label(
            frame,
            text="You may see a Keychain prompt to trust the local proxy certificate.",
            wraplength=520,
        ).pack(anchor=tk.W, padx=16, pady=(0, 4))
        ttk.Button(
            frame,
            text="Quit Safari & reopen Majsoul",
            command=self._reopen_safari,
        ).pack(anchor=tk.W, padx=16)

        ttk.Separator(frame).pack(fill=tk.X, pady=8)

        ttk.Label(frame, text="3. Optional: LLM Why? (OpenAI key)", font=("", 11, "bold")).pack(
            anchor=tk.W, **pad
        )
        ttk.Label(
            frame,
            text="Leave blank to use offline template explanations.",
            wraplength=520,
        ).pack(anchor=tk.W, padx=16)
        ttk.Entry(frame, textvariable=self._api_key_var, width=56, show="•").pack(
            anchor=tk.W, padx=16, pady=4
        )

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X, pady=16)
        ttk.Button(btn_row, text="Skip for now", command=self._on_skip).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Finish setup", command=self._on_finish).pack(side=tk.RIGHT)

    def _pick_model(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Select Mortal model (.pth)",
            filetypes=[("PyTorch model", "*.pth"), ("All files", "*.*")],
        )
        if not path:
            return
        self._model_path = Path(path)
        self._model_label.config(text=str(self._model_path))

    def _reopen_safari(self) -> None:
        try:
            quit_safari_and_open(self.st.ms_url)
            messagebox.showinfo(
                "Safari",
                "Safari was quit and Majsoul was opened. Join a friend or practice game.",
                parent=self,
            )
        except SafariReconnectError as exc:
            messagebox.showerror("Safari", str(exc), parent=self)

    def _on_skip(self) -> None:
        self.destroy()
        if self._on_done:
            self._on_done()

    def _on_finish(self) -> None:
        if not self._practice_var.get():
            messagebox.showwarning(
                "Practice only",
                "Please confirm practice-only use before continuing.",
                parent=self,
            )
            return

        if self._model_path and self._model_path.is_file():
            models_dir = sub_folder(Folder.MODEL)
            dest = models_dir / "mortal.pth"
            try:
                shutil.copy2(self._model_path, dest)
                self.st.model_file = "mortal.pth"
            except OSError as exc:
                LOGGER.warning("Could not copy model: %s", exc)
                messagebox.showerror("Model", f"Could not copy model:\n{exc}", parent=self)
                return
        elif not self._model_path:
            if not messagebox.askyesno(
                "No model",
                "No model file was selected. You can add one later in Settings.\n\nContinue anyway?",
                parent=self,
            ):
                return

        self.st.safari_mode = self._safari_var.get()
        self.st.auto_launch_browser = False
        self.st.enable_proxinject = False

        api_key = self._api_key_var.get().strip()
        if api_key:
            write_sensei_env(openai_api_key=api_key, use_llm=True)
            try:
                from shanten_sensei.envutil import load_dotenv
                from common.sensei_paths import sensei_env_path

                load_dotenv(sensei_env_path(), override=True)
            except ImportError:
                pass

        self.st.setup_complete = True
        self.st.save_json()
        messagebox.showinfo(
            "Ready",
            "Setup saved. Start the overlay, open Majsoul in Safari, and press Why? on your turn.",
            parent=self,
        )
        self.destroy()
        if self._on_done:
            self._on_done()


def show_first_run_wizard(parent: tk.Tk, setting: Settings, *, on_done: Callable | None = None) -> None:
    """Open wizard when setup is incomplete (macOS live path)."""
    if setting.setup_complete or sys.platform != "darwin":
        return
    FirstRunWizard(parent, setting, on_done=on_done)
