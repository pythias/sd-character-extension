from character.lib import log, get_from_request, request_is_t2i

def apply_auto_upscale(request):
    auto_upscale = get_from_request(request, "character_auto_upscale", True)
    if not auto_upscale:
        return

    if request_is_t2i(request):
        # 默认参数
        # todo 对用户输入的处理
        request.hr_scale = get_from_request(request, "hr_scale", 2)
        request.hr_upscaler = get_from_request(request, "hr_upscaler", "Latent")
        request.denoising_strength = get_from_request(request, "denoising_strength", 0.6)
        request.enable_hr = True
        log(f"hr enabled, {request.hr_scale}x{request.hr_upscaler}, denoising_strength: {request.denoising_strength}, enable_hr: {request.enable_hr}")
        return
    
