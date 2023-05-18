from character.lib import log, LogLevel
from character.models import *
from character.face import apply_face_repairer
from character.metrics import hT2I, hSD, hCaption

from fastapi import FastAPI, Request

from modules import shared, script_callbacks
from modules.api import api
from modules.api.models import TextToImageResponse


class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/character/v2/txt2img", self.character_v2_txt2img, tags=["Character"], methods=["POST"], response_model=V2ImageResponse)
        self.add_api_route("/character/v2/img2img", self.character_v2_img2img, tags=["Character"], methods=["POST"], response_model=V2ImageResponse)
        self.add_api_route("/character/v2/caption", self.character_v2_caption, tags=["Character"], methods=["POST"], response_model=CaptionResponse)

    @hT2I.time()
    def character_v2_txt2img(self, request: CharacterV2Txt2ImgRequest):
        request_prepare(request)
        apply_controlnet(request)
        apply_face_repairer(request)
        return self.wrap_call(self.text2imgapi, t2i_counting, request)

    @hT2I.time()
    def character_v2_img2img(self, request: CharacterV2Img2ImgRequest):
        request_prepare(request)
        return self.wrap_call(self.img2imgapi, t2i_counting, request)

    @hCaption.time()
    def character_v2_caption(self, request: CaptionRequest):
        shared.state.begin()
        shared.state.job = 'caption'
        caption = clip_b64img(request.image)
        shared.state.end()

        return CaptionResponse(caption=caption)


    def wrap_call(self, processor_call, counting_call, request):
        try:
            counting_call(request)
            character_params = remove_character_fields(request)

            with hSD.time():
                response = processor_call(request)
            return convert_response(request, character_params, response)
        except ApiException as e:
            return e.response()


api.Api = ApiHijack

log("API loaded")
