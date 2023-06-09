from character import input, lib

from modules.processing import StableDiffusionProcessingTxt2Img, StableDiffusionProcessingImg2Img
from modules.scripts import PostprocessImageArgs
from modules import postprocessing
from modules.api import api

max_size = 1536
min_size = 128

def format_size_t2i(request: StableDiffusionProcessingTxt2Img):
    scale_by = float(input.get_extra_value(request, "scale_by", 0))
    request.width, request.height = lib.limit_size(request.width, request.height, request.width / request.height, min_size, max_size)

    lib.log(f"t2i-size, scale_by:{scale_by}, request-size:{request.width}x{request.height}")

def format_size_i2i(request: StableDiffusionProcessingImg2Img):
    scale_by = float(input.get_extra_value(request, "scale_by", 0))

    img = api.decode_base64_to_image(request.init_images[0])
    
    if request.width > 0 and request.height > 0:
        request.width, request.height = lib.limit_size(request.width, request.height, request.width / request.height, min_size, max_size)
    else:
        image_width, image_height = img.size[0:2]
        request.width, request.height = lib.limit_size(image_width, image_height, image_width / image_height, min_size, max_size)

    lib.log(f"i2i-size, scale_by:{scale_by}, image-size:{img.size[0]}x{img.size[1]}, wants-size:{request.width}x{request.height}")

def run(p, pp: PostprocessImageArgs):
    scale_by = float(input.get_extra_value(p, "scale_by", 0))
    if scale_by <= 0:
        return
    
    upscale_dict = {
        "resize_mode": 0,
        "show_extras_results": False,
        "gfpgan_visibility": 0,
        "codeformer_visibility": 0,
        "codeformer_weight": 0,
        "upscaling_resize": scale_by,
        "upscaling_resize_w": 0,
        "upscaling_resize_h": 0,
        "upscaling_crop": False,
        "extras_upscaler_2_visibility": 0,
        "upscale_first": False,
        "image": pp.image,
        "extras_upscaler_1": "4x-UltraSharp",
        "extras_upscaler_2": "None",
    }

    lib.log(f"run upscale, scale_by:{scale_by}, image-size:{pp.image.size[0]}x{pp.image.size[1]}")

    result = postprocessing.run_extras(extras_mode=0, image_folder="", input_dir="", output_dir="", save_output=False, **upscale_dict)
    if len(result) > 0:
        pp.image = result[0][0]
