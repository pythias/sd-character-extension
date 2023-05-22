import gradio as gr
from character.lib import log
from modules import shared, scripts

class Script(scripts.Script):
    def title(self):
        return "Extend Character Information"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Checkbox(label="Extend Character Information", value=True)]
    
    def process(self, p, *args):
        # todo
        p.extra_generation_params["Character"] = {
            "name": "Character",
        }

shared.opts.data.update({'control_net_no_detectmap': True})

log("Character Information Extension loaded")
