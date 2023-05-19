import gradio as gr

from character import upscale, lib
from character.models import get_cn_empty_unit

from fastapi import FastAPI

from modules import shared, scripts, script_callbacks
from modules.processing import Processed, StableDiffusionProcessing, StableDiffusionProcessingImg2Img, process_images

from scripts import external_code

class Upscaler(scripts.Script):
    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return upscale.NAME

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        enabled = gr.Checkbox(label="Auto Upscale", value=True)
        return [enabled]

    def postprocess(self, p, processed, enabled:bool, *args):
        """
        This function is called after processing ends for AlwaysVisible scripts.
        args contains all values returned by components from ui()
        """

        lib.log(f"{upscale.NAME} postprocess, {args}")

        if not enabled:
            return

        if "auto-upscale-processing" in p.extra_generation_params:
            return

        hires_images = []
        seed_index = 0
        subseed_index = 0
        for i, image in enumerate(processed.images):
            up = StableDiffusionProcessingImg2Img()
            up.__dict__.update(p.__dict__)
            up.extra_generation_params["auto-upscale-processing"] = True
            up.init_images = [image]
            up.batch_size = 1
            up.width, up.height = image.size
            up.do_not_save_samples = True
            up.do_not_save_grid = True
            up.denoising_strength = 0.75

            cn_script = external_code.find_cn_script(up.scripts)
            up.scripts = scripts.scripts_txt2img
            up.scripts.alwayson_scripts = [cn_script]

            max_models = shared.opts.data.get("control_net_max_models_num", 1)
            up.script_args = [None] * max_models

            units = self.get_units(image)
            external_code.update_cn_script_in_processing(up, units, is_img2img=True, is_ui=False)

            if seed_index < len(processed.all_seeds):
                up.seed = processed.all_seeds[seed_index]
                seed_index += 1
            if subseed_index < len(processed.all_subseeds):
                up.subseed = processed.all_subseeds[subseed_index]
                subseed_index += 1
            
            hires_result = process_images(p)
            hires_images.append(hires_result.images[0])
        
        processed.images.extend(hires_images)

    def get_tile_unit(self, image):
        return {
            "model": "controlnet11Models_tile [39a89b25]",
            "module": "none",
            "enabled": True,
            "image": image,
        }

    def get_units(self, image):
        units = [
            self.get_tile_unit(image), 
            get_cn_empty_unit(), 
            get_cn_empty_unit()
        ]
        return [external_code.ControlNetUnit(**unit) for unit in units]

lib.log(f"{upscale.NAME} loaded")