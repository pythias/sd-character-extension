from character import lib

def require_upscale(request):
    return lib.get_extra_value(request, "require_upscale", True)


def apply_auto_upscale(request):
    if not require_upscale(request):
        return

    if lib.request_is_t2i(request):
        # 关闭系统自带参数，使用character_extra里的参数
        request.hr_scale = lib.get_extra_value(request, "hr_scale", 2)
        request.hr_upscaler = lib.get_extra_value(request, "hr_upscaler", "Latent")
        request.denoising_strength = lib.get_extra_value(request, "denoising_strength", 0.6)
        request.enable_hr = True

        lib.log(f"ENABLE-UPSCALE-t2i, scale: {request.hr_scale}, by: {request.hr_upscaler}, size:{lib.get_request_value(request, 'width', 512)}x{lib.get_request_value(request, 'height', 512)}")
