import gradio as gr
from httpx import request

from character import input, lib, upscale, third_face, metrics, nsfw, errors, names, models
from modules import scripts
from modules.processing import StableDiffusionProcessing
from modules.api.api import decode_base64_to_image

from starlette.exceptions import HTTPException

class Script(scripts.Script):
    def title(self):
        return names.ExNameI2I

    def show(self, is_img2img):
        if is_img2img:
            return scripts.AlwaysVisible
        
        return False

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]
    
    def before_process(self, p, *args):
        if input.from_webui(p):
            return
        
        image_b64 = input.get_i2i_image(p)
        if not image_b64 or len(image_b64) < lib.min_base64_image_size:
            raise HTTPException(status_code=422, detail="Input image not found")
        
        img = decode_base64_to_image(image_b64)
        
        metrics.count_request(p)
        third_face.apply_face_repairer(p)
        models.append_image_caption(p, img)
        models.final_prompts_before_processing(p)
