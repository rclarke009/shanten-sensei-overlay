""" Settings file and options """

import json
import sys
from pathlib import Path
from typing import Callable
from .log_helper import LOGGER
from .lan_str import DEFAULT_LANGUAGE, DEFAULT_MAJSOUL_URL, LanStr, LAN_OPTIONS
from . import utils

DEFAULT_SETTING_FILE = 'settings.json'
# Bump when deliverable installs should re-apply English UI + YoStar URL (e.g. after update).
LOCALE_DEFAULTS_VERSION = 1


def apply_deliverable_locale_defaults(settings: "Settings") -> bool:
    """English overlay UI + YoStar Majsoul URL for Mac deliverable installs."""
    changed = False
    if settings.language != DEFAULT_LANGUAGE:
        settings.language = DEFAULT_LANGUAGE
        changed = True
    if settings.ms_url != DEFAULT_MAJSOUL_URL:
        settings.ms_url = DEFAULT_MAJSOUL_URL
        changed = True
    return changed


def _migrate_deliverable_locale(settings: "Settings") -> None:
    """Re-apply English defaults once per LOCALE_DEFAULTS_VERSION (covers app updates)."""
    if settings.locale_defaults_version >= LOCALE_DEFAULTS_VERSION:
        return
    apply_deliverable_locale_defaults(settings)
    settings.locale_defaults_version = LOCALE_DEFAULTS_VERSION

def _settings_path(json_file: str) -> str:
    """Resolve settings file path (writable; Application Support when frozen)."""
    path = Path(json_file)
    if path.is_absolute():
        return str(path)
    if getattr(sys, "frozen", False):
        from common.sensei_paths import app_support_dir
        return str(app_support_dir() / json_file)
    return utils.sub_file(".", json_file)

