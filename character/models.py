import os
import sys
import json
import logging

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

from character import face
from character.lib import log, get_or_default, clip_b64img
from character.errors import *
from character.metrics import *
from character.nsfw import image_has_nsfw, image_has_illegal_words

from modules import shared, images
from modules.api.models import *
from modules.paths_internal import extensions_dir
from modules.api.api import decode_base64_to_image

negative_default_prompts = "EasyNegative,worst quality,low quality"
negative_nsfw_prompts = "nsfw,naked,nude,sex,ass,pussy,loli,kids,kid,child,children,teenager,teenagers,teen,baby face,big breasts"
negative_watermark_prompts = "text,watermark,signature,logo"
negative_body_prompts = "zombie,extra fingers,six fingers,missing fingers,extra arms,missing arms,extra legs,missing legs,bad face,bad hair,bad hands,bad pose"

high_quality_prompts = "8k,high quality,<lora:add_detail:1>"

# 加载ControlNet，启动添加参数 --controlnet-dir
extensions_control_net_path = os.path.join(extensions_dir, "sd-webui-controlnet")
sys.path.append(extensions_control_net_path)
from scripts import external_code, global_state

# todo load from config
# default_control_net_model = "controlnet11Models_softedge [f616a34f]"
# default_control_net_module = "softedge_pidisafe"
default_control_net_model = "controlnet11Models_lineart [5c23b17d]"
default_control_net_module = "lineart_realistic"
default_open_pose_model = "controlnet11Models_openpose [73c2b67d]"
default_open_pose_module = "openpose"
default_tile_model = "controlnet11Models_tile [39a89b25]"
default_tile_module = "tile_resample"

control_net_models = external_code.get_models(update=True)

def find_closest_cn_model_name(search: str):
    if not search:
        return None

    if search in global_state.cn_models:
        return search

    search = search.lower()
    if search in global_state.cn_models_names:
        return global_state.cn_models_names.get(search)
    
    applicable = [name for name in global_state.cn_models_names.keys() if search in name.lower()]
    if not applicable:
        return None

    applicable = sorted(applicable, key=lambda name: len(name))
    return global_state.cn_models_names[applicable[0]]


field_prefix = "character_"

min_base64_image_size = 1000

class CharacterV2Txt2ImgRequest(StableDiffusionTxt2ImgProcessingAPI):
    # 大部分参数都丢 extra_generation_params 里面（默认值那种，省得定义那么多）
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler", title='Sampler', description='The sampler to use.')
    character_image: str = Field(default="", title='Character Image', description='The character image in base64 format.')
    character_pose: str = Field(default="", title='Character Pose', description='The character pose in base64 format.')
    character_face: bool = Field(default=False, title='Character Face', description='Whether to crop faces.')
    extra_generation_params: dict = Field(default={}, title='Extra Generation Params', description='Extra generation params.')

class CharacterV2Img2ImgRequest(StableDiffusionImg2ImgProcessingAPI):
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler", title='Sampler', description='The sampler to use.')
    denoising_strength = Field(default=0.75, title='Denoising Strength', description='The strength of the denoising.')
    character_image: str = Field(default="", title='Character Image', description='The character image in base64 format.')
    character_pose: str = Field(default="", title='Character Pose', description='The character pose in base64 format.')
    extra_generation_params: dict = Field(default={}, title='Extra Generation Params', description='Extra generation params.')
    

