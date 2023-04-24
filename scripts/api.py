from character.lib import log, LogLevel
from character.models import *
from character.metrics import hT2I

from fastapi import FastAPI, Request

from modules import script_callbacks
from modules.api import api
from modules.api.models import TextToImageResponse

import gradio as gr
import time

class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/character/v1/txt2img", self.character_txt2img, tags=["Character"], methods=["POST"], response_model=ImageResponse)

    @hT2I.time()
    def character_txt2img(self, request: CharacterTxt2ImgRequest):
        args = vars(request)
        lightRequest = CharacterTxt2Img(**args)
        origin_response = self.text2imgapi(lightRequest.to_full())
        return to_image_response(origin_response)

api.Api = ApiHijack

def character_api(_: gr.Blocks, app: FastAPI):
    @app.middleware("http")
    async def log_time(req: Request, call_next):
        ts = time.time()
        res: Response = await call_next(req)
        duration = str(round(time.time() - ts, 4))
        endpoint = req.scope.get('path', 'err')
        if endpoint.startswith('/character'):
            log('API {code} {prot}/{ver} {method} {endpoint} {cli} {duration}'.format(
                code = res.status_code,
                ver = req.scope.get('http_version', '0.0'),
                cli = req.scope.get('client', ('0:0.0.0', 0))[0],
                prot = req.scope.get('scheme', 'err'),
                method = req.scope.get('method', 'err'),
                endpoint = endpoint,
                duration = duration,
            ))
        return res


script_callbacks.on_app_started(character_api)

log("API loaded")