class Settings:
    """ Settings class to load and save settings to json file"""
    def __init__(self, json_file:str=DEFAULT_SETTING_FILE) -> None:
        self._json_file = json_file
        self._settings_path = _settings_path(json_file)
        self._settings_dict:dict = self.load_json()        
        # read settings or set default values
        # variable names must match keys in json, for saving later

        # UI settings
        self.update_url:str = self._get_value("update_url", "https://update.mjcopilot.com", self.valid_url) # not shown
        self.auto_launch_browser:bool = self._get_value("auto_launch_browser", False, self.valid_bool)
        self.gui_set_dpi:bool = self._get_value("gui_set_dpi", True, self.valid_bool)
        self.browser_width:int = self._get_value("browser_width", 1280, lambda x: 0 < x < 19999)
        self.browser_height:int = self._get_value("browser_height", 720, lambda x: 0 < x < 19999)
        self.ms_url:str = self._get_value("ms_url", DEFAULT_MAJSOUL_URL, self.valid_url)
        self.enable_chrome_ext:bool = self._get_value("enable_chrome_ext", False, self.valid_bool)
        self.mitm_port:int = self._get_value("mitm_port", 10999, self.valid_mitm_port)
        self.upstream_proxy:str = self._get_value("upstream_proxy","")  # mitm upstream proxy server e.g. http://ip:port
        self.enable_proxinject:bool = self._get_value("enable_proxinject", False, self.valid_bool)
        self.inject_process_name:str = self._get_value("inject_process_name", "jantama_mahjongsoul")
        self.language:str = self._get_value("language", DEFAULT_LANGUAGE, self.valid_language)
        self.enable_overlay:bool = self._get_value("enable_overlay", True, self.valid_bool) # not shown
        # Safari companion: PAC-scoped proxy + companion window (macOS); no Playwright Chromium
        self.safari_mode: bool = self._get_value("safari_mode", False, self.valid_bool)
        
        # AI Model settings
        self.model_type:str = self._get_value("model_type", "Local")
        """ model type: local, mjapi"""
        # for local model
        self.model_file:str = self._get_value("model_file", "mortal.pth")
        self.model_file_3p:str = self._get_value("model_file_3p", "mortal_3p.pth")
        # akagi ot model
        self.akagi_ot_url:str = self._get_value("akagi_ot_url", "")
        self.akagi_ot_apikey:str = self._get_value("akagi_ot_apikey", "")
        # for mjapi
        self.mjapi_url:str = self._get_value("mjapi_url", "https://mjai.7xcnnw11phu.eu.org", self.valid_url)
        self.mjapi_user:str = self._get_value("mjapi_user", "")
        self.mjapi_secret:str = self._get_value("mjapi_secret", "")
        self.mjapi_models:list = self._get_value("mjapi_models",[])
        self.mjapi_model_select:str = self._get_value("mjapi_model_select","baseline")
        
        # Automation settings
        self.enable_automation:bool = self._get_value("enable_automation", False, self.valid_bool)
        self.auto_idle_move:bool = self._get_value("auto_idle_move", False, self.valid_bool)
        self.auto_random_move:bool = self._get_value("auto_random_move", False, self.valid_bool)
        self.auto_reply_emoji_rate:float = self._get_value("auto_reply_emoji_rate", 0.3, lambda x: 0 <= x <= 1)
        self.auto_emoji_intervel:float = self._get_value("auto_emoji_intervel", 5.0, lambda x: 1.0 < x < 30.0)
        self.auto_dahai_drag:bool = self._get_value("auto_dahai_drag", True, self.valid_bool)
        self.ai_randomize_choice:int = self._get_value("ai_randomize_choice", 1, lambda x: 0 <= x <= 5)
        self.delay_random_lower:float = self._get_value("delay_random_lower", 1, lambda x: 0 <= x )
        self.delay_random_upper:float = self._get_value(
            "delay_random_upper",max(2, self.delay_random_lower), lambda x: x >= self.delay_random_lower)
        self.auto_retry_interval:float = self._get_value("auto_retry_interval", 1.5, lambda x: 0.5 < x < 30.0)  # not shown
        
        self.auto_join_game:bool = self._get_value("auto_join_game", False, self.valid_bool)
        self.auto_join_level:int = self._get_value("auto_join_level", 1, self.valid_game_level)
        self.auto_join_mode:int = self._get_value("auto_join_mode", utils.GAME_MODES[0], self.valid_game_mode)

        # Sensei: auto-regenerate Why? when Mortal tip changes (API cost per tip)
        self.auto_why: bool = self._get_value("auto_why", False, self.valid_bool)
        # Sensei: opt-in lead/trail/late-game point-situation tips (default off)
        self.score_tips: bool = self._get_value("score_tips", False, self.valid_bool)
        # Sensei: terms the player already knows (hide parenthetical definitions)
        raw_known = self._get_value("known_terms", [], self.valid_known_terms_list)
        self.known_terms: list = self._normalize_known_terms(raw_known)
        # Compact coaching: hide Mortal % options; smaller teaching window
        self.hide_ai_options: bool = self._get_value(
            "hide_ai_options", True, self.valid_bool
        )
        # Dark chrome for the coaching window (matches Sensei review page)
        self.dark_theme: bool = self._get_value("dark_theme", True, self.valid_bool)
        # Keep coaching window above other apps (tk -topmost)
        self.always_on_top: bool = self._get_value(
            "always_on_top", False, self.valid_bool
        )
        # Session-only: collapse setup toolbars during play (not persisted across launches)
        self.hide_toolbars: bool = False
        # First-run wizard completed (model, Safari, optional API key)
        self.setup_complete: bool = self._get_value(
            "setup_complete", False, self.valid_bool
        )
        self.locale_defaults_version: int = self._get_value(
            "locale_defaults_version", 0, lambda x: isinstance(x, int)
        )
        _migrate_deliverable_locale(self)
        if self.hide_ai_options and not self.auto_why:
            self.auto_why = True
        
        self.save_json()
        LOGGER.info("Settings initialized and saved to %s", self._settings_path)
        
    def load_json(self) -> dict:
        """ Load settings from json file into dict"""
        try:
            with open(self._settings_path, 'r',encoding='utf-8') as file:
                settings_dict:dict = json.load(file)
        except Exception as e:
            LOGGER.warning("Error loading settings. Will use defaults. Error: %s", e)
            settings_dict = {}
        
        return settings_dict
    
    def save_json(self):
        """ Save settings into json file"""
        # save all non-private variables (not starting with "_") into dict
        settings_to_save = {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
            and not callable(value)
            and key != "hide_toolbars"
        }
        with open(self._settings_path, 'w', encoding='utf-8') as file:
            json.dump(settings_to_save, file, indent=4, separators=(', ', ': '))
    
    def _get_value(self, key:str, default_value:any, validator:Callable[[any],bool]=None) -> any:
        """ Get value from settings dictionary, or return default_value if error"""
        try:
            value = self._settings_dict[key]
            if not validator:
                return value
            if validator(value):
                return value
            else:
                LOGGER.warning("setting %s uses default value '%s' because original value '%s' is invalid"
                    , key, default_value, value)
                return default_value
        except Exception as e:
            LOGGER.warning("setting '%s' use default value '%s' due to error: %s", key, default_value,e)
            return default_value
    
    def lan(self) -> LanStr:
        """ return the LanString instance"""
        return LAN_OPTIONS[self.language]
    
    ### Validate functions: return true if the value is valid
       
    def valid_language(self, lan_code:str):
        """ return True if given language code is valid"""
        return (lan_code in LAN_OPTIONS)
    
    def valid_mitm_port(self, port:int):
        """ return true if port number if valid"""
        if 1000 <= port <= 65535:
            return True
        else:
            return False
    
    def valid_bool(self, value):
        """ return true if value is bool"""
        if isinstance(value,bool):
            return True
        else:
            return False

    def valid_known_terms_list(self, value) -> bool:
        """True when value is a list of strings (ids validated on normalize)."""
        if not isinstance(value, list):
            return False
        return all(isinstance(x, str) for x in value)

    def _normalize_known_terms(self, value) -> list:
        """Drop unknown catalog ids; keep a stable sorted list."""
        if not isinstance(value, list):
            return []
        try:
            from shanten_sensei.glosses import normalize_known_terms

            return sorted(normalize_known_terms(value))
        except Exception:
            return sorted({x for x in value if isinstance(x, str) and x})
        
    def valid_username(self, username:str) -> bool:
        """ return true if username valid"""
        if username:
            if len(username) > 1:
                return True
        else:
            return False
    
    def valid_game_level(self, level:int) -> bool:
        """ return true if game level is valid"""
        if 0 <= level <= 4:
            # 0 Bronze 1 Silver  2 Gold  3 Jade  4 Throne
            return True
        else:
            return False
        
    def valid_game_mode(self, mode:str) -> bool:
        """ return true if game mode is valid"""
        if mode in utils.GAME_MODES:
            return True
        else:
            return False
        
    def valid_url(self, url:str) -> bool:
        """ validate url"""
        valid_prefix = ["https://", "http://"]
        for p in valid_prefix:
            if url.startswith(p):
                return True
        return False