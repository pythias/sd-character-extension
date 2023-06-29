import base64
import itertools
import logging
import numpy as np
import os
import requests
import time
import uuid

from hashlib import md5

from modules import scripts, shared, deepbooru
from modules.api import api
from modules.api.api import decode_base64_to_image
from PIL import Image
from starlette.exceptions import HTTPException

from character.metrics import hCaption
from character import logger

version_flag = "v1.4.0"
character_dir = scripts.basedir()
keys_path = os.path.join(character_dir, "configs/keys")
models_path = os.path.join(character_dir, "configs/models")

min_base64_image_size = 1000

# Set up the logger
request_id = logger.new_id()
_logger = logger.create_logger()

def load_models():
    started_at = time.time()
    shared.interrogator.load()
    log(f"interrogator loaded in {time.time() - started_at:.3f} seconds")

    started_at = time.time()
    deepbooru.model.load()
    log(f"deepbooru loaded in {time.time() - started_at:.3f} seconds")

def set_request_id(id):
    global request_id
    request_id = id

def get_request_id():
    return request_id


def debug(message):
    log(message, logging.DEBUG)


def error(message):
    log(message, logging.ERROR)


def log(message, level = logging.INFO):
    _logger.log(level, message, extra={
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

def get_or_default(obj, key, default = None):
    if obj is None:
        return default
        
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

def valid_base64(image_b64):
    if not image_b64 or len(image_b64) < min_base64_image_size:
        return False

    try:
        return decode_base64_to_image(image_b64)
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

    return caption


def deepbooru_b64img(image_b64, throw_exception = False):
    if isinstance(image_b64, str):
        img = decode_base64_to_image(image_b64)
    else:
        img = image_b64

    caption = deepbooru.model.tag(img.convert('RGB'))
    if throw_exception and is_empty_caption(caption):
        raise HTTPException(status_code=422, detail="Interrogate fail")

    return caption


def wb14_b64img(image_b64, throw_exception = False):
    return ""


def is_empty_caption(caption):
    """
    判断是否为空标签, caption = 基础标签, artists.txt, flavors.txt, mediums.txt, movements.txt
    """
    return caption == "" or caption == "<error>" or caption[0] == ','


def is_webui():
    return not shared.cmd_opts.nowebui


def limit_size(w, h, radio, min, max):
    w, h = limit_size_min(w, h, radio, min)
    w, h = limit_size_max(w, h, radio, max)
    return w, h


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


def simply_prompts(prompt: str):
    if not prompt:
        return ""

    # split the prompts and keep the original case
    prompts = prompt.split(",")

    unique_prompts = {}
    for p in prompts:
        p_stripped = p.strip()  # remove leading/trailing whitespace
        if p_stripped != "":
            # note the use of lower() for the comparison but storing the original string
            unique_prompts[p_stripped.lower()] = p_stripped

    return ",".join(unique_prompts.values())


def to_multi_prompts(prompt: str):
    if prompt.find("|") == -1 and prompt.find(";") == -1:
        return [prompt]

    if ";" in prompt:
        prompts = prompt.split(";")
        return [split_prompt.strip() for split_prompt in prompts if split_prompt.strip()]

    # split the prompt into tags
    tags = prompt.split(',')
    
    # for each tag, split it further by '|' and strip whitespace
    split_tags = [tag.split('|') for tag in tags]
    
    # remove empty strings
    split_tags = [[item.strip() for item in tag_list if item.strip()] for tag_list in split_tags]
    
    # get the cartesian product of all split tags
    product = list(itertools.product(*split_tags))
    
    # join the individual tuples in the cartesian product with ','
    return [','.join(tup) for tup in product]


def truncate_large_value(data, max_size: int = 2000, truncated_size = 20, replacement: str = '...[truncated]'):
    if isinstance(data, dict):
        return {key: truncate_large_value(value, max_size, truncated_size, replacement) for key, value in data.items()}
    elif isinstance(data, str) and len(data) > max_size:
        return data[:truncated_size] + replacement
    elif isinstance(data, list):
        return [truncate_large_value(item, max_size, truncated_size, replacement) for item in data]
    else:
        return data


def _get_output_path(file_name, is_cache = False):
    if is_cache:
        file_relative_path = os.path.join("outputs", shared.cmd_opts.character_short_name, 'cache')
    else:
        file_relative_path = os.path.join("outputs", shared.cmd_opts.character_short_name, time.strftime("%Y%m%d"))

    file_dir = os.path.join(shared.cmd_opts.character_output_dir, file_relative_path)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    file_fullpath = os.path.join(file_dir, file_name)
    return [file_relative_path, file_fullpath]


def _save_file(file_fullpath, file_bytes):
    with open(file_fullpath, 'wb') as f:
        return f.write(file_bytes) == len(file_bytes)
    

def save_image(b64):
    """
    save base64 image to disk, return url
    """
    try:
        if b64.startswith("data:image/"):
            b64 = b64.split(";")[1].split(",")[1]
        
        img_filename = str(uuid.uuid4()) + '.png'
        [imd_relative_path, img_filepath] = _get_output_path(img_filename)

        img_bytes = base64.b64decode(b64)
        if len(img_bytes) > 0 and _save_file(img_filepath, img_bytes):
            return [os.path.join(shared.cmd_opts.character_host, imd_relative_path, img_filename), img_filepath]
        else:
            log("save_image error: save file failed")
    except Exception as e:
        log("save_image error: %s" % e)
    
    return [b64, ""]
    

def download_to_base64(value):
    # empty value
    if value == "" or value == None or value == "None":
        return ""

    if not value.startswith("http"):
        return value
    
    url = value

    download_filename = md5(url.encode('utf-8')).hexdigest() + '.cache'
    [_, file_fullpath] = _get_output_path(download_filename, True)
    
    if os.path.exists(file_fullpath):
        with open(file_fullpath, 'rb') as f:
            file_bytes = f.read()
            if len(file_bytes) > 0:
                return base64.b64encode(file_bytes).decode('utf-8')

    try:
        file_bytes = requests.get(url, timeout=5).content

        if len(file_bytes) > 0:
            _save_file(file_fullpath, file_bytes)
            return base64.b64encode(file_bytes).decode('utf-8')
        
        return ""
    except Exception as e:
        log("download_file error: %s" % e)
        return ""



