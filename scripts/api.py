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

        # v1 仅为原始接口封装
        # v2 改变了返回值，info 从 str -> dict
        # v2 添加使用ControlNet处理图片
        # v2 添加预设场景
        self.add_api_route("/character/v1/txt2img", self.character_txt2img, tags=["Character"], methods=["POST"], response_model=ImageResponse)
        # self.add_api_route("/character/v1/img2img", self.character_img2img, tags=["Character"], methods=["POST"], response_model=ImageResponse)
        self.add_api_route("/character/v2/txt2img", self.character_v2_txt2img, tags=["Character"], methods=["POST"], response_model=V2ImageResponse)
        # self.add_api_route("/character/v2/img2img", self.character_v2_img2img, tags=["Character"], methods=["POST"], response_model=V2ImageResponse)

    @hT2I.time()
    def character_txt2img(self, request: CharacterTxt2ImgRequest):
        request_prepare(request)
        return self.wrap_call(self.text2imgapi, t2i_counting, request, False)

    @hT2I.time()
    def character_v2_txt2img(self, request: CharacterV2Txt2ImgRequest):
        request_prepare(request)

        try:
            # 获取预设场景有效性判断
            fashions = get_fashions(request)
        except ApiException as e:
            return e.response()
        
        # 如果存在control_net/image，预处理
        apply_controlnet(request)

        responses = []
        for name in fashions:
            copied_request = apply_fashion(request, name)
            response = self.wrap_call(self.text2imgapi, t2i_counting, copied_request, True)
            responses.append(response)

        return merge_v2_responses(responses)

    # @hI2I.time()
    # def character_img2img(self, request: CharacterImg2ImgRequest):
    #     request_prepare(request)
    #     return self.wrap_call(self.img2imgapi, t2i_counting, request, False)

    # @hI2I.time()
    # def character_v2_img2img(self, request: CharacterV2Img2ImgRequest):
    #     request_prepare(request)
    #     t2i_counting(request)
    #     response = self.img2imgapi(request)
    #     return convert_response(request, response, True)

    
    def wrap_call(self, processor_call, counting_call, request, v2):
        try:
            counting_call(request)
            remove_character_fields(request)
            response = processor_call(request)
            return convert_response(request, response, v2)
        except ApiException as e:
            return e.response()


api.Api = ApiHijack

def character_api(_: gr.Blocks, app: FastAPI):
    @app.middleware("http")
    async def log_time(req: Request, call_next):
        ts = time.time()
        res: Response = await call_next(req)
        duration = str(round(time.time() - ts, 4))
        endpoint = req.scope.get('path', 'err')
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
