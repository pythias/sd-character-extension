from datetime import datetime
from enum import Enum
from colorama import Fore, Style
from modules import scripts, shared, deepbooru
from modules.api import api
from modules.api.api import decode_base64_to_image
from PIL import Image
from starlette.exceptions import HTTPException

from character.metrics import hCaption

import os
import numpy as np
import logging
import re

version_flag = "v1.2.7"
character_dir = scripts.basedir()
keys_path = os.path.join(character_dir, "configs/keys")
models_path = os.path.join(character_dir, "configs/models")

request_id = "init"

min_base64_image_size = 1000

# Set up the logger
logger = logging.getLogger("fastapi")
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s %(server_name)s %(server_version)s %(request_id)s %(message)s",
)

def set_request_id(id):
    global request_id
    request_id = id

def get_request_id():
    return request_id

def log(message, level = logging.INFO):
    logger.log(level, message, extra={
        "server_name": shared.cmd_opts.character_server_name,
        "server_version": version_flag,
        "request_id": request_id
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

def replace_man_with_men(text):
    """
    特殊模型的处理, 某些模型识别man很差, 改成men
    """
    return re.sub(r'\bman\b', 'men', text, flags=re.IGNORECASE)

def valid_base64(image_b64):
    if not image_b64 or len(image_b64) < min_base64_image_size:
        return False

    try:
        decode_base64_to_image(image_b64)
        return True
    except Exception as e:
        return False

@hCaption.time()
def clip_b64img(image_b64, throw_exception = False):
    if isinstance(image_b64, str):
        img = decode_base64_to_image(image_b64)
    else:
        img = image_b64

    caption = shared.interrogator.interrogate(img.convert('RGB'))
    if throw_exception and is_empty_caption(caption):
        raise HTTPException(status_code=422, detail="Interrogate fail")

    # 优化tags
    return replace_man_with_men(caption)


def is_empty_caption(caption):
    """
    判断是否为空标签, caption = 基础标签, artists.txt, flavors.txt, mediums.txt, movements.txt
    """
    return caption == "" or caption == "<error>" or caption[0] == ', '


def request_is_t2i(request):
    if isinstance(request, dict):
        return "hr_scale" in request
        
    return hasattr(request, "hr_scale")


def limit_size_max(w, h, radio, max):
    """
    限制最大尺寸
    """
    if w <= max and h <= max:
        return w, h

    if w > h:
        w = max
        h = int(w / radio)
    else:
        h = max
        w = int(h * radio)
    
    return w, h


def limit_size_min(w, h, radio, min):
    """
    限制最小尺寸
    """
    if w >= min and h >= min:
        return w, h

    if w < h:
        w = min
        h = int(w / radio)
    else:
        h = min
        w = int(h * radio)
    
    return w, h
