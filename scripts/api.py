from character.lib import log, LogLevel
from character.models import *
from character.tables import *

from fastapi import FastAPI
from modules import script_callbacks
from modules.api import api
from modules.api.models import TextToImageResponse

import gradio as gr

class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/character/v1/txt2img", self.character_txt2img, tags=["Character"], methods=["POST"], response_model=ImageResponse)
        self.add_api_route("/character/v1/img2img", self.character_img2img, tags=["Character"], methods=["POST"], response_model=ImageResponse)

    def character_txt2img(self, request: CharacterTxt2ImgRequest):
        args = vars(request)
        lightRequest = CharacterTxt2Img(**args)
        origin_response = self.text2imgapi(lightRequest.to_full())
        return to_image_response(origin_response)

    def character_img2img(self, request: CharacterTxt2ImgRequest):
        args = vars(request)
        lightRequest = CharacterTxt2Img(**args)
        origin_response = self.text2imgapi(lightRequest.to_full())
        return to_image_response(origin_response)

api.Api = ApiHijack

def character_api(_: gr.Blocks, app: FastAPI):
    @app.get('/character/v1/status', tags=["Character"])
    def status():
        return {"online": True}

    @app.get('/character/v1/poses', tags=["Character"], response_model=List[PoseRow])
    def poses():
        return pose_table.poses

    @app.get('/character/v1/fashions', tags=["Character"], response_model=List[FashionRow])
    def fashions():
        return fashion_table.fashions


script_callbacks.on_app_started(character_api)

log("API loaded")
