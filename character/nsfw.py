from PIL import Image
import numpy as np
import re
import logging
import opennsfw2 as n2
import tensorflow as tf
import time

from modules.api.api import decode_base64_to_image

from character.metrics import hDN
from character.lib import models_path, log, clip_b64img

safety_model_id = "CompVis/stable-diffusion-safety-checker"
safety_feature_extractor = None
safety_checker = None
n2_model = None
cpu_device = '/cpu:0'
cpu_all = "cpu"


@hDN.time()
def image_nsfw_score(base64_image):
    with tf.device(cpu_all):
        try:
            global n2_model
            if n2_model is None:
                started_at = time.time()
                n2_model = n2.make_open_nsfw_model(weights_path=models_path + "/open_nsfw_weights.h5")
                log(f"nsfw model loaded in {(time.time() - started_at):.3f} seconds")

            pil_image = decode_base64_to_image(base64_image)
            n2_image = n2.preprocess_image(pil_image)
            n2_image = np.expand_dims(n2_image, 0)
            n2_image = n2_model(n2_image).numpy()
            nsfw_probability = float(n2_image[0][1])
            return nsfw_probability
        except Exception as e:
            log(f"image_nsfw_score error: {e}", logging.ERROR)
            return False


def image_has_illegal_words(base64_image):
    """
    if captions contains "flag", "banner", "pennant",  "flags", "banners", "pennants" return True
    """
    caption = clip_b64img(base64_image)
    return prompt_has_illegal_words(caption)


def prompt_has_illegal_words(prompt):
    """
    if prompt contains "flag", "banner", "pennant",  "flags", "banners", "pennants" return True
    """
    if type(prompt) == str:
        prompts = [prompt]
    else:
        prompts = prompt

    for prompt in prompts:
        words = re.split(', | ', prompt)

        # Defining the keywords
        keywords = ["flag", "banner", "pennant", "flags", "banners", "pennants", "map", "maps"]

        # Check if any of the keywords is in the caption
        for keyword in keywords:
            if keyword in words:
                log(f"image has illegal word, {keyword}", logging.WARN)
                return keyword

    return False

