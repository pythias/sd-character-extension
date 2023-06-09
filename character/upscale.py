from character import lib, requests
from modules.processing import StableDiffusionProcessingTxt2Img, StableDiffusionProcessingImg2Img

max_size = 1536
min_size = 256

def require_upscale(request):
    return requests.get_extra_value(request, "require_upscale", True)


def apply_t2i_upscale(request: StableDiffusionProcessingTxt2Img):
    if not require_upscale(request):
        return

    # p.setup_prompts() 在 process 之后，所以需要处理一下高清时的参数
    request.enable_hr = True
    request.setup_prompts()

    # 默认放大图片的两倍
    scale_by = requests.get_extra_value(request, "scale_by", 0)
    if (scale_by > 0 and scale_by < 10):
        request.hr_scale = scale_by
    
    width, height = lib.limit_size(request.width * request.hr_scale, request.height * request.hr_scale, request.width / request.height, min_size, max_size)

    # 回到放大前的尺寸
    request.width = int(width / request.hr_scale)
    request.height = int(height / request.hr_scale)

    lib.log(f"ENABLE-UPSCALE, scale:{request.hr_scale}, in:{request.width}x{request.height}, target:{width}x{height}, denoising:{request.denoising_strength}, scaler:{request.hr_upscaler}")


def apply_i2i_upscale(request: StableDiffusionProcessingImg2Img, img):
    if not require_upscale(request):
        return
    
    image_width, image_height = img.size[0:2]
    
    if request.width > 0 and request.height > 0:
        # 必须同时指定width和height, 管大不管小
        request.width, request.height = lib.limit_size(request.width, request.height, request.width / request.height, min_size, max_size)
        lib.log(f"ENABLE-UPSCALE, in-size:{image_width}x{image_height}, set-size:{request.width}x{request.height}, denoising:{request.denoising_strength}, cfg:{request.image_cfg_scale}")
    else:
        # 没有指定width和height, 以图片的大小为准
        image_radio = image_width / image_height

        # 默认放大图片的两倍
        scale_by = requests.get_extra_value(request, "scale_by", 2)
        target_width = image_width * scale_by
        target_height = image_height * scale_by
        request.width, request.height = lib.limit_size(target_width, target_height, image_radio, min_size, max_size)
        lib.log(f"ENABLE-UPSCALE, in-size:{image_width}x{image_height}, out-size:{request.width}x{request.height}, denoising:{request.denoising_strength}, cfg:{request.image_cfg_scale}")