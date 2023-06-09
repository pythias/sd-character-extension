import base64
import itertools
import logging
import numpy as np
import os
import requests
import sys
import time
import uuid
import glob
import re

from hashlib import md5

from modules import scripts, shared, deepbooru
from modules.api import api
from modules.api.api import decode_base64_to_image
from PIL import Image
from starlette.exceptions import HTTPException

from character.metrics import hCaption, hVideo
from character import logger

version_flag = "v1.5.0"
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
    # elif type(image) is cv2.Mat:
    #     _, img_buff = cv2.imencode('.png', image)
    #     return base64.b64encode(img_buff).decode('utf-8')
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


def _get_output_path(name):
    url_relative_path = os.path.join("outputs", shared.cmd_opts.character_short_name, name)
    url_full = os.path.join(shared.cmd_opts.character_host, url_relative_path)
    file_fullpath = os.path.join(shared.cmd_opts.character_output_dir, url_relative_path)
    if not os.path.exists(os.path.dirname(file_fullpath)):
        os.makedirs(os.path.dirname(file_fullpath))

    return [url_full, file_fullpath]


def _save_file(file_fullpath, file_bytes):
    with open(file_fullpath, 'wb') as f:
        return f.write(file_bytes) == len(file_bytes)
    

def save_image(b64, img_filename = ""):
    """
    save base64 image to disk, return url
    """
    try:
        if img_filename == "":
            img_filename = os.path.join(time.strftime("%Y%m%d"),  str(uuid.uuid4()) + '.png')

        [img_url, img_path] = _get_output_path(img_filename)
        
        if b64.startswith("data:image/"):
            b64 = b64.split(";")[1].split(",")[1]
        img_bytes = base64.b64decode(b64)
        if len(img_bytes) > 0 and _save_file(img_path, img_bytes):
            return [img_url, img_path]
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

    download_filename = os.path.join("cache", md5(url.encode('utf-8')).hexdigest() + '.cache')
    [_, file_fullpath] = _get_output_path(download_filename)
    
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
    

def load_extension(name):
    from modules.paths_internal import extensions_dir
    extension_path = os.path.join(extensions_dir, name)
    if os.path.isdir(extension_path):
        # Add the path to sys.path so that we can import the module
        if extension_path not in sys.path:
            sys.path.append(os.path.join(extensions_dir, name))
            log(f"Loading extension: {name}")
        else:
            log(f"Extension already loaded: {name}")
    else:
        log(f"Extension not found: {name}")

def _count_files(file_pattern, regex_pattern):
    files = glob.glob(file_pattern)
    matched_files = [file for file in files if re.match(regex_pattern, os.path.basename(file))]
    return len(matched_files)

def _get_logo_video(width, height):
    logo_file = os.path.join("cache", f"hello-weibo-{width}x{height}.mp4")
    [_, file_fullpath] = _get_output_path(logo_file)

    if not os.path.exists(file_fullpath):
        cmd = f"ffmpeg -y -t 1 -s {width}x{height} -f rawvideo -pix_fmt rgb24 -r 24 -i /dev/zero -vf \"drawtext=text='MiaoMiao':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2\" \"{file_fullpath}\""
        os.system(cmd)
        log(f"create logo video: {file_fullpath}, cmd: {cmd}")
                                  
    return file_fullpath

@hVideo.time()
def ffmpeg_to_video(video_path, width = 512, height = 512):
    [video_url, video_full_path] = _get_output_path(video_path + '.mp4')

    # remove .mp4 video_full_path
    video_full_dir = video_full_path[:-4]
    video_images = os.path.join(video_full_dir, "v-%03d.png")
    video_original_file = os.path.join(video_full_dir, "tmp.mp4")

    # 计算视频长度
    fps = 4
    image_count = _count_files(os.path.join(video_full_dir, "*.png"), r"v-\d{3}.png")
    video_length = int(image_count / fps)
    
    # 添加淡入淡出效果, 添加背景音乐
    started_at = time.time()
    cmd_original = f"ffmpeg -y -r {fps} -i \"{video_images}\" -vf \"fade=in:st=0:d=2, fade=out:st={video_length - 2}:d=2\" -pix_fmt yuv420p -crf 24 -s:v {width}x{height} -vcodec libx264 {video_original_file}"
    os.system(cmd_original)

    # 添加logo
    logo_video = _get_logo_video(width, height)
    cmd_with_logo = f"ffmpeg -y -i {video_original_file} -i {logo_video} -filter_complex \"[0:v][1:v] concat=n=2:v=1:a=0\" {video_full_path}"
    os.system(cmd_with_logo)
    
    log(f"to-video, images: {image_count}, fps: {fps}, length: {video_length}, ffmpeg in {time.time() - started_at:.3f}s, cmd: '{cmd_original}', combine: '{cmd_with_logo}'")

    return video_url
