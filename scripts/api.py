from character import models, errors, lib, face
from character.metrics import hT2I, hI2I, hSD

from modules.api import api


class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/character/v2/txt2img", self.character_v2_txt2img, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/img2img", self.character_v2_img2img, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)

        lib.log("API loaded")

    @hT2I.time()
    def character_v2_txt2img(self, request: models.CharacterV2Txt2ImgRequest):
        # 由于需要控制其他script的参数，所以必须在接口层而不是 script 的生命周期中处理（顺序控制需要修改WebUI的代码）
        models.prepare_request_t2i(request)
        # face.apply_face_repairer(request)
        # models.apply_controlnet(request)
        return self.wrap_call(self.text2imgapi, request)

    @hI2I.time()
    def character_v2_img2img(self, request: models.CharacterV2Img2ImgRequest):
        models.prepare_request_i2i(request)
        # face.apply_face_repairer(request)
        # models.apply_controlnet(request)
        return self.wrap_call(self.img2imgapi, request)

    def wrap_call(self, processor_call, request):
        try:
            with hSD.time():
                response = processor_call(request)
            return models.convert_response(request, response)
        except errors.ApiException as e:
            return e.response()


api.Api = ApiHijack


