from email.mime import image
import json
import time
import logging
from click import prompt

from pydantic import BaseModel, Field
from typing import List
from enum import Enum

from character import lib, output, requests, errors, names, third_cn, third_face
from character.metrics import cNSFW, cIllegal, cFace
from character.nsfw import image_has_illegal_words, image_nsfw_score, prompt_has_illegal_words

from modules import processing
from modules.processing import StableDiffusionProcessing
from modules.api.models import StableDiffusionTxt2ImgProcessingAPI, StableDiffusionImg2ImgProcessingAPI

negative_default_prompts = "BadDream,FastNegativeEmbedding"
high_quality_prompts = "8k,high quality,<lora:add_detail:1>"
    

class CharacterV2Txt2ImgRequest(StableDiffusionTxt2ImgProcessingAPI):
    # 大部分参数都丢 extra_generation_params 里面（默认值那种，省得定义那么多）
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler a", title='Sampler', description='The sampler to use.')
    hr_upscaler: str = Field(default="Latent", title='HR Upscaler', description='The HR upscaler to use.')
    denoising_strength: float = Field(default=0.5, title='Denoising Strength', description='The strength of the denoising.')
    character_image: str = Field(default="", title='Character Image', description='The character image in base64 format.')
    character_extra: dict = Field(default={}, title='Character Extra Params', description='Character Extra Params.')
    extra_generation_params: dict = Field(default={}, title='Extra Generation Params', description='Extra Generation Params.')


class CharacterV2Img2ImgRequest(StableDiffusionImg2ImgProcessingAPI):
    steps: int = Field(default=20, title='Steps', description='Number of steps.')
    sampler_name: str = Field(default="Euler a", title='Sampler', description='The sampler to use.')
    image_cfg_scale: float = Field(default=7.0, title='Image Scale', description='The scale of the image.')
    denoising_strength: float = Field(default=0.5, title='Denoising Strength', description='The strength of the denoising.')
    character_input_image: str = Field(default="", title='Character Input Image', description='The character input image in base64 format.')
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
    mask: str = Field(default="", title='Mask', description='The mask of the segment.')


class SegmentResponse(BaseModel):
    segments: List[SegmentItem] = Field(default=None, title="Segments", description="The segments of the image.")


def convert_response(request, response):
    params = response.parameters
    info = json.loads(response.info)

    if requests.is_debug(request):
        info["nsfw-scores"] = []
        info["nsfw-words"] = []

    # 注意中途产生的扩展信息只有info中有，request在过程很多都是复制
    if requests.has_illegal_words(info):
        info["illegal"] = True
        return errors.nsfw()

    faces = []
    source_images = response.images
    if third_face.require_face_repairer(request) and not third_face.keep_original_image(request):
        batch_size = requests.get_value(request, "batch_size", 1)
        multi_count = requests.get_multi_count(request)
        source_images = source_images[(batch_size * multi_count):]

        lib.log(f"remove original images after face repair, batch: {batch_size}, multi: {multi_count}, size:{len(response.images)} -> {len(source_images)}", logging.DEBUG)
    
    crop_face = third_face.require_face(request)

    image_urls = []
    safety_images = []
    index = 0
    for base64_image in source_images:
        image_url, image_file = output.save_image(base64_image)
        image_urls.append(image_url)
        index += 1

        if requests.is_debug(request):
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
                lib.log(f"nsfw, score: {nsfw_score}, at {index}/{len(source_images)}, file: {image_file}")
                cNSFW.inc()
                continue

            if image_has_illegal_words(base64_image):
                lib.log(f"illegal word, at {index}/{len(source_images)}, file: {image_file}")
                cIllegal.inc()
                continue

        safety_images.append(base64_image)

        if crop_face:
            # todo 脸部裁切，在高清修复脸部时有数据
            image_faces = third_face.crop(base64_image)
            cFace.inc(len(image_faces))
            faces.extend(image_faces)

    if len(safety_images) == 0:
        return errors.nsfw()

    if not requests.is_debug(request):
        params = {}

    if output.required_save(request):
        face_urls = []
        for b64 in faces:
            image_url, _ = output.save_image(b64)
            face_urls.append(image_url)

        return V2ImageResponse(images=image_urls, parameters=params, info=info, faces=face_urls)
    else:
        return V2ImageResponse(images=safety_images, parameters=params, info=info, faces=faces)


def _prepare_request(request):
    requests.extra_init(request)
    
    if request.negative_prompt is None:
        request.negative_prompt = ""

    if request.prompt is None:
        request.prompt = ""

    if prompt_has_illegal_words(request.prompt):
        errors.raise_nsfw()

    _remove_character_fields(request)


def prepare_request_i2i(request):
    _prepare_request(request)
    third_cn.apply_args(request)

    image_b64 = requests.get_i2i_image(request)
    request.init_images = [image_b64]
    _apply_multi_process(request)

def prepare_request_t2i(request):
    _prepare_request(request)
    third_cn.apply_args(request)
    _apply_multi_process(request)


def _remove_character_fields(request):
    params = vars(request)
    keys = list(params.keys())
    for key in keys:
        if not key.startswith("character_"):
            continue
        
        delattr(request, key)


def _apply_multi_process(p: StableDiffusionProcessing):
    prompts = lib.to_multi_prompts(p.prompt)
    if len(prompts) == 1:
        return
    
    processing.fix_seed(p)
    same_seed = requests.get_extra_value(p, names.ParamMultiSameSeed, False)

    p.prompt = prompts
    p.batch_size = 1
    p.n_iter = len(p.prompt)
    p.seed = [p.seed + (0 if same_seed else i) for i in range(len(p.prompt))]

    requests.set_multi_count(p, len(p.prompt))

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


def final_prompts_before_processing(p):
    p.negative_prompt = p.negative_prompt + "," + negative_default_prompts
    p.negative_prompt = lib.simply_prompts(p.negative_prompt)

    if type(p.prompt) == str:
        p.prompt = lib.simply_prompts(p.prompt + "," + high_quality_prompts)
    else:
        for i in range(len(p.prompt)):
            p.prompt[i] = lib.simply_prompts(p.prompt[i] + "," + high_quality_prompts)

    p.setup_prompts()

    requests.clear_temporary_extras(p)