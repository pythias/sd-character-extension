import copy
import pydantic
import os
import sys

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

from character.tables import *
from character.lib import log, LogLevel
from character.nsfw import image_has_nsfw, tags_has_nsfw
from character.face import detect_face_and_crop_base64
from character.errors import *
from character.metrics import *
from character.translate import translate

from modules import shared
from modules.api.models import *
from modules.paths_internal import extensions_dir

negative_default_prompts = "EasyNegative,worst quality,low quality"
negative_nsfw_prompts = "nsfw,naked,nude,sex,ass,pussy,loli,kids,kid,child,children,teenager,teenagers,teen,baby face,big breasts"
negative_watermark_prompts = "text,watermark,signature,artist name,artist logo"
negative_body_prompts = "zombie,extra fingers,six fingers,missing fingers,extra arms,missing arms,extra legs,missing legs,bad face,bad hair,bad hands,bad pose"

high_quality_prompts = "8k,high quality,raw"

# 加载ControlNet
extensions_control_net_path = os.path.join(extensions_dir, "sd-webui-controlnet")
sys.path.append(extensions_control_net_path)

from scripts import external_code, global_state

# 修改 sd-webui-controlnet/scripts/global_state.py
# cn_path = os.path.join(extensions_dir, "sd-webui-controlnet")
# cn_models_dir = os.path.join(models_path, "ControlNet")
# cn_models_dir_old = os.path.join(cn_path, "models")
# default_conf = os.path.join(cn_models_dir_old, "cldm_v15.yaml")
# default_conf_adapter = os.path.join(cn_models_dir_old, "t2iadapter_sketch_sd14v1.yaml")

control_net_models = external_code.get_models(update=True)
log(f"ControlNet loaded, models: {control_net_models}")


def create_request_model(p_api_class, fields):
    class RequestModel(p_api_class):
        class Config(p_api_class.__config__):
            @staticmethod
            def schema_extra(schema: dict, _):
                props = {}
                for k, v in schema.get('properties', {}).items():
                    if not v.get('_deprecated', False):
                        props[k] = v
                    if v.get('docs_default', None) is not None:
                        v['default'] = v['docs_default']
                if props:
                    schema['properties'] = props

    return pydantic.create_model(f'Character{p_api_class.__name__}', __base__=RequestModel, **fields, **default_fields)


field_prefix = "character_"

default_fields = {
    "restore_faces": (bool, Field(default=True, title='Restore faces', description='Restore faces in the generated image.')),
    "steps": (int, Field(default=20, title='Steps', description='Number of steps.')),
    "sampler_name": (str, Field(default="Euler a", title='Sampler', description='The sampler to use.')),
}

v1_fields = {
    f"{field_prefix}face": (bool, Field(default=True, title='With faces', description='Faces in the generated image.')),
}
v2_fields = {
    f"{field_prefix}face": (bool, Field(default=True, title='With faces', description='Faces in the generated image.')),
    f"{field_prefix}image": (str, Field(default=None, title='Image', description='The image in base64 format.')),
    f"{field_prefix}fashions": (List[str], Field(default=None, title='Fashions', description='The fashion tags to use.')),
}

CharacterTxt2ImgRequest = create_request_model(StableDiffusionTxt2ImgProcessingAPI, v1_fields)
CharacterImg2ImgRequest = create_request_model(StableDiffusionImg2ImgProcessingAPI, v1_fields)
CharacterV2Txt2ImgRequest = create_request_model(StableDiffusionTxt2ImgProcessingAPI, v2_fields)
CharacterV2Img2ImgRequest = create_request_model(StableDiffusionImg2ImgProcessingAPI, v2_fields)

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


def merge_v2_responses(responses: List[V2ImageResponse]):
    if not responses:
        return None

    if len(responses) == 1:
        return responses[0]

    merged_response = copy.deepcopy(responses[0])
    merged_response.images = []
    merged_response.faces = []
    merged_response.info['all_seeds'] = []
    for response in responses:
        merged_response.images.extend(response.images)
        merged_response.faces.extend(response.faces)
        merged_response.info['all_seeds'].extend(response.info['all_seeds'])

    return merged_response


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


def get_fashions(request):
    fashions = [""]
    field_name = f"{field_prefix}fashions"
    if not hasattr(request, field_name) or not getattr(request, field_name):
        return fashions
    
    fashions = getattr(request, field_name)
    for name in fashions:
        if fashion_table.get_by_name(name) == None:
            raise ApiException(code_character_unknown_fashion, f"not found fashion {name}, fashions: {fashions}")

    return fashions

def apply_fashion(request, fashion):
    if fashion is None:
        return request

    prompts, negative_prompts = fashion_table.get_fashion_prompts(fashion)
    if not prompts:
        return request

    # todo 优化prompts的位置
    copied_request = copy.deepcopy(request)
    copied_request.prompt += "," + prompts
    copied_request.negative_prompt += "," + negative_prompts
    return copied_request


def clip_b64img(image_b64):
    from modules.api.api import decode_base64_to_image
    img = decode_base64_to_image(image_b64)
    pil_image = img.convert('RGB')
    return shared.interrogator.interrogate(pil_image)


def apply_controlnet(request):
    field_image = f"{field_prefix}image"
    if not hasattr(request, field_image) or not getattr(request, field_image):
        return

    image_b64 = getattr(request, field_image)
    caption = clip_b64img(image_b64)
    request.prompt = caption + "," + request.prompt

    log(f"image, caption: {caption}, new-prompt: {request.prompt}")

    units = [
        {
            "model": "controlnet11Models_softedge [f616a34f]",
            "module": "softedge_pidisafe",
            "image": image_b64,
            "enabled": True,
        }, 
        {
            "model": "controlnet11Models_softedge [f616a34f]",
            "module": "softedge_pidisafe",
            "enabled": False,
        }, 
        {
            "model": "controlnet11Models_softedge [f616a34f]",
            "module": "softedge_pidisafe",
            "enabled": False,
        }
    ]

    request.alwayson_scripts.update({'ControlNet': {'args': [external_code.ControlNetUnit(**unit) for unit in units]}})


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

