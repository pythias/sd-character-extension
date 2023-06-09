import gradio as gr
from httpx import request

from character import requests, lib, upscale, third_face, metrics, nsfw, errors, names, models
from modules import scripts
from modules.processing import StableDiffusionProcessing
from modules.api.api import decode_base64_to_image

from starlette.exceptions import HTTPException

class Script(scripts.Script):
    prompts_from_image = {}

    def title(self):
        return names.ExtensionI2I

    def show(self, is_img2img):
        if is_img2img:
            return scripts.AlwaysVisible
        
        return False

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]
    
    def process(self, p, *args):
        if requests.from_webui(p):
            return
        
        if nsfw.prompt_has_illegal_words(p.prompt):
            errors.raise_nsfw()
        
        image_b64 = requests.get_i2i_image(p)
        if not image_b64 or len(image_b64) < lib.min_base64_image_size:
            raise HTTPException(status_code=422, detail="Input image not found")
        
        img = decode_base64_to_image(image_b64)
        upscale.apply_i2i_upscale(p, img)

        caption = lib.clip_b64img(img, True)
        requests.update_extra(p, "prompt-caption", caption)

        models.append_prompt(p, caption)

        if nsfw.prompt_has_illegal_words(caption):
            errors.raise_nsfw()

        metrics.count_request(p)
        third_face.apply_face_repairer(p)
        requests.clear_temporary_extras(p)

        
