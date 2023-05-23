from modules.api.models import StableDiffusionProcessingImg2Img, StableDiffusionProcessingTxt2Img

from character.lib import log, get_or_default, get_from_request
from character.models import CharacterV2Txt2ImgRequest, CharacterV2Img2ImgRequest

def apply_auto_upscale(request):
    auto_upscale = get_from_request(request, "character_auto_upscale", True)
    if not auto_upscale:
        return

    if isinstance(request, CharacterV2Txt2ImgRequest):
        # 默认参数
        # todo 对用户输入的处理
        request.hr_scale = 2
        request.hr_upscaler = "Latent"
        request.denoising_strength = 0.6
        request.enable_hr = True
        log(message=f"hr enabled, {request.hr_scale}x{request.hr_upscaler}, denoising_strength: {request.denoising_strength}, enable_hr: {request.enable_hr}")
        return
    
    # StableDiffusionProcessingImg2Img
    if isinstance(request, CharacterV2Img2ImgRequest):
        # todo 计算图片大小
        return
