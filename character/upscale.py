from character import lib

def require_upscale(request):
    return lib.get_extra_value(request, "require_upscale", True)


def apply_auto_upscale(request):
    if not require_upscale(request):
        return

    if lib.request_is_t2i(request):
        # 默认参数
        # todo 对用户输入的处理
        request.hr_scale = lib.get_request_value(request, "hr_scale", 2)
        request.hr_upscaler = lib.get_request_value(request, "hr_upscaler", "Latent")
        request.denoising_strength = lib.get_request_value(request, "denoising_strength", 0.6)
        request.enable_hr = True

        log(f"HR-ENABLED, scale: {request.hr_scale} by: {request.hr_upscaler}, denoising_strength: {request.denoising_strength}, enable_hr: {request.enable_hr}")

    