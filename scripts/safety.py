import gradio as gr
import time

from character import lib
from character.lib import log, get_or_default
from character.nsfw import image_has_nsfw, image_has_illegal_words
from character.metrics import cNSFW, cIllegal

from modules import shared, scripts
from modules.processing import Processed

class Script(scripts.Script):
    started_at = None

    def title(self):
        return "Character Safety Checker"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Checkbox(label="Character On UI", value=True)]
        
    def postprocess(self, p, processed: Processed, *args):
        from_ui = get_or_default(p.extra_generation_params, "character_from_ui", True)
        if from_ui:
            return
        
        if face.require_face_repairer(request) and not face.keep_original_image(request):
            batch_size = get_or_default(request, "batch_size", 1)
            for _ in range(batch_size):
                response.images.pop()

        safety_images = []
        for i in range(len(processed.images)):
            base64_image = processed.images[i]
            if image_has_nsfw(base64_image):
                cNSFW.inc()
                continue

            if image_has_illegal_words(base64_image):
                cIllegal.inc()
                continue

            safety_images.append(base64_image)
        
        processed.images = safety_images

log("Safety loaded")
