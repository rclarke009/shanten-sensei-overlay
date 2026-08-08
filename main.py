""" Mahjong Copilot

Copyright (C) 2024 Latorc (Github page: https://github.com/latorc)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from pathlib import Path

from gui.main_gui import MainGUI
from common import utils
from common.log_helper import LogHelper
from common.settings import Settings
from bot_manager import BotManager


def _load_sensei_env() -> None:
    """Load OPENAI_API_KEY / SENSEI_API_KEY for Why? (app support, cwd, or sibling .env)."""
    try:
        from shanten_sensei.envutil import load_dotenv
        from common.sensei_paths import sensei_env_path
    except ImportError:
        return
    app_env = sensei_env_path()
    if app_env.is_file() and load_dotenv(app_env):
        return
    if load_dotenv():
        return
    sibling = Path(__file__).resolve().parent.parent / "shanten_sensei" / ".env"
    if sibling.is_file():
        load_dotenv(sibling)


def main():
    """ Main entry point """
    LogHelper.config_logging()
    _load_sensei_env()
    setting = Settings()
    # utils.set_dpi_awareness()
    utils.prevent_sleep()
    bot_manager = BotManager(setting)
    gui = MainGUI(setting, bot_manager)
    gui.mainloop()

if __name__ == "__main__":
    main()