class V2ImageResponse(BaseModel):
    images: List[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: dict
    faces: List[str]


def convert_response(request, response):
    params = response.parameters
    info = json.loads(response.info)

    faces = []

    if face.require_face_repairer(p) and not face.keep_original_image(p):
        batch_size = get_or_default(p, "batch_size", 1)
        for _ in range(batch_size):
            response.images.pop()

    crop_face = face.require_face(request)

    safety_images = []
    for base64_image in response.images:
        if image_has_nsfw(base64_image):
            cNSFW.inc()
            continue

        if image_has_illegal_words(base64_image):
            cIllegal.inc()
            continue

        safety_images.append(base64_image)

        if crop_face:
            # todo 脸部裁切，在高清修复脸部时有数据
            image_faces = face.crop(base64_image)
            cFace.inc(len(image_faces))
            faces.extend(image_faces)

    if len(safety_images) == 0:
        return ApiException(code_character_nsfw, f"has nsfw concept, info:{info}").response()

    return V2ImageResponse(images=safety_images, parameters=params, info=info, faces=faces)


def simply_prompts(prompts: str):
    if not prompts:
        return ""

    # split the prompts and keep the original case
    prompts = prompts.split(",")

    unique_prompts = {}
    for p in prompts:
        p_stripped = p.strip()  # remove leading/trailing whitespace
        if p_stripped != "":
            # note the use of lower() for the comparison but storing the original string
            unique_prompts[p_stripped.lower()] = p_stripped

    return ",".join(unique_prompts.values())



def request_prepare(request):
    if request.negative_prompt is None:
        request.negative_prompt = ""

    if request.prompt is None:
        request.prompt = ""

    request.negative_prompt = request.negative_prompt + "," \
        + negative_default_prompts + "," \
        + negative_nsfw_prompts + "," \
        + negative_watermark_prompts + "," \
        + negative_body_prompts

    request.prompt = request.prompt + "," + high_quality_prompts

    request.prompt = simply_prompts(request.prompt)
    request.negative_prompt = simply_prompts(request.negative_prompt)
    request.extra_generation_params['character_from_ui'] = False


def remove_character_fields(request):
    params = vars(request)
    keys = list(params.keys())
    for key in keys:
        if not key.startswith(field_prefix):
            continue

        if not isinstance(params[key], str) or (len(params[key]) < min_base64_image_size and len(params[key]) > 0):
            request.extra_generation_params[key] = params[key]
        
        delattr(request, key)


def apply_controlnet(request):
    units = [
        get_cn_image_unit(request),
        get_cn_pose_unit(request),
        get_cn_empty_unit()
    ]

    # todo 对用户输入的处理
    request.alwayson_scripts.update({'ControlNet': {'args': [external_code.ControlNetUnit(**unit) for unit in units]}})


def valid_base64(image_b64):
    if not image_b64 or len(image_b64) < min_base64_image_size:
        return False

    try:
        decode_base64_to_image(image_b64)
        return True
    except Exception as e:
        log(f"valid_base64 error: {e}", logging.ERROR)
        return False


def get_cn_image_unit(request):
    image_b64 = get_or_default(request, f"{field_prefix}image", "")
    if not valid_base64(image_b64):
        return get_cn_empty_unit()

    request.prompt = clip_b64img(image_b64) + "," + request.prompt

    return {
        "module": get_or_default(request, f"{field_prefix}cn_preprocessor", default_control_net_module),
        "model": find_closest_cn_model_name(get_or_default(request, f"{field_prefix}cn_model", default_control_net_model)),
        "enabled": True,
        "image": image_b64,
    }


def get_cn_pose_unit(request):
    pose_b64 = get_or_default(request, f"{field_prefix}pose", "")
    if not valid_base64(pose_b64):
        return get_cn_empty_unit()

    return {
        "module": get_or_default(request, f"{field_prefix}pose_preprocessor", default_open_pose_module),
        "model": find_closest_cn_model_name(get_or_default(request, f"{field_prefix}pose_model", default_open_pose_model)),
        "enabled": True,
        "image": pose_b64,
    }


def get_cn_tile_unit(request):
    auto_upscale = get_or_default(request, f"{field_prefix}auto_upscale", False)
    if not auto_upscale:
        return get_cn_empty_unit()

    return {
        "module": get_or_default(request, f"{field_prefix}tile_preprocessor", default_tile_module),
        "model": find_closest_cn_model_name(get_or_default(request, f"{field_prefix}tile_model", default_tile_model)),
        "enabled": True,
        "image": "",
    }


def get_cn_empty_unit():
    return {
        "model": "none",
        "module": "none",
        "enabled": False,
        "image": "",
    }


def t2i_counting(request):
    cT2I.inc()
    cT2IImages.inc(request.batch_size)
    params_counting(request)


def params_counting(request):
    cPrompts.inc(request.prompt.count(",") + 1)
    cNegativePrompts.inc(request.negative_prompt.count(",") + 1)
    cLoras.inc(request.prompt.count("<"))
    cSteps.inc(request.steps)
    cPixels.inc(request.width * request.height)

