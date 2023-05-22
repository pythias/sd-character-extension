from datetime import datetime
from enum import Enum
from colorama import Fore, Style
from modules import scripts, shared

import os
import colorama
import numpy as np

from PIL import Image

from modules.api import api

# Initialize colorama
colorama.init()

version_flag = "v1.0.7"
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

def to_rgb_image(img):
    if not hasattr(img, 'mode') or img.mode != 'RGB':
        return img.convert('RGB')
    
    return img

def encode_to_base64(image):
    if type(image) is str:
        return image
    elif type(image) is Image.Image:
        return api.encode_pil_to_base64(image)
    elif type(image) is np.ndarray:
        return encode_np_to_base64(image)
    else:
        return ""

def encode_np_to_base64(image):
    pil = Image.fromarray(image)
    return api.encode_pil_to_base64(pil)


def get_or_default(obj, key, default):
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)
