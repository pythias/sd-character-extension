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

    return pydantic.create_model(
        f'Character{p_api_class.__name__}',
        __base__=RequestModel,
        **fields)


field_prefix = "character_"
v1_fields = {
    f"{field_prefix}face": (bool, Field(default=True, title='With faces', description='Faces in the generated image.')),
}
v2_fields = {
    f"{field_prefix}face": (bool, Field(default=True, title='With faces', description='Faces in the generated image.')),
    f"{field_prefix}control_net": (bool, Field(default=True, title='Control Net', description='Use Control Net.')),
    f"{field_prefix}image": (str, Field(default="", title='Image', description='The image in base64 format.')),
    f"{field_prefix}fashions": (List[str], Field(default="[]", title='Fashions', description='The fashion tags to use.')),
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

        if request.get(f"{field_prefix}face"):
            image_faces = detect_face_and_crop_base64(base64_image)
            cFace.inc(len(image_faces))
            faces.extend(image_faces)

        safety_images.append(base64_image)

    if v2:
        return V2ImageResponse(images=safety_images, parameters=params, info=info, faces=faces)
    else:
        return ImageResponse(images=safety_images, parameters=params, info=response.info, faces=faces)


def merge_v2_responses(responses: List[V2ImageResponse]):
    if not responses:
        return None

    if len(responses) == 1:
        return responses[0]

    merged_response = copy.deepcopy(responses[0])
    merged_response.images = []
    merged_response.faces = []
    for response in responses:
        merged_response.images.extend(response.images)
        merged_response.faces.extend(response.faces)
        merged_response.info.seeds.extend(response.info.seeds)

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

    # todo
    # 如果存在 control_net 和 image


def remove_character_fields(request):
    params = vars(request)
    for k, v in params.items():
        if not k.startswith(field_prefix):
            continue
        delattr(request, k)


def check_fashions(request):
    if request.fashions is None:
        request.fashions = [""]
        return

    for name in request.fashions:
        if name not in fashion_table.fashions:
            raise ApiException(code_character_unknown_fashion, f"not found fashion {name}")


def apply_fashion(request, fashion):
    if fashion is None:
        return None

    prompts, negative_prompts = fashion_table.get_fashion_prompts(fashion)
    if not prompts:
        return None

    # todo 优化prompts的位置
    copied_request = copy.deepcopy(request)
    copied_request.prompt += "," + prompts
    copied_request.negative_prompt += "," + negative_prompts
    return copied_request


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

