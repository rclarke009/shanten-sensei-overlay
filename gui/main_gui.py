"""
Main GUI for Shanten Sensei overlay (fork of Mahjong Copilot).
Desktop app based on tkinter: browser control, AI guidance, Why? coaching.
"""

import os
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from bot_manager import BotManager, mjai_reaction_2_guide
from common.utils import Folder, GameMode, GAME_MODES, GameClientType
from common.utils import UiState, sub_file, error_to_str
from common.log_helper import LOGGER, LogHelper
from common.settings import Settings
from common.mj_helper import GameInfo, MJAI_TILE_2_UNICODE
from updater import Updater, UpdateStatus
from .utils import GUI_STYLE, window_size
from .settings_window import SettingsWindow
from .help_window import HelpWindow
from .first_run_wizard import show_first_run_wizard
from .widgets import *  # pylint: disable=wildcard-import, unused-wildcard-import


class MainGUI(tk.Tk):
    """ Main GUI Window"""
    def __init__(self, setting:Settings, bot_manager:BotManager):
        super().__init__()
        self.bot_manager = bot_manager
        self.st = setting
        self.updater = Updater(self.st.update_url)
        self.after_idle(self.updater.load_help)
        self.after_idle(self.updater.check_update)        # check update when idle
        
        icon = tk.PhotoImage(file=sub_file(Folder.RES,'icon.png'))
        self.iconphoto(True, icon)
        self.protocol("WM_DELETE_WINDOW", self._on_exit)        # confirmation before close window  
        default_size, min_size = self._window_sizes(
            self.st.hide_ai_options, hide_toolbars=False
        )
        self.geometry(f"{default_size[0]}x{default_size[1]}")
        self.minsize(*min_size)
        self._reason_log_len = 0
        self._why_text = ""
        self._yakuman_said_bye = False
        self._yakuman_pose = "idle"
        self._reason_log_expanded = False
        self._gameinfo_expanded = False
        self._layout_stage = -1
        self._layout_adapt_pending = False
        self._safari_reconnect_pending = False
        self._safari_reconnect_waiting = False
        # None = auto may collapse/expand; True/False = user forced visible/hidden this session
        self._toolbar_user_override: bool | None = None
        self._last_in_game: bool | None = None
        # Styling
        scaling_factor = self.winfo_fpixels('1i') / 96
        GUI_STYLE.set_dpi_scaling(scaling_factor)
        style = ttk.Style(self)
        GUI_STYLE.set_style_normal(style, dark=self.st.dark_theme)
        GUI_STYLE.paint_root(self)
        # icon resources:
        self.icon_green = sub_file(Folder.RES,'green.png')
        self.icon_red = sub_file(Folder.RES,'red.png')
        self.icon_yellow = sub_file(Folder.RES,'yellow.png')
        self.icon_gray =sub_file(Folder.RES,'gray.png')
        self.icon_ready = sub_file(Folder.RES,'ready.png')

        # create window widgets
        self._create_widgets()

        self.bot_manager.start()        # start the main program
        self.gui_update_delay = 50      # in ms
        self._update_gui_info()         # start updating gui info
        self.after(400, lambda: show_first_run_wizard(self, self.st))
        

    def _create_widgets(self):
        """ Create all widgets in the main window"""
        # Main window properties
        self.title(self.st.lan().APP_TITLE)
        style = ttk.Style(self)
        GUI_STYLE.set_style_normal(style, dark=self.st.dark_theme)
        GUI_STYLE.paint_root(self)
        
        # container for grid control
        self.grid_frame = tk.Frame(self)
        GUI_STYLE.paint_frame(self.grid_frame)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        grid_args = {'column':0, 'sticky': tk.EW, 'padx': 5, 'pady': 2}
        self._toolbar_grid_args = grid_args
        sunken = GUI_STYLE.sunken_kwargs()

        # === controls header (always visible; toggles toolbars) ===
        cur_row = 0
        self.controls_header = tk.Frame(self.grid_frame)
        GUI_STYLE.paint_frame(self.controls_header)
        self.controls_header.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        self.btn_controls = ttk.Button(
            self.controls_header,
            text=self.st.lan().CONTROLS_HIDE,
            command=self._on_controls_toggle,
        )
        self.btn_controls.pack(side=tk.LEFT)
        
        # === toolbar frame ===
        cur_row += 1
        self._toolbar_row = cur_row
        tb_ht = 70
        pack_args = {'side':tk.LEFT, 'padx':4, 'pady':4}
        self.toolbar = ToolBar(self.grid_frame, tb_ht)
        self.toolbar.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        
        # start game button (Yakuman + play triangle)
        self.toolbar.add_sep()
        self.btn_start_browser = self.toolbar.add_button(
            self.st.lan().START_BROWSER, 'yakuman_play.png', self._on_btn_start_browser_clicked)
        # buttons on toolbar
        self.toolbar.add_sep()
        self.toolbar.add_button(self.st.lan().SETTINGS, 'settings.png', self._on_btn_settings_clicked)
        self.toolbar.add_button(self.st.lan().OPEN_LOG_FILE, 'log.png', self._on_btn_log_clicked)
        self.btn_help = self.toolbar.add_button(self.st.lan().HELP, 'help.png', self._on_btn_help_clicked)
        self.toolbar.add_sep()
        self.toolbar.add_button(self.st.lan().EXIT, 'exit.png', self._on_exit)
        
        # === 2nd toolbar ===
        cur_row += 1
        self._tb2_row = cur_row
        self.tb2 = ToolBar(self.grid_frame, tb_ht)
        self.tb2.grid(row=cur_row, **grid_args)
        sw_ft_sz = 10
        self.tb2.add_sep()
        # Switches
        self.switch_overlay = ToggleSwitch(
            self.tb2, self.st.lan().WEB_OVERLAY, tb_ht, font_size=sw_ft_sz, command=self._on_switch_hud_clicked)
        self.switch_overlay.pack(**pack_args)
        self.tb2.add_sep()
        self.switch_autoplay = ToggleSwitch(
            self.tb2, self.st.lan().AUTOPLAY, tb_ht, font_size=sw_ft_sz, command=self._on_switch_autoplay_clicked)
        self.switch_autoplay.pack(**pack_args)
        # auto join
        self.tb2.add_sep()
        self.switch_autojoin = ToggleSwitch(
            self.tb2, self.st.lan().AUTO_JOIN_GAME, tb_ht, font_size=sw_ft_sz, command=self._on_switch_autojoin_clicked)
        self.switch_autojoin.pack(**pack_args)
        # combo boxrd for auto join level and mode
        _frame = tk.Frame(self.tb2)
        GUI_STYLE.paint_frame(_frame)
        _frame.pack(**pack_args)
        self.auto_join_level_var = tk.StringVar(value=self.st.lan().GAME_LEVELS[self.st.auto_join_level])
        options = self.st.lan().GAME_LEVELS
        combo_autojoin_level = ttk.Combobox(_frame, textvariable=self.auto_join_level_var, values=options, state="readonly", width=8)
        combo_autojoin_level.grid(row=0, column=0, padx=3, pady=3)   
        combo_autojoin_level.bind("<<ComboboxSelected>>", self._on_autojoin_level_selected)        
        mode_idx = GAME_MODES.index(self.st.auto_join_mode)
        self.auto_join_mode_var = tk.StringVar(value=self.st.lan().GAME_MODES[mode_idx])
        options = self.st.lan().GAME_MODES
        combo_autojoin_mode = ttk.Combobox(_frame, textvariable=self.auto_join_mode_var, values=options, state="readonly", width=8)
        combo_autojoin_mode.grid(row=1, column=0, padx=3, pady=3)
        combo_autojoin_mode.bind("<<ComboboxSelected>>", self._on_autojoin_mode_selected)
        # timer
        self.timer = Timer(self.tb2, tb_ht, sw_ft_sz, self.st.lan().AUTO_JOIN_TIMER)
        self.timer.set_callback(self.bot_manager.disable_autojoin)        # stop autojoin when time is up
        self.timer.pack(**pack_args)
        self.tb2.add_sep()

        # Always start with Controls expanded (session collapse only; not persisted)
        self._set_toolbars_visible(True)
               
        # === practice banner ===
        cur_row += 1
        self._banner_row = cur_row
        self.banner_frame = tk.Frame(self.grid_frame)
        GUI_STYLE.paint_frame(self.banner_frame)
        self.banner_frame.grid(row=cur_row, **grid_args)
        self.banner_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        self.banner_var = tk.StringVar(value=self.st.lan().PRACTICE_ONLY)
        banner_fg = "#e8b86d" if self.st.dark_theme else "#8B4513"
        self.banner_label = ttk.Label(
            self.banner_frame,
            textvariable=self.banner_var,
            foreground=banner_fg,
        )
        self.banner_label.grid(row=0, column=0, sticky=tk.W)
        self.btn_reconnect_safari = ttk.Button(
            self.banner_frame,
            text=self.st.lan().SAFARI_RECONNECT,
            command=self._on_reconnect_safari_clicked,
        )
        self.btn_reconnect_safari.grid(row=0, column=1, sticky=tk.E, padx=(8, 0))

        wrap = 440 if self.st.hide_ai_options else 580

        # === Aiming for (always visible) + Yaku list + Why? button ===
        cur_row += 1
        self.aim_header = tk.Frame(self.grid_frame)
        GUI_STYLE.paint_frame(self.aim_header)
        self.aim_header.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        ttk.Label(self.aim_header, text=self.st.lan().AIMING_FOR).pack(side=tk.LEFT)
        self.btn_why = ttk.Button(
            self.aim_header, text=self.st.lan().WHY_BUTTON, command=self._on_btn_why_clicked
        )
        self.btn_why.pack(side=tk.RIGHT, padx=4)
        self.btn_yaku_list = ttk.Button(
            self.aim_header,
            text=self.st.lan().YAKU_LIST,
            command=self._on_btn_yaku_list_clicked,
        )
        self.btn_yaku_list.pack(side=tk.RIGHT, padx=4)
        cur_row += 1
        self.aiming_var = tk.StringVar()
        self.text_aiming = tk.Label(
            self.grid_frame,
            textvariable=self.aiming_var,
            font=GUI_STYLE.font_normal("Segoe UI", 12),
            height=2, anchor=tk.W, justify=tk.LEFT, wraplength=wrap,
            relief=tk.SUNKEN, padx=5, pady=3,
            **sunken,
        )
        self.text_aiming.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)

        # === AI guidance (hidden in compact coach mode) ===
        cur_row += 1
        self.ai_header = tk.Frame(self.grid_frame)
        GUI_STYLE.paint_frame(self.ai_header)
        self._ai_header_row = cur_row
        ttk.Label(self.ai_header, text=self.st.lan().AI_OUTPUT).pack(side=tk.LEFT)
        if not self.st.hide_ai_options:
            self.ai_header.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)

        cur_row += 1
        self._ai_guide_row = cur_row
        self.ai_guide_var = tk.StringVar()
        self.text_ai_guide = tk.Label(
            self.grid_frame,
            textvariable=self.ai_guide_var,
            font=GUI_STYLE.font_normal("Segoe UI Emoji", 22),
            height=5, anchor=tk.NW, justify=tk.LEFT,
            relief=tk.SUNKEN, padx=5, pady=5,
            **sunken,
        )
        if not self.st.hide_ai_options:
            self.text_ai_guide.grid(row=cur_row, **grid_args)
            self.grid_frame.grid_rowconfigure(cur_row, weight=1)
        else:
            self.grid_frame.grid_rowconfigure(cur_row, weight=0)

        # === Yakuman Why? row (sprite + scrollable tip) ===
        cur_row += 1
        ttk.Label(self.grid_frame, text=self.st.lan().SENSEI_EXPLAIN).grid(
            row=cur_row, **grid_args
        )
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        cur_row += 1
        self.why_row = tk.Frame(self.grid_frame)
        GUI_STYLE.paint_frame(self.why_row)
        self.why_row.grid(row=cur_row, column=0, sticky=tk.NSEW, padx=5, pady=2)
        self.why_row.grid_columnconfigure(1, weight=1)
        self.why_row.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(cur_row, weight=2, minsize=110)

        self._yakuman_img_idle = tk.PhotoImage(
            file=sub_file(Folder.RES, "yakuman_idle.png")
        ).subsample(4, 4)
        self._yakuman_img_talk = tk.PhotoImage(
            file=sub_file(Folder.RES, "yakuman_talk.png")
        ).subsample(4, 4)
        yakuman_kwargs = {"image": self._yakuman_img_idle, "bd": 0, "highlightthickness": 0}
        if GUI_STYLE.dark:
            yakuman_kwargs["bg"] = GUI_STYLE.bg
        self.yakuman_label = tk.Label(self.why_row, **yakuman_kwargs)
        self.yakuman_label.grid(row=0, column=0, sticky=tk.N, padx=(0, 6), pady=2)

        why_height = 6 if self.st.hide_ai_options else 7
        self.text_why = scrolledtext.ScrolledText(
            self.why_row,
            height=why_height,
            wrap=tk.WORD,
            font=GUI_STYLE.font_normal("Segoe UI Emoji", 14),
            relief=tk.SUNKEN,
            padx=5,
            pady=5,
            state=tk.DISABLED,
            **GUI_STYLE.text_kwargs(),
        )
        self.text_why.grid(row=0, column=1, sticky=tk.NSEW)
        self._why_text = ""
        self._set_why_text(self.st.lan().YAKUMAN_INTRO)

        # === Reason log (collapsed until user unfolds) ===
        cur_row += 1
        self._reason_log_header_row = cur_row
        self._reason_log_header = tk.Frame(self.grid_frame)
        GUI_STYLE.paint_frame(self._reason_log_header)
        self._reason_log_header.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        self._reason_log_header_label = ttk.Label(
            self._reason_log_header, text="", cursor="hand2"
        )
        self._reason_log_header_label.pack(side=tk.LEFT)
        self._reason_log_header_label.bind("<Button-1>", self._toggle_reason_log)
        self._reason_log_header.bind("<Button-1>", self._toggle_reason_log)
        cur_row += 1
        self._reason_log_row = cur_row
        self.reason_log_text = scrolledtext.ScrolledText(
            self.grid_frame,
            height=5,
            wrap=tk.WORD,
            font=GUI_STYLE.font_normal("Segoe UI", 11),
            relief=tk.SUNKEN,
            padx=4,
            pady=4,
            state=tk.DISABLED,
            **GUI_STYLE.text_kwargs(),
        )
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        self._reason_log_len = 0
        self._reason_log_expanded = False
        self._update_reason_log_header()

        # === game info (collapsed until user unfolds) + status strip ===
        cur_row += 1
        self._gameinfo_header_row = cur_row
        self._gameinfo_header = tk.Frame(self.grid_frame)
        GUI_STYLE.paint_frame(self._gameinfo_header)
        self._gameinfo_header.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        self._gameinfo_header_label = ttk.Label(
            self._gameinfo_header, text="", cursor="hand2"
        )
        self._gameinfo_header_label.pack(side=tk.LEFT)
        self._gameinfo_header_label.bind("<Button-1>", self._toggle_gameinfo)
        self._gameinfo_header.bind("<Button-1>", self._toggle_gameinfo)
        cur_row += 1
        self._gameinfo_row = cur_row
        self.gameinfo_var = tk.StringVar()
        self.text_gameinfo = tk.Label(
            self.grid_frame,
            textvariable=self.gameinfo_var,
            height=2, anchor=tk.W, justify=tk.LEFT,
            font=GUI_STYLE.font_normal("Segoe UI Emoji", 22),
            relief=tk.SUNKEN, padx=5, pady=5,
            **sunken,
        )
        # Body starts collapsed; grid only when expanded
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        self._gameinfo_expanded = False
        self._update_gameinfo_header()

        cur_row += 1
        self._status_header_row = cur_row
        self._status_header = ttk.Label(self.grid_frame, text=self.st.lan().STATUS_STRIP)
        self._status_header.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        cur_row += 1
        self._status_row = cur_row
        self.status_strip_var = tk.StringVar()
        self.text_status_strip = tk.Label(
            self.grid_frame,
            textvariable=self.status_strip_var,
            height=1, anchor=tk.W, justify=tk.LEFT,
            font=GUI_STYLE.font_normal("Segoe UI", 12),
            relief=tk.SUNKEN, padx=5, pady=3,
            **sunken,
        )
        self.text_status_strip.grid(row=cur_row, **grid_args)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        
        # === Model info ===
        cur_row += 1
        self.model_bar = StatusBar(self.grid_frame, 2)
        self.model_bar.grid(row=cur_row, column=0, sticky='ew', padx=1, pady=1)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)
        
        # === status bar ===
        cur_row += 1
        self.status_bar = StatusBar(self.grid_frame, 3)
        self.status_bar.grid(row=cur_row, column=0, sticky='ew', padx=1, pady=1)
        self.grid_frame.grid_rowconfigure(cur_row, weight=0)

        self._layout_stage = -1
        self.unbind("<Configure>")
        self.bind("<Configure>", self._on_root_configure)
        self.after_idle(self._adapt_layout_height)
        self.after_idle(self._apply_startup_geometry)

    def _apply_startup_geometry(self) -> None:
        """Apply window size after widgets are laid out (macOS/tk needs post-layout geometry)."""
        self.update_idletasks()
        size, min_size = self._window_sizes(
            self.st.hide_ai_options, self.st.hide_toolbars
        )
        self.minsize(*min_size)
        self.geometry(f"{size[0]}x{size[1]}")

    @staticmethod
    def _window_sizes(
        hide_ai_options: bool, hide_toolbars: bool = False
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """Return (default_geometry, minsize) for the coaching window."""
        size = window_size(hide_ai_options, hide_toolbars)
        min_h = max(size[1] - 100, 280)
        return size, (size[0], min_h)

    def _apply_window_size(self) -> None:
        size, min_size = self._window_sizes(
            self.st.hide_ai_options, self.st.hide_toolbars
        )
        self.minsize(*min_size)
        self.geometry(f"{size[0]}x{size[1]}")

    def _update_controls_header(self) -> None:
        if not hasattr(self, "btn_controls"):
            return
        if self.st.hide_toolbars:
            self.btn_controls.config(text=self.st.lan().CONTROLS_SHOW)
        else:
            self.btn_controls.config(text=self.st.lan().CONTROLS_HIDE)

    def _set_toolbars_visible(self, visible: bool) -> None:
        """Show or hide the two setup toolbar rows; keep coaching panels."""
        hide = not visible
        changed = self.st.hide_toolbars != hide
        self.st.hide_toolbars = hide

        if visible:
            self.toolbar.grid(row=self._toolbar_row, **self._toolbar_grid_args)
            self.tb2.grid(row=self._tb2_row, **self._toolbar_grid_args)
        else:
            self.toolbar.grid_remove()
            self.tb2.grid_remove()

        self._update_controls_header()
        if changed:
            self._apply_window_size()

    def _on_controls_toggle(self) -> None:
        visible = self.st.hide_toolbars  # currently hidden → show
        self._toolbar_user_override = visible
        self._set_toolbars_visible(visible)

    def _maybe_auto_collapse_toolbars(self) -> None:
        """Collapse in-game / expand in lobby unless user overrode this session."""
        in_game = self.bot_manager.is_in_game()
        if self._last_in_game is None:
            self._last_in_game = in_game
            return
        if in_game == self._last_in_game:
            return
        self._last_in_game = in_game
        if self._toolbar_user_override is not None:
            return
        # Entering game → hide; leaving game → show
        self._set_toolbars_visible(not in_game)
    
    def report_callback_exception(self, exc, val, tb):
        """ override exception handling: write to log"""
        LOGGER.error("GUI uncaught exception: %s", exc, exc_info=True)
        # super().report_callback_exception(exc, val, tb)
    
    def _on_autojoin_level_selected(self, _event):
        new_value = self.auto_join_level_var.get()    # convert to index
        self.st.auto_join_level = self.st.lan().GAME_LEVELS.index(new_value)
        
        
    def _on_autojoin_mode_selected(self, _event):
        new_mode = self.auto_join_mode_var.get()  # convert to string
        new_mode = self.st.lan().GAME_MODES.index(new_mode)
        new_mode = GAME_MODES[new_mode]
        self.st.auto_join_mode = new_mode
        

    def _on_btn_start_browser_clicked(self):
        if self.st.safari_mode:
            return
        self.btn_start_browser.config(state=tk.DISABLED)
        self.bot_manager.start_browser()
        

    def _on_switch_hud_clicked(self):
        if self.st.safari_mode:
            return
        self.switch_overlay.switch_mid()
        if not self.st.enable_overlay:
            self.bot_manager.enable_overlay()
        else:
            self.bot_manager.disable_overlay()
            
            
    def _on_switch_autoplay_clicked(self):
        self.switch_autoplay.switch_mid()
        if self.st.enable_automation:
            self.bot_manager.disable_automation()
        else:
            self.bot_manager.enable_automation()
            

    def _on_switch_autojoin_clicked(self):
        self.switch_autojoin.switch_mid()
        if self.st.auto_join_game:
            self.bot_manager.disable_autojoin()
        else:
            self.bot_manager.enable_autojoin()

    def _on_btn_yaku_list_clicked(self):
        """Open the illustrated yaku reference in the default browser."""
        try:
            from shanten_sensei.glosses import YAKU_REFERENCE_URL
        except ImportError:
            YAKU_REFERENCE_URL = "https://www.mahjongmaster.co/learn/riichi/yaku/"
        webbrowser.open(YAKU_REFERENCE_URL)

    def _on_btn_why_clicked(self):
        """On-demand Sensei explanation for the pending Mortal recommendation."""
        if not self.bot_manager.why_enabled():
            mode = self.bot_manager.get_mode_verdict()
            self._set_why_text(
                self.st.lan().WHY_DISABLED + f" ({mode.reason})"
            )
            return
        result = self.bot_manager.explain_why_now()
        if result.ok:
            self._set_why_text(result.summary)
            if result.status_line:
                self.status_strip_var.set(result.status_line)
            if result.aiming_for:
                self.aiming_var.set(result.aiming_for)
            self._sync_reason_log(force=True)
        else:
            self._set_why_text(result.error or "Why? failed")

    def _set_yakuman_pose(self, pose: str) -> None:
        """Swap idle/talk sprite without animating or bouncing."""
        if pose == self._yakuman_pose:
            return
        img = self._yakuman_img_talk if pose == "talk" else self._yakuman_img_idle
        self.yakuman_label.configure(image=img)
        self._yakuman_pose = pose

    def _set_why_text(self, text: str, *, pose: str | None = None) -> None:
        """Update the Yakuman tip box; skip rewrite when unchanged."""
        if text == self._why_text:
            return
        self._why_text = text
        self.text_why.config(state=tk.NORMAL)
        self.text_why.delete("1.0", tk.END)
        if text:
            self.text_why.insert(tk.END, text)
            self.text_why.see("1.0")
        self.text_why.config(state=tk.DISABLED)
        if pose is not None:
            self._set_yakuman_pose(pose)
        elif text == self.st.lan().YAKUMAN_INTRO or text == self.st.lan().YAKUMAN_BYE:
            self._set_yakuman_pose("idle")
        elif text:
            self._set_yakuman_pose("talk")
        else:
            self._set_yakuman_pose("idle")

    def _update_reason_log_header(self) -> None:
        mark = "▾" if self._reason_log_expanded else "▸"
        base = self.st.lan().REASON_LOG
        n = self._reason_log_len
        suffix = f" ({n})" if n and not self._reason_log_expanded else ""
        self._reason_log_header_label.config(text=f"{mark} {base}{suffix}")

    def _toggle_reason_log(self, _event=None) -> None:
        self._set_reason_log_expanded(not self._reason_log_expanded)

    def _set_reason_log_expanded(self, expanded: bool) -> None:
        self._reason_log_expanded = expanded
        if expanded:
            self.reason_log_text.grid(
                row=self._reason_log_row, column=0, sticky=tk.NSEW, padx=5, pady=2
            )
            self.grid_frame.grid_rowconfigure(self._reason_log_row, weight=1)
        else:
            self.reason_log_text.grid_remove()
            self.grid_frame.grid_rowconfigure(self._reason_log_row, weight=0)
        self._update_reason_log_header()
        # Re-evaluate sacrificial rows after log open/close changes preferred height
        self._layout_stage = -1
        self.after_idle(self._adapt_layout_height)

    def _update_gameinfo_header(self) -> None:
        mark = "▾" if self._gameinfo_expanded else "▸"
        self._gameinfo_header_label.config(text=f"{mark} {self.st.lan().GAME_INFO}")

    def _toggle_gameinfo(self, _event=None) -> None:
        self._set_gameinfo_expanded(not self._gameinfo_expanded)

    def _set_gameinfo_expanded(self, expanded: bool) -> None:
        self._gameinfo_expanded = expanded
        if expanded:
            self.text_gameinfo.grid(
                row=self._gameinfo_row, column=0, sticky=tk.EW, padx=5, pady=2
            )
        else:
            self.text_gameinfo.grid_remove()
        self._update_gameinfo_header()
        self._layout_stage = -1
        self.after_idle(self._adapt_layout_height)

    def _on_root_configure(self, event) -> None:
        if event.widget is not self:
            return
        if self._layout_adapt_pending:
            return
        self._layout_adapt_pending = True
        self.after_idle(self._adapt_layout_height)

    def _adapt_layout_height(self) -> None:
        """Hide Hand status, then Game Info, when the window is short."""
        self._layout_adapt_pending = False
        if not hasattr(self, "_status_header"):
            return
        h = self.winfo_height()
        if h <= 1:
            return
        preferred = 620
        if self._reason_log_expanded:
            preferred += 120
        if h >= preferred - 50:
            stage = 0
        elif h >= preferred - 110:
            stage = 1
        else:
            stage = 2
        if stage == self._layout_stage:
            return
        self._apply_layout_stage(stage)

    def _apply_layout_stage(self, stage: int) -> None:
        self._layout_stage = stage
        grid_args = {"column": 0, "sticky": tk.EW, "padx": 5, "pady": 2}
        show_game = stage < 2
        show_status = stage < 1
        if show_game:
            self._gameinfo_header.grid(row=self._gameinfo_header_row, **grid_args)
            if self._gameinfo_expanded:
                self.text_gameinfo.grid(row=self._gameinfo_row, **grid_args)
            else:
                self.text_gameinfo.grid_remove()
        else:
            self._gameinfo_header.grid_remove()
            self.text_gameinfo.grid_remove()
        if show_status:
            self._status_header.grid(row=self._status_header_row, **grid_args)
            self.text_status_strip.grid(row=self._status_row, **grid_args)
        else:
            self._status_header.grid_remove()
            self.text_status_strip.grid_remove()

    def _sync_reason_log(self, *, force: bool = False) -> None:
        entries = self.bot_manager.get_reason_log()
        if not force and len(entries) == self._reason_log_len:
            return
        self._reason_log_len = len(entries)
        lines = []
        for e in entries:
            pin = e.pinned_action or "?"
            k = e.kyoku if e.kyoku is not None else "?"
            h = e.honba if e.honba is not None else 0
            lines.append(f"[kyoku {k}/{h}] {pin}\n  {e.summary}")
        text = "\n\n".join(lines)
        self.reason_log_text.config(state=tk.NORMAL)
        self.reason_log_text.delete("1.0", tk.END)
        if text:
            self.reason_log_text.insert(tk.END, text)
            self.reason_log_text.see(tk.END)
        self.reason_log_text.config(state=tk.DISABLED)
        self._update_reason_log_header()

    def _on_btn_log_clicked(self):
        # LOGGER.debug('Open log')
        try:
            os.startfile(LogHelper.log_file_name)
        except AttributeError:
            # macOS / Linux
            import subprocess
            subprocess.Popen(["open", LogHelper.log_file_name])  # noqa: S603
        

    def _on_btn_settings_clicked(self):
        # open settings dialog (modal/blocking)
        settings_window = SettingsWindow(self, self.st)
        settings_window.transient(self)
        settings_window.grab_set()
        self.wait_window(settings_window)
        
        if settings_window.exit_save:
            if settings_window.model_updated:
                self.bot_manager.set_bot_update()
            if settings_window.gui_need_reload:
                self.reload_gui()
            # mitm port occupy issue. Need to restart program for now
            # if settings_window.mitm_proxinject_updated:
                # message box to tell user to restart
                
            #     self.bot_manager.set_mitm_proxinject_update()
            

    def _on_btn_help_clicked(self):
        # open help dialog        
        help_win = HelpWindow(self, self.st, self.updater)
        help_win.transient(self)
        help_win.grab_set()

    def _on_reconnect_safari_clicked(self):
        if self._safari_reconnect_pending:
            return
        lan = self.st.lan()
        if not messagebox.askokcancel(
            lan.SAFARI_RECONNECT_TITLE,
            lan.SAFARI_RECONNECT_CONFIRM,
            parent=self,
        ):
            return

        self._safari_reconnect_pending = True
        self.btn_reconnect_safari.config(state=tk.DISABLED)

        def _run_reconnect():
            error = None
            try:
                self.bot_manager.reconnect_safari_client()
            except Exception as exc:  # pylint: disable=broad-exception-caught
                LOGGER.error("Safari reconnect failed: %s", exc, exc_info=True)
                error = exc

            def _finish():
                self._safari_reconnect_pending = False
                if error is None:
                    self._safari_reconnect_waiting = True
                else:
                    self._safari_reconnect_waiting = False
                    messagebox.showerror(
                        lan.SAFARI_RECONNECT_TITLE,
                        error_to_str(error, lan),
                        parent=self,
                    )
                self._update_gui()

            self.after(0, _finish)

        threading.Thread(target=_run_reconnect, name="SafariReconnect", daemon=True).start()
        
    
    def _on_exit(self):
        # Exit the app
        # pop up that confirm if the user really wants to quit
        if messagebox.askokcancel(self.st.lan().EXIT, self.st.lan().EIXT_CONFIRM, parent=self):
            try:
                LOGGER.info("Exiting GUI and program")
                self.status_bar.update_column(2, self.st.lan().EXIT + "ing...", self.icon_yellow)
                self.update_idletasks()
                self.st.save_json()
                self.bot_manager.stop(True)
            except: #pylint:disable=bare-except
                pass
            self.quit()
            
            
    def reload_gui(self):
        """ Clear UI compontes and rebuid widgets"""       
        for widget in self.winfo_children():
            widget.destroy()
        default_size, min_size = self._window_sizes(
            self.st.hide_ai_options, self.st.hide_toolbars
        )
        self.geometry(f"{default_size[0]}x{default_size[1]}")
        self.minsize(*min_size)
        self._reason_log_expanded = False
        self._gameinfo_expanded = False
        self._layout_stage = -1
        self._layout_adapt_pending = False
        self._safari_reconnect_pending = False
        self._safari_reconnect_waiting = False
        self._create_widgets()
        

    def _update_gui_info(self):
        """ Update GUI widgets status with latest info from bot manager"""
        try:
            self._update_gui_info_inner()
        except Exception as e:
            LOGGER.error("Error updating GUI: %s", e, exc_info=True)
        self.after(self.gui_update_delay, self._update_gui_info)
            
    def _update_gui_info_inner(self):
        """ Update GUI widgets status with latest info from bot manager"""
        # start browser button state (disabled in Safari companion mode)
        if self.st.safari_mode:
            self.btn_start_browser.config(state=tk.DISABLED)
        elif not self.bot_manager.browser.is_running():
            if self.bot_manager.get_game_client_type() == GameClientType.PROXY:
                self.btn_start_browser.config(state=tk.DISABLED)    # disable when proxy client running
            else:
                self.btn_start_browser.config(state=tk.NORMAL)
        else:
            self.btn_start_browser.config(state=tk.DISABLED)

        # help button
        if self.updater.update_status in (
            UpdateStatus.NEW_VERSION,
            UpdateStatus.DOWNLOADING,
            UpdateStatus.UNZIPPING,
            UpdateStatus.PREPARED
        ):
            self.toolbar.set_img(self.btn_help, 'help_update.png')
        else:
            self.toolbar.set_img(self.btn_help, 'help.png')
        
        # update switch states (in-page Overlay is Chromium-only; clicks no-op in safari_mode)
        sw_list = [
            (self.switch_overlay, lambda: False if self.st.safari_mode else self.st.enable_overlay),
            (self.switch_autoplay, lambda: self.st.enable_automation),
            (self.switch_autojoin, lambda: self.st.auto_join_game)
        ]
        for sw, func in sw_list:
            if func():
                sw.switch_on()
            else:
                sw.switch_off()

        # Practice banner + Why? button state (+ Safari dual-window hint)
        mode = self.bot_manager.get_mode_verdict()
        client_type = self.bot_manager.get_game_client_type()
        if self.bot_manager.is_in_game() and not mode.why_enabled:
            self.banner_var.set(self.st.lan().WHY_DISABLED + f" — {mode.reason}")
            self.btn_why.config(state=tk.DISABLED)
            self._safari_reconnect_waiting = False
        elif self._safari_reconnect_waiting and self.st.safari_mode:
            self.banner_var.set(
                self.st.lan().PRACTICE_ONLY + " — " + self.st.lan().SAFARI_RECONNECT_WAITING
            )
            self.btn_why.config(
                state=tk.NORMAL if self.bot_manager.why_enabled() else tk.DISABLED
            )
        elif self.st.safari_mode:
            self.banner_var.set(
                self.st.lan().PRACTICE_ONLY + " — " + self.st.lan().SAFARI_HINT
            )
            self.btn_why.config(
                state=tk.NORMAL if self.bot_manager.why_enabled() else tk.DISABLED
            )
        else:
            self.banner_var.set(self.st.lan().PRACTICE_ONLY)
            self._safari_reconnect_waiting = False
            self.btn_why.config(
                state=tk.NORMAL if self.bot_manager.why_enabled() else tk.DISABLED
            )

        if (
            self.st.safari_mode
            and client_type != GameClientType.PROXY
            and not self._safari_reconnect_pending
        ):
            self.btn_reconnect_safari.grid(row=0, column=1, sticky=tk.E, padx=(8, 0))
            self.btn_reconnect_safari.config(state=tk.NORMAL)
        elif self._safari_reconnect_pending:
            self.btn_reconnect_safari.grid(row=0, column=1, sticky=tk.E, padx=(8, 0))
            self.btn_reconnect_safari.config(state=tk.DISABLED)
        else:
            self.btn_reconnect_safari.grid_remove()
            if client_type == GameClientType.PROXY:
                self._safari_reconnect_waiting = False

        # Update AI guide from Reaction (skip when compact coach hides options)
        pending_reaction = self.bot_manager.get_pending_reaction()
        if self.st.hide_ai_options:
            self.ai_guide_var.set("")
        elif pending_reaction:
            ai_guide_str, options = mjai_reaction_2_guide(pending_reaction, 3, self.st.lan())
            ai_guide_str += '\n'
            for tile_str, weight in options:
                ai_guide_str += f" {tile_str:8}  {weight*100:4.0f}%\n"
            self.ai_guide_var.set(ai_guide_str)
        else:
            self.ai_guide_var.set("")

        # Yakuman Why? + status strip + aiming (keep intro/bye; blank only stale tips)
        ended = bool(
            self.bot_manager.game_state and self.bot_manager.game_state.is_game_ended
        )
        if not ended:
            self._yakuman_said_bye = False
        intro = self.st.lan().YAKUMAN_INTRO
        bye = self.st.lan().YAKUMAN_BYE
        if ended and not self._yakuman_said_bye:
            self._yakuman_said_bye = True
            self._set_why_text(bye, pose="idle")
        elif ended and self._yakuman_said_bye:
            pass  # keep goodbye until the next game
        else:
            why = self.bot_manager.get_last_why()
            if why and why.ok:
                self._set_why_text(why.summary, pose="talk")
            elif self._why_text == intro:
                pass  # intro stays until the first tip
            else:
                self._set_why_text("")
        status = self.bot_manager.get_status_line()
        if status:
            self.status_strip_var.set(status)
        else:
            self.status_strip_var.set("")
        aiming = self.bot_manager.get_aiming_for()
        if aiming:
            self.aiming_var.set(aiming)
        else:
            self.aiming_var.set("")
        self._sync_reason_log()

        # update game info: display tehai + tsumohai
        gi:GameInfo = self.bot_manager.get_game_info()
        if gi and gi.my_tehai:
            tehai = gi.my_tehai
            tsumohai = gi.my_tsumohai
            hand_str = ''.join(MJAI_TILE_2_UNICODE[t] for t in tehai)
            if tsumohai:
                hand_str += f" + {MJAI_TILE_2_UNICODE[tsumohai]}"
            self.gameinfo_var.set(hand_str)
        else:
            self.gameinfo_var.set("")

        # bot/model info
        if self.bot_manager.is_bot_created():
            mode_strs = []
            for m in GameMode:
                if m in self.bot_manager.bot.supported_modes:
                    mode_strs.append('✔' + m.value)
                else:
                    mode_strs.append('✖' + m.value)
            mode_str = ' | '.join(mode_strs)
            text = f"{self.st.lan().MODEL}: {self.st.model_type} ({mode_str})"
            self.model_bar.update_column(0, text, self.icon_green)
            if self.bot_manager.is_game_syncing():
                self.model_bar.update_column(1, '⌛ ' + self.st.lan().SYNCING)
            elif self.bot_manager.is_bot_calculating():
                self.model_bar.update_column(1, '⌛ ' + self.st.lan().CALCULATING)
            else:
                self.model_bar.update_column(1, 'ℹ️' + self.bot_manager.bot.info_str)
        else:   # bot is not ready
            if self.bot_manager.is_loading_bot:
                text = self.st.lan().MODEL_LOADING
                icon = self.icon_yellow
            else:
                text = self.st.lan().MODEL_NOT_LOADED
                icon = self.icon_red
            self.model_bar.update_column(0, text, icon)
            self.model_bar.update_column(1, '')

        # Status bar
        # main thread
        fps_disp = min([999, self.bot_manager.fps_counter.fps])
        fps_str = f"({fps_disp:3.0f})"
        if self.bot_manager.is_running():       # main thread
            self.status_bar.update_column(0, self.st.lan().MAIN_THREAD + fps_str, self.icon_green)
        else:
            self.status_bar.update_column(0, self.st.lan().MAIN_THREAD + fps_str, self.icon_red)        

        # client/browser
        client_type = self.bot_manager.get_game_client_type()
        if client_type == GameClientType.PLAYWRIGHT:
            fps_disp = min(999, self.bot_manager.browser.fps_counter.fps)
            fps_str = f"({fps_disp:3.0f})"
            status_str = self.st.lan().BROWSER+fps_str
            if self.bot_manager.browser.is_running():
                icon = self.icon_green
            else:
                icon = self.icon_gray
        elif client_type == GameClientType.PROXY:
            status_str = self.st.lan().PROXY_CLIENT
            icon = self.icon_green
        elif self.st.safari_mode:
            status_str = self.st.lan().SAFARI_WAITING
            icon = self.icon_ready
        else:
            status_str = self.st.lan().GAME_NOT_RUNNING
            icon = self.icon_ready
        self.status_bar.update_column(1, status_str, icon)
            
        # status (last col)
        status_str, icon = self._get_status_text_icon(gi)
        self.status_bar.update_column(2, status_str, icon)
        
        ### update overlay
        self.bot_manager.update_overlay()

    def _get_status_text_icon(self, gi:GameInfo) -> tuple[str, str]:
        # Get text and icon for status bar last column, based on bot running info
        # show info as : thread error > game error > game status
        bot_exception = self.bot_manager.main_thread_exception
        if bot_exception:
            return error_to_str(bot_exception, self.st.lan()), self.icon_red
        else:   # no exception in bot manager
            pass
        
        game_error:Exception = self.bot_manager.get_game_error()
        if game_error:
            return error_to_str(game_error, self.st.lan()), self.icon_red
        if self.bot_manager.is_browser_zoom_off():
            return self.st.lan().BROWSER_ZOOM_OFF, self.icon_red        
            
        if self.bot_manager.is_in_game():
            info_str = self.st.lan().GAME_RUNNING
            if self.bot_manager.is_game_syncing():
                info_str += " - " + self.st.lan().SYNCING
                return info_str, self.icon_green
            else:   # game in progress
                if gi and gi.bakaze:
                    info_str += ' '.join([
                        "", "-",
                        f"{self.st.lan().mjai2str(gi.bakaze)}",
                        f"{gi.kyoku} {self.st.lan().KYOKU}",
                        f"{gi.honba} {self.st.lan().HONBA}",
                    ])
                else:
                    info_str += " - " + self.st.lan().GAME_STARTING
                return info_str, self.icon_green
        else:
            state_dict = {
                UiState.MAIN_MENU: self.st.lan().MAIN_MENU,
                UiState.GAME_ENDING: self.st.lan().GAME_ENDING,
                UiState.NOT_RUNNING: self.st.lan().GAME_NOT_RUNNING,
            }
            info_str = self.st.lan().READY_FOR_GAME + " - " + state_dict.get(self.bot_manager.automation.ui_state, "")
            return info_str, self.icon_ready
