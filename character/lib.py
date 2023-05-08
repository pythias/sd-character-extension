from datetime import datetime
from enum import Enum
from colorama import Fore, Style
from modules import scripts, shared

import os
import colorama

# Initialize colorama
colorama.init()

version_flag = "v0.2.6"
character_dir = scripts.basedir()
keys_path = os.path.join(character_dir, "configs/keys")
models_path = os.path.join(character_dir, "configs/models")


class LogLevel(Enum):
    DEBUG = (Fore.BLUE, "DEBUG")
    INFO = (Fore.GREEN, "INFO")
    WARNING = (Fore.YELLOW, "WARNING")
    ERROR = (Fore.RED, "ERROR")


def log(message, level=LogLevel.INFO):
    """Log a message to the console."""
    # with microsecond precision
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    level_color, level_name = level.value
    print(f'{level_color}{current_time}{Style.RESET_ALL} {shared.cmd_opts.character_server_name} {version_flag}: {message}')
