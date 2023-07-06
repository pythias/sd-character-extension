import gradio as gr

from character import input, names
from modules import scripts
from modules.scripts import PostprocessImageArgs

class Script(scripts.Script):
    processes = []

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

        # 根据参数确定后续处理的流程
        self.processes = []

    def postprocess_image(self, p, pp: PostprocessImageArgs, *args):
        # 包括重绘、放大等操作
        pass