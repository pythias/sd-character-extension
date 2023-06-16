from character import models, errors, lib
from character.metrics import hT2I, hI2I, hSD

from modules.api import api
from modules.call_queue import wrap_queued_call

from fastapi.responses import JSONResponse

class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/character/v2/txt2img", self.character_v2_txt2img, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/img2img", self.character_v2_img2img, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/repaint", self.character_v2_repaint, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/expand", self.character_v2_expand, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/caption", self.character_v2_caption, tags=["Character"], methods=["POST"], response_model=models.CaptionResponse)

        lib.log("API loaded")

    @hT2I.time()
    def character_v2_txt2img(self, request: models.CharacterV2Txt2ImgRequest):
        # 由于需要控制其他script的参数，所以必须在接口层而不是 script 的生命周期中处理（顺序控制需要修改WebUI的代码）
        models.prepare_request_t2i(request)
        return self._generate(self.text2imgapi, request)


    @hI2I.time()
    def character_v2_img2img(self, request: models.CharacterV2Img2ImgRequest):
        models.prepare_request_i2i(request)
        return self._generate(self.img2imgapi, request)


    def character_v2_repaint(self, request: models.CharacterV2Txt2ImgRequest):
        models.prepare_request_t2i(request)
        return self._generate(self.text2imgapi, request)
    

    def character_v2_expand(self, request: models.CharacterV2Txt2ImgRequest):
        models.prepare_request_t2i(request)
        return self._generate(self.text2imgapi, request)


    def character_v2_caption(self, request: models.CaptionRequest):
        def caption_api(request):
            caption = lib.clip_b64img(request.image)
            return models.CaptionResponse(caption=caption)
            
        return self._queued_call(caption_api, request)


    def _generate(self, func, request):
        with hSD.time():
            response = self._queued_call(func, request)
            if isinstance(response, JSONResponse):
                return response
            
            return models.convert_response(request, response)


    def _queued_call(self, func, request):
        try:
            return wrap_queued_call(func(request))
        except errors.ApiException as e:
            return e.response()


api.Api = ApiHijack
