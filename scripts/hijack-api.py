from character import input, models, errors, lib, third_segments, third_cn, third_age
from character.metrics import hT2I, hI2I, hSD

from modules.api import api
from modules import shared

from fastapi.responses import JSONResponse

import traceback

class ApiHijack(api.Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/character/v2/txt2img", self.character_v2_txt2img, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/img2img", self.character_v2_img2img, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/repaint_segments", self.character_v2_repaint_segments, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/repaint_background", self.character_v2_repaint_background, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/expand", self.character_v2_expand, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/caption", self.character_v2_caption, tags=["Character"], methods=["POST"], response_model=models.CaptionResponse)
        self.add_api_route("/character/v2/segment", self.character_v2_segment, tags=["Character"], methods=["POST"], response_model=models.SegmentResponse)
        self.add_api_route("/character/v2/tryon", self.character_v2_tryon, tags=["Character"], methods=["POST"], response_model=models.V2ImageResponse)
        self.add_api_route("/character/v2/age", self.character_v2_age, tags=["Character"], methods=["POST"], response_model=models.AgeResponse)
        self.add_api_route("/character/v2/i2v", self.character_v2_video, tags=["Character"], methods=["POST"], response_model=models.I2VResponse)

        lib.log("API loaded")

    @hT2I.time()
    def character_v2_txt2img(self, request: models.CharacterV2Txt2ImgRequest):
        # 由于需要控制其他script的参数，所以必须在接口层而不是 script 的生命周期中处理（顺序控制需要修改WebUI的代码）
        models.prepare_for_t2i(request)

        # 为避免循环引用，把third_cn放出来
        # 由于无法确定ControlNet生命是否会有变更，所以每次请求都在入口层做参数初始化
        # 带来的问题就是有些GPU的过程可能会在没有锁的情况下执行，但是再加一层锁会有死锁的问题
        third_cn.apply_args(request)
        return self._generate(self.text2imgapi, request)


    @hI2I.time()
    def character_v2_img2img(self, request: models.CharacterV2Img2ImgRequest):
        models.prepare_for_i2i(request)
        third_cn.apply_args(request)
        return self._generate(self.img2imgapi, request)


    def character_v2_repaint_segments(self, request: models.CharacterV2Img2ImgRequest):
        third_segments.prepare_for_segments(request)
        return self._generate(self.img2imgapi, request)


    def character_v2_repaint_background(self, request: models.CharacterV2Img2ImgRequest):
        third_segments.prepare_for_background(request)
        return self._generate(self.img2imgapi, request)
    

    def character_v2_expand(self, request: models.CharacterV2Img2ImgRequest):
        models.prepare_for_i2i(request)
        return self._generate(self.img2imgapi, request)
    

    def character_v2_tryon(self, request: models.CharacterV2Img2ImgRequest):
        models.prepare_for_i2i(request)
        return self._generate(self.img2imgapi, request)


    def character_v2_caption(self, request: models.CaptionRequest):
        def f(request: models.CaptionRequest):
            if request.algorithm == models.CaptionAlgorithm.DEEPBOORU:
                caption = lib.deepbooru_b64img(request.image)
            elif request.algorithm == models.CaptionAlgorithm.CLIP or request.algorithm == models.CaptionAlgorithm.BLIP:
                caption = lib.clip_b64img(request.image)
            else:
                caption = lib.wb14_b64img(request.image)
            return models.CaptionResponse(caption=caption)

        return self._api_call(f, request)


    def character_v2_segment(self, request: models.SegmentRequest):
        def f(request: models.SegmentRequest):
            segments = third_segments.segment(request.image, request.algorithm, mask_color=[1, 1, 1])
            return models.SegmentResponse(segments=third_segments.to_items(segments))

        return self._queued_call(f, request)


    def character_v2_age(self, request: models.AgeRequest):
        def f(request: models.AgeRequest):
            age = third_age.get_age(request.image)
            return models.AgeResponse(age=age)

        return self._api_call(f, request)
    

    def character_v2_video(self, request: models.CharacterV2Img2ImgRequest):
        models.prepare_for_i2v(request)
        response = self._api_call(self.img2imgapi, request)
        if isinstance(response, JSONResponse):
            return response

        return models.to_video(request, response)


    def _generate(self, func, request):
        with hSD.time():
            response = self._api_call(func, request)
            if isinstance(response, JSONResponse):
                return response
            
            return models.convert_response(request, response)


    def _api_call(self, func, request):
        try:
            return func(request)
        except errors.ApiException as e:
            if input.is_debug(request):
                traceback.print_exc()
            return e.response()
        except Exception as e:
            if input.is_debug(request):
                traceback.print_exc()
                return errors.ApiException(errors.code_error, message=vars(e).get('detail', '')).response()
            else:
                return errors.ApiException.fromException(e).response()
        

    def _queued_call(self, func, request):
        with self.queue_lock:
            return self._api_call(func, request)
        

api.Api = ApiHijack
