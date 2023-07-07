import json
import time

from copy import deepcopy
from pydantic import BaseModel, Field
from typing import List
from enum import Enum

from character import input, lib, errors, names, third_face
from character.metrics import cNSFW, cIllegal, cFace
from character.nsfw import image_has_illegal_words, image_nsfw_score, prompt_has_illegal_words

from modules import processing, shared
from modules.processing import StableDiffusionProcessing
from modules.api.models import StableDiffusionTxt2ImgProcessingAPI, StableDiffusionImg2ImgProcessingAPI
from modules.sd_models import checkpoints_list

negative_default_prompts = "BadDream,FastNegativeEmbedding"
high_quality_prompts = "8k,high quality,<lora:add_detail:1>"
    

class CharacterV2Txt2ImgRequest(StableDiffusionTxt2ImgProcessingAPI):
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler a", title='Sampler', description='The sampler to use.')
    hr_upscaler: str = Field(default="Latent", title='HR Upscaler', description='The HR upscaler to use.')
    denoising_strength: float = Field(default=0.5, title='Denoising Strength', description='The strength of the denoising.')
    character_extra: dict = Field(default={}, title='Character Extra Params', description='Character Extra Params.')
    extra_generation_params: dict = Field(default={}, title='Extra Generation Params', description='Extra Generation Params.')


class CharacterV2Img2ImgRequest(StableDiffusionImg2ImgProcessingAPI):
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler a", title='Sampler', description='The sampler to use.')
    image_cfg_scale: float = Field(default=7.0, title='Image Scale', description='The scale of the image.')
    denoising_strength: float = Field(default=0.5, title='Denoising Strength', description='The strength of the denoising.')
    character_extra: dict = Field(default={}, title='Character Extra Params', description='Character Extra Params.')
    extra_generation_params: dict = Field(default={}, title='Extra Generation Params', description='Extra Generation Params.')
    width: int = Field(default=0, title='Width', description='The width of the image.')
    height: int = Field(default=0, title='Height', description='The height of the image.')


