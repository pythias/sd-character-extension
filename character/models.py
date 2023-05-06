import copy
import pydantic
import os
import sys
import json

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

from character.lib import log, LogLevel
from character.nsfw import image_has_nsfw, tags_has_nsfw
from character.face import detect_face_and_crop_base64
from character.errors import *
from character.metrics import *
from character.translate import translate

from modules import shared, images
from modules.api.models import *
from modules.paths_internal import extensions_dir

negative_default_prompts = "EasyNegative,worst quality,low quality"
negative_nsfw_prompts = "nsfw,naked,nude,sex,ass,pussy,loli,kids,kid,child,children,teenager,teenagers,teen,baby face,big breasts"
negative_watermark_prompts = "text,watermark,signature,artist name,artist logo"
negative_body_prompts = "zombie,extra fingers,six fingers,missing fingers,extra arms,missing arms,extra legs,missing legs,bad face,bad hair,bad hands,bad pose"

high_quality_prompts = "4k,8k,high quality"

# 加载ControlNet
# 注意，需要修改 sd-webui-controlnet/scripts/global_state.py
extensions_control_net_path = os.path.join(extensions_dir, "sd-webui-controlnet")
sys.path.append(extensions_control_net_path)

from scripts import external_code, global_state
control_net_models = external_code.get_models(update=True)
log(f"ControlNet loaded, models: {control_net_models}")

# todo load from config
default_control_net_model = "controlnet11Models_softedge [f616a34f]"
default_control_net_module = "softedge_pidisafe"
default_open_pose_model = "controlnet11Models_openpose [73c2b67d]"
default_open_pose_module = "openpose_full"

field_prefix = "character_"

class CharacterDefaultProcessing(StableDiffusionTxt2ImgProcessingAPI):
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler a", title='Sampler', description='The sampler to use.')
    character_face: bool = Field(default=True, title='With faces', description='Faces in the generated image.')


class CharacterTxt2ImgRequest(CharacterDefaultProcessing):
    pass


class CharacterV2Txt2ImgRequest(CharacterDefaultProcessing):
    character_image: str = Field(default="", title='Image', description='The image in base64 format.')
    character_pose: str = Field(default="", title='Pose', description='The pose of the character.')


class ImageResponse(BaseModel):
    images: List[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: str
    faces: List[str]


class V2ImageResponse(BaseModel):
    images: List[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: dict
    faces: List[str]


def convert_response(request, response, v2):
    params = response.parameters
    info = json.loads(response.info)

    faces = []
    safety_images = []
    for base64_image in response.images:
        if image_has_nsfw(base64_image):
            cNSFW.inc()
            return ApiException(code_character_nsfw, f"has nsfw concept, info:{info}").response()

        field_name = f"{field_prefix}face"
        if hasattr(request, field_name) and getattr(request, field_name):
            image_faces = detect_face_and_crop_base64(base64_image)
            log(f"got {len(image_faces)} faces, prompt: {request.prompt}")

            cFace.inc(len(image_faces))
            faces.extend(image_faces)

        safety_images.append(base64_image)

    if v2:
        return V2ImageResponse(images=safety_images, parameters=params, info=info, faces=faces)
    
    return ImageResponse(images=safety_images, parameters=params, info=response.info, faces=faces)


def simply_prompts(prompts: str):
    if not prompts:
        return ""

    prompts = prompts.split(",")
    unique_prompts = []
    [unique_prompts.append(p) for p in prompts if p not in unique_prompts]
    return ",".join(unique_prompts)


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

    request.prompt = translate(request.prompt) + "," + high_quality_prompts
    request.prompt = simply_prompts(request.prompt)
    request.negative_prompt = simply_prompts(request.negative_prompt)


def remove_character_fields(request):
    params = vars(request)
    keys = list(params.keys())
    for key in keys:
        if not key.startswith(field_prefix):
            continue

        delattr(request, key)


def clip_b64img(image_b64):
    from modules.api.api import decode_base64_to_image
    img = decode_base64_to_image(image_b64)
    pil_image = img.convert('RGB')
    return shared.interrogator.interrogate(pil_image)


def resize_b64img(image_b64):
    MAX_SIZE = (1024, 1024)
    pass


def apply_controlnet(request):
    field_image = f"{field_prefix}image"
    if not hasattr(request, field_image):
        return

    image_b64 = getattr(request, field_image)
    if not image_b64 or len(image_b64) < 100:
        return

    # append image caption to prompt
    caption = clip_b64img(image_b64)
    request.prompt = caption + "," + request.prompt
    log(f"image, caption: {caption}, new-prompt: {request.prompt}")

    units = [
        get_control_net_unit_0(request, image_b64), 
        get_control_net_unit_1(request), 
        get_control_net_unit_2(request)
    ]

    request.alwayson_scripts.update({'ControlNet': {'args': [external_code.ControlNetUnit(**unit) for unit in units]}})


def get_control_net_unit_0(request, image_b64):
    model = default_control_net_model
    module = default_control_net_module

    if hasattr(request, f"{field_prefix}model"):
        model = getattr(request, f"{field_prefix}model")

    if hasattr(request, f"{field_prefix}module"):
        module = getattr(request, f"{field_prefix}module")

    return {
        "model": model,
        "module": module,
        "enabled": True,
        "image": image_b64,
    }


def get_control_net_unit_1(request):
    field = f"{field_prefix}pose"
    pose_b64 = ""
    if hasattr(request, field):
        pose_b64 = getattr(request, getattr(request, field))
        log(f"image with pose")

    return {
        "model": default_open_pose_model,
        "module": default_open_pose_module,
        "enabled": pose_b64 and len(pose_b64) > 1,
        "image": pose_b64,
    }


def get_control_net_unit_2(request):
    return {
        "model": default_control_net_model,
        "module": default_control_net_module,
        "enabled": False,
        "image": "",
    }


def t2i_counting(request):
    cT2I.inc()
    cT2IImages.inc(request.batch_size)
    params_counting(request)


def i2i_counting(request):
    cI2I.inc()
    cI2IImages.inc(request.batch_size)
    params_counting(request)


def params_counting(request):
    cPrompts.inc(request.prompt.count(",") + 1)
    cNegativePrompts.inc(request.negative_prompt.count(",") + 1)
    cLoras.inc(request.prompt.count("<"))
    cSteps.inc(request.steps)
    cPixels.inc(request.width * request.height)


log("Loading blip models...")
shared.interrogator.load()
shared.interrogator.unload()
log("Blip loaded")

