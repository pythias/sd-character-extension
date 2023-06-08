import gradio as gr

from character import requests, lib, upscale, face, metrics, nsfw, errors, names
from modules import scripts

class Script(scripts.Script):
    prompts_from_image = {}

    def title(self):
        return names.ExtensionT2I

    def show(self, is_img2img):
        if is_img2img:
            return False
        
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]
    
    def process(self, p, *args):
        if requests.from_webui(p):
            return

        if nsfw.prompt_has_illegal_words(p.prompt):
            errors.raise_nsfw()

        face.apply_face_repairer(p)
        upscale.apply_t2i_upscale(p)

        image_b64 = requests.get_cn_image(p)
        if not image_b64 or len(image_b64) < lib.min_base64_image_size:
            metrics.count_request(p)
            return
        
        requests.update_extra(p, "prompt-origin", p.prompt)
        caption = lib.clip_b64img(image_b64, True)
        requests.update_extra(p, "prompt-caption", caption)
        p.prompt = caption + "," + p.prompt

        if nsfw.prompt_has_illegal_words(caption):
            errors.raise_nsfw()

        metrics.count_request(p)
        
