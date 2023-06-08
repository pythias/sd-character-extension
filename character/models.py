import os
import sys
import json
import logging
import math

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

from character import face, lib, output, requests, errors, names
from character.errors import *
from character.metrics import *
from character.nsfw import image_has_illegal_words, image_has_nsfw_v2

from modules import shared, images, processing
from modules.processing import StableDiffusionProcessing
from modules.api.models import *
from modules.paths_internal import extensions_dir


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

default_control_net_model = "controlnet11Models_lineart"
default_control_net_module = "lineart_realistic"
default_open_pose_model = "controlnet11Models_openpose"
default_open_pose_module = "openpose"
default_tile_model = "controlnet11Models_tile"
default_tile_module = "tile_resample"

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
    if face.require_face_repairer(request) and not face.keep_original_image(request):
        batch_size = requests.get_value(request, "batch_size", 1)
        multi_count = requests.get_multi_count(request)
        source_images = response.images[(batch_size * multi_count):]
    else:
        source_images = response.images

    crop_face = face.require_face(request)

    image_urls = []
    safety_images = []
    for base64_image in source_images:
        image_url, _ = output.save_image(base64_image)
        image_urls.append(image_url)

        if image_has_nsfw_v2(base64_image):
            info["nsfw"] += 1
            cNSFW.inc()

            if not requests.get_extra_value(request, "allow_nsfw", False):
                continue

        if image_has_illegal_words(base64_image):
            info["illegal"] += 1
            cIllegal.inc()

            if not requests.get_extra_value(request, "allow_illegal", False):
                continue

        safety_images.append(base64_image)

        if crop_face:
            # todo 脸部裁切，在高清修复脸部时有数据
            image_faces = face.crop(base64_image)
            cFace.inc(len(image_faces))
            faces.extend(image_faces)

    if len(safety_images) == 0:
        return errors.nsfw()

    if requests.get_extra_value(request, "out_no_parameters", True):
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


def _prepare_request(request):
    requests.extra_init(request)
    
    if request.negative_prompt is None:
        request.negative_prompt = ""

    if request.prompt is None:
        request.prompt = ""

    request.negative_prompt = request.negative_prompt + "," + negative_default_prompts
    request.prompt = request.prompt + "," + high_quality_prompts

    request.prompt = lib.simply_prompts(request.prompt)
    request.negative_prompt = lib.simply_prompts(request.negative_prompt)

    _remove_character_fields(request)


def prepare_request_i2i(request):
    _prepare_request(request)
    _apply_controlnet(request)

    image_b64 = requests.get_i2i_image(request)
    request.init_images = [image_b64]

def prepare_request_t2i(request):
    _prepare_request(request)
    _apply_controlnet(request)

def _remove_character_fields(request):
    params = vars(request)
    keys = list(params.keys())
    for key in keys:
        if not key.startswith("character_"):
            continue
        
        delattr(request, key)


def _apply_controlnet(request):
    units = [
        get_cn_image_unit(request),
        get_cn_pose_unit(request),
        
        _get_cn_empty_unit(),
        _get_cn_empty_unit(),
        _get_cn_empty_unit()
    ]

    requests.update_script_args(request, "ControlNet", [_to_process_unit(unit) for unit in units])

def get_cn_image_unit(request):
    image_b64 = requests.get_cn_image(request)
    if not lib.valid_base64(image_b64):
        return _get_cn_empty_unit()

    return {
        "module": requests.get_extra_value(request, "cn_preprocessor", default_control_net_module),
        "model": requests.get_extra_value(request, "cn_model", default_control_net_model),
        "enabled": True,
        "image": image_b64,
    }


def get_cn_pose_unit(request):
    pose_b64 = requests.get_pose_image(request)
    if not lib.valid_base64(pose_b64):
        return _get_cn_empty_unit()

    return {
        "module": requests.get_extra_value(request, "pose_preprocessor", default_open_pose_module),
        "model": requests.get_extra_value(request, "pose_model", default_open_pose_model),
        "enabled": True,
        "image": pose_b64,
    }


def get_cn_tile_unit(p):
    if not requests.get_extra_value(p, "scale_by_tile", False):
        return _get_cn_empty_unit()

    return {
        "module": default_tile_module,
        "model": default_tile_model,
        "enabled": True,
        "image": "",
    }


def _get_cn_empty_unit():
    return {
        "model": "none",
        "module": "none",
        "enabled": False,
        "image": "",
    }


def _to_process_unit(unit):
    if unit["enabled"]:
        unit["model"] = find_closest_cn_model_name(unit["model"])

    return external_code.ControlNetUnit(**unit)


def apply_multi_process(p: StableDiffusionProcessing):
    if not requests.multi_enabled(p):
        return
    
    # request.prompt only
    if p.prompt.find("|") == -1:
        return
    
    prompts = lib.to_multi_prompts(p.prompt)
    
    p.prompt = prompts
    p.n_iter = math.ceil(len(p.prompt) * p.batch_size)
    processing.fix_seed(p)
    p.seed = [p.seed + i for i in range(len(p.prompt))]

    requests.set_multi_count(p, len(p.prompt))
