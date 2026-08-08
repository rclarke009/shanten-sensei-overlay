"""Scrollable Terms I know checklist dialog."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from common.settings import Settings
from .utils import GUI_STYLE


def _checklist_items() -> list[tuple[str, str, str]]:
    """Return (id, group, gloss) rows; fall back if Sensei missing."""
    try:
        from shanten_sensei.glosses import GLOSS_CHECKLIST

        return [(i.id, i.group, i.gloss) for i in GLOSS_CHECKLIST]
    except Exception:
        return [
            ("ukeire", "Metrics", "tiles that improve the hand"),
            ("shanten", "Metrics", "steps from ready"),
            ("tanyao", "Yaku", "2–8 only; no 1/9, winds, or dragons"),
        ]


class TermsWindow(tk.Toplevel):
    """Checklist of coaching terms the player already knows."""

    def __init__(
        self,
        parent: tk.Misc,
        setting: Settings,
        *,
        initial_terms: list[str] | None = None,
    ):
        super().__init__(parent)
        self.st = setting
        self.exit_save = False
        seed = list(initial_terms if initial_terms is not None else self.st.known_terms)
        self.result_terms: list[str] = list(seed)

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"420x520+{parent_x + 40}+{parent_y + 40}")
        self.minsize(360, 420)
        self.title(self.st.lan().KNOWN_TERMS)

        style = ttk.Style(self)
        GUI_STYLE.set_style_normal(style, dark=self.st.dark_theme)
        GUI_STYLE.paint_root(self)

        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(
            button_frame, text=self.st.lan().CANCEL, command=self._on_cancel
        ).pack(side=tk.LEFT, padx=16, pady=10)
        ttk.Button(
            button_frame, text=self.st.lan().SAVE, command=self._on_save
        ).pack(side=tk.RIGHT, padx=16, pady=10)

        ttk.Label(self, text=self.st.lan().KNOWN_TERMS_HINT).pack(
            anchor="w", padx=16, pady=(0, 6)
        )

        canvas = tk.Canvas(self, highlightthickness=0)
        GUI_STYLE.paint_frame(canvas)
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=8)

        inner = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(window_id, width=canvas.winfo_width())

        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_configure)

        known = set(seed)
        self._vars: dict[str, tk.BooleanVar] = {}
        current_group = None
        for term_id, group, gloss in _checklist_items():
            if group != current_group:
                current_group = group
                ttk.Label(inner, text=group).pack(anchor="w", pady=(10, 2))
            var = tk.BooleanVar(value=term_id in known)
            self._vars[term_id] = var
            ttk.Checkbutton(
                inner,
                variable=var,
                text=f"{term_id}  ({gloss})",
            ).pack(anchor="w", padx=8)

        self.transient(parent)
        self.grab_set()

    def _on_save(self) -> None:
        self.result_terms = sorted(
            tid for tid, var in self._vars.items() if var.get()
        )
        self.exit_save = True
        self.destroy()

    def _on_cancel(self) -> None:
        self.exit_save = False
        self.destroy()
