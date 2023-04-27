import pydantic
from character.tables import *
from character.lib import log, LogLevel
from character.nsfw import image_has_nsfw, tags_has_nsfw
from character.face import detect_face_and_crop_base64
from character.errors import *
from character.metrics import *
from character.translate import translate

from enum import Enum
from modules.api.models import *
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

from modules import shared
from modules.api.models import TextToImageResponse

import copy

negative_default_prompts = "EasyNegative,worst quality,low quality"
negative_nsfw_prompts = "nsfw,naked,nude,sex,ass,pussy,loli,kids,kid,child,children,teenager,teenagers,teen,baby face,big breasts"
negative_watermark_prompts = "text,watermark,signature,artist name,artist logo"
negative_body_prompts = "zombie,extra fingers,six fingers,missing fingers,extra arms,missing arms,extra legs,missing legs,bad face,bad hair,bad hands,bad pose"

high_quality_prompts = "8k,high quality,raw"


def create_request_model(p_api_class):
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

    return pydantic.create_model(
        f'Character{p_api_class.__name__}',
        __base__=RequestModel,
        **c2i_fields)


field_prefix = "character_"
c2i_fields = {
    f"{field_prefix}fashions": (List[str], Field(default="[]", title='Fashions', description='The fashion tags to use.')),
}

CharacterTxt2ImgRequest = create_request_model(StableDiffusionTxt2ImgProcessingAPI)

class ImageResponse(BaseModel):
    images: List[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: str
    faces: List[str]


def to_image_response(response: TextToImageResponse):
    params = response.parameters
    info = json.loads(response.info)

    faces = []
    safety_images = []
    for base64_image in response.images:
        if image_has_nsfw(base64_image):
            cT2INSFW.inc()
            return ApiException(code_character_nsfw, f"has nsfw concept, info:{info}").response()

        image_faces = detect_face_and_crop_base64(base64_image)
        faces.extend(image_faces)
        safety_images.append(base64_image)

    cT2ISuccess.inc()
    return ImageResponse(images=safety_images, parameters=params, info=response.info, faces=faces)


def simply_prompts(prompts: str):
    if not prompts:
        return ""

    prompts = prompts.split(",")
    unique_prompts = []
    [unique_prompts.append(p) for p in prompts if p not in unique_prompts]
    return ",".join(unique_prompts)


def t2i_prepare(request: CharacterTxt2ImgRequest):
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

    counting_request(request)
    remove_character_fields(request)


def remove_character_fields(request: CharacterTxt2ImgRequest):
    for k, v in c2i_fields.items():
        delattr(request, k)


def apply_fashion(request: CharacterTxt2ImgRequest, fashion: str):
    if fashion is None:
        return

    # todo 每个样式一张图
    # todo 每个动作一张图

    prompts, negative_prompts = fashion_table.get_fashion_prompts(fashion)
    if not prompts:
        return

    request.prompt += "," + prompts
    request.negative_prompt += "," + negative_prompts


def counting_request(request: CharacterTxt2ImgRequest):
    cT2I.inc()
    cT2IImages.inc(request.batch_size)
    cT2IPrompts.inc(request.prompt.count(",") + 1)
    cT2INegativePrompts.inc(request.negative_prompt.count(",") + 1)
    cT2ILoras.inc(request.prompt.count("<"))
    cT2ISteps.inc(request.steps)
    cT2IPixels.inc(request.width * request.height)

