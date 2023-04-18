import pydantic
from character.tables import *
from character.lib import log, LogLevel
from character.nsfw import predict_image, predict_text
from character.face import detect_face_and_crop_base64

from enum import Enum
from modules.api.models import *
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List

from modules.api.models import TextToImageResponse

negative_default_prompts = "EasyNegative,worst quality,low quality"
negative_nsfw_prompts = "nsfw,naked,nude,sex,ass,pussy,loli,kids,kid,child,children,teenager,teenagers,teen,baby face,big breasts"
negative_watermark_prompts = "text,watermark,signature,artist name,artist logo"
negative_body_prompts = "zombie,extra fingers,six fingers,missing fingers,extra arms,missing arms,extra legs,missing legs,bad face,bad hair,bad hands,bad pose"

high_quality_prompts = "8k UHD,high quality,RAW"

class ImageResponse(BaseModel):
    images: List[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: str
    faces: List[str]
    nsfw: bool


def filter_response(response: TextToImageResponse):
    nsfw = False
    faces = []
    filtered_images = []
    for b64image in response.images:
        faces.extend(detect_face_and_crop_base64(b64image))
        if not predict_image(b64image):
            filtered_images.append(b64image)
            nsfw = nsfw or False
        else:
            nsfw = True

    return ImageResponse(images=filtered_images, parameters=response.parameters, info=response.info, faces=faces, nsfw=nsfw)


def simply_prompts(prompts: str):
    if not prompts:
        return ""

    prompts = prompts.split(",")
    unique_prompts = []
    [unique_prompts.append(p) for p in prompts if p not in unique_prompts]
    return ",".join(unique_prompts)

class CharacterTxt2Img:
    def __init__(self, prompt: str = "", styles: List[str] = None, seed: int = -1, sampler_name: str = "Euler a", batch_size: int = 1, steps: int = 20, cfg_scale: float = 7.0, width: int = 512, height: int = 512, restore_faces: bool = True, negative_prompt: str = "", fashions: list[str] = None, pose: str = None):
        self.prompt = prompt
        self.styles = styles
        self.seed = seed
        self.sampler_name = sampler_name
        self.batch_size = batch_size
        self.steps = steps
        self.cfg_scale = cfg_scale
        self.width = width
        self.height = height
        self.restore_faces = restore_faces
        self.negative_prompt = negative_prompt

        self.fashions = fashions
        self.pose = pose

    def to_full(self):
        args = vars(self)

        self.negative_prompt = negative_default_prompts + "," \
            + negative_nsfw_prompts + "," \
            + negative_watermark_prompts + "," \
            + negative_body_prompts + ","  \
            + self.negative_prompt

        if self.fashions and len(self.fashions) > 0:
            prompts, negative_prompts = fashion_table.get_fashion_prompts(self.fashions)
            if prompts:
                self.prompt += "," + prompts

            if negative_prompts:
                self.negative_prompt += "," + negative_prompts

            log(f"Fashions: {str(self.fashions)}, prompts: {prompts}, negative prompts: {negative_prompts}")

        pose = pose_table.get_by_name(self.pose)
        if pose:
            log(f"Use pose: {pose.name} ({pose.model})")

        self.prompt = self.prompt + "," + high_quality_prompts

        self.prompt = simply_prompts(self.prompt)
        self.negative_prompt = simply_prompts(self.negative_prompt)

        return StableDiffusionTxt2ImgProcessingAPI(
            sampler_index="",
            script_name=None,
            script_args=[],
            send_images=True,
            save_images=False,
            alwayson_scripts={},
            **args
        )


CharacterTxt2ImgRequest = PydanticModelGenerator(
    "CharacterTxt2Img",
    CharacterTxt2Img,
    [
        {"key": "sampler_name", "type": str, "default": "Euler a"},
        {"key": "fashions", "type": list, "default": []},
        {"key": "pose", "type": str, "default": None},
    ]
).generate_model()
