import gradio as gr

from character import requests, lib, names
from modules import scripts

class TryOnScript(scripts.Script):
    def __init__(self) -> None:
        super().__init__()
        self.__is_running = False

    def title(self):
        return names.ExtensionTryOn

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return [gr.Label(visible=False)]

    def before_process_batch(self, p, *args, **kwargs):
        if self.__is_running:
            return
        
        p.do_not_save_samples = True

        requests.update_scripts_order(p, self, -1)

    def postprocess(self, o, res, *args):
        if self.__is_running:
            return

        try:
            self.__is_running = True
            lib.log("try-on started")
            o.do_not_save_samples = False
        finally:
            self.__is_running = False
