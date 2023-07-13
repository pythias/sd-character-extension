import gradio as gr

from character import input, names, lib, upscale

from modules import scripts
from modules.scripts import PostprocessImageArgs
from modules import postprocessing
from modules.api import api

class Script(scripts.Script):
    def title(self):
        return names.ExNameEffects

    def show(self, is_img2img):
        if is_img2img:
            return False
        
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]
    
    def before_process(self, p, *args):
        if input.from_webui(p):
            return

        input.update_scripts_order(p, self, names.ExIndexEffects)

    def postprocess_image(self, p, pp: PostprocessImageArgs, *args):
        upscale.run(p, pp)
        
