from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from colorama import Fore, Style
from modules import scripts, shared
from modules.api import api
from modules.api.api import decode_base64_to_image
from PIL import Image

import os
import colorama
import numpy as np
import logging


version_flag = "v1.0.8"
character_dir = scripts.basedir()
keys_path = os.path.join(character_dir, "configs/keys")
models_path = os.path.join(character_dir, "configs/models")

request_id_var = ContextVar('request_id')
request_id_var.set("started")


# Initialize colorama
colorama.init()

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        level = record.levelno
        if(level>=logging.ERROR):
            color = Fore.RED
        elif(level>=logging.WARN):
            color = Fore.YELLOW
        elif(level>=logging.INFO):
            color = Fore.GREEN
        elif(level>=logging.DEBUG):
            color = Fore.BLUE
        else:
            color = Fore.WHITE
        
        asctime = self.formatTime(record, self.datefmt)
        return f"{color}{record.levelname}{Style.RESET_ALL} {asctime} {record.message}"

# Set up the logger
logger = logging.getLogger("fastapi")
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log(message, level = logging.INFO):
    logger.log(level, f"{shared.cmd_opts.character_server_name} v{version_flag} {request_id_var.get()} : {message}")

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
    if obj is None:
        return default
        
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def get_from_request(request, key, default):
    params = get_or_default(request, "extra_generation_params", None)
    return get_or_default(params, key, default)


def clip_b64img(image_b64):
    try:
        img = decode_base64_to_image(image_b64)
        return shared.interrogator.interrogate(img.convert('RGB'))
    except Exception as e:
        return ""
