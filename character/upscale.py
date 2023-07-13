from character import input, lib
from modules.processing import StableDiffusionProcessingTxt2Img, StableDiffusionProcessingImg2Img

max_size = 1536
min_size = 128

def apply_t2i_upscale(request: StableDiffusionProcessingTxt2Img):
    scale_by = float(input.get_extra_value(request, "scale_by", 0))
    width, height = lib.limit_size(request.width, request.height, request.width / request.height, min_size, max_size)
    request.width = width
    request.height = height

    lib.log(f"ENABLE-UPSCALE, scale_by:{scale_by}, request-size:{request.width}x{request.height}")


def apply_i2i_upscale(request: StableDiffusionProcessingImg2Img, img):
    scale_by = float(input.get_extra_value(request, "scale_by", 0))

    image_width, image_height = img.size[0:2]
    
    if request.width > 0 and request.height > 0:
        # 必须同时指定width和height
        request.width, request.height = lib.limit_size(request.width, request.height, request.width / request.height, min_size, max_size)
        lib.log(f"ENABLE-UPSCALE, scale_by:{scale_by}, image-size:{image_width}x{image_height}, request-size:{request.width}x{request.height}")
    else:
        # 没有指定width和height, 以图片的大小为准
        image_radio = image_width / image_height
        request.width, request.height = lib.limit_size(image_width, image_height, image_radio, min_size, max_size)
        lib.log(f"ENABLE-UPSCALE, scale_by:{scale_by}, image-size:{image_width}x{image_height}")
