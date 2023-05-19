import gradio as gr
import numpy as np

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
        enabled = gr.Checkbox(label="Auto Upscale", value=False)
        return [enabled]

    def postprocess(self, p, processed, enabled:bool, *args):
        """
        This function is called after processing ends for AlwaysVisible scripts.
        args contains all values returned by components from ui()
        """
        if not enabled:
            return

        if "auto-upscale-processing" in p.extra_generation_params:
            lib.log(f"{upscale.NAME} already done, skipping")
            return

        hires_images = []
        seed_index = 0
        subseed_index = 0
        for i, image in enumerate(processed.images):
            lib.log(message=f"Upscaling image {i+1}/{len(processed.images)}")

            up = StableDiffusionProcessingImg2Img()

            # log type of image
            lib.log(message=f"Image type: {type(image)}")

            # PIL.Image.Image to base64
            image_base64 = shared.image_to_base64(image)

            
            up.__dict__.update(p.__dict__)
            up.extra_generation_params["auto-upscale-processing"] = True
            up.init_images = [image]
            up.batch_size = 1
            up.width, up.height = image.size
            up.do_not_save_samples = True
            up.do_not_save_grid = True
            up.denoising_strength = 0.75

            cn_script = external_code.find_cn_script(up.scripts)
            args_len = cn_script.args_to - cn_script.args_from
            args_bak = up.script_args[cn_script.args_from:cn_script.args_to]

            cn_script.args_from = 0
            cn_script.args_to = args_len

            up.scripts = scripts.ScriptRunner()
            up.scripts.alwayson_scripts = [cn_script]
            up.script_args = args_bak

            units = self.get_units(lib.encode_to_base64(image))
            external_code.update_cn_script_in_processing(up, units, is_img2img=True, is_ui=False)

            if seed_index < len(processed.all_seeds):
                up.seed = processed.all_seeds[seed_index]
                seed_index += 1
            if subseed_index < len(processed.all_subseeds):
                up.subseed = processed.all_subseeds[subseed_index]
                subseed_index += 1
            
            hires_result = process_images(up)
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