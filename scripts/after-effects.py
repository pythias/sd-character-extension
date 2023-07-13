import gradio as gr

from character import input, names, lib

from modules import scripts
from modules.scripts import PostprocessImageArgs
from modules import postprocessing
from modules.api import api

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
        scale_by = float(input.get_extra_value(request, "scale_by", 0))
        if scale_by > 0:
            # 放大
            upscale_dict = {
                "upscale_mode": 0,
                "upscaling_resize": scale_by,
                "upscaler_1": "4x-UltraSharp",
                "image": pp.image,
            }
            result = postprocessing.run_extras(extras_mode=0, image_folder="", input_dir="", output_dir="", save_output=False, **upscale_dict)
            pp.image = api.encode_pil_to_base64(result[0][0])

            lib.log(f"upscale, scale_by:{scale_by}")
