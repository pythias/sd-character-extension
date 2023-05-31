import torch
from diffusers.pipelines.stable_diffusion.safety_checker import StableDiffusionSafetyChecker
from transformers import AutoFeatureExtractor
from PIL import Image
import numpy as np
import base64
import io
import re
import logging
import opennsfw2 as n2


from character.metrics import hDN
from character.lib import models_path, log, clip_b64img

safety_model_id = "CompVis/stable-diffusion-safety-checker"
safety_feature_extractor = None
safety_checker = None
n2_model = None

def numpy_to_pil(images):
    if images.ndim == 3:
        images = images[None, ...]
    images = (images * 255).round().astype("uint8")
    pil_images = [Image.fromarray(image) for image in images]

    return pil_images

@hDN.time()
def image_has_nsfw_v2(image_path):
    global n2_model
    if n2_model is None:
        n2_model = n2.make_open_nsfw_model(weights_path=models_path + "/open_nsfw_weights.h5")
        
    return n2.predict_image(image_path) > 0.8


@hDN.time()
def image_has_nsfw(base64_image):
    global safety_feature_extractor, safety_checker
    if safety_feature_extractor is None:
        safety_feature_extractor = AutoFeatureExtractor.from_pretrained(safety_model_id, cache_dir=models_path)
        safety_checker = StableDiffusionSafetyChecker.from_pretrained(safety_model_id, cache_dir=models_path)

    image = Image.open(io.BytesIO(base64.b64decode(base64_image)))
    np_image = np.array(image) / 255.0
    np_image = np.expand_dims(np_image, axis=0)
    pil_images = numpy_to_pil(np_image)

    safety_checker_input = safety_feature_extractor(pil_images, return_tensors="pt")
    _, has_nsfw_concept = safety_checker(images=np_image, clip_input=safety_checker_input.pixel_values)

    if len(has_nsfw_concept) > 0:
        return has_nsfw_concept[0]
    
    return False


def image_has_illegal_words(base64_image):
    """
    if captions contains "flag", "banner", "pennant",  "flags", "banners", "pennants" return True
    """
    caption = clip_b64img(base64_image)
    words = re.split(', | ', caption)

    # Defining the keywords
    keywords = ["flag", "banner", "pennant", "flags", "banners", "pennants", "map", "maps"]

    # Check if any of the keywords is in the caption
    for keyword in keywords:
        if keyword in words:
            log(f"image has illegal word, {keyword}", logging.WARN)
            return True

    return False

