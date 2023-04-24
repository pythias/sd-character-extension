import torch
from diffusers.pipelines.stable_diffusion.safety_checker import StableDiffusionSafetyChecker
from transformers import AutoFeatureExtractor
from PIL import Image
import numpy as np
import base64
import io

from character.metrics import hDN

safety_model_id = "CompVis/stable-diffusion-safety-checker"
safety_feature_extractor = None
safety_checker = None


def numpy_to_pil(images):
    if images.ndim == 3:
        images = images[None, ...]
    images = (images * 255).round().astype("uint8")
    pil_images = [Image.fromarray(image) for image in images]

    return pil_images

@hDN.time()
def image_has_nsfw(base64_image):
    global safety_feature_extractor, safety_checker
    if safety_feature_extractor is None:
        safety_feature_extractor = AutoFeatureExtractor.from_pretrained( safety_model_id)
        safety_checker = StableDiffusionSafetyChecker.from_pretrained(safety_model_id)

    image = Image.open(io.BytesIO(base64.b64decode(base64_image)))
    np_image = np.array(image) / 255.0
    np_image = np.expand_dims(np_image, axis=0)
    pil_images = numpy_to_pil(np_image)

    safety_checker_input = safety_feature_extractor(pil_images, return_tensors="pt")
    checked_image, has_nsfw_concept = safety_checker(images=np_image, clip_input=safety_checker_input.pixel_values)

    if len(has_nsfw_concept) > 0:
        return has_nsfw_concept[0]
    
    return False


def tags_has_nsfw(tags):
    return False
