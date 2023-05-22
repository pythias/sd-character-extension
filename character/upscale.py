from modules.api.models import StableDiffusionProcessingImg2Img, StableDiffusionProcessingTxt2Img

from character.lib import log


def apply_auto_upscale(request):
    auto_upscale = getattr(request, "character_auto_upscale", False)
    if not auto_upscale:
        return

    if isinstance(request, StableDiffusionProcessingTxt2Img):
        # 默认参数
        # todo 对用户输入的处理
        request.hr_scale = 2
        request.hr_upscaler = "Latent"
        request.denoising_strength = 0.6
        request.enable_hr = True
        return
    
    # StableDiffusionProcessingImg2Img
    if isinstance(request, StableDiffusionProcessingImg2Img):
        # todo 计算图片大小
        return


















