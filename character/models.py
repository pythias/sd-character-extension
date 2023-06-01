import os
import sys
import json
import logging

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

from character import face, lib, upscale, output
from character.errors import *
from character.metrics import *
from character.nsfw import image_has_nsfw, image_has_illegal_words, image_has_nsfw_v2

from modules import shared, images
from modules.api.models import *
from modules.paths_internal import extensions_dir
from modules.api.api import decode_base64_to_image

negative_default_prompts = "BadDream,FastNegativeEmbedding"
high_quality_prompts = "8k,high quality,<lora:add_detail:1>"

# 加载ControlNet，启动添加参数 --controlnet-dir
extensions_control_net_path = os.path.join(extensions_dir, "sd-webui-controlnet")
sys.path.append(extensions_control_net_path)
from scripts import external_code, global_state

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

default_control_net_model = find_closest_cn_model_name("controlnet11Models_lineart")
default_control_net_module = "lineart_realistic"
default_open_pose_model = find_closest_cn_model_name("controlnet11Models_openpose")
default_open_pose_module = "openpose"
default_tile_model = find_closest_cn_model_name("controlnet11Models_tile")
default_tile_module = "tile_resample"
lib.log(f"ControlNet default models, i2i:{default_control_net_model}, pose:{default_open_pose_model}, tile:{default_tile_model}")

field_prefix = "character_"

min_base64_image_size = 1000

class CharacterV2Txt2ImgRequest(StableDiffusionTxt2ImgProcessingAPI):
    # 大部分参数都丢 extra_generation_params 里面（默认值那种，省得定义那么多）
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler a", title='Sampler', description='The sampler to use.')
    hr_upscaler: str = Field(default="Latent", title='HR Upscaler', description='The HR upscaler to use.')
    denoising_strength: float = Field(default=0.5, title='Denoising Strength', description='The strength of the denoising.')
    character_image: str = Field(default="", title='Character Image', description='The character image in base64 format.')
    character_extra: dict = Field(default={}, title='Character Extra Params', description='Character Extra Params.')
    extra_generation_params: dict = Field(default={}, title='Extra Generation Params', description='Extra Generation Params.')


class CharacterV2Img2ImgRequest(StableDiffusionImg2ImgProcessingAPI):
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler a", title='Sampler', description='The sampler to use.')
    image_cfg_scale: float = Field(default=7.0, title='Image Scale', description='The scale of the image.')
    denoising_strength: float = Field(default=0.5, title='Denoising Strength', description='The strength of the denoising.')
    character_input_image: str = Field(default="", title='Character Input Image', description='The character input image in base64 format.')
    character_extra: dict = Field(default={}, title='Character Extra Params', description='Character Extra Params.')
    extra_generation_params: dict = Field(default={}, title='Extra Generation Params', description='Extra Generation Params.')
    

