import gradio as gr

from character import input, lib, names
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
    
    def before_process(self, p, *args):
        if self.__is_running:
            return
        
        input.update_scripts_order(p, self, -2)

    def postprocess(self, o, res, *args):
        if self.__is_running:
            lib.log("try-on already started")
            return
        
        try:
            self.__is_running = True
            lib.log("try-on started")
        finally:
            self.__is_running = False
