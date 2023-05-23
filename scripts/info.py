import gradio as gr
import time

from character.lib import log, version_flag
from modules import shared, scripts
from modules.processing import Processed

class Script(scripts.Script):
    started_at = None

    def title(self):
        return "Extend Character Information"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Checkbox(label="Extend Character Information", value=True)]
    
    def process(self, p, *args):
        self.started_at = time.perf_counter()

        p.extra_generation_params["Character"] = {
            "name": shared.cmd_opts.character_server_name,
            "version": version_flag,
            "started_at": time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime()),
        }
    
    def postprocess(self, p, processed: Processed, *args):
        elapsed = time.perf_counter() - self.started_at
        for i, info in enumerate(processed.infotexts):
            processed.infotexts[i] = f"{info}, Took {elapsed:.2f} seconds."

        for i in range(len(processed.images)):
            processed.images[i].info["parameters"] = f"{processed.images[i].info['parameters']}, Took {elapsed:.2f} seconds."

log("Information loaded")
