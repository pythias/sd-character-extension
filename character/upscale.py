from character import lib, requests

max_size = 1536
min_size = 256

def require_upscale(request):
    return requests.get_extra_value(request, "require_upscale", True)


def apply_t2i_upscale(request):
    if not require_upscale(request):
        return

    # p.setup_prompts() 在 process 之后，所以需要处理一下高清时的参数
    request.enable_hr = True
    request.setup_prompts()

    request.width, request.height = lib.limit_size_max(request.width, request.height, request.width / request.height, max_size)
    lib.log(f"ENABLE-UPSCALE, scale:{request.hr_scale}, size:{request.width}x{request.height}, denoising:{request.denoising_strength}, scaler:{request.hr_upscaler}")


def apply_i2i_upscale(request, img):
    if not require_upscale(request):
        return
    
    scale_by = 2
    image_width, image_height = img.size[0:2]
    image_radio = image_width / image_height
    
    # 如果请求中extra(忽略原SD-API的)指定了width和height，则按照指定的宽高放大
    extra_width = requests.get_extra_value(request, "width", 0)
    extra_height = requests.get_extra_value(request, "height", 0)

    if extra_width > 0 and extra_height > 0:
        # 必须同时指定width和height, 管大不管小
        request.width, request.height = lib.limit_size_max(extra_width, extra_height, image_radio, max_size)
    else:
        # 默认放大图片的两倍
        scale_by = requests.get_extra_value(request, "scale_by", 2)
        target_width = image_width * scale_by
        target_height = image_height * scale_by
        request.width, request.height = lib.limit_size_max(target_width, target_height, image_radio, max_size)
        request.width, request.height = lib.limit_size_min(request.width, request.height, image_radio, min_size)

    lib.log(f"ENABLE-UPSCALE, scale:{scale_by}, in-size:{image_width}x{image_height}, set-size:{extra_width}x{extra_height}, out-size:{request.width}x{request.height}, denoising:{request.denoising_strength}, cfg:{request.image_cfg_scale}")