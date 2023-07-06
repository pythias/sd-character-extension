import gradio as gr
import time

from character import input, lib, names
from modules import shared, scripts
from modules.processing import Processed, program_version

class Script(scripts.Script):
    started_at = 0.0

    def title(self):
        return names.ExNameInfo

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]
    
    def before_process_batch(self, p, *args, **kwargs):
        self.started_at = time.perf_counter()
        
    def before_process(self, p, *args):
        input.update_extras(p, {
            "name": shared.cmd_opts.character_server_name,
            "version": lib.version_flag,
            "program_version": program_version(),
            "request_at": time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime()),
            "request_id": lib.get_request_id(),
        })

        input.update_scripts_order(p, self, names.ExIndexInfo)

    def postprocess(self, p, processed: Processed, *args):
        elapsed = time.perf_counter() - self.started_at
        for i, info in enumerate(processed.infotexts):
            processed.infotexts[i] = f"{info}, Elapsed: {elapsed:.3f}"

        for i in range(len(processed.images)):
            if i < len(processed.infotexts):
                info =  processed.infotexts[i]
            else:
                info = f"{processed.images[i].info['parameters']}, Elapsed: {elapsed:.3f}"
            processed.images[i].info["parameters"] = info