class V2ImageResponse(BaseModel):
    images: List[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: dict
    faces: List[str]


class CaptionAlgorithm(Enum):
    DEEPBOORU = "deepbooru"
    CLIP = "clip"
    BLIP = "blip"
    WB14 = "wb14"


class CaptionRequest(BaseModel):
    image: str = Field(default="", title='Image', description='The image in base64 format.')
    algorithm: CaptionAlgorithm = Field(default=CaptionAlgorithm.DEEPBOORU, title='Algorithm', description='The algorithm to use.')


class CaptionResponse(BaseModel):
    caption: str = Field(default="", title='Caption', description='The caption of the image.')


class SegmentAlgorithm(Enum):
    UFADE20K = "ufade20k"
    OFCOCO = "ofcoco"
    OFADE20K = "ofade20k"


class SegmentRequest(BaseModel):
    image: str = Field(default="", title='Image', description='The image in base64 format.')
    algorithm: SegmentAlgorithm = Field(default=SegmentAlgorithm.OFADE20K, title='Algorithm', description='The algorithm to use.')


class SegmentItem(BaseModel):
    label: str = Field(default="", title='Label', description='The label of the segment.')
    score: float = Field(default=0.0, title='Score', description='The score of the segment.')
    color: str = Field(default="", title='Color', description='The color of the segment.')


class SegmentResponse(BaseModel):
    segments: List[SegmentItem] = Field(default=None, title="Segments", description="The segments of the image.")


def convert_response(request, response):
    info = json.loads(response.info)

    if input.is_debug(request):
        info["nsfw-scores"] = []
        info["nsfw-words"] = []

    # 注意中途产生的扩展信息只有info中有，request在过程很多都是复制
    if input.has_illegal_words(info):
        info["illegal"] = True
        return errors.nsfw()

    crop_avatar = input.required_face(request)
    require_url = input.required_save(request)
    source_images = response.images

    faces = []
    safety_images = []
    index = 0
    for base64_image in source_images:
        index += 1

        if input.is_debug(request):
            started_at = time.perf_counter()
            nsfw_score = image_nsfw_score(base64_image)
            seconds = time.perf_counter() - started_at
            lib.log(f"nsfw: {nsfw_score}, time: {seconds}, at {index}/{len(source_images)}")

            started_at = time.perf_counter()
            illegal_word = image_has_illegal_words(base64_image)
            seconds = time.perf_counter() - started_at
            lib.log(f"word: {illegal_word}, time: {seconds:.3f}, at {index}/{len(source_images)}")

            info["nsfw-scores"].append({"score": nsfw_score, "time": round(seconds, 3)})
            info["nsfw-words"].append({"word": illegal_word, "time": round(seconds, 3)})
        else:
            nsfw_score = image_nsfw_score(base64_image)
            if nsfw_score > 0.75:
                _, img_filepath = lib.save_image(base64_image)

                lib.log(f"nsfw, score: {nsfw_score}, at {index}/{len(source_images)}, image: {img_filepath}")
                cNSFW.inc()
                continue

            if image_has_illegal_words(base64_image):
                _, img_filepath = lib.save_image(base64_image)

                lib.log(f"illegal word, at {index}/{len(source_images)}, image: {img_filepath}")
                cIllegal.inc()
                continue

        # 图片
        if require_url:
            image_url, _ = lib.save_image(base64_image)
            safety_images.append(image_url)
        else:
            safety_images.append(base64_image)

        if crop_avatar:
            image_faces = third_face.crop(base64_image)
            cFace.inc(len(image_faces))

            if require_url:
                for b64 in image_faces:
                    image_url, _ = lib.save_image(b64)
                    faces.append(image_url)
            else:
                faces.extend(image_faces)

    if len(safety_images) == 0:
        return errors.nsfw()

    if input.is_debug(request):
        parameters = response.parameters
    else:
        parameters = {}

    v2_response = V2ImageResponse(images=safety_images, parameters=parameters, info=info, faces=faces)
    _log_response(v2_response)
    return v2_response


def _log_response(response: V2ImageResponse):
    response_copy = deepcopy(response)
    # del response_copy.info
    # del response_copy.parameters
    data = vars(response_copy)
    data = lib.truncate_large_value(data)
    lib.log(f"response, count: {len(response_copy.images)}/{len(response_copy.faces)}, data: {data}")


def _log_request(request):
    request_copy = deepcopy(request)
    data = vars(request_copy)
    data = lib.truncate_large_value(data)
    lib.log(f"request, data: {data}")


def prepare_request(request):
    _log_request(request)
    input.extra_init(request)
    
    if request.negative_prompt is None:
        request.negative_prompt = ""

    if request.prompt is None:
        request.prompt = ""

    if prompt_has_illegal_words(request.prompt):
        errors.raise_nsfw()

    _remove_character_fields(request)
    _apply_multi_process(request)


def prepare_for_i2i(request):
    prepare_request(request)

    image_b64 = input.get_i2i_image(request)
    request.init_images = [image_b64]


def prepare_for_t2i(request):
    prepare_request(request)
    

def _remove_character_fields(request):
    parameters = vars(request)
    keys = list(parameters.keys())
    for key in keys:
        if not key.startswith("character_"):
            continue
        
        delattr(request, key)


def _apply_multi_process(p: StableDiffusionProcessing):
    prompts = lib.to_multi_prompts(p.prompt)
    if len(prompts) == 1:
        return
    
    processing.fix_seed(p)
    same_seed = input.get_extra_value(p, names.ParamMultiSameSeed, False)

    p.prompt = prompts
    p.batch_size = 1
    p.n_iter = len(p.prompt)
    p.seed = [p.seed + (0 if same_seed else i) for i in range(len(p.prompt))]

    input.set_multi_count(p, len(p.prompt))

    lib.log(f"ENABLE-MULTIPLE, count: {len(p.prompt)}, {p.seed}, {p.subseed}")


def append_prompt(p, prompt, priority=True):
    if type(p.prompt) == str:
        if priority:
            p.prompt = prompt + "," + p.prompt
        else:
            p.prompt = p.prompt + "," + prompt
        
        return
    
    for i in range(len(p.prompt)):
        if priority:
            p.prompt[i] = p.prompt[i] + "," + prompt
        else:
            p.prompt[i] = prompt + "," + p.prompt[i]


def append_image_caption(p, img):
    if input.ignore_caption(p):
        return
    
    caption = lib.clip_b64img(img, True)
    if prompt_has_illegal_words(caption):
        input.set_has_illegal_words(p)
        return

    input.update_extra(p, names.ExtraImageCaption, caption)
    append_prompt(p, caption, True)


def final_prompts_before_processing(p):
    p.negative_prompt = p.negative_prompt + "," + negative_default_prompts
    p.negative_prompt = lib.simply_prompts(p.negative_prompt)

    if type(p.prompt) == str:
        p.prompt = lib.simply_prompts(p.prompt + "," + high_quality_prompts)
    else:
        for i in range(len(p.prompt)):
            p.prompt[i] = lib.simply_prompts(p.prompt[i] + "," + high_quality_prompts)

    p.setup_prompts()

    input.clear_temporary_extras(p)


def load_models():
    started_at = time.time()
    shared.refresh_checkpoints()
    for name in list(checkpoints_list.keys()):
        checkpoint = checkpoints_list[name]
        if checkpoint.sha256 is None:
            lib.error(f"Hashing {name}")
            sd_model_hash = checkpoint.calculate_shorthash()
            lib.log(f"Hashed {name} to {sd_model_hash}")

    lib.log(f"Checkpoints has been refreshed in {(time.time() - started_at):.3f} seconds")