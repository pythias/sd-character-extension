import gradio as gr

from character import requests, lib, upscale, third_face, metrics, nsfw, errors, names, models
from modules import scripts
from modules.processing import StableDiffusionProcessing

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

        upscale.apply_t2i_upscale(p)
        metrics.count_request(p)
        third_face.apply_face_repairer(p)
        
        image_b64 = requests.get_cn_image(p)
        if not image_b64 or len(image_b64) < lib.min_base64_image_size:
            return
        
        # 图片信息的处理
        caption = lib.clip_b64img(image_b64, True)
        if nsfw.prompt_has_illegal_words(caption):
            # script 退出不影响其他，所以这里就不抛异常了
            requests.set_has_illegal_words(p)
            models.final_prompts_before_processing(p)
            return
        
        requests.update_extra(p, names.ExtraImageCaption, caption)
        models.append_prompt(p, caption, True)
        models.final_prompts_before_processing(p)
