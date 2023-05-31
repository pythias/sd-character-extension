from character import lib

def require_upscale(request):
    return lib.get_extra_value(request, "require_upscale", True)


def apply_t2i_upscale(request):
    if not require_upscale(request):
        return

    request.enable_hr = True

    lib.log(f"ENABLE-UPSCALE-t2i, scale:{request.hr_scale}, size:{lib.get_request_value(request, 'width', 512)}x{lib.get_request_value(request, 'height', 512)}, denoising:{request.denoising_strength}, scaler:{request.hr_upscaler}")


def apply_i2i_upscale(request, img):
    if not require_upscale(request):
        return

    scale_by = lib.get_extra_value(request, "scale_by", 2)
    request.width = lib.get_extra_value(request, "width", img.size[0] * scale_by)
    request.height = lib.get_extra_value(request, "height", img.size[1] * scale_by)

    if request.width > 2048 or request.height > 2048:
        if request.width > request.height:
            radio = request.width / 2048
        else:
            radio = request.height / 2048
        
        request.width = int(request.width / radio)
        request.height = int(request.height / radio)

    lib.log(f"ENABLE-UPSCALE-i2i, scale:{scale_by}, size:{request.width}x{request.height}, denoising:{request.denoising_strength}, cfg:{request.image_cfg_scale}")