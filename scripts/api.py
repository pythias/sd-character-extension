from character.lib import log, LogLevel
from character.models import *
from character.metrics import hT2I, hI2I

from fastapi import FastAPI, Request

from modules import script_callbacks
from modules.api import api
from modules.api.models import TextToImageResponse

import gradio as gr
import time

class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/character/v2/txt2img", self.character_v2_txt2img, tags=["Character"], methods=["POST"], response_model=V2ImageResponse)
        # self.add_api_route("/character/v2/img2img", self.character_v2_img2img, tags=["Character"], methods=["POST"], response_model=V2ImageResponse)

    @hT2I.time()
    def character_v2_txt2img(self, request: CharacterV2Txt2ImgRequest):
        request_prepare(request)
        apply_controlnet(request)
        return self.wrap_call(self.text2imgapi, t2i_counting, request)

    # @hI2I.time()
    # def character_v2_img2img(self, request: CharacterV2Img2ImgRequest):
    #     request_prepare(request)
    #     t2i_counting(request)
    #     response = self.img2imgapi(request)
    #     return convert_response(request, response, True)

    
    def wrap_call(self, processor_call, counting_call, request):
        try:
            counting_call(request)
            remove_character_fields(request)
            response = processor_call(request)
            return convert_response(request, response)
        except ApiException as e:
            return e.response()


api.Api = ApiHijack

def character_api(_: gr.Blocks, app: FastAPI):
    @app.middleware("http")
    async def log_time(req: Request, call_next):
        ts = time.time()
        res: Response = await call_next(req)
        duration = str(round(time.time() - ts, 4))
        
        log('API {code} {prot}/{ver} {method} {endpoint} {host} {client} {duration}'.format(
            code = res.status_code,
            ver = req.scope.get('http_version', '0.0'),
            host = req.headers.get('host', 'err'),
            client = req.scope.get('client', 'err'),
            prot = req.scope.get('scheme', 'err'),
            method = req.scope.get('method', 'err'),
            endpoint = req.scope.get('path', 'err'),
            duration = duration,
        ))
        return res


script_callbacks.on_app_started(character_api)

log("API loaded")
