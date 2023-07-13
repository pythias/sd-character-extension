import gradio as gr

from character import input, lib, upscale, third_face, metrics, nsfw, errors, names, models
from modules import scripts
from modules.processing import StableDiffusionProcessing

class Script(scripts.Script):
    def title(self):
        return names.ExNameT2I

    def show(self, is_img2img):
        if is_img2img:
            return False
        
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]
    
    def before_process(self, p, *args):
        if input.from_webui(p):
            return

        metrics.count_request(p)
        third_face.apply_face_repairer(p)

        image_b64 = input.get_t2i_image(p)
        if image_b64 and len(image_b64) >= lib.min_base64_image_size:
            models.append_image_caption(p, image_b64)
            
        models.final_prompts_before_processing(p)
