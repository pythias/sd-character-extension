from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from colorama import Fore, Style
from modules import scripts, shared
from modules.api import api
from modules.api.api import decode_base64_to_image
from PIL import Image

import os
import numpy as np
import logging
import sys

version_flag = "v1.0.9"
character_dir = scripts.basedir()
keys_path = os.path.join(character_dir, "configs/keys")
models_path = os.path.join(character_dir, "configs/models")

request_id_var = ContextVar('request_id')
request_id_var.set("initialization")

# Set up the logger
logger = logging.getLogger("fastapi")
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s %(server_name)s %(server_version)s %(request_id)s %(message)s",
)

def log(message, level = logging.INFO):
    logger.log(level, message, extra={
        "server_name": shared.cmd_opts.character_server_name,
        "server_version": version_flag,
        "request_id": request_id_var.get()
    })

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
