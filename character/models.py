import pydantic
from character.tables import *
from enum import Enum
from modules.api.models import *
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List


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

        if self.fashions and len(self.fashions) > 0:
            log("Fashions: " + str(self.fashions))
            fashion_tags = fashion_table.get_fashion_tags(self.fashions)
            if len(fashion_tags) > 0:
                self.prompt += " " + " ".join(fashion_tags)

        if self.pose:
            pose = pose_table.poses.get(self.pose)
            if pose:
                log(f"Use pose: {pose.name} ({pose.model})")

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
