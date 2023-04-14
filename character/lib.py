from datetime import datetime
from enum import Enum
from colorama import Fore, Style, init
from modules.paths_internal import extensions_dir

import os

# Initialize colorama
init()

extension_name = "sd-character-extension"
keys_path = os.path.join(extensions_dir, extension_name, "keys")
database_path = os.path.join(extensions_dir, extension_name, "database")

class LogLevel(Enum):
    DEBUG = (Fore.BLUE, "DEBUG")
    INFO = (Fore.GREEN, "INFO")
    WARNING = (Fore.YELLOW, "WARNING")
    ERROR = (Fore.RED, "ERROR")


def log(message, level=LogLevel.INFO):
    """Log a message to the console."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    level_color, level_name = level.value
    print(f'{Fore.CYAN}{current_time}{Style.RESET_ALL} - {level_color}{level_name}{Style.RESET_ALL} - Character: {message}')
