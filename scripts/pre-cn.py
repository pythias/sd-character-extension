import gradio as gr

from character import models, lib
from modules import scripts

class Script(scripts.Script):
    prompts_from_image = {}

    def title(self):
        return "Character Preprocessing For ControlNet"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Checkbox(label="Character Preprocessing For ControlNet", value=True)]
    
    def process(self, p, *args):
        models.apply_controlnet(p)
