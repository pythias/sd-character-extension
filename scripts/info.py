import gradio as gr
from character.lib import log, version_flag
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
            "name": shared.cmd_opts.character_server_name,
            "version": version_flag,
        }

shared.opts.data.update({'control_net_no_detectmap': True})

log("Character Information Extension loaded")
