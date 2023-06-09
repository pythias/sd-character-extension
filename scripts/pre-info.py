import gradio as gr
import time

from character import requests, lib
from modules import shared, scripts
from modules.processing import Processed, program_version

class Script(scripts.Script):
    started_at = 0.0

    def title(self):
        return "Character Info"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]
    
    def process(self, p, *args):
        self.started_at = time.perf_counter()
        requests.update_extras(p, {
            "name": shared.cmd_opts.character_server_name,
            "version": lib.version_flag,
            "program_version": program_version(),
            "request_at": time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime()),
            "request_id": lib.get_request_id(),
        })

    def postprocess(self, p, processed: Processed, *args):
        elapsed = time.perf_counter() - self.started_at
        for i, info in enumerate(processed.infotexts):
            processed.infotexts[i] = f"{info}, Took {elapsed:.2f} seconds."

        for i in range(len(processed.images)):
            processed.images[i].info["parameters"] = f"{processed.images[i].info['parameters']}\nTook: {elapsed:.2f}"
