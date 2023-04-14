import pydantic
from typing import Any, Optional, Dict, List
from modules.api.models import *
from enum import Enum
from pydantic import BaseModel, Field


class FashionItem(BaseModel):
    name: str = Field(title="Name")
    description: Optional[str] = Field(title="Description")
    lora: str = Field(title="LoRA model name")


class PoseItem(BaseModel):
    name: str = Field(title="Name")
    description: Optional[str] = Field(title="Description")
    # 经过处理以后的图片，砍掉 Preprocessor 的过程
    image: str = Field(title="ControlNet Image Path")
    model: str = Field(title="ControlNet Model Name")


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

        # todo + controlnet
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
        {"key": "user_name", "type": str, "default": ""},
        {"key": "fashions", "type": list, "default": []},
        {"key": "pose", "type": str, "default": None},
    ]
).generate_model()
