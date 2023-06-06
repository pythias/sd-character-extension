import gradio as gr

from character import requests, lib, upscale, face, metrics, nsfw, errors
from modules import scripts
from modules.api.api import decode_base64_to_image

from starlette.exceptions import HTTPException

class Script(scripts.Script):
    prompts_from_image = {}

    def title(self):
        return "character i2i"

    def show(self, is_img2img):
        if is_img2img:
            return scripts.AlwaysVisible
        
        return False

    def ui(self, is_img2img):
        return [gr.Checkbox(label="Character I2I", value=True)]
    
    def process(self, p, *args):
        if nsfw.prompt_has_illegal_words(p.prompt):
            raise errors.ApiException(errors.code_character_nsfw, "has nsfw concept")
        
        image_b64 = requests.get_i2i_image(p)
        if not image_b64 or len(image_b64) < lib.min_base64_image_size:
            raise HTTPException(status_code=422, detail="Input image not found")
        
        img = decode_base64_to_image(image_b64)
        upscale.apply_i2i_upscale(p, img)

        requests.update_extra(p, "prompt-origin", p.prompt)
        caption = lib.clip_b64img(img, True)
        requests.update_extra(p, "prompt-caption", caption)
        p.prompt = caption + "," + p.prompt

        if nsfw.prompt_has_illegal_words(caption):
            raise errors.ApiException(errors.code_character_nsfw, "has nsfw concept")

        metrics.count_request(p)
        face.apply_face_repairer(p)

        