class V2ImageResponse(BaseModel):
    images: List[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: dict
    faces: List[str]


def convert_response(request, response):
    params = response.parameters
    info = json.loads(response.info)
    info["nsfw"] = 0
    info["illegal"] = 0

    faces = []
    source_images = []
    if face.require_face_repairer(request) and not face.keep_original_image(request):
        batch_size = lib.get_request_value(request, "batch_size", 1)
        source_images = response.images[batch_size:]

    crop_face = face.require_face(request)

    image_urls = []
    safety_images = []
    for base64_image in source_images:
        image_url, _ = output.save_image(base64_image)
        image_urls.append(image_url)

        if image_has_nsfw_v2(base64_image):
            info["nsfw"] += 1
            cNSFW.inc()

            if not lib.get_extra_value(request, "allow_nsfw", False):
                continue

        if image_has_illegal_words(base64_image):
            info["illegal"] += 1
            cIllegal.inc()

            if not lib.get_extra_value(request, "allow_illegal", False):
                continue

        safety_images.append(base64_image)

        if crop_face:
            # todo 脸部裁切，在高清修复脸部时有数据
            image_faces = face.crop(base64_image)
            cFace.inc(len(image_faces))
            faces.extend(image_faces)

    if len(safety_images) == 0:
        return ApiException(code_character_nsfw, f"has nsfw concept, info:{info}").response()

    if lib.get_extra_value(request, "out_no_parameters", True):
        # 因为请求参数中也有图片的存在，调试时用 parameters
        params = {}

    if output.required_save(request):
        face_urls = []
        for b64 in faces:
            image_url, _ = output.save_image(b64)
            face_urls.append(image_url)

        return V2ImageResponse(images=image_urls, parameters=params, info=info, faces=face_urls)
    else:
        return V2ImageResponse(images=safety_images, parameters=params, info=info, faces=faces)


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


def request_prepare(request):
    if isinstance(request, dict):
        request.setdefault('extra_generation_params', {})
    else:
        if not hasattr(request, 'extra_generation_params') or request.extra_generation_params is None:
            request.extra_generation_params = {}

    if lib.name_flag not in request.extra_generation_params:
        request.extra_generation_params[lib.name_flag] = {}

    extra = lib.get_request_value(request, 'character_extra', {})
    if isinstance(extra, dict):
        request.extra_generation_params[lib.name_flag].update(extra)

    request.extra_generation_params[lib.name_flag].update({"from_ui": False, "is_t2i": lib.request_is_t2i(request)})

    if request.negative_prompt is None:
        request.negative_prompt = ""

    if request.prompt is None:
        request.prompt = ""

    request.negative_prompt = request.negative_prompt + "," + negative_default_prompts
    request.prompt = request.prompt + "," + high_quality_prompts

    request.prompt = simply_prompts(request.prompt)
    request.negative_prompt = simply_prompts(request.negative_prompt)
    

def remove_character_fields(request):
    params = vars(request)
    keys = list(params.keys())
    for key in keys:
        if not key.startswith(field_prefix):
            continue

        # if not isinstance(params[key], str) or (len(params[key]) < min_base64_image_size and len(params[key]) > 0):
        #     request.extra_generation_params['Character'].update({key[len(field_prefix):]: params[key]})
        
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
        lib.log(f"valid_base64 error: {e}", logging.ERROR)
        return False


def get_cn_image_unit(request):
    image_b64 = lib.get_request_value(request, f"{field_prefix}image", "")
    if not valid_base64(image_b64):
        return get_cn_empty_unit()

    request.prompt = lib.clip_b64img(image_b64) + "," + request.prompt

    return {
        "module": lib.get_extra_value(request, "cn_preprocessor", default_control_net_module),
        "model": find_closest_cn_model_name(lib.get_extra_value(request, "cn_model", default_control_net_model)),
        "enabled": True,
        "image": image_b64,
    }


def get_cn_pose_unit(request):
    pose_b64 = lib.get_request_value(request, f"{field_prefix}pose", "")
    if not valid_base64(pose_b64):
        return get_cn_empty_unit()

    return {
        "module": lib.get_extra_value(request, "pose_preprocessor", default_open_pose_module),
        "model": find_closest_cn_model_name(lib.get_extra_value(request, "pose_model", default_open_pose_model)),
        "enabled": True,
        "image": pose_b64,
    }


def get_cn_tile_unit(request):
    if not lib.get_extra_value(request, "scale_by_tile", False):
        return get_cn_empty_unit()

    return {
        "module": default_tile_module,
        "model": default_tile_model,
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


def apply_i2i_request(request):
    image_b64 = lib.get_request_value(request, "character_input_image", "")

    if not image_b64 or len(image_b64) < min_base64_image_size:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        request.init_images = [image_b64]

        img = decode_base64_to_image(image_b64)
        caption = lib.clip_b64img(img)
        request.prompt = caption + "," + request.prompt

        upscale.apply_i2i_upscale(request, img)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Input image was invalid")


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

